# Current implementation — 30 September 2026

Installed OpenMausBot 0.1.91 with its managed Codex 0.159.2, authenticated ChatGPT provider and six migrated assistant profiles/workspaces. All six profiles now use the user-selected `gpt-6.1-sol` with medium effort. Ask approvals remain enabled. Recorded earlier workflows used `gpt-6-sol`. Historical conversations remain archived; obsolete assistant memory was archived privately and replaced with current operating rules.

Hospital: Bahmni/OpenMRS, DCM4CHEE5 storage and modality worklist, OHIF and Weasis, on a persistent KVM server VM. Raster/iPACS and Agile Health were not installed because vendor installation media/licences were unavailable; this is the approved open-source fallback. Native physician report saving is configured, without a signature/lock extension.

Recordings are served from the VM at https://radiology.demo/demos/. Evidence metadata in `docs/evidence/local-hospital/`: five complete recordings and assistant/physician reports; real public study manifest; all six authenticated desktop sessions; native read-only write denials; native Firefox CT rendering; 17 studies/1016 instances and seven technical report notes; encrypted cold backup and isolated restore proof including all six GPT-6.1-Sol profile selections, browser preferences, authentication and the message database; scoped legacy retirement.

Source collections: COVID-19-NY-SBU (DX/CT), PROSTATEx (MR), Prostate-MRI-US-Biopsy (US), CMMD (MG). Two source studies per modality. Pixel bytes and native geometry are preserved; synthetic demographic and order fields plus remapped UIDs associate the public cases with local orders. Ultrasound spatial frames are not a temporal cine claim; mammography detector-plane spacing is not a patient-plane calibration claim.

Limitations: external-drive backup copy remains outstanding. A fresh live read-only CT pilot passed using current native screens. All five specialists returned sourced checks in the native mammography team workflow, followed by separate physician save/reopen. The earlier interrupted pilot is retained as failed evidence. Early worklist modality fields and overlong procedure identifiers were repaired through native PACS APIs and checked with DIMSE C-FIND; the restarted native HL7 service passed the future mapping replay while preserving study identity. No clinical interpretation validation or clinical production certification is claimed.

Start with [Doctor quick start](DOCTOR_QUICK_START.md) and [Operations](OPERATIONS.md). Older setup documents describe the superseded host stack.
