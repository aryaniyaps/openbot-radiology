# Execute a decision-grade medical-imaging benchmark using OpenMausbot

Act as a multidisciplinary research team with expertise in diagnostic radiology, medical-imaging AI, agent evaluation, benchmark engineering, and biostatistics.

**This investigation will inform important decisions. I need an executed, auditable evaluation with defensible conclusions—not a superficial benchmark, speculative rankings, or a comprehensive-looking report unsupported by evidence.**

Your responsibility is to establish what the tested systems demonstrably can and cannot do, how certain those findings are, and which decisions the evidence supports. Negative and inconclusive findings are acceptable. Fabricated results, hidden methodological weaknesses, and false confidence are not.

## 1. Objectives and systems to evaluate

Evaluate these requested models:

- `gpt-6-luna`
- `gpt-6.1-sol`
- `gpt-6-astra`

Also evaluate **MedGemma** as a potential standalone image interpreter, delegated imaging specialist, and independent second reader.

My impression is that earlier general-purpose models were mainly useful for narrow tasks such as chest X-ray interpretation. Investigate that premise rather than accepting it. Determine whether current capabilities extend meaningfully to other medical-imaging modalities and clinically relevant cases.

Use existing datasets with reference answers. Compare two methods of presenting the **same underlying patient studies**:

**Arm A — Computer use:** The model operates a DICOM viewer through screenshots and graphical interactions, examining studies broadly as a human reader would.

**Arm B — Direct image input:** The model receives supported image attachments, genuinely supported native DICOM inputs, or a documented pipeline that renders and chunks DICOM studies into supported visual inputs.

For each method, determine diagnostic performance, clinically important failures, operational reliability, time, and cost.

The central question is:

> Which tested model–workflow combinations produce sufficiently reliable results, for which imaging tasks and under what conditions, to justify further engineering investment or controlled clinical validation?

A small retrospective benchmark must not be presented as proof of readiness for autonomous clinical use.

## 2. Use the existing OpenMausbot setup

**OpenMausbot is already available and has bots and agents that can access an HMS, a DICOM viewer, and related tools. Use this existing setup as the execution platform.**

Begin by inspecting the accessible environment, configurations, documentation, and tools. Verify the capabilities actually available rather than designing an imaginary system.

Identify the relevant workspaces, bots, model adapters, HMS access, viewer, attachment pathways, serving endpoints, execution resources, and logging facilities.

Reuse existing capabilities. Make only minimal, authorized, workspace-local additions needed for the benchmark. Do not start by installing a replacement platform or proposing a parallel architecture that ignores what already exists.

Distinguish capabilities confirmed through configuration or successful tests from capabilities merely described or assumed.

**The primary deliverable is an executed investigation, not instructions for someone else to execute it.** If a capability is inaccessible, state the exact blocker and complete everything that can genuinely be done. Never claim access, successful execution, or completed experiments without evidence.

## 3. Mandatory: Do not disturb the existing Codex session

**A Codex session is already running and controlling a separate OpenMausbot workspace. It must continue uninterrupted. Run this investigation in parallel in a dedicated, independently allocated workspace.**

Reuse the platform, not the other session’s workspace, desktop, browser, mutable state, or working files.

### Resource ownership and isolation

Start with read-only discovery of resource allocations. Identify a safe benchmark workspace and create a unique run identifier. Maintain a manifest of benchmark-owned agent sessions, processes, containers, directories, browser sessions, displays, ports, and service namespaces.

Treat resources with unknown ownership as unavailable until ownership is established. An idle-looking browser, process, or workspace is not permission to take it over.

Do not inspect the other session’s task contents or private outputs except where strictly necessary to establish resource ownership.

Use independent agent conversations, memory, temporary files, outputs, logs, viewer state, and benchmark-specific HMS records.

**Separate browser profiles or tabs are not sufficient isolation when agents share desktop-level mouse, keyboard, focus, or screenshot capture.** Verify the actual control boundary. Use a separately allocated desktop, display, container, or equivalent supported isolation mechanism where necessary.

Confirm that benchmark actions and screenshots target only benchmark resources before beginning computer-use experiments.

### Protected resources and shared infrastructure

Do not stop, pause, restart, kill, reconnect, take over, or reconfigure the active Codex session or anything it owns.

Do not restart shared OpenMausbot services, modify global agent definitions, change shared model routing, rotate credentials, alter global environment variables, or install dependencies into shared environments.

Use an isolated checkout or appropriately configured worktree for code changes. Do not switch branches, reset files, or modify the working tree used by the other session.

Read-only sharing of immutable assets is acceptable where permissions allow it. Keep generated data and mutable caches separate.

### Capacity and cleanup

Check available capacity and impose benchmark-specific limits on concurrency, memory, CPU, GPU use, disk activity, and provider request rates. Separate workspaces may still share hardware and API quotas.

If capacity becomes constrained, reduce or pause **this benchmark**, not the other workload.

Record contention that could affect timing comparisons. Do not misrepresent shared-resource interference as intrinsic model performance.

Cleanup must affect only resources positively identified as benchmark-owned. Never use global shutdowns, broad process termination, or shared-directory deletion.

**Non-interference takes priority over completing an experiment.** If safe parallel execution is impossible for part of the evaluation, mark that part as blocked and continue independent work.

## 4. Verify model identity and current capabilities

Verify the exact models served behind the requested names. Record requested identifiers, providers, reported versions, checkpoint or snapshot information, inference settings, routing, and fallback behavior.

A bot’s display name is not sufficient proof of identity. Disable silent fallback for evaluation or detect and exclude affected runs. If multiple names resolve to the same underlying model, disclose that rather than treating them as independent systems.

For each model, verify visual-input support, attachment handling, computer-use integration, context and image limits, relevant tool interfaces, and pricing where available.

Distinguish file acceptance from actual interpretation of the file’s medical-image content. Do not assume native DICOM understanding because an upload succeeds.

Distinguish publicly documented capabilities from capabilities verified locally. Lack of public documentation alone does not establish that a locally configured model is unavailable.

For MedGemma, first inspect existing access. Check relevant official variants, including `google/medgemma-1.5-4b-it` and `google/medgemma-27b-it` as **candidate identifiers to verify**, not assumed available checkpoints. Check for newer relevant releases at execution time.

Verify whether each candidate is multimodal, its intended input preparation, hardware needs, license, and serving requirements. Record checkpoint revision, processor, inference-library versions, precision, quantization, and generation settings.

Do not silently substitute unavailable requested models. Use development cases—not held-out evaluation results—to select MedGemma configurations. Treat fine-tuned models as separate experimental conditions with separate training-data disclosures.

## 5. Define decisions, scope, and acceptance criteria before testing

Before inspecting held-out results, write a concise protocol defining the decisions this study is intended to inform and the evidence required for them.

Separate decisions about further engineering investment, narrowing to a particular modality or task, proceeding to controlled clinical validation, and deploying in patient care. These require different evidence.

Where acceptance thresholds are not supplied or clinically established, propose justified **provisional research thresholds**. Do not invent a universal “safe enough” accuracy percentage.

Construct a modality × anatomy × clinical-task coverage matrix. Assess feasible coverage of radiography beyond chest X-rays, CT, MRI, ultrasound, mammography, and nuclear medicine.

Distinguish materially different study types, such as still ultrasound versus cine, mammography versus tomosynthesis, and selected CT images versus complete volumetric studies.

Start with approximately **100–200 independent patient studies overall** as a practical exploratory target. Adjust based on available data, resources, and the precision required for the actual decision.

Do not claim that this sample validates “all medical imaging.” Prefer fewer well-supported tasks over superficial inclusion of every modality. If breadth and decision-grade precision conflict, explain the trade-off and prioritize the prespecified decision-critical tasks.

Define the task for every dataset: detection of a particular abnormality, diagnosis, differential diagnosis, localization, severity, or another explicit endpoint.

**A dataset labeled for one disease supports evaluation of that task, not unrestricted diagnostic competence.**

Freeze the protocol, prompts, sampling, preprocessing, scoring, retry rules, and operating budgets before held-out evaluation. Log subsequent deviations and their consequences.

## 6. Select credible datasets and prevent leakage

Prefer a small number of well-chosen, accessible datasets with usable imaging and reference answers.

For each dataset, document provenance, access requirements, license, modality, anatomy, format, study size, patient count, label coverage, and compatibility with each input arm.

Explain how reference answers were established: pathology, follow-up, expert consensus, reports, annotations, or another method. Assess the strength and completeness of the reference standard.

Include normal cases, positive cases, relevant mimics, and a reasonable difficulty range where supported. Document enrichment, institutional concentration, teaching-case selection, and exclusions.

Use the patient study or diagnostic case as the evaluation unit. Thousands of slices from a few patients are not thousands of independent diagnostic examples. Keep related studies from a patient together and check for duplicates across sources.

Use a separate development set for debugging, rendering validation, prompt refinement, and configuration selection.

Inspect filenames, directory structures, DICOM metadata, structured reports, overlays, annotations, burned-in text, and accompanying documents for answer leakage. Preserve technical information needed for interpretation while removing answer-bearing content.

Within the HMS, expose only prespecified clinical context. Hide final reports, diagnosis codes, pathology outcomes, treatment information, and other answer-bearing records unless explicitly included in the experimental condition.

Keep reference answers and scoring materials outside diagnostic-agent access. Audit shared memory, persistent threads, retrieval tools, inter-agent messages, and filesystem permissions. Use isolated sessions across cases and configurations.

Diagnostic agents must not search the internet or external answer repositories to identify public cases. Research agents may investigate dataset documentation separately without passing answers into evaluation sessions.

Assess possible training overlap with public datasets. State when contamination cannot be ruled out.

Do not call an additional model finding false merely because an incomplete label set omits it. Distinguish confirmed errors, unsupported findings, ambiguous findings, and unscorable outputs.

Use qualified clinical adjudication where necessary. Record reference corrections transparently and apply them consistently across all configurations. If appropriate adjudication is unavailable, restrict the conclusions accordingly.

## 7. Implement the two input arms faithfully

### Arm A: Computer use in the existing viewer

Use the existing DICOM viewer unless a demonstrated incompatibility requires a minimal change.

The diagnostic agent observes screenshots and uses authorized graphical interactions. Document available scrolling, series selection, window and level, zoom, pan, measurements, cine playback, and multiplanar reconstruction.

Standardize initial state, layout, display resolution, available controls, and clinical context. Record necessary modality-specific differences.

Do not bypass the viewer by reading underlying pixel arrays, hidden image APIs, filesystem contents, or answer-bearing DOM or network data.

Set explicit limits for elapsed time, interaction steps, model usage, and retries.

Capture replayable evidence of what was viewed: screenshots, actions, series selections, and slice or frame positions where feasible. Record study coverage, premature stopping, and omitted series.

Separate navigation failures, access failures, insufficient inspection, and interpretation errors. All matter for workflow performance, but they are not the same failure mechanism.

### Arm B: Direct visual input

Use existing attachment pathways where suitable. Verify that the model actually receives interpretable visual evidence.

If native DICOM interpretation is unsupported, implement a transparent conversion pipeline. Preserve relevant intensity transformations, windowing, orientation, resolution, series identity, acquisition information, and temporal or volumetric relationships.

Use modality-appropriate preparation. Do not assume that one generic contact sheet is adequate for CT, MRI, mammography, and ultrasound cine.

For oversized studies, evaluate a small number of practical strategies. Include a reproducible fixed-selection baseline and, where feasible, an adaptive approach through which the model requests additional series, slices, frames, windows, or resolutions.

The primary selection pipeline must not use reference diagnoses, lesion masks, abnormality annotations, or human-selected “best images.” Oracle-selected inputs may be studied only as a separately labeled upper bound.

Measure what was actually delivered: series coverage, slice or frame coverage, resolution, compression, and omissions. Track preprocessing and inference costs.

Visually validate representative outputs before evaluation. Confirm that conversion, sampling, or downscaling has not destroyed relevant information.

If an error results from missing or degraded input, report that explicitly rather than attributing it solely to diagnostic reasoning.

## 8. Evaluate MedGemma in distinct roles

Preserve the GPT-only baselines and compare the following configurations on the same eligible studies:

| Configuration | Purpose |
|---|---|
| **Primary model alone** | Establish each requested model’s original performance without MedGemma. |
| **MedGemma alone** | Measure its interpretation of the supplied images without another model improving its answer. |
| **Primary model with delegated MedGemma interpretation** | Test MedGemma as a specialist tool used to obtain findings or answer imaging questions. |
| **Primary model with an independent MedGemma second read** | Test whether an independent interpretation improves the primary model’s final answer. |
| **Selective delegation, if feasible** | Test a frozen policy that calls MedGemma only for a defined subset of cases. |

Not every configuration must exist in every input arm. Do not force MedGemma to control a viewer merely to make the matrix symmetrical. Explain which comparisons are valid.

### Specialist-tool interface

Expose MedGemma through a benchmark-local adapter with access only to the supplied case inputs.

The request should identify the study, task, allowed clinical context, and actual visual evidence. The response should contain findings, anatomical locations, supporting image references where feasible, uncertainty, and input limitations.

**Passing only the primary model’s written findings is a text consultation, not an independent image interpretation.** Label it separately.

Document which operations are deterministic preprocessing, which are performed by the primary model, and which are performed by MedGemma. Attribute results to the complete tested configuration.

### Independent reads and follow-up questions

For the second-reader condition, save the primary model’s initial answer before revealing MedGemma’s output. MedGemma’s initial read must also be blind to the primary model’s diagnosis.

Use neutral initial requests rather than instructions to confirm a suspected diagnosis.

Targeted follow-up questions are allowed in delegated workflows, but preserve their wording and record how they direct attention.

Retain the primary answer, specialist answer, and final synthesized answer separately. Freeze specialist-call limits, follow-up limits, and resource budgets.

### Preserve input-arm boundaries

In the computer-use condition, distinguish MedGemma receiving screenshots already available to the primary model from MedGemma receiving underlying study data through another pipeline.

The latter is a **hybrid computer-use plus direct-image configuration**, not a pure computer-use result.

Document model-specific preprocessing and differences in visual coverage. Do not attribute improvements to specialization if the specialist received substantially better evidence.

### Measure harm as well as benefit

Track whether consultation corrects a wrong answer, changes a correct answer into a wrong one, leaves a shared error unresolved, ignores a correct specialist finding, or introduces a new synthesis error.

Assess important omissions and false-positive additions, not just exact-match accuracy.

Where feasible, include a primary-model self-review control with a comparable additional budget. This helps distinguish MedGemma-specific benefit from simply spending more inference time.

Agreement between models is not proof of correctness.

Develop any selective-delegation policy on development data and freeze it before testing. Score the policy over all assigned cases, including cases where it chose not to consult.

Do not retrospectively route cases to whichever model happened to be correct. An oracle routing analysis is only a theoretical upper bound.

## 9. Make comparisons fair and manageable

Use the same patient studies, task definitions, clinical context, diagnostic instructions, and output requirements across comparable configurations.

Separate **practical end-to-end performance under an operating budget** from **interpretation performance with approximately matched visual evidence**.

Choose and justify the principal resource constraint, such as cost or elapsed time per study. Report actual usage and relevant mismatches.

Include a small matched-evidence analysis where feasible to separate interpretation quality from image coverage, resolution, navigation, and selection.

Do not expand the experiment matrix until execution becomes impractical. Prespecify primary comparisons and treat additional configurations as secondary.

Repeat a prespecified subset to assess run-to-run variability. Do not cherry-pick successful attempts.

If exploratory results determine which configuration receives further testing, use fresh held-out cases for confirmatory conclusions. Do not select and validate the apparent winner on the same data.

Conclusions must refer to the tested **model, input preparation, tools, and workflow**, not to every possible implementation of that model.

## 10. Define outputs, metrics, and adjudication

Require a consistent structured response containing the primary diagnosis or normal conclusion, a limited differential, key findings and locations, urgent findings, confidence, and any abstention or insufficiency-of-evidence declaration.

Request concise explanations grounded in visible evidence, with image references where feasible. Log observable actions and outputs; do not require private chain-of-thought.

Define correctness prospectively, including diagnostic specificity, synonyms, partial correctness, multiple abnormalities, and clinically important omissions.

Choose primary endpoints that the reference labels can actually support. Include:

**Diagnostic performance:** Task-level correctness, sensitivity, specificity, false-negative and false-positive rates where appropriate, important omissions, and unsupported findings.

**Workflow performance:** Successful case resolution across all assigned studies, completion rate, abstention, timeouts, tool failures, exhausted budgets, latency, and cost.

**MedGemma contribution:** Paired changes in correctness and important errors, correct-to-wrong reversals, successful corrections, consultation frequency, and incremental resource use.

Report performance both across all assigned cases and among completed cases. Failures and abstentions must not disappear from the denominator.

Do not automatically classify infrastructure failures as diagnostic false negatives. Count them as unsuccessful end-to-end cases and separately describe their failure category.

Specify the meaning of confidence values. Assess calibration only where the output definition and sample size support it.

Define clinically consequential errors and severity prospectively with appropriate clinical input. Do not invent severity weights after seeing results.

Automated scoring may assist with structured matching. Another language model must not be the sole authority for clinical correctness or error severity. Review ambiguous cases with qualified reviewers where available, preferably blinded to model and arm.

If only label agreement can be established, call it label agreement—not independently verified clinical accuracy.

## 11. Quantify uncertainty and avoid misleading conclusions

Compute all metrics from case-level records using reproducible code.

Use patient-level denominators and account for paired comparisons, repeated runs, and correlated observations. Select statistical methods appropriate to sample size and endpoint.

Report confidence intervals and positive and negative counts for every important task. Show modality-level and task-level results before pooled summaries.

Explain aggregation weights. Do not let a large or easy subgroup conceal poor performance elsewhere.

Distinguish dataset-specific results from modality-wide conclusions. Differences may reflect disease mix, anatomy, institution, reference standards, or input quality.

Zero observed errors must include an uncertainty bound. A small numerical advantage is not automatically a reliable ranking.

Treat multiple subgroup comparisons as exploratory where appropriate. Do not keep adding cases or modifying the pipeline until a preferred conclusion appears.

Calculate the additional sample size or evidence needed when uncertainty is too large for the intended decision.

A claim that MedGemma is cheaper with acceptably similar performance requires a prespecified acceptable degradation margin and supporting uncertainty analysis. A nonsignificant difference is not proof of equivalence.

Do not claim radiologist-level performance without an appropriate human comparison supporting that specific claim.

## 12. Execute in stages, with clear completion criteria

**Stage 1 — Inventory and isolation:** Verify access, model identities, resource ownership, safe parallel execution, and data-handling permissions.

**Stage 2 — Development and smoke tests:** Validate viewer control, attachment interpretation, rendering, MedGemma serving, logging, and scoring on non-evaluation cases.

**Stage 3 — Frozen exploratory benchmark:** Run the prespecified cases and configurations without answer-informed adjustments.

**Stage 4 — Audit and focused validation:** Audit results, investigate important failures, and conduct fresh-case follow-up where authorized and necessary for the decision.

Use existing authorized resources. Estimate spending before large runs, enforce explicit operating limits, and avoid unbounded charges. Do not purchase services, upgrade plans, or reconfigure shared infrastructure without authorization.

Include preprocessing, model inference, serving infrastructure, repeated runs, and human review in cost estimates. Do not describe local MedGemma inference as free.

If full execution is blocked, preserve completed work and identify the exact missing access, resource, authorization, or expertise. Do not substitute a hypothetical result.

Provide brief milestone updates reporting actual progress, completed cases, failures, and material protocol issues—not generic assurances.

## 13. Preserve an auditable evidence package

Every measured claim must be traceable to actual case-level outputs and execution evidence.

Preserve the frozen protocol, dataset manifest, model configurations, prompts, rendering settings, structured responses, scoring code, reviewer decisions, and replayable traces where supported.

Record case identifiers, source provenance, checksums where practical, assigned configuration, verified model identity, execution status, timestamps, usage, and image coverage.

Keep answer-bearing files separate from model-visible materials. Protect sensitive information and redact credentials in logs.

Provide machine-readable results and scripts that regenerate report tables. Reconcile all denominators, totals, exclusions, retries, and missing cases.

Perform an independent audit pass over a random sample and all cases driving major conclusions or serious-error claims. Examine apparent perfect results for leakage, trivial shortcuts, and scoring defects.

A second agent can audit computation and trace consistency; that does not replace qualified clinical adjudication.

If a material protocol defect or leakage is found, quarantine affected runs. Do not quietly repair the pipeline and combine incompatible results.

**An agent claiming that it completed a task is not sufficient evidence. Require the underlying outputs and traces.**

Use de-identified research data in isolated test records. Do not alter live clinical records, issue orders, or publish model diagnoses into production systems.

## 14. Research current evidence without confusing it with measured results

Use current official model documentation, original research, and dataset sources. Record the research date and relevant model-evaluation dates.

Distinguish narrow classification, examination questions, selected-image interpretation, complete-study interpretation, and clinical workflow evaluation.

Keep these categories visibly separate:

**Published evidence:** Results reported by external sources.

**Proposed experiments:** Work designed but not executed.

**Measured results:** Outcomes produced by actual runs in this investigation.

Cite factual claims using primary sources wherever possible. Do not transfer results between versions or imply that published results were reproduced here.

Never fabricate experiment counts, error rates, confidence intervals, costs, model rankings, artifacts, or successful runs.

## 15. Deliver a decision-ready report with a concrete outcome

Lead with what was actually established, not a long methodological preamble.

The report must include the verified environment and model identities; executed and unexecuted work; datasets and reference standards; the frozen protocol; results by modality and task; uncertainty; operational reliability and cost; MedGemma’s incremental contribution; representative successes and failures; audit findings; and explicit limitations.

Include a brief isolation statement identifying dedicated and shared resources, checks performed, and any remaining contention or isolation limitations.

For every major conclusion, state:

> **Tested scope → observed result → uncertainty → important failure modes → supported decision.**

Use clear verdicts such as **supported for the stated research decision**, **not supported**, or **insufficient evidence**. Explain the basis rather than assigning arbitrary scores.

Answer explicitly:

**For the requested models:** Which tasks and workflows performed reliably within the tested scope? Where did they fail, and was the limiting factor navigation, input coverage, preprocessing, interpretation, or reference quality?

**For the input methods:** When was computer use preferable to direct image input? When did direct input or a clearly labeled hybrid approach perform better? What practical limitations matter?

**For MedGemma:** Does it provide demonstrated value as a standalone interpreter, delegated specialist, or independent second reader? Does it reduce important errors, introduce new errors, save resources, or add complexity without sufficient benefit?

**For decision-making:** What action is justified now? What is not justified? What additional evidence would materially change the recommendation?

Save the reproducibility materials in the available benchmark workspace and identify their actual locations. Do not claim that artifacts exist unless they were created and verified.

**Success means an executed, reproducible investigation whose conclusions survive scrutiny—not merely a polished report. Prioritize validity over breadth, measured evidence over assumptions, and defensible decisions over forced certainty.**