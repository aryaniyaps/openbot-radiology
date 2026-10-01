# Local radiology workspace

Operational files for the installed OpenMausBot, Bahmni HMS, DCM4CHEE PACS/worklist, OHIF and Weasis environment. Start as a doctor at **https://doctor.radiology.demo/worklist/** ([deployment and login guide](docs/HOSPITAL-DEPLOYMENT.md)). IT management is at **https://it.radiology.demo/operations/**. Hospital applications remain at **https://radiology.demo/**; recorded modality demonstrations are at **https://radiology.demo/demos/** on the hospital VM.

- [Doctor quick start](docs/DOCTOR_QUICK_START.md)
- [Operations and full-system restore](docs/OPERATIONS.md)
- [Deployment plan](docs/DEPLOYMENT_PLAN.md)
- [Public imaging sources](docs/DATA_SOURCES.md)
- [Acceptance audit](docs/COMPLETION_AUDIT.md)

`config/server/` holds the pinned hospital deployment; `config/operations/` holds scheduled maintenance. `scripts/server/` and `scripts/operations/` contain the installation and maintenance tools. `config/data/public-manifest.json` records public data provenance. Python imaging helpers require `pip install -r requirements.lock.txt`; browser recording helpers require operator-managed Playwright in `.private/browser/`. Credentials and machine-specific operator state remain in `.private/server/`.

Check the existing installation with `python3 scripts/demo-stack.py status`. This repository is operational configuration, not a one-command fresh-machine installer. Follow the deployment and operations guides for prerequisites and provisioning.

## Portable OpenMausBot backup

[backups/openmausbot.backup.json](backups/openmausbot.backup.json) is a sanitized native `openmaus.backup` version 1 export containing the current six profiles, empty case threads, operating memory and team organization. Historical case messages and memory logs are excluded. Use the application's native team import controls to import it. Import adds profiles rather than overwriting existing ones.

Before import, sign in to Codex. Native v1 import does not restore credentials, model selections, enabled skills, desktop/browser connections or permission grants. Configure the role/model assignments in [role-guidance.json](config/openmausbot/role-guidance.json): Sol handles preparation, coordination and drafting; Astra handles image interpretation and independent checking. Install the three [native radiology skills](config/openmausbot/skills/), reconnect each read-only application desktop and configure allowed teammates. Apply [the routine permission policy](config/openmausbot/routine-permissions.json) through the paired IT session as described in the [workspace setup guide](config/openmausbot/README.md). The existing installation already uses native automatic tool review.

To refresh the portable backup, run `sudo -n python3 scripts/operations/export-openmausbot-backup.py --profiles-only --session <operator-session.json>`, then review the diff before committing. It uses the private native operator pairing and redacts known local credentials.

The encrypted nightly Restic backup described in the operations guide is the full-machine restore, including VM disk, provider authentication and browser state. Its encryption key, credentials, raw exports, source clones and recordings are excluded from Git. Historical local source and media are preserved outside this checkout; the VM continues serving all demonstrations.

## Completed imaging benchmark

Start with the [executive PDF report](output/pdf/Imaging-Benchmark-Executive-Report.pdf): seven pages covering the decisions, core results, uncertainty, specialist value, limitations and research agenda.

Read the [decision report](benchmark/runs/20260930T1418Z-graysby/DECISION-REPORT.md) and [requirement audit](benchmark/runs/20260930T1418Z-graysby/REQUIREMENT-AUDIT.md). The [delivery guide](benchmark/README.md) explains the curated artifacts, integrity checks and locally retained evidence.

## Direct frontier model evaluation

The current [Sol/Astra evaluation](benchmark/runs/20261001-frontier-v2/README.md) compares actual native reads across routine report-backed studies and published clinician case presentations. Its [executive PDF](output/pdf/Radiology-Frontier-Model-Evaluation.pdf) separates diagnosis recognition, report-assertion detection, technical availability and supplementary input/review experiments. These are exploratory supervised-assistant results, not hospital clinical certification or measured doctor time savings. The [frontier research report](docs/research/RADIOLOGY-FRONTIER-DEEP-RESEARCH.md) provides the external evidence context.
