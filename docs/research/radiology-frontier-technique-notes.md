# Direct frontier-model radiology: technique evidence

Research date: 1 October 2026. Scope: inference with publicly available general-purpose GPT, Gemini and Claude models; pixel interpretation is distinguished from reasoning over supplied imaging findings. This is a primary-source technique review, not a pooled clinical meta-analysis. No diagnostic calls, rescoring, or benchmark changes were performed.

## Decision findings

The evidence supports testing better image delivery and carefully specified prompting. It does **not** support a blanket claim that direct frontier models fail under every technique. Conversely, “video,” “more sequences,” “multiagent,” and “expert role” are not established routes to safe general radiology. The strongest controlled results are task-specific and include important negative findings.

* Public Gemini has been evaluated on lumbar MRI video, but the verified study did not compare video against still images. Its localizer overlay worsened numerical performance without a statistically significant paired difference.
* Adding T2 to T1 in a same-case Gemini 3.1 Pro experiment increased disc-herniation sensitivity while reducing specificity and overall accuracy. Calling this simply an improvement would hide the false-positive tradeoff.
* A GPT-4o dental study provides a genuine positive paired prompt/grounding result with pixels, although its task was verifying deliberately altered reports, rather than diagnosing an unselected CT/MRI study.
* Expert-written imaging descriptions often produce large gains. These results establish reasoning from interpreted findings; they do not demonstrate that the model extracted those findings from pixels.
* Single-prompt “multiagent” roleplay, consensus restricted to agreeing cases, repeated differential-diagnosis unions, and independent-agent synthesis are different interventions. Their denominators and coverage must be reported separately.

The prior selected-montage benchmark is evidence about that implemented pipeline. It does not test public Gemini full-video input, dense sequence-specific images, adaptive high-resolution crops, or all possible workflows.

## Controlled direct-model studies

### 1. Lumbar MRI videos and localizer overlays: negative overlay result

[Gebhard/Kartal et al., Global Spine Journal, 2026](https://journals.sagepub.com/doi/10.1177/21925682261448823) evaluated public Gemini 3 Pro using synchronized sagittal/axial T2 video montages from 100 RSNA exams, comprising 500 lumbar disc levels. Normal/mild stenosis accounted for 371/500 levels. Without localizers, accuracy was 75.6% (95% CI 71.6–79.3), weighted κ .39, and severe-stenosis sensitivity 41.8%. With localizer overlays, these were 73.2% (69.1–77.0), κ .32, and 30.9%. Paired accuracy and severe-sensitivity differences were nonsignificant (p=.303 and .286).

Without overlays, 24/55 severe levels were classified normal/mild; overlays increased that count to 29/55. The majority-class baseline is 74.2%, calculated from the published distribution. Levels are clustered within patients. The study compares overlay presentation, **not video versus stills**, and does not establish that more complete video input solves severe-stenosis detection. Its expert RSNA consensus is an existing reference, but public-dataset exposure and unavailable contributor agreement remain limitations. Published May 2026; full publisher text inspected.

### 2. Additional MRI sequence: increased sensitivity, decreased specificity

[Rodriguez et al., European Spine Journal, August 2026](https://pubmed.ncbi.nlm.nih.gov/42581174/) evaluated Gemini 3.1 Pro on the same 119 SPIDER cases: 31 with herniation and 88 without. Input was a mid-sagittal T1 slice, or paired T1/T2 slices. T1-only sensitivity was .58 (95% CI .41–.74), specificity .74 (.64–.82), accuracy .70 (.61–.77), precision .44 and F1 .50. T1+T2 sensitivity increased to .77 (.60–.89), while specificity fell to .51 (.41–.61), accuracy to .58 (.49–.67), precision to .36 and F1 to .49. T1-only accuracy was significantly higher by exact McNemar testing (p=.044).

False positives increased from 23 to 43. Three-slice supplementary inputs are mentioned, but their results were not verified from accessible full text. This is a selected-slice sequence comparison, not whole-volume MRI understanding. Abstract inspected; missing full-text details remain missing.

The [November 2025 Gemini 2.5 Pro preprint](https://doi.org/10.21203/rs.3.rs-7811515/v1) has different models/cohorts and unpaired input groups. It must not be counted as independent replication of the revised Gemini 3.1 study or used to infer a paired T1/T2 effect.

### 3. GPT-4o prompt and localization improvement: dental verification

[Xiong et al., Clinical Oral Investigations, 12 August 2025](https://pubmed.ncbi.nlm.nih.gov/40790280/) studied 230 panoramic radiographs with 300 manually inserted interpretation errors in accompanying findings. Providing images increased error recall from 2.67% to 43.33%. A meta-prompt integrating several strategies increased recall to 52.67% (p=.022), accuracy from 39.95% to 68.75% (p<.001), and F1 from .42 to .60. Localization succeeded for 137/300 targets, 45.67% (95% CI 40.00–51.34). Providing accurate localization cues added 5.49 percentage points of recall (p=.031).

This is positive controlled evidence that prompt design and grounding can help direct visual verification. The bundled meta-prompt does not isolate each component’s causal contribution. Localization supplied externally is an oracle aid; self-generated localization is a harder task. The 300 targets are not 300 patients, and the intervention is dental report-error verification, not blind CT/MRI diagnosis. Accessible primary abstract inspected; full prompt and split details not independently recovered.

### 4. Six prompts across public GPT, Claude and Gemini: small, inconsistent gains

[Han et al., Ultrasonography, May 2025](https://www.e-ultrasonography.org/journal/view.php?doi=10.14366/usg.25012) evaluated 67 selected KSUM quiz cases with GPT-4o, Claude 3.5 Sonnet and Gemini 1.5 Pro. Inputs included multiple-choice answers and clinical/imaging metadata. Six prompts included CoT, reflection, “multiagent,” and an automatically optimized prompt. **The multiagent condition was a single prompt with assigned roles, not independent model agents.** Pooled optimized-prompt accuracy was 46.3% versus 40.8% basic (p=.035), but differences versus CoT or role-multiagent prompts were nonsignificant. GPT’s prompt comparison was nonsignificant overall; effects varied by model.

Adding descriptions increased pooled accuracy from 46.3% to 66.2% for Claude, 43.5% to 57.5% for GPT, and 39.8% to 60.4% for Gemini. However, 25 descriptions originated in reference-answer material; 42 were written by a blinded radiologist. Six responses per case are repeated observations, not six patients. Public quiz exposure and answer-option cues limit generalization. Full original inspected; exact model versions and collection dates are in its methods.

### 5. Brain MRI prompt elements: expert text dominates; arrows hurt

[Schramm et al., Radiology, January 2025](https://pubs.rsna.org/doi/10.1148/radiol.240689) used 60 challenging, verified MRI cases, three repetitions per condition, and up to four selected sections from two sequences. GPT-4V was accessed through Perplexity, adding a wrapper/retrieval confound. Correctness meant the diagnosis appeared anywhere in the top three.

Image-only correctness was 4/180 (2.2%); images plus arrows 2/180 (1.1%); images plus history 50/180 (28%); images plus expert descriptions 106/180 (59%); the complete combination 124/180 (69%). Descriptions alone achieved 118/180 (66%), and history plus descriptions 117/180 (65%). Images did not independently improve performance significantly (p=.15); annotations were negatively associated with performance. Text-only conditions were added after observing description effects, making that comparison exploratory. Selected lesion-containing images and human descriptions provide substantial assistance; 1,260 outputs represent 60 cases. Full original inspected.

### 6. Clinical and answer-option context versus pixels

[Atakır et al., Diagnostic and Interventional Radiology, September 2025](https://doi.org/10.4274/dir.2025.253460) tested GPT-4o on 129 radiology cases across seven input conditions and three accounts. Image-only accuracy was 19.90%; image+clinical information+options reached 80.88%, while clinical information+options without images reached 75.45%. The image increment over clinical information/options was nonsignificant. Richer-input consistency was κ=.733.

This is a strong reason to include a text-only control when attributing performance to vision. Multiple-choice cues, selected public cases and repeated account responses do not establish clinical sensitivity/specificity or independent patient replication. Existing residents were a comparator, not newly requested review for this research. Original publisher PDF inspected.

### 7. Clinical MRI tumor cohort: reasoning gains, little incremental image benefit

[Sun et al., Neuroradiology, 19 January 2026](https://link.springer.com/article/10.1007/s00234-025-03896-4) evaluated 239 preoperative pathology-confirmed brain tumors, with three repetitions per input method. GPT-4o image-only final diagnosis accuracy was 32% and differential accuracy 54%. Radiological findings plus clinical history achieved 76% and 83%, respectively. Adding images to this text provided only a small, nonsignificant improvement.

This supports using structured interpreted findings for diagnostic reasoning. It does not prove automatic extraction of those findings, screening performance on normal exams, or whole-volume interpretation. Data are available by author request, not verified as a public downloadable image/report cohort. Accessible publisher abstract inspected; image-delivery and subgroup details behind subscription were not assumed.

### 8. Reasoning models, tokens and prompts

[Han et al., European Journal of Radiology, January 2026 online](https://pubmed.ncbi.nlm.nih.gov/41576425/) evaluated 73 quiz cases with o1, Claude 3.7 Sonnet and Gemini 2.0 Flash Thinking Experimental. Image-only CoT accuracy was 56.2%, 49.3% and 37%, respectively. o1 with descriptions reached 71.2%. Role prompts reduced tokens with comparable accuracy for some differential-diagnosis comparisons. Within o1, output token count correlated negatively with accuracy (r=−.41).

These observational correlations do not show that deliberately shortening reasoning causes better diagnoses. Likewise, cross-model token correlations do not establish a universal benefit from more inference compute. Exact prompt ablations and confidence intervals were not available in the inspected abstract. Public quiz selection, answer format and human description assistance must accompany the headline.

### 9. Temperature and repeated diagnosis lists

[Suh et al., Radiology, 2024](https://pubs.rsna.org/doi/10.1148/radiol.240273) studied 190 public Diagnosis Please cases with histories, image legends and selected images. Five repetitions and temperatures 0/.5/1 produced GPT-4V aggregate accuracies 41/45/49% and Gemini Pro Vision 29/36/39%. Temperature differences did not survive the stated multiplicity correction. GPT’s top-one accuracy at temperature 1 was 15%, substantially below its aggregate diagnostic-list result.

Repeated unions of differential diagnoses offer more opportunities to include the answer. They are not majority-vote self-consistency and should not be scored as a single autonomous final diagnosis. Public cases can overlap pretraining. This is weak evidence for a temperature intervention, stronger evidence that endpoint selection changes the apparent result.

### 10. Rich clinical context can coexist with extreme overcalling

[Nelles et al., Diagnostics, March 2026](https://www.mdpi.com/2075-4418/16/5/749) supplied representative MRI slices by sequence plus histories/referral questions to GPT-4o and Claude 3.5 Sonnet. The cohort contained 77 patients and 100 exams, with 50 positive and 50 negative exams. Both models achieved 100% sensitivity, but specificity was only 8% and 4%; accuracy was 54% and 52%. Both hallucinated additional lesions in 12% of exams.

The repeated exams are not 100 independent patients. Without an image-only/context-only ablation, context-induced anchoring is a hypothesis rather than a demonstrated mechanism. This study is direct MRI evidence against judging technique success by sensitivity alone.

### 11. Targeted CT crops, segmentation and guidelines: promising but bounded

[Shi et al., Health Information Science and Systems, online December 2025](https://link.springer.com/article/10.1007/s13755-025-00417-8) evaluated GPT-4.1/GPT-4o using 3D CT-derived multi-slice inputs, nodule coordinates/segmentation and clinical guidelines. The best GPT-4.1 combined setting achieved accuracy .722/AUC .780 on LIDC-IDRI and .767/.780 on LNDb.

Accessible abstract material supports a targeted lesion-characterization workflow, not unassisted full-volume nodule detection. “Lossless 3D” source preparation does not mean the API receives native voxels or preserves all slices internally. Known location/segmentation is external assistance. Sample sizes, exact ablation deltas, confidence intervals and pathology versus rating-based malignancy reference were not independently verified; they must remain unreported rather than inferred from dataset names. The 2026 issue date is not a second publication after its 2025 online release.

## Consensus, adaptive selection and evidence boundaries

[Fusion-Augmented LLMs, October 2025](https://arxiv.org/abs/2510.16057) reports a 234-study CheXpert experiment: GPT 62.8%, Claude 76.9%, similarity-consensus 77.6%; a separate 50-case synthetic-note experiment reports 84%, 76% and 91.3%. Consensus uses an agreement threshold and flags disagreements for review. Its accepted-case coverage and denominator need reconciliation before treating 91.3% as whole-cohort accuracy. Synthetic text provenance, model/input implementation and selective acceptance are material limitations. This is a primary preprint with claimed conference acceptance, not definitive clinical confirmation of independent-agent benefit.

[Medical AI Consensus, September 2025](https://arxiv.org/abs/2509.17353) describes a multi-agent report-generation/evaluation framework, with trained components and feedback. The inspected abstract does not establish a clean paired public-model pixel-reading improvement with verified cohort/CIs. It is a workflow candidate, not interchangeable with a single roleplay prompt or proof that agents improve diagnosis.

[Resolution Meets Reduction, August 2026](https://arxiv.org/abs/2608.08713) reports anatomy-guided visual-context gains in 19/20 matched-token configurations across two CT report datasets. Its systems use small trained models and domain-specific visual components. It motivates a controlled ROI-versus-global-context experiment but does not validate off-the-shelf GPT/Gemini/Claude cropping. Likewise, [GPTRadScore, March 2024](https://arxiv.org/abs/2403.05680) evaluates selected CT lesion interpretation and automated scoring; it does not prove blind full-volume coverage. Its later journal version is the same study family, not independent replication.

[Capabilities of Gemini Models in Medicine, April 2024](https://arxiv.org/abs/2404.18416) and [Advancing Multimodal Medical Capabilities of Gemini, May 2024](https://arxiv.org/abs/2405.03162) concern medically adapted Med-Gemini systems, including specialized multimodal/3D work. Their results must not be transferred to publicly available Gemini API models. The two companion papers also should not be casually counted as independent external replications.

[The 2025 JAMA neuroradiology case study](https://www.nature.com/articles/s41598-025-06458-z) uses original/rephrased public cases, images/text controls and repetitions. Rephrasing is a useful cue-sensitivity check, but cannot prove absence of training exposure to the original images or diagnoses. Public quiz accuracy is a different endpoint from prospective all-comers finding detection.

## Input transport is part of the technique

The following official documentation establishes supported mechanics, not radiology efficacy. Specifications are current observations and may differ from historical study versions.

* [Gemini video documentation](https://ai.google.dev/gemini-api/docs/video-understanding): default static processing samples at 1 FPS; newer supported models offer adaptive timeline processing. A fast slice cine can therefore omit most slices under default sampling. The uploaded video’s slice count is not the observed-frame count. Preserve frame-to-slice/time mapping and processing receipts. General long-video quality/token claims are not medical validation.
* [Gemini image documentation](https://ai.google.dev/gemini-api/docs/image-understanding): multiple images and coordinate-based outputs permit explicit slices/ROI workflows. This does not establish coordinate accuracy on lesions or native DICOM geometry interpretation.
* [Gemini media-resolution documentation](https://ai.google.dev/gemini-api/docs/media-resolution): visual token allocation is configurable. More allocation changes cost/fidelity; it is not evidence of a diagnostic gain by itself.
* [Claude vision documentation](https://platform.claude.com/docs/en/build-with-claude/vision): large images are downscaled according to model-specific patch and long-edge limits; animations use only the first frame. Current limits differ by tier. Coordinates refer to the resized view, so ROI navigation must map back to source geometry. Lossy recompression and small lesions can matter.
* [OpenAI image/vision documentation](https://developers.openai.com/api/docs/guides/images-vision): detail/tokenization varies by model, and even original-detail inputs can be resized. The documentation explicitly limits specialized medical-image interpretation. Native-image hashes, delivered dimensions and detail settings are needed to establish what a benchmark actually tested.

These are five distinct official sources; they are not five clinical studies. Video, multi-image and high-resolution availability support a feasible research implementation, without establishing comparative diagnostic performance.

## What a discriminating next experiment would measure

This is a prospective design recommendation, not authorization or execution of additional reads. Existing publicly released physician reports or published pathology/consensus references can support research without commissioning live doctors. Reference omissions, internal contradictions, historical findings and uncertainty need unscorable labels, not assumed negatives. Location information extracted from a reference report must not enter model input.

1. Compare the same cases/model/version/task under sparse montage, dense separate slices, and video with explicit frame sampling. Equalize or report visual-token budgets; preserve sequence names, orientation, spacing, plane and window transformations. The current evidence does not isolate a whole-video advantage.
2. Compare automatic adaptive slice/ROI selection against deterministic selection. Separately report an oracle-location upper bound; do not label it autonomous detection. Preserve global context alongside crops. An image selector with supervision is an additional model component.
3. Compare one sequence against clinically relevant multiple sequences/windows with sensitivity **and** specificity, per-class coverage, calibration/abstention and unresolved status. More sensitive but less specific is a tradeoff rather than universal improvement.
4. Separate ordinary clinical history, expert imaging descriptions and reference-derived descriptions. Include history-only and interpreted-findings-only controls. This isolates clinical reasoning from visual extraction and reveals answer-conditioned assistance.
5. Compare single-call reasoning, fixed self-consistency, independent-reader synthesis and grounded verification on the same cases. Score one committed final answer, report correction/reversal and unresolved outcomes, and retain all attempts. Consensus accuracy restricted to accepted cases needs its coverage beside it.
6. Reserve private/new cases or post-cutoff cases when possible; publicly accessible benchmark cases alone cannot rule out exposure. Use paired patient-level uncertainty, cluster multiple levels/exams within patients, and avoid treating model repetitions as new patients.

No reviewed source establishes that an adaptive public-frontier CT/MRI workflow is clinically equivalent to radiologists across routine all-comers exams. Equally, this review does not establish that all such workflows fail: the most useful missing evidence is a controlled, reference-isolated, same-patient comparison of image-delivery and grounding choices.

## Search and verification record

Applied the Firecrawl research-papers skill. Used its research index for three technique-focused query families (CT/MRI volume/video/adaptive/high-resolution inputs; prompting/self-consistency/multiagent/context; CT slice interpretation), followed related-paper expansion from MRI prompt and quiz-study seeds, then inspect/read calls for load-bearing papers. Related-paper expansion used indexed seed IDs 1974277019456353942 and 613875485137015510. The paper reader did not supply indexed full text for several retrieved records; this was not treated as a negative scientific result.

Publisher Firecrawl scrapes supplied the full lumbar-video, quiz-prompt and brain-MRI prompt originals. Primary publisher/PubMed/arXiv pages supplied inaccessible or unindexed articles’ abstracts, dates and source links. Where full text was inaccessible, numerical detail was restricted to the accessible primary abstract. Browser challenges and a failed Europe PMC retrieval were bypassed through other primary sources without inventing missing methods. Rate limits were respected; no paid upgrades or new model inference were used.

The linked collection includes more than twenty primary publications/version records and official technical sources, with evidence strength explicitly separated. Companion versions, preprints, domain-trained systems and documentation are not counted as independent controlled clinical trials. The review is extensive targeted retrieval, not a claim of systematic database completeness.
