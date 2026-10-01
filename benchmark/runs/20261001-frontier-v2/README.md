# Direct frontier radiology evaluation

Actual paired reads by `gpt-6.1-sol` and `gpt-6-astra`, high effort, through the unmodified installed OpenMausBot server and this operator's authenticated Codex account. Native role profiles and skills are installed separately in the live six-role workspace.

The primary comparison assigns both models to 106 studies: 40 fresh report-enriched OpenI chest radiographs, 20 reused CT-RATE chest CTs, 10 reused MR-RATE brain MRIs, and 36 held-out published clinician case presentations. Seven published development cases are excluded from primary metrics. Domain groups are CXR, general radiography, CT, MRI, ultrasound, mammography, fluoroscopy, PET/CT nuclear imaging and dental CBCT; these are not nine independent DICOM modalities.

## Read the results

- [Executive PDF](../../../output/pdf/Radiology-Frontier-Model-Evaluation.pdf)
- [Primary metrics, intervals and paired differences](report/summary.json)
- [Individual assignments](report/assignment-results.csv)
- [Complete model-generated reads, normalized view names only](report/structured-model-reads.json)
- [Report-assertion results](report/routine-assertions.json)
- [Published-case diagnosis recognition](report/teaching-case-results.json)
- [Supplement, controls, repeats, reviews and denser CT](report/experiments.json)
- [Native operation measurements](report/operational-metrics.csv)
- [Published case provenance](report/source-provenance.json)
- [Final input/model/reference audit](evidence/final-acceptance.json)

## Interpret the numbers correctly

Routine findings are matched against explicit assertions in existing physician reports. Uncertain, conflicting and omitted report assertions are unscorable; report silence never establishes normality. All-assigned positive detection includes uncertain/unassessable predictions and failures in the positive denominator. Definite-only sensitivity and specificity are also provided but can conceal poor coverage. Report concordance is not independent image adjudication. MR-RATE reference text includes machine translation/restructuring and is sparse.

Teaching cases use prespecified diagnosis-name and visible-morphology regular expressions frozen before held-out inference. Primary diagnosis and primary-plus-first-three differential term recognition are separate. Negated matches and abstentions score zero. These reproducible lexical measures do not replace clinical assessment of semantic equivalence or correctness. Figures are selected, rare positives are enriched, some figures contain multiple modalities/time points, and training contamination is unknown. A diagnosis that requires pathology/genetics cannot necessarily be established by pixels.

The separate ten-positive pneumothorax challenge reuses earlier benchmark patients because the fresh source pool had no remaining explicit positives. It supplies no diagnostic indication and has no specificity denominator. It brings the evaluation to 116 unique patients, without changing primary N. The denser CT presentation reuses two primary patients and bundles sampling, smaller montages and extra native turns; it is a two-patient mechanism experiment, not an independent cohort. Twelve fixed-case cross-reviews compare the checked read against the opposite model's primary proposal, using identical images. Context-only controls explicitly ask for abstention, so they cannot isolate causal image benefit. Four fresh repeats per model estimate only limited stability.

## Input and blinding boundaries

Chest radiographs use released source rasters. Primary CT uses 16 axial positions and lung/mediastinal windows; MRI uses sampled sequence montages. Neither is a complete examination. Native OpenMausBot admits four images per turn, so larger packets are presented across successive turns in one case thread, then consolidated. Delivery hashes, actual dimensions and counts are audited; native resizing is recorded. The denser CT arm uses 64 sampled axial positions, two windows and 32 smaller montage images.

Curator reference documents and source identifiers/answers remain root-protected during inference. Image readers receive neutral case identifiers, pre-imaging history where eligible, neutral chronology and images; no source title, diagnostic figure caption or gold report. All public figures were visually inspected before freezing. Printed-answer, modality mismatch, incompatible reference and follow-up-only candidates were excluded. Public-case memorization and residual clues within annotated published figures remain limitations.

The isolated native provider disables web, file/shell, skill discovery, hooks, apps and model delegation. Study-read/check procedures are injected directly. Native Ask mode resolves to workspace-write with network disabled; this is recorded honestly, and zero actual tool calls are required for qualification. Fresh independent cases, disabled automatic memory capture/recall and actual trace inspection prevent observed prior-conversation context. Backend weight revisions are not exposed; identity claims are limited to the verified provider model identifier.

## Reproduction

Preparation scripts require source access and locally retained licensed inputs. References, images, native transcripts, credentials and provider sessions are deliberately not published. Acquisition and protocol files identify provenance and hashes; public derived results permit scoring review without leaking account files. Scripts use the repository root derived from their location, not a hard-coded checkout.

1. Obtain the declared source studies and qualify development inputs, preserving licensed sources privately.
2. Freeze cohort, input/reference hashes and terminology before evaluation. Protect reference text from reader accounts.
3. Start a separate native OpenMausBot data directory/provider with the disabled capability policy. Use `run_batch.py` for each frozen protocol, without diagnostic retries. `continue_evaluation.py` records the ordered evaluation plan; global locks bound concurrent readers.
4. Run `test_scoring.py`, curator `build_results.py --require-complete`, `build_experiments.py --require-complete`, and `final_acceptance.py`.
5. Build the executive report with `scripts/operations/build-frontier-evaluation-report.py`, then render and visually inspect every page.

No dollar-cost estimate, measured physician time saving, hospital authorization, complete-study accuracy or autonomous-care approval is inferred from these experiments. Earlier delivered benchmark files remain unchanged.

## Recorded deviations and live integration

The installed server caches its committed attachment byte total. Terminal filesystem cleanup left that counter stale despite ample disk space, producing 65 pre-inference HTTP 507 failures (62 published-case assignments and three denser CT assignments). All initial failures are retained. Only cases with no issued model request were recovered once, in separately named `-transport-recovery` folders, after restarting the idle isolated native server with identical code/config/data. Public assignment data distinguish original availability from eventual first diagnostic output. Recoveries were processed in model blocks, leaving potential time/order confounding; backend weight revisions are not exposed. No generated diagnosis was retried or replaced. See [transport recovery receipt](evidence/transport-recovery.json).

Every direct reader's exact standing-prompt hash matches the original contract. One exploratory Sol cross-review received an additional attachment-handoff paragraph during native workflow configuration; it remains in descriptive results without retry, with an exact-prompt subset reported separately. The final audit records that deviation. A source audit found one case with legitimate prior lymphoma history matching the general disease-name target; the original 36-case result and a separate 35-case no-explicit-target-name subset are both published. Neither establishes causal image benefit.

The live [native handoff rehearsal](../../../docs/evidence/frontier-v2/native-handoff-rehearsal.json) verified real sequential case-prep, image-read, draft, independent-check and workflow returns, with two owned image tags for both image-reading roles. Read-only roles could not load skill files in the first rehearsal; the installer now includes the exact procedures in standing prompts. Native pair conversations preserve their own model settings; role-to-role execution threads are synchronized explicitly while human-created historical threads remain unchanged. The observed Sol/medium draft from the rehearsal is preserved rather than reclassified as high effort. This public attached-case integration test is distinct from complete hospital-screen or clinical reliability validation.
