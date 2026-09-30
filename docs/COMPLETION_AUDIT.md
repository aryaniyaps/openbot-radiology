# End-to-end completion audit

Current scope follows the 30 September installation and hospital plan. The older root specification describes the retired OpenEMR stack; the current Bahmni plan supersedes its hospital URLs and signature requirements.

| Requirement | Current evidence | Acceptance status |
|---|---|---|
| Released app, Codex and workspace migration | versions.lock.json, native six profiles, five real Codex draft recordings | Passed: final-profile-state.json; normal app launch, GPT-6.1-Sol and closed temporary debug port |
| Real software in persistent local VMs | Running shared KVM plus six native rootless desktops; native Firefox CT render | Passed: workstation-recreation.json and boot-recovery.json |
| HMS, orders, PACS and worklist | Five recorded native order/C-FIND/C-STORE workflows | Passed: worklist-repair.json, worklist-conformance.json and future-worklist-conformance.json |
| Real public data, each selected modality | Two studies each DX/CT/MR/US/MG; source manifest and pixel hashes | Passed: viewer-controls.json and rendered screenshots/recording |
| End-to-end recordings | Five modality videos including physician save/reopen | Passed: live-readonly-pilot.json, native-team.json and native-team-physician.json |
| Simple doctor interface | Portal verified patient/order links; doctor quick start | Passed: portal-checks.json |
| Read-only assistants, human reports | Six native POST denials before and after restart; blocked desktop DICOM upload | Passed: live-readonly-pilot.json |
| Regular backup and restore | Two encrypted cold snapshots; isolated boot recovered 17 studies/1016 instances/seven report notes | Latest restore passed including profiles/preferences/database/auth: restore.json. External copy remains deferred until a destination exists. |
| Preserve history and unrelated stacks | Scoped retirement receipt, rollback volumes/config, memory archive | Current guides and status updated |

Live screen-reading and the native specialist workflow have now passed. The separate physician saved and reopened the checked technical note; Workflow Steward independently reloaded and verified its content under GPT 6.1 Sol. No autonomous diagnosis, signature or locked status is claimed. Final normal-launch/provider capture passed; all six native read-only browser sessions renewed and finish on the simple portal, with developer tools closed. The current app is running without the temporary debugging listener.
