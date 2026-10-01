# Doctor quick start

Open **https://radiology.demo/** from the local machine or the Radiology workspace desktop shortcut.

1. Sign in to Hospital records with your physician account. Assistants use their own read-only accounts.
2. Enter the patient ID and accession on the portal. It verifies that the order belongs to the patient before opening images.
3. Use Open images for OHIF, or Open Weasis for the desktop viewer. Use the mouse wheel to move through slices or ultrasound frames. MRI contains separate series; mammography contains four CC/MLO images.
4. Start a new case thread with **Clinical Assistant**, supplying the patient ID, accession and desired result. Ask it to prepare the history, review available images, propose findings and a differential, draft the report, and obtain an independent check. It uses GPT-6.1-Sol for preparation/drafting and GPT-6-Astra for image reading/checking.
5. Review the proposed findings, examined series/views, urgent concerns and unresolved questions. Missing coverage must remain explicit. Approve read-only actions when prompted; keep clinical decisions with the radiologist.
6. Review and edit the draft yourself, then save through your authenticated Bahmni consultation. Reopen it to verify the saved report.

Example: patient **DEMO-003**, accession **ORD-4** opens the first CT case. The recorded demonstration patients are listed in [recorded-cases.json](evidence/local-hospital/recorded-cases.json).

Example request: “For DEMO-003, accession ORD-4, prepare the case, review every available CT series, propose an evidence-linked interpretation, draft the report and have Report Check review it independently. Show me the draft, urgent concerns and missing evidence.”

Public image pixels are real; patient identifiers and demographics are synthetic. Earlier recordings demonstrate technical workflow. Current assistant proposals need radiologist review; a supplied subset of images cannot establish a complete normal examination. Report saving does not implement a signature or report-locking workflow.

Watch all five demonstrations at **https://radiology.demo/demos/**. Videos are served from the hospital VM and excluded from Git. Capture and validation metadata remain in `docs/evidence/local-hospital/`.
