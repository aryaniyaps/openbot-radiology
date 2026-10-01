#!/usr/bin/env python3
"""Create the named separate IT guest without touching the hospital VM."""
import argparse, json, os, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
def run(*args):
    subprocess.run(list(args), check=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base-image', type=pathlib.Path, required=True)
    a = p.parse_args()
    assert os.geteuid() == 0, 'Run under the operator administrator account'
    private = ROOT / '.private/hospital-it'
    private.mkdir(parents=True, exist_ok=True); private.chmod(0o700)
    disk = pathlib.Path('/var/lib/libvirt/images/kauvery-it')
    assert not disk.exists(), 'Existing IT guest storage is protected against overwrite'
    assert subprocess.run(['virsh','dominfo','kauvery-it'], capture_output=True).returncode != 0
    run('ssh-keygen','-q','-t','ed25519','-N','','-f',str(private/'operator-key'))
    key = (private/'operator-key.pub').read_text().strip()
    # JSON is valid YAML, so cloud-config values cannot acquire shell syntax.
    config = {'hostname':'kauvery-it','manage_etc_hosts':True,'ssh_pwauth':False,
        'users':[{'name':'operator','primary_group':'operator','groups':['sudo'],'shell':'/bin/bash',
            'sudo':['ALL=(ALL) NOPASSWD:ALL'],'lock_passwd':True,'ssh_authorized_keys':[key]}],
        'package_update':True,'packages':['nginx','qemu-guest-agent','python3'],
        'runcmd':[['systemctl','enable','--now','qemu-guest-agent']]}
    (private/'user-data').write_text('#cloud-config\n'+json.dumps(config,indent=2))
    (private/'meta-data').write_text('instance-id: kauvery-it-20261001\nlocal-hostname: kauvery-it\n')
    disk.mkdir(mode=0o750)
    run('qemu-img','convert','-O','qcow2',str(a.base_image),str(disk/'server.qcow2'))
    run('qemu-img','resize',str(disk/'server.qcow2'),'10G')
    run('cloud-localds',str(disk/'seed.iso'),str(private/'user-data'),str(private/'meta-data'))
    run('chown','-R','libvirt-qemu:kvm',str(disk))
    run('virsh','net-update','kauvery-hospital','add-last','ip-dhcp-host',
        "<host mac='52:54:00:ca:00:11' name='kauvery-it' ip='192.168.178.11'/>",'--live','--config')
    run('virt-install','--name','kauvery-it','--memory','2048','--vcpus','2','--import',
        '--os-variant','ubuntu24.04','--disk',f'path={disk}/server.qcow2,format=qcow2,bus=virtio',
        '--disk',f'path={disk}/seed.iso,device=cdrom','--network',
        'network=kauvery-hospital,mac=52:54:00:ca:00:11,model=virtio','--graphics','none',
        '--noautoconsole')
    run('virsh','autostart','kauvery-it')
    (private/'guest.json').write_text(json.dumps({'name':'kauvery-it','ip':'192.168.178.11',
        'memory_mib':2048,'vcpus':2,'disk_virtual_gib':10,'hospital_vm_preserved':True},indent=2)+'\n')

if __name__ == '__main__': main()
