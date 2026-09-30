# Doctor quick start

Open **https://radiology.demo/** from the local machine or the Radiology workspace desktop shortcut.

1. Sign in to Hospital records with your physician account. The operator keeps credentials in `.private/server/hospital-state.json`; do not share the physician password with an assistant.
2. Enter the patient ID and accession on the portal. It verifies that the order belongs to the patient before opening images.
3. Use Open images for OHIF, or Open Weasis for the desktop viewer. Use the mouse wheel to move through slices or ultrasound frames. MRI contains separate series; mammography contains four CC/MLO images.
4. Ask an OpenMausBot assistant to verify the patient and accession and help organize supplied observations. Keep Ask approval enabled. Assistants use their own read-only accounts.
5. Review the draft yourself, then save through your authenticated Bahmni consultation. Reopen it to verify the saved report.

Example: patient **DEMO-003**, accession **ORD-4** opens the first CT case. The recorded demonstration patients are listed in [recorded-cases.json](evidence/local-hospital/recorded-cases.json).

Public image pixels are real; patient identifiers and demographics are synthetic. Recorded reports demonstrate technical workflow, not clinical diagnoses. Report saving does not implement a signature or report-locking workflow.

Watch all five demonstrations at **https://radiology.demo/demos/**. Videos are served from the hospital VM and excluded from Git. Capture and validation metadata remain in `docs/evidence/local-hospital/`.
