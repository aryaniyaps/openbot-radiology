"""Curator-only executive report from measured, reconciled case records."""
import pathlib, json, collections, statistics, time
from binary_metrics import proportion

R = pathlib.Path(__file__).resolve().parents[1]
O = R / 'report'
def read(name):
    return json.loads((O / (name + '.json')).read_text())
rows = read('assignment-results')
metrics = read('task-metrics')
pairs = read('paired-comparisons')
ops = read('operational-metrics')
tasks = read('task-results')
main_task_metrics=[x for x in metrics if x['stage']=='evaluation' and x['arm']=='B' and x['configuration']=='primary' and not x['attempt']]
display_targets={mod:max((x for x in main_task_metrics if x['modality']==mod),key=lambda x:(x['reference_positive'],x['task']))['task'] for mod in ['CXR','CT','MR']}
repeats = read('repeatability')
def prop(p):
    if p['estimate'] is None:
        return 'not estimable'
    lo, hi = p['ci95']
    return f"{p['numerator']}/{p['denominator']} ({100*p['estimate']:.1f}%; CI {100*lo:.1f}–{100*hi:.1f}%)"
def pair_interval(x):
    ci=x['ci_for_difference']
    if ci is None:return 'pending'
    value=f"{100*ci[0]:+.1f} to {100*ci[1]:+.1f} pp"
    if x.get('zero_discordance_exact_upper_probability') is not None:value+=f"; exact bound on absolute difference {100*x['zero_discordance_exact_upper_probability']:.1f} pp"
    if ci[0]==ci[1] and x.get('b_minus_a') not in [None,0]:value+=f"; exact paired p={x['exact_mcnemar_p']:.3g}; small-sample bootstrap boundary"
    return value
def model(s):
    return s.replace('google/medgemma-1.5-4b-it', 'MedGemma 1.5 4B NF4')
pending = sum(x['execution_status'] == 'not_run' for x in rows)
contaminated = [x for x in rows if x['prior_conversation_context_detected']]
recovered = [x for x in rows if x['setup_recovery']]
primary = [x for x in rows if x['stage'] == 'evaluation' and x['arm'] == 'B' and x['configuration'] == 'primary' and not x['attempt']]
observed_studies = {x['case_id'] for x in primary if x['primary_diagnosis'] is not None or x['execution_status'] in ['invalid_output', 'abstained', 'timeout', 'budget_exhausted']}
text = ['# OpenMausbot imaging investigation: decisions and measured evidence',
        f"Updated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}. {'Execution remains in progress.' if pending else 'Every frozen assignment has a recorded terminal outcome.'}",
        f"The direct-input investigation has observed diagnostic outcomes on {len(observed_studies)}/120 main studies. There are {pending} pending assignments across all workflows. The main cohort is 60 chest radiograph studies, 40 corrected chest CT volumes and 20 released MRI studies; 30 separate fresh studies and 20 development studies are separately identified.",
        '**Established:** the requested GPT identifiers and pinned MedGemma checkpoint can receive medical-image evidence through the existing OpenMausbot adapters. This investigation tests report-supported findings on radiographs, selected CT inputs and selected MRI inputs, plus budgeted graphical viewer workflows. It does not establish unrestricted diagnostic competence.',
        'The original premise of improvement over earlier GPT imaging models was not directly tested: no historical-model control was assigned. Executed CT/MRI access establishes technical feasibility beyond radiographs, not proof that broader radiology accuracy has improved.',
        'Published historical evidence already tested GPT-4V on selected CT, MRI and radiographic images in 2024, with strong modality recognition but unreliable diagnostic findings. The premise that earlier systems were useful mainly for chest X-rays is therefore too broad: modality access and clinical usefulness are different questions. That external study is not reproduced here and cannot supply a numerical historical baseline for these different cases and workflows. [Original Radiology study](https://pubs.rsna.org/doi/10.1148/radiol.240955).',
        f"**Material audit findings:** MedGemma’s volumetric montages are stretched to square by its processor, so intrinsic model ability cannot be separated from that input distortion. {len(contaminated)} viewer reads received unplanned earlier-conversation context, including prior model conclusions. These outputs and traces are retained; both sides of those pairs are excluded from independent A-versus-B comparisons. Clean subsequent contexts are audited at the native provider boundary. {len(recovered)} assignments currently have recovery-assisted outcomes after documented setup failures before any diagnostic dispatch.",
        '**Decision boundary:** patient-care deployment and radiologist equivalence are not supported. A research workflow may justify further engineering if it meets the frozen response-completion criterion and passes identity/isolation audit. Existing doctors’ reports support assertion concordance; no live clinicians reviewed these outputs. Translation, incomplete report assertions, public training exposure and small class counts limit clinical interpretation.',
        '## Requested models: execution under the frozen budget',
        'The table concerns recovery-assisted primary attachment workflows. The frozen mechanical gate is at least 95% qualified responses with a Wilson 95% lower bound at least 80%, and clean identity/isolation. It is an engineering gate, not an accuracy or clinical safety threshold. Gate verdicts require completed groups; any incomplete group remains pending.',
        '| Scope | Model | Qualified responses / assigned (95% CI) | Setup failures / recovered | Median inference seconds | Research execution verdict |',
        '|---|---|---|---|---|---|']
ct_nodule=[x for x in main_task_metrics if x['modality']=='CT' and x['task']=='pulmonary_nodule']
if not ct_nodule:
    ct_nodule=[x for x in main_task_metrics if x['modality']=='CT' and 'nodule' in x['task']]
ct_primary_ops=[x for x in ops if x['stage']=='evaluation' and x['arm']=='B' and x['configuration']=='primary' and not x['attempt'] and x['modality']=='CT']
if len(ct_nodule)==4 and all(not x['status_counts'].get('not_run',0) for x in ct_primary_ops):
    details='; '.join(f"{model(x['model'])}: {x['diagnostic_confusion_counts']['TP']}/{x['reference_positive']}" for x in ct_nodule)
    text.insert(6,'**Completed CT finding:** direct workflows resolved few explicit report-positive pulmonary nodules ('+details+'). Remaining assertions include explicit absent calls, abstentions, insufficient inputs and invalid outputs, separated in the full tables. No explicit target-negative nodule reference was available, so specificity cannot be estimated. This supports rejecting these tested workflows for that finding; it does not locate the cause in the weights alone.')
cxr_ptx=[x for x in main_task_metrics if x['modality']=='CXR' and x['task']=='pneumothorax']
cxr_primary_ops=[x for x in ops if x['stage']=='evaluation' and x['arm']=='B' and x['configuration']=='primary' and not x['attempt'] and x['modality']=='CXR']
if len(cxr_ptx)==4 and all(not x['status_counts'].get('not_run',0) for x in cxr_primary_ops):
    details='; '.join(f"{model(x['model'])}: {x['diagnostic_confusion_counts']['TP']}/{x['reference_positive']} resolved, {x['diagnostic_confusion_counts']['FN']} explicit absent calls" for x in cxr_ptx)
    text.insert(7,'**Completed radiograph finding:** pneumothorax resolution is poor despite all 60 primary responses being captured for each model ('+details+'). All ten positive reference reports, report/image mappings and PNG bytes passed an independent original-archive audit. Intervals and negative counts appear below; these are report-supported omissions, without clinical severity adjudication. Successful structured output therefore does not justify diagnostic trust in this workflow.')
mr_wm=[x for x in main_task_metrics if x['modality']=='MR' and x['task']=='white_matter_signal_abnormality']
mr_primary_ops=[x for x in ops if x['stage']=='evaluation' and x['arm']=='B' and x['configuration']=='primary' and not x['attempt'] and x['modality']=='MR']
if len(mr_wm)==4 and all(not x['status_counts'].get('not_run',0) for x in mr_primary_ops):
    details='; '.join(f"{model(x['model'])}: {prop(proportion(x['diagnostic_confusion_counts']['TP'],x['reference_positive']))}" for x in mr_wm)
    text.insert(8,'**Completed MRI finding:** mechanically coded white-matter signal-foci assertions are a possible narrower engineering target ('+details+'). Five coded positives give wide uncertainty even for five concordant outputs; MR-EVALUATION-005 and018 also have normal-examination impressions, so their pathological-abnormality interpretation is unresolved. These are not five confirmed pathological diagnoses, and there are no explicit target-negative MRI assertions under this frozen coder/sample. This supports a new report-grounded precision study, not MRI-wide diagnostic trust or a validated model ranking. A separately labeled post hoc source-scope sensitivity excluding those two reports leaves all three GPTs concordant on 3/3 assertions (Wilson 95% CI 43.9–100%) and MedGemma 0/3 (CI0–56.1%; two explicit absent calls and one invalid output). The frozen 5-case results remain unchanged; this restriction is an audit sensitivity, not a new clinical gold standard. Atrophy has no supported reference assertions in the primary MRI cohort and is unmeasured there.')
for x in ops:
    if x['stage'] != 'evaluation' or x['arm'] != 'B' or x['configuration'] != 'primary' or x['attempt']:
        continue
    p = x['valid_structured']; unresolved = x['status_counts'].get('not_run', 0)
    verdict = 'insufficient evidence: pending' if unresolved else 'supported for response-capture engineering' if p['estimate'] >= .95 and p['ci95'][0] >= .80 else 'not supported under this frozen execution gate'
    text.append(f"| {x['modality']} / supplied views | {model(x['model'])} | {prop(p)} | {x['first_attempt_setup_failure_count']} / {x['setup_recovered_count']} | {format(x['median_seconds'],'.1f') if x['median_seconds'] is not None else 'unmeasured'} | {verdict} |")
text += ['## What the existing doctors’ reports support','![Report-positive and report-negative finding resolution](report/finding-resolution.png)',
         'Each row is a separately scored finding. Counts use released study identities, with one selected CT/MRI study per released patient identifier. OpenI longitudinal patient linkage and cross-source linkage are unavailable; complete global patient independence cannot be certified, so independence-based intervals may be optimistic if identities overlap. Positive and negative report assertions are explicit; omissions, ambiguity and conflicts are excluded. End-to-end success retains failed or abstained assigned cases. Completed-only sensitivity and specificity appear in the full results, with confusion counts and missing-outcome bounds. These are not severity-weighted clinical error rates.',
         'The concise tables display the finding with the most explicit positive report assertions in each modality, selected by reference count rather than model results. All four findings appear in the figure and full appendix. Positive and negative resolution fractions below use all explicit assigned report assertions, including unresolved cases. They measure successful finding resolution under the workflow budget, not completed-only sensitivity/specificity. Pending fractions are execution progress until that group finishes.',
         '| Scope | Model | Finding | Positive assertions resolved (95% CI) | Negative assertions resolved (95% CI) |',
         '|---|---|---|---|---|']
for x in metrics:
    if x['stage'] == 'evaluation' and x['arm'] == 'B' and x['configuration'] == 'primary' and not x['attempt'] and x['task']==display_targets[x['modality']]:
        positive=proportion(x['diagnostic_confusion_counts']['TP'],x['reference_positive'])
        negative=proportion(x['diagnostic_confusion_counts']['TN'],x['reference_negative'])
        text.append(f"| {x['modality']} | {model(x['model'])} | {x['task']} | {prop(positive)} | {prop(negative)} |")
text += ['## Input methods: supported comparison and practical limits',
         'Scope → same underlying released studies, graphical Weasis versus fixed visual attachments. Observed result → the paired table below contains only clean, reference-supported pairs. Uncertainty → small class denominators and exploratory paired-study bootstrap intervals; a pending comparison has no effect estimate. Failure modes → limited viewer navigation and initial inferior CT slice, incomplete sampled volume coverage, different delivered resolutions, and the quarantined context defect. Decision → do not transfer any advantage to native DICOM understanding, full original examinations or model reasoning alone.',
         'Native GPT transport also changes image evidence: audited MRI samples were approximately aspect-preservingly resized from 2048×1620 RGB source montages to 1779×1408 RGBA before dispatch. All 240 images in 60 audited main MRI traces follow this transformation. [Exact Codex 0.159.2 source](https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/utils/image/src/lib.rs) confirms the high-detail patch-budget resize mechanism; integer rounding changes aspect ratio by about 0.056%. Source attachment hashes therefore do not prove native byte identity for those inputs. Audited case identity and four-image count remain correct; no scores, preprocessing or diagnostic turns were changed after this finding.',
         'Graphical call limits are controller targets, not proof that asynchronous requests stop exactly at the limit. Some retained timeout runs report 25–26 native tool calls against the configured 24-call budget; request counts, approvals and recorded completion differ. The coverage audit preserves these counts. No timeout is rescued as a valid response and no held-out turn is rerun.',
         'The research DICOM conversion preserves source intensities, affine orientation and spacing, and records windowing and sequence-family identity. It does not reconstruct original DICOM acquisition timing, echo/repetition parameters or contrast status from the released NIfTI/PNG sources. MRI contrast status is not inferred. These limits matter particularly for lesion characterization and prevent claiming faithful reproduction of every original clinical examination.',
         'Independent visual inspection of the clean CT-EVALUATION-010/Sol viewer trace found 11 delivered desktop screenshots covering nine distinct slice counters out of 247 available frames. Its declared image references were supported. This demonstrates navigation across the volume but sparse anatomical inspection; screenshot uniqueness is not unique slice coverage. The example is a trace audit, not an estimate of all viewer coverage or a clinically adjudicated explanation for a missed finding.',
         'One auxiliary CXR/Luna exact-screenshot re-interpretation was executed on the first technically eligible clean source case, using its two native model-delivered screenshots. It is not pooled with the primary cohort and cannot establish a general matched-evidence advantage. Other eligible comparisons exceed the original request budget. Adaptive slice requests, selective delegation and hybrid viewer-plus-specialist inference were not executed as primary conditions; their absence prevents broad separation of reasoning from evidence selection and navigation.',
         '| Scope | Model | Finding | Clean paired studies | Excluded context cases | B minus A label success | 95% exploratory bootstrap interval |',
         '|---|---|---|---|---|---|---|']
for x in pairs:
    if x['comparison'] == 'A-vs-B' and x['task']==display_targets[x['modality']]:
        difference = 'pending' if x['b_minus_a'] is None else f"{100*x['b_minus_a']:+.1f} pp"
        ci = pair_interval(x)
        text.append(f"| {x['modality']} | {model(x['model'])} | {x['task']} | {x['paired_patients']} | {len(x.get('excluded_context_cases', []))} | {difference} | {ci} |")
matched_path=O/'matched-screenshot-comparison.json'
if matched_path.exists():
    matched=json.loads(matched_path.read_text())
    text += ['## Auxiliary matched-screen case',
             'One CXR/Luna case received exactly the two screenshot byte strings previously delivered in its clean viewer read. Native input-image hashes equal both source screenshot hashes. This is one reused study, not an additional primary patient; tool affordances, instructions and time budgets differ. It demonstrates a technically feasible matched visual-input comparison, not general superiority.',
             '| Explicit finding | Reference | A viewer state | B original-image state | B exact-screen state |',
             '|---|---|---|---|---|']
    for item in matched['comparisons']:
        states=[item['conditions'][name]['state'] for name in ['A viewer','B original images','B exact screenshots']]
        text.append(f"| {item['task']} | {item['explicit_reference']} | {states[0]} | {states[1]} | {states[2]} |")
    text.append('Identity, durations, preserved result paths and assertion concordance are in `report/matched-screenshot-comparison.json`. No confidence interval or model ranking is inferred from this single study.')
text += ['## MedGemma: standalone, delegated and independent second reader',
         '**Verified MedGemma montage distortion:** the default processor stretches each 2048×1080 CT montage to 896×896, changing each tile’s aspect ratio by about 1.90. MRI montage distortion is about 1.26. This verifies the transformation, not a defect in the official processor or its training convention. The held-out pipeline is preserved unchanged; these results assess that workflow, not intrinsic volumetric ability or an optimized complete-volume input protocol.','Scope → pinned 4B multimodal weights, NF4 quantization, greedy bounded generation, up to four visual inputs prepared by the default square processor: released CXR views and fixed CT/MRI montages. It is not the untested 27B variant or Google’s complete-volume evaluation protocol. Independent MedGemma reads were saved before GPT consultation. Delegation calls exactly one assigned-study tool; second-reading reveals the saved initial GPT answer and the independent MedGemma read to a fresh GPT context. Self-review provides the initial GPT answer without a specialist.',
         'Some MedGemma outputs exhaust the frozen 1,600-token generation allowance with unfinished JSON; the platform rejects a non-stop completion. Separate image-free requests are rejected by the strict visual-evidence guard before any GPU inference, including processor preparation. Their exact relationship to each truncated read requires native request linkage and is not presumed. Original truncated responses and guard failures are preserved. Unusable first reads are not repaired or rerun. The generation cap, repetition controls and image guard remain unchanged.',
         'The following changes are report-supported label transitions among completed diagnostic labels, distinct from recovery of abstentions or technical failures. Zero reversals with a small sample do not establish safety. Agreement between models is not evidence of correctness. Degenerate bootstrap intervals with no discordance do not establish equivalence or noninferiority.',
         '`report/specialist-transitions.json` retains baseline, independent specialist and final assertion states. It separately counts shared wrong labels, correct specialist assertions followed by a wrong or unresolved final label, and both initially concordant readers followed by a discordant final label. These are observed three-way patterns, not proof that consultation caused an error or that the GPT deliberately ignored the specialist.',
         '| Scope | Model | Finding | Condition | Paired studies | Completed wrong→correct / correct→wrong | Label-success difference | 95% exploratory bootstrap interval |',
         '|---|---|---|---|---|---|---|---|']
for x in pairs:
    if x['comparison'] == 'A-vs-B' or x['task']!=display_targets[x['modality']]:
        continue
    difference = 'pending' if x['b_minus_a'] is None else f"{100*x['b_minus_a']:+.1f} pp"
    ci = pair_interval(x)
    transitions = 'pending' if x['pending_pairs'] else f"{x['completed_wrong_to_completed_correct']} / {x['completed_correct_to_completed_wrong']}"
    text.append(f"| {x['modality']} | {model(x['model'])} | {x['task']} | {x['comparison']} | {x['paired_patients']} | {transitions} | {difference} | {ci} |")
transitions=read('specialist-transitions')['records']
if transitions and not any(x['pending'] for x in transitions):
    text += ['### Measured specialist changes across supported assertions',
             'The following counts include all three GPTs. A finding/model/condition comparison is the counting unit; the same study and multiple findings recur, so these are not independent patient counts or a pooled clinical accuracy estimate. Gained/lost resolution includes recovery from, or loss to, an unresolved outcome. The completed-label columns separately count binary corrections/reversals. Observed recoveries accompany losses; these sparse exploratory changes do not establish a general specialist benefit or causal harm.',
             '| Scope / condition | Supported finding comparisons | Distinct supported studies | Gained / lost resolution | Completed-label corrections / reversals |',
             '|---|---|---|---|---|']
    for modality,configuration in sorted({(x['modality'],x['configuration']) for x in transitions}):
        z=[x for x in transitions if x['modality']==modality and x['configuration']==configuration]
        gain=sum(bool(not x['states']['baseline']['correct'] and x['states']['final']['correct']) for x in z)
        loss=sum(bool(x['states']['baseline']['correct'] and not x['states']['final']['correct']) for x in z)
        correction=sum(bool(x['states']['baseline']['scorable'] and not x['states']['baseline']['correct'] and x['states']['final']['correct']) for x in z)
        reversal=sum(bool(x['states']['baseline']['correct'] and x['states']['final']['scorable'] and not x['states']['final']['correct']) for x in z)
        text.append(f"| {modality} / {configuration} | {len(z)} | {len({x['case_id'] for x in z})} | {gain} / {loss} | {correction} / {reversal} |")
text.append('The sole completed binary reversal is the Luna delegated white-matter finding on MR-EVALUATION-005, whose normal-impression inconsistency is disclosed above. It remains a frozen-coded reversal, not confirmed clinical harm, and is excluded by the separately labeled source-scope sensitivity. Astra’s MRI resolution losses in both specialist conditions are MR-EVALUATION-001 infarction answers changing from present to abstained with an invalid specialist read. Luna’s shared-wrong emphysema assertion on CT-EVALUATION-002 persists in both specialist conditions. These named patterns do not isolate consultation causality.')
controlled_path=O/'self-review-controlled-comparisons.json'
if controlled_path.exists():
    controlled=json.loads(controlled_path.read_text())['records']
    text += ['### Specialist versus self-review on identical controls',
             'The ten control studies were prespecified. This exploratory same-case comparison was added during the audit while execution continued. It directly compares each specialist condition with a fresh self-review on those identical studies; comparing all 40 specialist studies against 10 self-review studies would confound case mix. Few explicit report assertions support each cell; no confirmatory specialist-benefit claim follows. Pending pairs have no effect estimate.',
             '| Scope | Model | Finding | Specialist condition | Supported control pairs | Specialist minus self-review success | Exploratory95% interval |',
             '|---|---|---|---|---|---|---|']
    for x in controlled:
        if x['task']!=display_targets[x['modality']]:continue
        delta='pending' if x['pending_pairs'] else 'not estimable' if x['b_minus_a'] is None else f"{100*x['b_minus_a']:+.1f} pp"
        ci='not estimable' if not x['paired_patients'] else pair_interval(x)
        text.append(f"| {x['modality']} | {model(x['model'])} | {x['task']} | {x['comparison'].replace('self-review-vs-','')} | {x['paired_patients']} | {delta} | {ci} |")
    if not any(x['pending_pairs'] for x in controlled):
        text.append('Of 66 estimable same-control task cells, the only nonzero success difference is Luna/CXR cardiomegaly in second-reading versus self-review: one additional resolved assertion among four supported pairs (+25 pp; exploratory bootstrap 0–75 pp; exact McNemar p=1.0). The other 65 estimable cells have zero observed difference, and six cells have no reference support. These small, repeated endpoint comparisons do not establish specialist benefit or equivalence.')
    text.append('All 72 control-task cells, reference-positive/negative counts, case IDs, gain/loss counts and exact discordance bounds are preserved in `report/self-review-controlled-comparisons.json`. This supplement leaves frozen scoring and primary comparisons unchanged.')
text += ['No claim of cheaper acceptably equivalent MedGemma performance is supported: subscription-dollar allocation and hardware costs are unavailable, and no confirmatory noninferiority analysis exists. The role comparisons and same-case controls are exploratory, with small endpoint support and no confirmatory specialist-benefit analysis.',
         '## Fresh studies, repeats and cost',
         'Fresh-case Sol and MedGemma testing was prespecified, not assigned to an apparent winner. Its 30 studies do not validate all three GPTs or specialist roles. Repeat runs are paired stability observations and never inflate patient counts.',
         '| Fresh scope | Model | Qualified responses /10 (95% CI) | Median seconds |',
         '|---|---|---|---|']
for x in ops:
    if x['stage'] == 'fresh-validation':
        text.append(f"| {x['modality']} | {model(x['model'])} | {prop(x['valid_structured'])} | {format(x['median_seconds'],'.1f') if x['median_seconds'] is not None else 'unmeasured'} |")
text.append('Fresh diagnostic support is sparse and does not replicate every primary endpoint: the ten fresh CXR studies contain no explicit positive effusion, pneumothorax or consolidation assertions; their five cardiomegaly positives resolve in 1/5 Sol and 3/5 MedGemma outputs. The ten fresh CT studies contain one explicit nodule positive: neither workflow resolves it (Sol unresolved, MedGemma explicitly absent). No reference-positive white-matter signal-foci assertion is coded in the ten fresh MRI studies under the frozen rule, so that narrower primary finding receives no scored fresh validation here. This is a coding limitation: MR-FRESH-003 describes frontal white-matter gliotic lesions that the narrow rule omitted, and MR-FRESH-002 describes cerebellar masses omitted by the mass rule. Neither omission means the reports lack those findings; both remain unscored without retrospective label changes. Both Sol and MedGemma resolve 1/2 atrophy positives and 1/1 chronic-infarction positive in fresh MRI; these tiny counts do not establish broad MRI accuracy. All class-specific denominators, unresolved categories and intervals are in the full tables.')
for name in sorted({x['model'] for x in repeats}):
    chosen = [x for x in repeats if x['model'] == name]
    both = sum(x['both_valid'] for x in chosen); same = sum(x['labels_identical'] is True for x in chosen)
    text.append(f"\n{model(name)}: {same}/{both} repeat pairs with identical finding-status objects among pairs with two qualified responses; {len(chosen)-both}/{len(chosen)} pairs lack two qualified responses. These are descriptive stability counts, not independent clinical cases.")
cost=read('resource-cost-inventory')
gpt_groups=[x for x in cost['platform_usage_by_stage_model'] if x['model'].startswith('gpt-')]
extra=cost['native_only_development_observed_usage']
gpt_input=sum(x['input_observed_subtotal'] or 0 for x in gpt_groups)+extra['input_tokens']
gpt_output=sum(x['output_observed_subtotal'] or 0 for x in gpt_groups)+extra['output_tokens']
text.append(f"Observed GPT diagnostic-case usage, including development and the four native-only receipts, is {gpt_input:,} input tokens and {gpt_output:,} output tokens. This is a measured subtotal separate from the investigation/curation assistants. Local MedGemma has {cost['medgemma_inference_records_with_duration']} measured serving records totaling {cost['medgemma_inference_seconds_observed_sum']:.1f} inference seconds, plus {cost['medgemma_inference_duration_missing_count']} records without duration; {cost['medgemma_requests_rejected_before_inference']} additional guard rejections occur before inference. Serving records include development and cannot be substituted for the 160 frozen study reads. These quantities are not dollar or energy totals.")
control_cost=read('role-cost-attribution')['same_case_control_groups']
text += ['### Component timing on identical control studies',
         'These medians restrict all three role workflows to the same prespecified controls within each modality/model. They sum recorded diagnostic components for a hypothetical separately deployed workflow, including specialist inference where required. They exclude setup/preprocessing, are not observed serial wall time, and do not establish a price or latency ranking. Pending or incomplete timing remains unavailable. No additional inference was performed for this accounting refinement.',
         '| Scope / model | Same control studies | Delegated seconds | Second-reader seconds | Self-review seconds |',
         '|---|---|---|---|---|']
for modality,name in sorted({(x['modality'],x['model']) for x in control_cost}):
    values=[next(x for x in control_cost if x['modality']==modality and x['model']==name and x['configuration']==configuration) for configuration in ['delegated','second-reader','self-review']]
    duration=[f"{x['median_serial_diagnostic_component_seconds']:.1f}" if x['median_serial_diagnostic_component_seconds'] is not None else 'pending / unmeasured' for x in values]
    text.append(f"| {modality} / {model(name)} | {values[0]['planned_cases']} | {duration[0]} | {duration[1]} | {duration[2]} |")
text += ['The original self-imposed conversation ceiling was 1000, based on 29 development conversations. Independent native-thread reconciliation found 31, including two off-depth quarantined reads. Before reaching the original ceiling, the operating cap was prospectively corrected to 1002 to finish the same 970 frozen assignments plus one auxiliary read. The original protocol remains unchanged and the deviation is explicit in evidence/budget-accounting-correction.json. All development dispatches count, including failures and quarantines; no extra experimental conditions were added.',
         '\nNo purchases or upgrades were made. The authorized free banked reset was used. Existing account quota, CPU and GPU are shared; durations include contention. Cached input is a subset of input and is not added twice. Missing usage is not zero cost. Native case starts are limited to 6/min; internal graphical-agent model round trips are not independently rate-limited by that dispatch limiter. MedGemma serving compute is measured locally; electricity, depreciation and clinician costs are unpriced.',
         'The 180s/120s limits govern diagnostic turns after setup/dispatch. Recovery-assisted closure and preprocessing can take much longer and are not included in median inference latency. First-attempt workspace reliability differs from recovery-assisted response capture; both are recorded in operational-metrics.','A cached specialist read is physically inferred once. An independently deployed consultation workflow must account for initial GPT inference, specialist inference and synthesis inference; the tool’s cached lookup time alone is not the full cost. Machine-readable operational data contain usage subtotals, missing-measurement counts, latency and status categories. `report/resource-cost-inventory.json` separately includes development, all recorded local inference durations and the latest per-case preprocessing receipts; overlapping rerun receipts are not added. Four additional development dispatches lack framework results but have audited native receipts: 434573 input tokens, including 341632 cached, and 1927 output tokens. These are counted once in the corrected guards and separate cost inventory, without inventing controller outcomes. Whole lifecycle dollar/energy cost remains unavailable.',
         'Controller development, investigation, curation and audit assistant usage is outside the diagnostic-case token ledger. Consequently the case totals do not represent the complete cost of this investigation. `report/response-coverage-audit.json` separately records descriptive prompt-limit violations, exact filename references, actual native screenshot counts and recorded graphical action outcomes; it does not retrospectively change frozen clinical scoring. Screenshot counts alone do not prove unique slices or complete anatomical coverage.',
         '`report/role-cost-attribution.json` attributes delegated roles to the fresh GPT turn plus independent specialist inference; second-reading to original GPT, specialist and synthesis turns; and self-review to two GPT turns. These are component duration/token observations for separate deployment scenarios, not measured serial wall time or additional physical GPU executions. Preprocessing and setup remain separate. A standalone limited differential was not elicited by the frozen schema, so differential-diagnosis quality is unmeasured.',
         '## Representative report-supported outcomes and failures',
         'Examples below are selected by deterministic case ordering to illustrate measured categories, not to estimate their prevalence. They concern only explicit report assertions. Additional findings without a reference assertion are unscorable, rather than automatically false. Detailed causal inspection and independent trace audits accompany the final report.',
         'The major-conclusion source audit checks all ten report-positive pneumothorax studies and all nineteen nodule-positive CT studies. CT-EVALUATION-008 has one historical nonvisualized nodule clause incorrectly tagged present by the mechanical coder; independent current nodules and the impression support the case-level positive label. The clause defect is retained and disclosed, with no label, denominator or result change. Existing report concordance does not establish whether a lesion is visible in the particular delivered frames.',
         '| Category | Scope / model / case | Finding | Reference → output | Preserved result |',
         '|---|---|---|---|---|']
examples = []
for modality in ['CXR', 'CT', 'MR']:
    eligible = [x for x in tasks if x['stage'] == 'evaluation' and x['arm'] == 'B' and x['configuration'] == 'primary' and not x['attempt'] and x['modality'] == modality]
    for category, predicate in [('confirmed concordance', lambda x:x['scorable'] and x['correct']), ('explicit report-positive omission', lambda x:x['scorable'] and x['label'] == 1 and x['prediction'] == 0), ('explicit report-negative addition', lambda x:x['scorable'] and x['label'] == 0 and x['prediction'] == 1), ('insufficient or failed label resolution', lambda x:not x['scorable'] and x['status'] != 'not_run')]:
        chosen = sorted((x for x in eligible if predicate(x)), key=lambda x:(x['case_id'],x['model'],x['task']))
        if chosen:
            x = chosen[0]; result = next(r for r in rows if r['stage']==x['stage'] and r['case_id']==x['case_id'] and r['model']==x['model'] and r['arm']=='B' and r['configuration']=='primary' and not r['attempt'])
            examples.append(dict(category=category, **x, result_path=result['result_path']))
            output = 'present' if x['prediction'] == 1 else 'absent' if x['prediction'] == 0 else x['status']
            text.append(f"| {category} | {modality} / {model(x['model'])} / {x['case_id']} | {x['task']} | {'present' if x['label'] else 'absent'} → {output} | [{x['case_id']}]({result['result_path']}) |")
(O/'decision-example-cases.json').write_text(json.dumps(examples,indent=2)+'\n')
text += ['## Concrete action and remaining evidence',
         '**Supported for the stated research decision:** retain reproducible image-attachment and isolated-viewer engineering only where its completed operational gate and trace audit pass. Use the measured task-specific intervals to choose a narrower external validation target; do not choose a general-purpose “best radiology model” from this cohort.',
         '**Not supported:** autonomous clinical use, radiologist-level claims, universal modality coverage, treating successful JSON as a correct diagnosis, claiming MedGemma is free or equivalent, or deploying the originally contaminated viewer-context configuration.',
         '**Insufficient evidence:** broad MRI accuracy and specificity, institution-independent generalization, severity of unadjudicated errors, full-study versus selected-image interpretation, matched-evidence model superiority, and dollar return on investment. Under the frozen conservative clause coder, the selected MRI reference assertions include no target negatives; this is a limitation of this sampled endpoint/coding policy, not a claim that the source dataset has no normal studies. Reports were translated/restructured by dataset authors using another model.',
         'To change those decisions, obtain institution-separated existing report-grounded cases with explicit positive and negative references, stronger original-language/reference reconciliation, technical coverage audits and preregistered precision targets. About 385 independent positives and 385 negatives per task provide a worst-case normal-approximation 95% margin near ±5 percentage points; zero misses in 59 positives yields a one-sided exact 95% upper miss-rate bound below 5%. This is sample planning, not a claim that case counts alone establish clinical safety.',
         '## Full tables, provenance and reproducibility',
         'The following appendix is regenerated from frozen assignments and preserved case records. It includes modality/task uncertainty, all-assigned failures, role transitions, source limitations, identifiers, isolation, sources and artifact paths. Private credentials and original reports remain separately protected. See [the requirement-to-evidence audit](REQUIREMENT-AUDIT.md) for all 15 requested responsibilities, their artifact locations and explicit gaps.']
formatted=[]
for line in text:
    if formatted and not (line.startswith('|') and formatted[-1].startswith('|')):
        formatted.append('')
    formatted.append(line)
full = '\n'.join(formatted) + '\n\n---\n\n' + (R/'REPORT.md').read_text()
out = R/'DECISION-REPORT.md'; out.write_text(full); out.chmod(0o600)
