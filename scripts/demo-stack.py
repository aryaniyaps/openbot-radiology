#!/usr/bin/env python3
"""Operate the named KVM hospital, never the superseded host Compose stack."""
import argparse,pathlib,subprocess,json,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('action',choices=['status','start','backup','restore-check','provision']);a=p.parse_args()
if a.action=='status':cmd=['python3',str(ROOT/'scripts/operations/status.py')]
elif a.action=='start':cmd=['sudo','-n','virsh','start','kauvery-hospital']
elif a.action=='backup':cmd=['sudo','-n','systemctl','start','kauvery-backup.service']
elif a.action=='restore-check':cmd=['sudo','-n','python3',str(ROOT/'scripts/operations/restore-check.py')]
else:cmd=['python3',str(ROOT/'scripts/server/provision-workstations.py')]
raise SystemExit(subprocess.run(cmd,cwd=ROOT).returncode)
