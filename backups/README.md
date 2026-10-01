# IT and doctor workspace backups

The current backup receipts are in [workspace-backup-refresh.json](../docs/evidence/hospital-deployment/workspace-backup-refresh.json).

| Workspace | Backup | Verified recovery coverage |
|---|---|---|
| Doctor | Encrypted `kauvery-hospital` Restic snapshot | Native profiles, automatic-review permissions, history database, provider authentication, six browser preference sets, workstation data and hospital disk |
| IT | Encrypted `radiology-it` Restic snapshot | Gateway configuration and credentials, doctor client assets, monitoring database, operator state, deployment kit and IT domain definition |
| Portable doctor setup | [openmausbot.backup.json](openmausbot.backup.json) | Six native profiles with empty case threads; no historical case messages or credentials |

The private snapshots live in `/var/backups/kauvery-hospital/restic`. Their root-only recovery key is `/var/lib/kauvery-hospital/backup/restic-password`. Neither belongs in Git. Restore checks compare actual decrypted configuration and history data; the latest refresh did not boot a full restored hospital VM. No external backup replica is configured.

Import the portable doctor export through native OpenMausBot team import. Native v1 import omits models, enabled skills, browser connections and permission grants. Follow [workspace setup](../config/openmausbot/README.md), including the separate [routine permission policy](../config/openmausbot/routine-permissions.json). IT setup and recovery use the operator-owned deployment kit described in [the deployment guide](../docs/HOSPITAL-DEPLOYMENT.md).

The operational snapshots include the current checkout's deployment code and reports. Large benchmark weights, downloaded research inputs and raw traces are excluded from that operational backup and retained locally. Clinical workspace data remains in the encrypted snapshots.
