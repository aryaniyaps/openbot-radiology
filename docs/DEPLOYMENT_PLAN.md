# Current deployment plan

This is the 30 September plan implemented after the packaged-app demonstration. It supersedes the former OpenEMR deployment URLs and sign/lock requirements in the historical September 28 specification.

Use the released OpenMausBot, its native Codex subscription provider, native Chief of Staff and five specialists, separate read-only hospital accounts, and six persistent native desktop workspaces. Preserve prior workspace history as archive; current case facts must come from current hospital screens.

Run one persistent shared KVM hospital server: Bahmni/OpenMRS for patients, radiology orders and human report saving; DCM4CHEE5 for DICOM storage and modality worklist; OHIF and Weasis for imaging. Vendor Raster/iPACS/Agile media were unavailable, so use the approved open-source fallback. Do not build a replacement agent backend, signature/lock extension or autonomous diagnosis.

Use two publicly licensed studies each for DX, CT, MR, US and MG. Preserve real pixels and geometry, remap identifiers to synthetic hospital records, qualify acquisition/order/worklist and the relevant viewer controls, and record five modality workflows plus a genuine native team workflow. Specialists discover evidence through their own hospital screens. The operator performs the synthetic physician review/save/reopen demonstration in a separate session.

Provide a simple doctor portal, concise doctor/operator guides, persistent applications and browser preferences, automatic restart/session recovery, regular encrypted backups retaining seven daily and four weekly points, and an isolated restore rehearsal covering hospital data and assistant configuration. A second copy on external storage is deferred until a destination is available; the single internal disk is not protected against disk failure.

Retire only this project's obsolete services after restore proof. Preserve rollback volumes and configuration and all unrelated host applications. Leave the packaged app running normally with Ask approvals enabled and no temporary debugging listener.

Completion requires the evidence audit in [COMPLETION_AUDIT.md](COMPLETION_AUDIT.md); configuration alone is insufficient.
