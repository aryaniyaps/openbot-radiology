# Deep Research: What Has Worked in Radiology, with Direct Frontier Models as the Priority

**Research date:** 1 October 2026. **Scope:** direct, off-the-shelf GPT/Gemini/Claude image interpretation first; techniques, report reasoning and specialist systems second. **Depth:** exhaustive, targeted primary-source synthesis. This is not a registered systematic review or a new diagnostic benchmark.

## Executive summary

**Yes: successful radiology AI exists, and there are genuine positive results using frontier models directly. Our previous benchmark does not show that all frontier-model approaches fail.** The strongest direct positives are bounded tasks with carefully constructed evidence: GPT-4o correctly diagnosed 37/45 selected emergency abdominal CT cases using several representative slices and clinical context; Gemini 3 Pro Preview achieved about 90% accuracy on a narrowly defined CBCT abnormality task with an external sample. These are meaningful results, but the investigators or radiologists selected diagnostically useful images. They do not establish that the models can search an unselected examination, find every important lesion and produce a safe final report. [Abdominal CT study](https://www.mdpi.com/2379-139X/11/10/108), [CBCT study](https://pmc.ncbi.nlm.nih.gov/articles/PMC13499149/).

**The most consistent frontier-model strength is reasoning from reliable findings, rather than discovering those findings in pixels.** In a 128-case thoracic study, GPT-5 top-five diagnosis accuracy increased from 24.7% with images to 59.1% with radiologist-written descriptions. In 228 histopathology-confirmed liver lesions, two-step GPT-4o reached 78.9% using the findings section of existing reports, versus 68.0% for a one-step approach. Neither study establishes autonomous visual diagnosis. [Thoracic parsing/reasoning study](https://snu.elsevierpure.com/en/publications/decoupling-visual-parsing-and-diagnostic-reasoning-for-vision-lan/), [Liver-lesion study](https://onlinelibrary.wiley.com/doi/10.1111/liv.70115).

**The best next investigation for this project is a stronger direct-frontier input and evaluation protocol, not a larger generic prompt or an automatic retreat to MedGemma.** Compare a current GPT with native high-resolution images, a Gemini with controlled volume/video input, and a Claude with explicit resolution controls. Use patient-held-out, existing-report-grounded cases; separate visual discovery, localization, diagnostic reasoning and report quality; freeze prompts and thresholds before testing. This recommendation is an inference from the literature and API capabilities, not a demonstrated hospital-ready solution. The evidence also contains large direct-frontier failures, including 10,675 pneumothorax images and poor lesion-localization results in a real DICOM viewer. [Large pneumothorax study](https://pmc.ncbi.nlm.nih.gov/articles/PMC13530647/), [ABRA viewer benchmark](https://arxiv.org/abs/2605.11224).

[Executive PDF](../../output/pdf/Radiology-Frontier-Research-Executive-Report.pdf) provides a five-page decision brief; the sections below retain the full evidence and proposed protocol.

## 1. What counts as a success?

Six different endpoints are often described as “AI interpreting radiology.” They must remain separate:

| Endpoint | What a good result demonstrates | What it does not demonstrate |
|---|---|---|
| Exam or quiz answering | Choosing a diagnosis from a teaching case or answer options | Discovering abnormalities in an unselected study |
| Selected-image classification | Recognizing a named finding on a representative image | Selecting the relevant slice or finding other abnormalities |
| Full-study visual discovery | Finding and localizing abnormalities across an examination | Complete reporting, management or patient benefit |
| Findings-to-diagnosis reasoning | Converting reliable imaging observations and context into a differential | Independent verification that the observations are present |
| Report quality assurance | Detecting specified errors or inconsistencies | Safe automatic edits or detection of every clinically important error |
| Hospital workflow improvement | Measured improvement in reading, triage or care delivery | Autonomous diagnosis, unless specifically tested |

The distinction is empirical. A direct GPT-4o CT study obtained 82% final-diagnosis accuracy but substantial unsupported findings in a separate image-only task. A specialized mammography randomized trial improved detection and reduced reading workload while retaining human readers. These outcomes answer different questions. [CT study](https://www.mdpi.com/2379-139X/11/10/108), [MASAI screening analysis](https://www.sciencedirect.com/science/article/pii/S258975002400267X).

The evidence classifications below are descriptive: prospective clinical evidence; external retrospective validation; single-center retrospective evaluation; public teaching/exam benchmark; research preprint; official implementation documentation. They are not formal GRADE ratings. Results are not pooled across diseases, prevalences, inputs or model versions.

## 2. Direct frontier models: the credible positive results

### 2.1 GPT-4o can answer some well-constructed CT diagnostic questions

The emergency abdominal CT study included 45 retrospectively selected cases and 243 JPEG images, with four to seven images per case. Radiologists selected and windowed representative slices. GPT-4o received age, sex, presenting complaint, examination and laboratory information, and was asked for one diagnosis. It was correct in 37/45 cases, or 82.22%; six residents scored 34–40/45. The numerical comparison is encouraging, but a nonsignificant difference in a small study is not equivalence. [Primary full text](https://www.mdpi.com/2379-139X/11/10/108).

In a separate session, an image-only prompt asked for findings. The reported 75% hallucination figure refers to the proportion of listed findings without a correlate on the supplied images. It is **not** 75% of patients receiving an incorrect final diagnosis and is **not** the same prompt as the 82% diagnostic result. The practical lesson is to measure supported observations separately from the final answer. Several correct diagnoses can coexist with unreliable supporting descriptions. [Methods and results](https://www.mdpi.com/2379-139X/11/10/108).

**Transfer to our setup:** reproduce a bounded, clinically contextualized question on several appropriately windowed images. Keep a distinct full-study-discovery arm. Do not give a model gold diagnoses, postoperative outcomes or a report impression and call the answer visual diagnosis. Expert image selection is a major privileged input; an automated selector must earn that capability separately.

### 2.2 Gemini 3 Pro Preview has a narrow externally tested visual success

The CBCT study evaluated condylar osseous changes using one sagittal image for each of 72 internal patients, then 70 external images with 35 abnormal and 35 normal cases. Gemini 3 Pro Preview achieved 90.3% internal accuracy and 90.0% external accuracy; external sensitivity was 85.71% and specificity 94.29%. A fixed anatomical checklist asked about cortical integrity, erosions, osteophytes and related features. [Primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13499149/).

This is a genuine zero-shot frontier result, but the model did not search the CBCT volume. Radiologists chose the affected side or the most conspicuous lesion, and external cases with artifacts or incomplete anatomy were excluded. Labels were newly assigned by radiologists. It therefore cannot be reproduced under our “existing doctors' reports only” constraint without an independently available report-supported reference set. The apparent Gemini advantage over GPT-5.2 did not meet the paper's multiplicity-adjusted significance threshold. Temperature zero without repeat testing does not establish deterministic reliability. [Methods and statistics](https://pmc.ncbi.nlm.nih.gov/articles/PMC13499149/).

**Transfer:** a systematic anatomical checklist and a tightly defined endpoint are worth testing. This study does not establish Gemini as the best general radiology model, nor establish clinical authorization for its use.

### 2.3 Frontier models can use images on examinations, but examinations are a different task

On a 100-question Japanese radiology board examination, Gemini 2.5 Pro Preview scored 76% and o3 75%, above the human mean of 72.9%. For the image-question subset, Gemini improved from 63.5% without images to 75.0% with images. This is evidence of an actual visual contribution, rather than entirely text-driven performance. Multiple-choice options and teaching-image selection still make it unlike a whole examination. The paper's 2025 model prices are historical and are not used here as current costs. [Primary article](https://www.sciencedirect.com/science/article/pii/S1076633225010372).

A separate 282-question residency examination found Gemini 2.5 Pro at 83.0% and GPT-5 at 82.3% overall, versus residents at 78.2%; residents led the image subset, 80.4% versus GPT-5 at 73.6%. Overall exam scores can conceal a visual performance gap. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/41224539/).

### 2.4 Some direct pneumothorax results are positive, but highly dependent on the cohort

In 220 standing PA chest radiographs, evenly split positive/negative, GPT-4o detected 78/110 pneumothoraces and correctly rejected 106/110 negatives: sensitivity 70.9%, specificity 96.4%. Most positives were large; trauma, postoperative and ICU cases were excluded. Small-lesion AUC was 0.439, versus 0.894 for large lesions. This is a bounded image-only success, with an important small-lesion failure. [Primary full text](https://link.springer.com/article/10.1186/s12890-025-04041-w).

Another study of 172 CT-confirmed positive cases found markedly better performance in older patients and large pneumothoraces than in children or small lesions. Its lack of negatives prevents specificity assessment, and its terminology for three-repeat accuracy is inconsistent. Do not treat its repeat-based percentages as ordinary per-read sensitivity. [Primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12431401/).

The headline “GPT-5.1: 100% sensitivity” from a 240-patient study requires caution. The methods list diagnoses, surgical status and length of stay among available data and say all available data were shared. They do not clearly establish that these outcome-related fields were withheld. The reported 30/30 sensitivity is therefore not accepted here as clean image-detection evidence; leakage remains unresolved, rather than proven. [Primary full text](https://link.springer.com/article/10.1186/s12890-026-04151-z).

## 3. The clearest frontier strength: reasoning and checking from established findings

### 3.1 Separating perception from reasoning changes the conclusion

In the thoracic study of 128 sourced quiz cases, GPT-4o top-five accuracy was 15.9% with images and 40.1% with radiologist descriptions; GPT-5 was 24.7% and 59.1%, respectively. Patient metadata accompanied both conditions. Median model-generated imaging-description quality was only 2/4. Better descriptions were associated with more accurate diagnoses. The study supports a **perception bottleneck**, not a conclusion that model reasoning is useless. Top-five differential inclusion is also less demanding than a correct single final diagnosis. [Author-hosted primary abstract](https://snu.elsevierpure.com/en/publications/decoupling-visual-parsing-and-diagnostic-reasoning-for-vision-lan/).

The 67-case KSUM quiz study similarly found that adding descriptive imaging text raised diagnosis performance across GPT, Claude and Gemini. This intervention supplied expert observations; it did not merely improve the model's own pixels. Its “multiagent” prompt was role-play within one prompt, not independent model readers. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12081132/).

In 56 JAMA neuroradiology quizzes, Claude 3.5 achieved 76.8% with rephrased text plus images and the same 76.8% with rephrased text alone. Image-only localization was much weaker. Public-case exposure and wording changes do not eliminate all memorization concerns. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12675488/).

### 3.2 Existing reports offer a feasible, separately useful evaluation track

The focal liver-lesion study evaluated 228 lesions with histopathology references. Models received clinical information and human-written findings, excluding the impression used for comparison. Two-step GPT-4o achieved 78.9% diagnosis accuracy, versus 68.0% single-step and 73.2% Gemini. Real-world reports reached 80.0%. GPT assistance did not improve the radiologists' diagnostic accuracy. The exact two-step supplementary prompt was inaccessible in this collection, so it must not be invented as a ready-to-run recipe. [Primary abstract](https://onlinelibrary.wiley.com/doi/10.1111/liv.70115).

This is particularly compatible with the user's constraint: use cases with valid existing reports and evaluate findings-to-differential reasoning without commissioning new doctor labels. It measures reasoning from already interpreted images. It should be presented as that useful task, rather than as automated image interpretation.

### 3.3 Proofreading can help, but false alerts and harmful revisions matter

GPT-4 detected 124/150 inserted errors in 200 reports in a 2024 study, or 82.7%. This is encouraging for defined reporting mistakes, not proof that it catches all clinical errors. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/38625012/).

The larger head-CT validation is more instructive. In its enriched test component, sensitivity was 84% for interpretive and 89% for factual errors. On 10,000 unaltered reports, however, GPT-4 flagged **1,792 reports**, with **96 true errors confirmed**, giving PPV **0.054**. The 96 is the true-error count, not the total alert count. A hospital workflow must account for roughly nineteen alerts per true error in this dataset. Some false-positive suggestions were useful stylistically, but that does not make them true error detections. [Full-text Experiment 2](https://pubs.rsna.org/doi/10.1148/radiol.240701).

A 2026 zero-shot study of GPT-4.1 on 1,024 deliberately corrupted report variants found substantial failures on anatomical and physiologically impossible statements. Another evaluation of real report revisions found a fraction of suggestions potentially harmful. The credible role is inspectable suggestions with source quotations, rather than automatic “correction” or silent overwriting of physician text. [Error-type benchmark](https://link.springer.com/article/10.1007/s00330-026-12697-z), [Real-world revision study](https://pubmed.ncbi.nlm.nih.gov/40576664/).

## 4. Direct frontier failures that a better protocol must address

| Study | Evidence construction | Result | Why it matters |
|---|---|---|---|
| [10,675 pneumothorax CXR](https://pmc.ncbi.nlm.nih.gov/articles/PMC13530647/) | SIIM-ACR; 2,379 positives, 8,296 negatives; aspect-preserving 1024 PNG; zero-shot binary APIs | Sensitivity: GPT-4o 17%, Claude 4 Sonnet 23%, Gemini 2 Pro 22%; specificity 92–95% | Mostly-negative overall accuracy can conceal extensive misses. This corroborates our weak pneumothorax findings. |
| [CheXpert operating points](https://pmc.ncbi.nlm.nih.gov/articles/PMC13361219/) | Three balanced cohorts, 1,500 images each; binary label plus confidence | GPT-5.4 edema: AUC .836, sensitivity 4.3%, specificity 99.7%. Gemini 2.5 Pro: sensitivity 97.3%, specificity 24.1% | Good score ranking does not mean a usable binary decision. Opposite model biases need calibration and false-positive analysis. |
| [Thoracic device positioning](https://pmc.ncbi.nlm.nih.gov/articles/PMC13257059/) | 4,813 complete CXR cases; GPT-4o, Gemini 3.1 Flash Lite Preview, Claude Sonnet 4.6 | Abnormal-position balanced accuracy .41–.53; humans numerically better in all 42 paired comparisons | Device presence and correct position are different visual tasks. Prompt variants changed sensitivity substantially. |
| [377 teaching-image cases](https://pmc.ncbi.nlm.nih.gov/articles/PMC12341017/) | Selected radiograph/CT/MRI thumbnails; no complete volumes | 33.2% satisfactory diagnosis **or** description; both correct in 24.1% | Even expert image selection does not guarantee useful general reporting. |
| [RadLE](https://arxiv.org/abs/2509.25559) | 50 deliberately difficult spot diagnoses; repeated frontier runs; preprint | Radiologists 83%, trainees 45%, GPT-5 30%, Gemini 2.5 Pro 29% | Longer reasoning did not remove a visual gap. Difficulty-enriched results are not general hospital prevalence estimates. |
| [ABRA](https://arxiv.org/abs/2605.11224) | 655 generated tasks in real OHIF/Orthanc, including annotation and longitudinal studies; preprint | Real annotation outcome 0–25%; oracle annotation 69–100%; tool execution high | Driving the viewer is easier than finding the lesion. An oracle detector is a diagnostic-information intervention, not a demonstrated detector. |

These studies do not all measure the same endpoint, and cannot be averaged into a general “radiology accuracy.” They do show why completion, prose fluency, model size and a medical exam score cannot stand in for lesion-level performance.

### The operating-point opportunity is real, but remains an experiment

The CheXpert study derived continuous scores from self-reported confidence and binary decisions. GPT-5.4 had useful ranking discrimination while making very conservative binary calls; Gemini frequently overcalled. That is a reason to test prompt operating points and development-set thresholds. It is **not** evidence that choosing a threshold has already made either model clinically satisfactory, or that confidence is a calibrated probability. [Primary results](https://pmc.ncbi.nlm.nih.gov/articles/PMC13361219/).

Before any threshold experiment, verify the exact score convention: confidence in the chosen answer and probability of disease are not interchangeable. Re-estimate discrimination and calibration on held-out patients; do not select a threshold on the final test set. Missing or abstained answers must remain visible. A low-prevalence hospital can have substantially more false alerts than a balanced research set.

## 5. Which techniques actually improved results?

| Technique | Evidence | Assessment for this project |
|---|---|---|
| Relevant pre-imaging clinical context + several useful slices | Positive 45-case GPT-4o CT diagnostic exercise | High-priority hypothesis. Compare context-only controls; do not include gold impressions or outcome data. |
| Anatomical checklist + selected key image | Positive Gemini CBCT classification with an external set | Useful bounded-task design. Full-volume selection remains untested. |
| Findings-first, diagnosis-second | Thoracic visual-versus-description ablation; liver two-step reasoning | Strongest support when findings are reliably supplied. A model inventing its own findings has not earned the same advantage. |
| Multiple MRI sequences | [Gemini 3.1 Pro disc-herniation study](https://pubmed.ncbi.nlm.nih.gov/42581174/) | Sensitivity rose, but specificity and accuracy fell. More evidence is not automatically a net benefit. |
| Video with localization overlays | [Gemini 3 Pro lumbar stenosis](https://doi.org/10.1177/21925682261448823) | Overlay did not improve performance; no video-versus-still ablation. Test controlled sampling rather than assume video solves volumes. |
| Longer reasoning / repeated answers | RadLE; repeated pneumothorax studies | No established general rescue. More tokens and correlated votes cannot create missing visual information. |
| Meta-prompted report checking | [Dental image/report-error study](https://pubmed.ncbi.nlm.nih.gov/40790280/) | Prompting improved a narrow report-verification endpoint; localization still limited. Not general CT/MRI diagnosis. |
| Frontier plus specialist tools | [MedRAX](https://arxiv.org/abs/2502.02673), [MRI tool agents](https://arxiv.org/abs/2604.16729) | Demonstrated research gains for defined tools/tasks. This is a hybrid, not direct frontier-only perception. |
| Ground-truth-fed adaptive memory | [Evo-MedAgent](https://arxiv.org/abs/2604.14475) | Reported gains rely on answer feedback during sequential evaluation. Freeze learning on development cases before a hospital-like test. |
| Native detail, crops and iterative reinspection | Official API capabilities; trained visual-agent studies | Plausible engineering improvements; direct radiology benefit must be measured in an ablation. |

### 5.1 More MRI data can increase misses-to-false-alert tradeoffs

For Gemini 3.1 Pro disc herniation, the paired cohort had 119 patients: 31 positive and 88 negative. T1-only input yielded sensitivity .58, specificity .74, accuracy .70. Adding T2 increased sensitivity to .77 but reduced specificity to .51 and accuracy to .58; false positives rose from 23 to 43. Accuracy was significantly worse in the paired comparison. The primary input was mid-sagittal slices, not an unrestricted full-volume read. [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/42581174/).

In the lumbar-stenosis video study, 100 examinations contributed 500 spinal levels. Without an overlay, accuracy was 75.6%, weighted kappa .39 and severe-stenosis sensitivity 41.8%. With an overlay, those were 73.2%, .32 and 30.9%; differences were not significant. Most levels were normal, so aggregate accuracy is an inadequate summary. There was no controlled comparison proving video superior to selected still images. [Primary paper](https://doi.org/10.1177/21925682261448823).

### 5.2 Tools can work when the underlying measurement is trustworthy

GPT-5.4's handoff-based MRI agents achieved human-assessed response accuracy of 95.8% for single-timepoint and 91.3% for longitudinal questions using local segmentation, registration and volumetry. The overall tasks contained 150 and 75 cases, respectively; human assessment covered a fixed 30% of cases per run, so those percentages are not an all-case clinical diagnostic accuracy. Images were not sent to the LLM; it operated tools and consumed their outputs. Pathology was already described, and segmentation accuracy bounded the results. This is promising quantitative assistance, not proof of discovering an unknown disease directly. [Research preprint](https://arxiv.org/abs/2604.16729).

MedRAX improved a six-option chest-case benchmark from GPT-4o's 56.4% to 63.1% with specialist tools. It used public cases and generated questions, and the reference implementation relied on an RTX 6000. Neither clinical deployment nor our 8 GB feasibility follows from the result. [Research preprint](https://arxiv.org/abs/2502.02673).

These successes also explain why our previous MedGemma consultation result should not be generalized to all hybrid systems. A weak or invalid specialist answer does not provide a reliable measurement. Useful augmentation must add independently informative evidence, rather than another model's unsupported opinion.

## 6. Direct frontier input: a material gap in our previous evaluation

Our completed benchmark tested one fixed, budgeted pipeline: original CXR views, selected CT/MRI montages, limited graphical inspection, specific prompts and model versions. It did not compare current native-resolution API input, comprehensive volume coverage, every possible window/sequence, adaptive crops, calibrated thresholds or all current Gemini/Claude models. The existing protocol and failure results remain intact. [Local decision report](../../benchmark/runs/20260930T1418Z-graysby/DECISION-REPORT.md).

### 6.1 Current GPT image preprocessing differs by detail mode and adapter

OpenAI's current image documentation lists `gpt-6-astra` support for `original` detail. Its original mode preserves dimensions subject to documented limits and rejects images beyond a separate 30,000-patch input ceiling; high mode has a smaller resizing budget. This is an actionable reason to test native detail instead of assuming the upload resolution is the delivered resolution. [Official documentation](https://developers.openai.com/api/docs/guides/images-vision).

Our managed Codex path resized audited MRI montages from 2048×1620 to 1779×1408 before dispatch. Changing a downstream API detail flag cannot restore pixels already discarded upstream. A direct-input evaluation must audit the entire source-to-model path. Preserving pixels does not solve small lesions hidden in unsupplied slices, and this research has not measured the accuracy gain from native detail. [Retained coverage analysis](../../benchmark/runs/20260930T1418Z-graysby/DECISION-REPORT.md).

OpenAI also explicitly describes specialized CT interpretation as outside its vision models' suitable use. That is provider guidance, not a performance measurement and not a declaration that research is impossible. It prevents presenting a successful prototype as provider-endorsed clinical imaging. [Official limitations](https://developers.openai.com/api/docs/guides/images-vision#limitations).

### 6.2 Gemini video is not automatically complete scan coverage

Google's current documentation describes default static video sampling at one frame per second, customizable sampling, and higher-resolution frame settings. If a CT cine traverses ten slices per second, default one-FPS sampling can omit about nine of every ten slices. That example is an inference from the documented sampling rate; actual extracted coverage must be audited. [Official video documentation](https://ai.google.dev/gemini-api/docs/video-understanding).

Gemini image and video frame budgets differ. A high-resolution individual image can have substantially more visual tokens than an ordinary video frame. A long video can therefore preserve anatomical coverage while sacrificing per-frame detail. Use a controlled frame-to-slice mapping, explicit series/window labels and targeted high-resolution stills. Verify those advantages against identical-evidence image and video arms rather than declaring video inherently better. [Official resolution documentation](https://ai.google.dev/gemini-api/docs/media-resolution).

The current docs also describe newer agentic video modes and newer model releases. Their general-video quality claims are not radiology results. Literature on Gemini 2.5 or 3.1 cannot be assigned to a newer 3.8 model. Likewise, older GPT-5 evidence cannot be treated as direct validation of our GPT-6 identifiers. Pin exact model versions and record changes.

### 6.3 Claude detail and localization require explicit coordinate handling

Anthropic documents different native image-resolution tiers and automatic resizing. Crop coordinates refer to the image the model actually sees; reproject them to the original source. The current higher-resolution tier does not itself establish better disease detection. Claude also states that it is not designed for complex diagnostic CT/MRI interpretation. [Official vision documentation](https://platform.claude.com/docs/en/build-with-claude/vision), [Coordinate transformation guidance](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates).

### 6.4 More resolution is necessary in some tasks, not sufficient

A recent grounding audit found that good chest-question accuracy could arise partly from language priors. Image removal, region occlusion and replacement exposed differences that ordinary correctness scores missed. GPT-5 did use images selectively, but not uniformly across findings. The paper is a preprint and its intervention metrics should not be treated as a new clinical gold standard. It supports adding appropriate image-dependence controls to a prospective evaluation design. [Grounding audit](https://arxiv.org/abs/2606.17710).

For our proposed test, compare safe-context-only, image-only and combined inputs; optionally replace images with clearly opposite-label cases under the same prompt. Do not demand that an answer change when swapping two images with the same relevant finding. Cropping out an entire lesion may also create an unnatural image. Grounding controls require careful interpretation, not another easy score to optimize.

## 7. What to test first, respecting the preference for direct frontier models

| Candidate lane | Why it deserves a test | Evidence boundary |
|---|---|---|
| Current GPT/Astra with audited native image detail | Existing GPT workflow, documented original-detail capability, strong findings-to-diagnosis reasoning in earlier models | No broad clinical validation of our exact identifiers found; the managed Codex adapter and direct API are different input/access paths, and direct API access or billing has not been established here |
| Gemini with controlled slices/video and high-resolution follow-up stills | Genuine visual contribution on examinations; narrow CBCT positive; native video support | Mixed/negative MRI studies; no general volume-diagnosis solution; newer versions require new testing |
| Claude with explicit image sizing and an independent findings check | Useful comparison of model-specific operating behavior, report reasoning and high-resolution image access | Weak spatial/device results; not established as a best direct image reader |
| Text findings-to-differential / report-consistency lane | Stronger and more reproducible frontier reasoning evidence; existing reports can supply inputs and references separately | Answers depend on human-written observations; not independent image discovery |
| Optional fixed-measurement/tool lane | Strong performance on defined volumetry and segmentation-supported questions | A hybrid comparator, not the user's preferred direct model architecture |

**Priority recommendation:** first test a better direct GPT/Gemini comparison on one task with explicit positive and negative report support. Include Claude if resources allow an informative operating-point comparison. Prefer the model that passes that task's held-out criteria; do not select a universal “best radiologist model” from unrelated papers. Preserve direct inference as a primary arm, and make any tool-assisted arm an explicit comparator.

The simplest defensible architecture is a deterministic imaging front end plus one frontier model per read: normalize orientation and windowing, preserve aspect ratio, expose complete series coverage, provide labeled views, allow a bounded crop/reinspection action, and require traceable per-finding responses. This is an engineering proposal; these combined choices have not been jointly validated here. OpenMausBot can remain the interaction shell if it preserves the required evidence and isolation.

## 8. Other approaches that demonstrably worked in hospitals

The point of these comparators is to identify why success occurred, not to redirect the project automatically to proprietary products.

| Successful approach | Strongest relevant evidence | What made it work |
|---|---|---|
| Specialized mammography triage and reading assistance | MASAI: cancer detection 6.4 versus 5.0/1,000; 44.2% fewer readings. Later interval-cancer analysis met noninferiority, not superiority. | Narrow modality, domain-trained model, defined thresholds, large prospective trial and retained human readers. [Screening analysis](https://www.sciencedirect.com/science/article/pii/S258975002400267X), [Interval cancers](https://www.sciencedirect.com/science/article/pii/S014067362502464X) |
| AI replacing one screening reader | ScreenTrustCAD: 55,581 women, 261 versus 250 screen-detected cancers, noninferior paired design | A constrained reading role with downstream consensus; not unsupervised care. [Primary trial](https://www.sciencedirect.com/science/article/pii/S258975002300153X) |
| Chest-nodule detection assistance | Randomized screening study: actionable nodules 31/5,238 versus 13/5,238 | Task-specific detector plus radiologist, CT confirmation. Not general CT reporting. [Primary trial](https://snu.elsevierpure.com/en/publications/ai-improves-nodule-detection-on-chest-radiographs-in-a-health-scr/) |
| Stroke detection plus notification | Cluster randomized CTA/LVO workflow: door-to-groin 11.2 minutes shorter | Detection coupled to secure communication and an actionable care pathway; functional outcome benefit not established. [Primary study](https://europepmc.org/article/MED/37721738) |
| Domain-trained VLM report drafting | Janus-Pro-CXR: 296 prospective patients, 18.3% shorter drafting/interpretation time with better assessed report quality | Domain adaptation, junior reader editing and senior approval. Not off-the-shelf DeepSeek or autonomous reporting. [Primary study](https://www.nature.com/articles/s41467-026-72680-6) |

One narrow regulatory example makes the distinction concrete: qXR-PTX-PE has an FDA triage/prioritization indication for adult frontal CXR pneumothorax and pleural effusion. Its submitted 613-case pneumothorax validation reported 94.53% sensitivity and 96.36% specificity. It is not labeled for stand-alone clinical decisions. Lunit's CXR triage and Aidoc's noncontrast-head-CT hemorrhage software similarly have specific workflow indications. These are U.S. device records; they do not establish authorization in India, nor numerical superiority in a head-to-head comparison with our cases. [qXR record](https://www.accessdata.fda.gov/cdrh_docs/pdf23/K230899.pdf), [Lunit record](https://www.accessdata.fda.gov/cdrh_docs/pdf21/K211733.pdf), [Aidoc record](https://www.accessdata.fda.gov/cdrh_docs/pdf22/K221240.pdf).

### Important counterexamples

The LungIMPACT randomized trial analyzed 93,326 CXRs and did not demonstrate faster CXR-to-CT or cancer diagnosis from AI prioritization. Downstream scanner capacity, referrals and care coordination can erase an imaging-model advantage. [Primary trial](https://www.nature.com/articles/s41591-026-04253-5).

A 63,083-study silent normal-CXR trial found clinically significant misses despite high abnormality sensitivity. Selective normal-study automation is a narrower prospect than general reporting, but needs audit and conditional miss rates; a tiny fraction of **all studies** can conceal a larger risk among the auto-cleared subset. Retrospective estimates of potential automation, including ChestLink, are not equivalent to safe prospective autonomous use. [Silent trial](https://europepmc.org/article/MED/42017801), [Autonomous-reporting estimation](https://pubmed.ncbi.nlm.nih.gov/36880947/).

## 9. Open models and volume-aware techniques: useful secondary comparators

**MedGemma 1.5:** Google's volume method uses up to 85 individual axial slices with slice indexes and targeted condition queries: CT uses multichannel HU windows, while MRI uses per-volume min–max normalization. It does not use four distorted wide montages. Our earlier run did not test that method. Even with the official method, CT-RATE macro F1 was 27.0%, precision 34.2%, recall 42.0%. Correcting input mismatch is justified, but is not a promised rescue. Long-context memory fit on our 8 GB GPU has not been established. [Technical report](https://arxiv.org/abs/2604.05081), [Official model card](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card), [Volume notebook](https://github.com/Google-Health/medgemma/blob/main/notebooks/high_dimensional_ct_hugging_face.ipynb).

**Med-Gemini:** published domain-tuned research models generated some radiologist-acceptable reports, including 53% acceptable CT reports. These are not simply the public Gemini API under a good prompt. They demonstrate that adaptation can work, while also illustrating that even dedicated research models did not produce acceptable reports consistently. [Technical paper](https://arxiv.org/abs/2405.03162).

**CT-CLIP/CT-CHAT, Merlin and Pillar-0:** these operate on volumetric representations and report finding-specific discrimination. Merlin has multi-institutional external validation; Pillar offers gated modality-specific weights. They are serious technical baselines but not turnkey general radiologists. CT-CLIP's noncommercial license prevents assuming commercial hospital-use rights. Reported speed or parameter count is not a verified local 8 GB fit. [CT-CLIP paper](https://arxiv.org/abs/2403.17834), [License and implementation](https://github.com/ibrahimethemhamamci/CT-CLIP), [Merlin publication](https://www.nature.com/articles/s41586-026-10181-8), [Pillar-0](https://arxiv.org/abs/2511.17803).

**TotalSegmentator/nnU-Net and nnFoundation:** fixed anatomical segmentation can provide inspectable measurements for a frontier orchestrator; accuracy must be verified for the selected anatomy, protocol and downstream task. Model licenses vary by task; segmentation overlap is not diagnostic accuracy. nnFoundation is a very recent 3D encoder release, not an autonomous clinician. [TotalSegmentator](https://github.com/wasserth/TotalSegmentator), [nnFoundation paper](https://arxiv.org/abs/2609.26924), [Release repository](https://github.com/MIC-DKFZ/nnssl).

These systems should remain optional comparators while direct frontier models are the main investigation. Their role is to help identify whether the limiting factor is visual representation, localization, report reasoning or orchestration.

## 10. A concrete next study without commissioning live doctor review

This is a proposed separately authorized study, not a rerun or retrospective change to the completed benchmark.

### A. Choose a report-supported endpoint

Start with one clear finding and adequate explicit positives and negatives. Retain existing original reports and study identifiers. Do not infer a negative because a finding was omitted from a report. Separate translated, contradictory, historical and uncertain clauses. If reports do not establish lesion visibility or location, mark localization unvalidated rather than invent coordinates.

### B. Separate the clinical questions

1. **Visual discovery:** images plus permissible pre-imaging context; no report findings or impression.
2. **Image-conditioned diagnosis:** several supplied images and safe clinical information; score both the answer and supported observations.
3. **Findings-to-differential reasoning:** existing findings supplied, impression hidden; explicitly a text/reasoning task.
4. **Report consistency:** source statements and a candidate draft; suggestions must quote the conflict and avoid automatic edits.

A success in lane 3 cannot repair a failure in lane 1. A high-quality draft cannot establish that an unseen lesion was excluded.

### C. Use a small, informative set of paired input conditions

Compare the previous montage baseline with individual high-resolution views. For CT/MRI, record window/sequence, slice index and coverage. Add one controlled video or multi-image condition with auditable sampling, then one bounded reinspection condition. Include context-only controls to detect answering from text clues. Avoid testing dozens of prompt variants on the final holdout.

### D. Develop, freeze, then evaluate

Use development cases to set prompts, anatomy checklists, thresholds, crop budgets and parser behavior. Freeze them before patient-separated evaluation. Memory learned from answer feedback stays in development. The final reference reports remain outside the inference context. Validate provider-specific transformations, exact snapshot identifiers and repeatability rather than assume deterministic temperature-zero behavior.

### E. Report the outcomes that can change a decision

For each finding: sensitivity, specificity, positive/negative predictive value at the study prevalence, uncertainty, abstentions and failures. Report unresolved cases in all-assigned bounds, not only completed responses. Separately score supported/unsupported findings, localization where existing references permit, final diagnosis and operational completion. Record actual image evidence, inference latency, total workflow latency, tokens and measured resource costs separately.

### F. Keep the conclusion within the reference standard

Existing doctors' reports permit meaningful retrospective comparisons without recruiting live clinicians. They do not prove every model error's severity, comprehensive image truth or patient-care safety. If a method succeeds, the justified first conclusion is that it meets the defined offline endpoint on held-out report-grounded cases. Hospital deployment and jurisdiction-specific device requirements remain separate questions.

## 11. Contrarian views, uncertainties and unanswered questions

- **“The frontier model is simply too weak.”** Large studies confirm visual gaps, but selected-image successes and operating-point differences show that this is not the whole explanation. Our own input design, coverage and output conventions are potential contributors, not proven causes.
- **“A larger model or more thinking will fix it.”** Difficult-case and device-localization studies do not support this assumption. Public-model reasoning can be good while pixel parsing remains poor.
- **“A high AUC means a usable detector.”** It does not select a clinical operating point or account for missing outputs, prevalence and uncalibrated confidence.
- **“Video supplies the full study.”** Not without verified frame sampling, adequate resolution, every required series and correct orientation/windowing.
- **“The model got the diagnosis, so the observations are trustworthy.”** The CT and quiz results contradict this inference. Supporting findings need separate evaluation.
- **“Fine-tuned research systems prove consumer Gemini/DeepSeek can do it.”** The architecture, training data and evaluation conditions differ. They provide design clues, not model equivalence.
- **“An existing report is complete image truth.”** Reports can omit findings, refer to prior studies, conflict internally or use translated language. We should preserve their limits rather than manufacture certainty.
- **“There is a best frontier model for all radiology.”** The collected evidence does not establish one. Model, task, input and operating point interact; newer available versions are not validated by older papers.

Open questions worth testing: Does native image detail recover small findings under the same case mix? Can complete and labeled slice coverage improve sensitivity without intolerable false alarms? Does model-driven reinspection actually identify relevant regions? Can development-only prompt/threshold calibration generalize? Can a findings-first direct model produce a useful differential without inventing observations? Which modality-specific tasks have enough existing positive and negative reference assertions to answer these questions precisely?

## 12. Sources, collection and reproducibility

The accompanying evidence matrix contains **43 study rows**; these are not 43 independent patient cohorts (for example, MASAI follow-up uses the same randomized cohort). The source index contains **95 distinct URLs**, including alternate publisher/index/repository records for some works.

Evidence was collected with **firecrawl-deep-research** for web/implementation context and **firecrawl-research-papers** for semantic paper search, related-paper expansion, metadata inspection and in-body verification. Primary publisher text, official repositories and author-hosted abstracts were used when indexed passages were unavailable. Some publisher pages failed, PubMed/PMC pages presented CAPTCHA, or supplementary methods were inaccessible; these are explicitly noted rather than filled in from secondary claims.

The source-specific contributions are retained in:

- [Clinical evidence notes](radiology-clinical-evidence-notes.md): direct successes, failures, prospective trials and exact denominator caveats.
- [Model and technique notes](radiology-model-technique-notes.md): current frontier comparisons, task specialization, volume processing and implementation rights.
- [Frontier technique notes](radiology-frontier-technique-notes.md): paired input/prompt effects and methodological controls.
- [Evidence matrix](radiology-frontier-evidence-matrix.csv): study-level endpoints, limitations and source URLs.
- [Source index](radiology-frontier-sources.md): deduplicated URLs from this report and its evidence notes, with source descriptions.

Raw fetched pages and paper-tool results are kept in the Git-ignored `.firecrawl/` directory. No new diagnostic model inference, patient-care decision, purchase, model training or clinician recruitment was performed for this research. The prior benchmark's cases, labels, protocol and outcomes were not changed.

### Rerun inputs

```yaml
workflow: firecrawl-deep-research
paper_workflow: firecrawl-research-papers
topic: Successful radiology AI approaches, prioritizing direct off-the-shelf frontier models
depth: exhaustive
research_cutoff: 2026-10-01
primary_angles:
  - GPT, Gemini and Claude direct pixel interpretation
  - full-volume, video, native resolution, crops and iterative inspection
  - clinical context, findings-first reasoning, calibration and report verification
  - positive, negative and externally validated results
  - specialized clinical successes as comparator architectures
constraints:
  - existing doctors reports as references for any proposed local evaluation
  - no live clinician review commissioned
  - no new inference or retrospective changes to completed benchmark
output: markdown report, evidence CSV, source index and independent review
```
