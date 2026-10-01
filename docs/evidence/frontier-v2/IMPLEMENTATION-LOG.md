# Frontier radiology v2 implementation record

User goal: native OpenMausBot assistance with actual gpt-6.1-sol and gpt-6-astra diagnosis data across feasible modalities. Existing doctors reports only; no newly recruited clinicians. Prior benchmark remains immutable.

## Verified progress

- Replaced technical-only role restrictions with provisional interpretation, differential, evidence-linked drafting and independent checking, retaining human save/sign/release and read-only hospital access.
- Created three native self-contained skills; all passed skill validation. Independent four-scenario forward-test passed with bounded coverage and uncertainty.
- Updated all six native profiles via existing paired operator session. Model changes require the explicit thread PATCH with `updateBotDefault`; general bot PATCH rejects model changes for profiles with multiple threads. Preserved other threads, peer lists and approval settings.
- Native skill-template API requires description as well as name/source/text/enabled; installed and verified actual bytes for every selected role.
- Preserved full original native state privately before changes; retained sanitized profile/skill hash receipts.
- Started a separate unmodified installed OpenMausBot server using `OMB_DATA_DIR`, never replacing the live deployment. Native config rejected an incomplete threads schema; corrected `maxConcurrentPerBot` before any inference.
- Corrected provider wrapper so agents MCP disablement is added only when transport exists; otherwise catalog probes fail `invalid transport`. Refreshed native catalog and verified both exact models through the real account.
- Codex 0.159.3, native OpenMausBot installed server, high effort selected for the paired image-read evaluation. Account allowance verified; no reset or purchase used.

## Evaluation preparation

Reference sources, figures, native traces and account files are private. Public reports will distinguish routine source-report cohorts from peer-reviewed teaching-case diagnosis agreement. Case source identifiers, diagnoses and figure captions stay out of model-visible inputs. No inferred normality from absent report assertions, and no post-test reference relabeling.

Remaining: acquire and qualify broader modality cases; prepare and audit visual inputs; freeze targets/scoring and protocol; run development smoke then fixed paired tests; independent report-check and workflow tests; report per-model/per-modality results, uncertainty and operational data; executive PDF; native export and main publication.

## Native evaluation and source recovery

- Ordinary image GET and cloud interactive browser both returned publisher security interstitials. Firecrawl text sourcing succeeded; a throttled CLI recovered source rate-limit failures. PubMed Central XML plus official CDN figure URLs supplied a reproducible alternative without changing source image content.
- Native bot creation ignores persona/access fields; required a supported post-create settings PATCH and exact soul readback before inference. Earlier development transport probes were quarantined and excluded. Official Ask mode resolves to workspace-write with no network, even when a CLI default requests read-only. Custom mode is desktop-only; retained that gate and disabled provider file/web/tool features instead. Gold/source documents are curator/root-only. Actual sandbox policies and zero tool calls are recorded honestly.
- Both requested models completed correctly configured CXR development reads with verified identifiers. Astra completed a seven-image CBCT development read across two native turns, verifying the four-images-per-turn workaround without dropping views.
- Froze the 70-study routine cohort before its first diagnostic output: 40 fresh report-enriched OpenI studies, 20 reused CT-RATE and 10 reused MR-RATE image packets. Primary paired runs are active; failures remain in the assigned denominator.
- Qualified 43 published case presentations spanning eight modality groups; 36 are held out. Visual QA inspected all 85 candidate figures. Excluded a mammography/ultrasound mismatch, a printed-answer image, incompatible ultrasound/final-diagnosis reference, and a follow-up-only MRI case; no pixel edits or lesion crops. Mixed modality/time-point composites remain explicitly disclosed. Frozen diagnosis terminology targets are separate from morphological term recognition and routine report assertions.
- Updated six native MEMORY.md operating notes through journaled, hash-checked APIs, replacing the obsolete technical-only rule. Preserved before-state privately and historical conversations unchanged. Refreshed a sanitized profile-only native backup; native v1 exports do not include skill files or model/permission settings, which remain explicit operator setup.

## Complete-case isolation and additional experiments

- Disabled automatic case-memory upkeep for every live role and automatic cross-conversation recall in the dedicated clinical workspace. Current journaled policy replaces old technical-only restrictions; history was not erased.
- The 70-study paired routine batch completed all 140 primary reads, plus twelve context-only controls and eight fresh repeats. No diagnostic retry or answer repair is permitted. Existing clinician report assertions remain the reference; omission is not an absence label.
- Fresh OpenI selection had no remaining pneumothorax-positive patients. Added a separately frozen ten-positive challenge from earlier benchmark patients, modality-only context; no primary cohort change and no specificity claim. Both requested models produced zero definite positive assertions in ten assigned cases. Definite misses and unresolved cases are separately retained.
- Aggregate sampled-CT results left nine of ten report-positive nodule assertions unresolved for each model. Added a bounded denser-input experiment on the first two explicitly positive CT case IDs, chosen without per-case output selection. It uses original voxel geometry, 64 sampled axial positions, two HU windows and 32 smaller montages across eight native turns. Representative montages were visually checked. Changes are bundled and two patients cannot support a general effectiveness claim.
- Published-case development reads completed before held-out inference. Fixed targets, prompts and selection are retained despite model errors. Additional review cases were frozen by ID before inspecting individual primary diagnostic outcomes.
- Native v1 profile-only export excludes case messages, case memory logs and routines; it also cannot export model/skill/permission/connection settings. Repository instructions expose that native format boundary rather than promising a complete reinstall from one JSON file.

## Attachment-accounting recovery

The first dense Sol read completed all eight turns and identified the source-report nodule assertion. Three other dense assignments failed during upload, before any model turn, with HTTP 507. Disk contained only 7.7 MiB of attachments, but installed native code keeps `committedAttachmentBytes` in memory: our terminal raw-file cleanup did not decrement that cache. Native accounting refreshes at startup. Preserve all three pre-inference failures; pause the owned continuation parent at its control/review boundary, wait for current turns to finish, then restart only the isolated server with the same native bundle/config/data. Repeat only those upload failures as explicitly named transport-recovery assignments; no diagnostic answer is retried or replaced. Account for both first-attempt technical failures and recovered first diagnostic outputs separately.

## Reader prompt integrity correction

While preparing live attachment-handoff guidance, one extra transport-only paragraph was briefly put in shared guidance. It was immediately moved to coordinator-only instructions, keeping the primary reader contract unchanged. Hash audit found all direct/primary reader prompts match the original exact bytes. One exploratory cross-review (ROUTINE-CXR-023, Sol) received that additional attachment-handoff paragraph; its actual answer is retained without retry and the review deviation is disclosed. Clinical procedure/reference data did not change. Standing-prompt hash checks now enforce the original exact direct-reader instructions at final acceptance.

## Live procedure delivery and source-context audit

The first real native public-image rehearsal completed all five specialist handoffs after its 900-second observer window; initial manual one-shot coordination approvals contributed delay. Its timeout and later terminal state are retained separately. Multiple roles reported that their read-only tool surface could not open installed SKILL.md files. Updated the native installer to supply the exact relevant enabled procedures inside each standing prompt, preserving canonical installed skills and avoiding additional filesystem grants. All six souls were read back and verified for the complete procedure text. Coordinator-only guidance now requires real native attachment markup for image-read/check handoffs; plain paths do not establish native pixel delivery. A fresh rehearsal checks that update, using one-shot internal coordination approvals and no persistent permission grant.

A systematic source-context terminology audit flagged one teaching case: prior follicular lymphoma is legitimate clinical history, but the frozen general lymphoma name matcher can recognize that history without proving new pulmonary-vein involvement. Preserve the original 36-case denominator and unchanged reference; additionally report the 35-case no-explicit-target-name subset. This does not establish causal benefit of the pixels. No new live clinician review is used.

Six scoring/integrity checks pass, including recovery preservation and refusal to recover any case that already issued a model request. The earlier delivered benchmark checksum package passes unchanged.

The fresh rehearsal confirms two native attachment tags in Image Assistant's actual delivered brief and the requested Astra/high thread selection. It also revealed that the existing Report Draft pair conversation retained Sol/medium despite its updated Sol/high default. Native pair threads keep their own model settings. The installer now synchronizes only active, role-to-role pair threads to the declared model/effort, with readback receipts, while preserving human-created historical threads and their messages. The observed draft is retained as Sol/medium evidence; no clinical answer is rerun to conceal this setup deviation.

## Supplementary measured outcomes

- Dense CT: both models retained present for DENSE-CT-001 and uncertain for DENSE-CT-002. There was no nodule-detection gain on these two patients, despite 32 delivered images/eight turns and approximately 575-697 seconds per read. The early impression that identifying a nodule meant improvement was corrected after checking the paired baseline. It does not: the baseline already detected that patient's nodule.
- Cross-review: both checkers retained 26/31 matching explicit physician-report assertions, with no corrected or newly introduced concordance mismatches. Astra changed one definite error to uncertainty, without obtaining a correct assertion. Review is not a substitute for image discovery or clinician validation.
- Context-only: all 28 controls abstained, with zero supplied images. They were explicitly instructed to abstain, so this is a policy check rather than a causal vision ablation.
- Repeat: Sol matched all four cases' structured target states exactly; Astra matched three of four exactly, with one target-state difference in the fourth. The subset is too small to establish deployment stability.
