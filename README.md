# Local radiology workspace

Operational files for the installed OpenMausBot, Bahmni HMS, DCM4CHEE PACS/worklist, OHIF and Weasis environment. Start at **https://radiology.demo/**; recorded modality demonstrations are at **https://radiology.demo/demos/** on the hospital VM.

- [Doctor quick start](docs/DOCTOR_QUICK_START.md)
- [Operations and full-system restore](docs/OPERATIONS.md)
- [Deployment plan](docs/DEPLOYMENT_PLAN.md)
- [Public imaging sources](docs/DATA_SOURCES.md)
- [Acceptance audit](docs/COMPLETION_AUDIT.md)

`config/server/` holds the pinned hospital deployment; `config/operations/` holds scheduled maintenance. `scripts/server/` and `scripts/operations/` contain the installation and maintenance tools. `config/data/public-manifest.json` records public data provenance. Python imaging helpers require `pip install -r requirements.lock.txt`; browser recording helpers require operator-managed Playwright in `.private/browser/`. Credentials and machine-specific operator state remain in `.private/server/`.

Check the existing installation with `python3 scripts/demo-stack.py status`. This repository is operational configuration, not a one-command fresh-machine installer. Follow the deployment and operations guides for prerequisites and provisioning.

## Portable OpenMausBot backup

[backups/openmausbot.backup.json](backups/openmausbot.backup.json) is a sanitized native `openmaus.backup` version 1 export containing the current six profiles, tasks, message history, memory and team organization. Secrets are redacted; this file is suitable for this public repository. Use the application's native team import controls to import it. Import adds profiles rather than overwriting existing ones.

Before import, sign in to Codex and select **GPT-6.1-Sol / medium** as the default. Native import does not restore provider credentials, model selections, computer/browser connections or permission grants. Reconnect each desktop, sign in with its assigned read-only application account, explicitly configure allowed teammates and retain Ask approval before handing it to a doctor. Imported routines are paused. Review restored history before repurposing the demonstration.

To refresh the portable backup, run `sudo -n python3 scripts/operations/export-openmausbot-backup.py`, then review the diff before committing. It uses the private native operator pairing and redacts known local credentials.

The encrypted nightly Restic backup described in the operations guide is the full-machine restore, including VM disk, provider authentication and browser state. Its encryption key, credentials, raw exports, source clones and recordings are excluded from Git. Historical local source and media are preserved outside this checkout; the VM continues serving all demonstrations.

## Completed imaging benchmark

Read the [decision report](benchmark/runs/20260930T1418Z-graysby/DECISION-REPORT.md) and [requirement audit](benchmark/runs/20260930T1418Z-graysby/REQUIREMENT-AUDIT.md). The [delivery guide](benchmark/README.md) explains the curated artifacts, integrity checks and locally retained evidence.
