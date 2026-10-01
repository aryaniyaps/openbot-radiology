# Hospital practice deployment

The doctor client and IT management server are running on this machine. They use the existing native OpenMausBot application and hospital systems. This is a synthetic practice environment for exercising the physician workflow; it has not been qualified for live patient care.

## Start as a doctor

1. Open **Radiology Assistant** in the application launcher, or [the doctor worklist](https://doctor.radiology.demo/worklist/).
2. Read `.private/HOSPITAL-DEMO-ACCESS.txt` for the doctor gateway and hospital-record logins. The IT login is separate. Credentials are intentionally excluded from Git.
3. Choose a case. Open **Patient record** and **Review images** to verify the patient, accession and full supplied study.
4. Inspect the visible assistant image packet and its coverage limits, then choose **Prepare this case**. A new native Clinical Assistant conversation opens. Teammate handoffs use automatic permission review. The assistant reads the assigned packet, obtains a real independent image read and report check, and returns a provisional report.
5. Review and edit the proposal against the full images. Open **Write / save report**, expand the order, enter the reviewed text in **Radiology Notes**, and choose **Save**. Reload to confirm it persisted. Saving this practice note does not demonstrate electronic signing or release.

Keep one case active at a time. The client refuses to replace a working coordinator conversation. Closing the assistant tab does not cancel native work. Use the native conversation controls if you need to stop your own case.

| Case | Patient | Accession | Supplied study | Assistant packet |
|---|---|---|---|---|
| DX | PRACTICE001 · Dev Shah | ORD-22 | 1 AP chest image | 1 display view |
| CT | PRACTICE002 · Arun Kumar | ORD-23 | 241 instances | 16 positions, lung and mediastinal windows |
| MRI | PRACTICE003 · Vikram Rao | ORD-24 | 95 instances in 3 series | 16/19 T2, 16/19 ADC, 16/57 diffusion |
| Ultrasound | PRACTICE004 · Rahul Mehta | ORD-25 | 1 object, 227 spatial frames | 16 spatial frames; not temporal cine |
| Mammography | PRACTICE005 · Asha Iyer | ORD-26 | 4 source views | 4 resized display views |

Demographics and orders are synthetic. Images are deidentified public TCIA data with source dates that can differ substantially from the current practice encounter. No indication or symptom history was added. The assistant must disclose missing history, sampled coverage and uncertainty. [Packet credits and limits](../config/doctor/packets/README.md) identify the public collections.

## IT ownership

Open [IT operations](https://it.radiology.demo/operations/) to view availability, image archive counts, role/model configuration, working/waiting status, disk reserve and session-expiry alerts. **Manage OpenMausBot** opens the native administrator interface for configuration. Doctors cannot mutate models, SOULs, profiles, permanent approvals or administrator sessions through their gateway.

All six roles use native **Approve for me** (`approvalMode: auto`), with the existing explicit teammate lists and read-only clinical sessions. The provider reviews tool requests automatically; this retains its sandbox and denial rules. Clinical decisions, identity discrepancies and essential missing clinical information go to the doctor. Record writes, signing, release and orders remain in the doctor's separate session; technical configuration belongs to IT. A provider or access failure can still require operator intervention. The policy is in `config/openmausbot/routine-permissions.json`; while the team is idle, install it with `sudo -n python3 scripts/operations/apply-routine-permissions.py --apply`. Existing active and unarchived internal handoff threads are updated without deleting history.

| System | Actual location | Responsibility |
|---|---|---|
| IT management | `kauvery-it`, 192.168.178.11, 2 vCPU / 2 GiB / 10 GiB virtual disk | TLS gateway, doctor assets, native management gateway, monitoring |
| Hospital | `kauvery-hospital`, 192.168.178.10, 8 vCPU / 12 GiB | Bahmni/OpenMRS, DCM4CHEE worklist/archive, OHIF and Weasis |
| Native execution | Existing restricted `kauvery-demo` host account and six rootless workstations | OpenMausBot 0.1.91, actual Sol/Astra execution, history and provider login |
| Doctor boundary | Host system service, `127.0.0.1:8798` | Additional execution-setting and permanent-permission restrictions |

The separate IT guest reaches the existing native host over an SSH tunnel restricted to two loopback endpoints. The guest exposes only the authenticated TLS origins on its private bridge address. This host resolves the demo names and trusts the hospital CA; another workstation requires equivalent DNS/hosts routing and CA trust. No external LAN exposure is configured by this deployment.

Clinical Assistant, Case Prep, Report Draft and Workflow Steward use `gpt-6.1-sol`. Image Assistant and Report Check use `gpt-6-astra`. The current benchmark and its limitations remain in [the evaluation PDF](../output/pdf/Radiology-Frontier-Model-Evaluation.pdf). Availability and a successful workflow do not establish diagnostic reliability or measured physician time savings.

Telemetry stores operational samples only, every 20 seconds for 30 days: service availability, counts, role/model settings and busy/waiting status. It does not persist patient messages, prompts, images or case titles. Native clinical history itself remains in the existing OpenMausBot workspace.

## Maintenance and recovery

The stable operator kit is `/opt/radiology-deployment`; private operator state is `/var/lib/radiology-deployment/operator` (root only). The checkout's `.private/hospital-it` points to that state. Never publish either private location. Native backend data remains under the existing execution account; moving this checkout does not move or erase the native workspace.

- Host doctor boundary: `sudo systemctl status openmausbot-doctor-workspace`.
- IT guest services: `radiology-tunnel`, `radiology-observability`, `nginx`. Use the pinned operator key and known-hosts file in the private operator state for SSH.
- Guest monitoring history: `/var/lib/radiology-it/telemetry.sqlite`.
- Host gateway renewal: `radiology-it-session-renewal.timer`, daily 04:00. It renews within 14 days of native expiry, defers during active case work, installs replacements, then revokes old gateway sessions. To renew deliberately while idle: `sudo python3 /opt/radiology-deployment/scripts/operations/deploy-it-services.py --renew-now`.
- Host IT configuration backup: `radiology-it-backup.timer`, daily 04:30. Run `sudo python3 /opt/radiology-deployment/scripts/operations/backup-it-server.py` for an encrypted configuration backup with an exact-bundle and SQLite restore check. The separately scheduled hospital backup covers the hospital disk and existing native workstation data.
- Both KVM guests are persistent and configured to autostart. The native backend is preserved during IT maintenance.
- TLS certificates are valid for 180 days from issuance. They use the existing private hospital CA. Gateway maintenance reissues the certificate when less than 30 days remain, using the existing private hospital CA. The IT dashboard alerts within 21 days; do not disable certificate verification. Basic-auth doctor/IT passwords are operator-managed demo credentials and are not automatically rotated with native sessions.

Encrypted snapshots are stored in `/var/backups/kauvery-hospital/restic`, with the root-only password file `/var/lib/kauvery-hospital/backup/restic-password`. Keep an independent copy of both the backup repository and its recovery key off this machine for disaster recovery. No external replica is configured. Configuration restore checks do not claim a full rebuilt-hardware recovery rehearsal.

## Verified boundary

See [deployment evidence](evidence/hospital-deployment/). The evidence distinguishes native GUI workflow, assigned-packet workflow, physician-role save/reload, access controls, five rendered modality viewers, backup restore and IT recovery. Failed attempts and changes are preserved in [the implementation record](evidence/hospital-deployment/IMPLEMENTATION-LOG.md).

Doctor authentication is a dedicated demo gateway login. The six-role native workspace has shared visible history and persistent teammate threads, not per-patient privacy isolation. Individual SSO, professional clinician validation, institutional security review, electronic report signing/release, full examination performance validation, high availability and an external backup replica remain outside the demonstrated deployment. Sampled image packets can miss small or unsampled findings; mandatory physician review remains essential.

## Reports and video

[Executive deployment PDF](../output/pdf/Hospital-Radiology-Deployment.pdf) summarizes observed results and decisions. Watch the [edited doctor workflow video](https://doctor.radiology.demo/worklist/Hospital-Doctor-Workflow.mp4) after doctor gateway login. It shows the actual native draft, physician-role practice-note Save and subsequent saved-note history. Raw recordings are private and excluded from Git.
