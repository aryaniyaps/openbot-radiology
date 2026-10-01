# Radiology models and techniques: primary-source evidence notes

Research date: 1 October 2026. Collection: Firecrawl paper-index semantic searches, related-paper expansion from CT-CLIP, in-body verification where indexed, then Firecrawl scraping of publisher full text and official repositories/model cards. This is an evidence contribution to the broader research report, not a new benchmark or clinical deployment qualification. Published endpoints below are not directly interchangeable with our frozen study.

## Decision-relevant findings

Successful radiology AI exists, including narrow positive results from direct frontier models. The useful question is which specific imaging task, input construction, reference standard and deployment role produced the success. Broad examination diagnosis, binary classification of a radiologist-selected key slice, segmentation, report formatting and text-based clinical reasoning are different endpoints.

For a new frontier-model evaluation, prioritize actual high-resolution study inspection with preserved series/window metadata, bounded region zoom, anatomical checklists, explicit per-finding outputs and patient-separated calibration. A single montage and free-form report may discard the information needed for a small finding. However, better prompting, more reasoning or adding tools alone has not consistently fixed the underlying problem. The strongest directly relevant evidence supports testing these methods, not presuming that they have already solved general radiology.

## Direct frontier models: measured successes and important counterexamples

### 1. Gemini 3 Pro Preview: positive, narrowly defined CBCT result

An August 2026 International Dental Journal study evaluated Gemini 3 Pro Preview, GPT-5.2 and Qwen3-VL-235B-A22B-Thinking on condylar osseous changes. There were 72 internal patients, represented by one sagittal CBCT slice each, and 70 external cases constructed as 35 abnormal/35 normal. Gemini achieved internal accuracy 90.3%, sensitivity 84.4%, specificity 95.0%; external accuracy 90.0%, sensitivity 85.71%, specificity 94.29%. GPT-5.2 internal accuracy was 75.0%. This is a real direct frontier-model positive result, with an external dataset. [Full paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13499149/).

The exact Gemini alias was `google/gemini-3-pro-preview`, accessed through OpenRouter. The prompt specified sequential examination of condylar surfaces, cortical integrity, osteophytes, erosions and cysts, followed by a binary conclusion and structured explanation. It was frozen before model testing. This supports a reproducible checklist-style evaluation rather than an unrestricted request to describe a scan. [Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC13499149/).

Critical limits: radiologists examined the full volume and selected the affected side for unilateral disease or the most conspicuous lesion for bilateral disease. The model did not find the key image autonomously. The external sample excluded truncated anatomy and artifacts and used newly assigned radiologist consensus labels. It therefore does not directly meet our constraint of evaluation using only existing doctors' reports. The Gemini–GPT-5.2 difference did not survive the paper's Bonferroni threshold (unadjusted McNemar P=.0266 versus required .0167). No repeated runs were performed; the authors' claim that temperature zero guarantees deterministic outputs should not be accepted as a reliability demonstration. [Methods and results](https://pmc.ncbi.nlm.nih.gov/articles/PMC13499149/).

### 2. GPT-5.4, Claude Opus 4.5, Gemini 2.5 Pro: useful discrimination, badly different operating points

A July 2026 CheXpert study tested three balanced, pathology-specific cohorts of 1,500 images: cardiomegaly, edema and pleural effusion. These are 4,500 cohort entries, not necessarily 4,500 unique patients. Commercial APIs were accessed March–April 2026. Aspect-preserving RGB JPEGs had maximum side 1,024 and quality 95. The identical prompt requested binary PRESENT/ABSENT and confidence 0–100. AUROC used a derived probability from that confidence, while sensitivity/specificity used the emitted binary label. [Full paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13361219/).

| Finding | GPT-5.4 sensitivity / specificity; AUROC | Claude Opus 4.5 sensitivity / specificity; AUROC | Gemini 2.5 Pro sensitivity / specificity; AUROC |
| --- | --- | --- | --- |
| Cardiomegaly | 29.3% / 97.7%; .859 | 64.8% / 73.1%; .742 | 91.6% / 44.9%; .760 |
| Pulmonary edema | 4.3% / 99.7%; .836 | 87.6% / 46.1%; .761 | 97.3% / 24.1%; .745 |
| Pleural effusion | 42.4% / 97.9%; .883 | 39.6% / 86.3%; .698 | 67.3% / 80.4%; .770 |

Every number is from [Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC13361219/table/diagnostics-16-02131-t002/). Strong ranking discrimination can coexist with almost complete omission at the model's default decision point. A validation-selected threshold, alternative prompt or calibrated classifier is therefore a plausible experiment. The reported confidence is not established as a calibrated probability; the paper did not show a successful externally validated recalibration intervention. Its conclusion rejects autonomous interpretation.

### 3. GPT-4o emergency abdominal CT: context plus several slices can work on a selected diagnostic exercise

On 45 emergency abdominal CT cases, each represented by 4–7 slices plus consistent clinical/laboratory data, GPT-4o achieved 82% most-likely-diagnosis accuracy, within the range of six residents (76–89%). There were 243 images altogether. This supports testing multi-image input and relevant pre-imaging context. It does not establish complete-volume case discovery: cases were curated, only selected slices were supplied, and the study reported a 75% hallucination rate in its image-interpretation assessment. Non-significance against residents was not an equivalence trial. [Tomography paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12567681/).

### 4. Claude 3.5 on JAMA neuroradiology quizzes: separate reasoning from vision

In 56 public JAMA cases, Claude 3.5 reached 80.4% on original text-plus-images and 76.8% on rephrased text-plus-images. It also reached 76.8% with rephrased text alone. Across models, image-only pathological localization was 21.5–63.1%. This illustrates why excellent clinical quiz answers do not prove visual discovery. Rephrasing reduces literal memorization but does not eliminate training exposure to public cases. [Scientific Reports paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12675488/).

### 5. Positive pneumothorax claims need endpoint and leakage review

In 172 CT-confirmed pneumothorax cases, GPT-4o correctly identified all three repeated reads for 69.6% of older-than-12 patients, versus 20.8% of pediatric patients. Adult large versus small pneumothorax results were 81.6% versus 42.2%. Since there were no negative cases, specificity is unmeasured. The paper uses conflicting terminology for all-three versus majority-correct accuracy in different sections; counts and definitions should be retained explicitly. [PLOS ONE study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12431401/).

A second study reported GPT-5.1 sensitivity 100% and specificity 91.4% in 240 patients with 30 positives, but supplied extensive clinical data including diagnoses, surgical status and length of stay. That is not clean evidence of image-only detection; the broader report's clinical-evidence reviewer audits this leakage concern. Even there, side identification and management endpoints were weak. [BMC study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12964938/).

### 6. More reasoning is not a general fix

RadLE assessed 50 deliberately difficult spot-diagnosis cases, with repeated frontier-chatbot runs and partial-credit scoring. Board-certified radiologists achieved 83%, trainees 45%, GPT-5 30%, Gemini 2.5 Pro 29%, o3 23%, Grok-4 12% and Claude Opus 4.1 1%. Extended GPT-5 reasoning brought little gain while increasing response time about sixfold. This is a small, difficulty-enriched preprint and consumer interfaces limit version control, but it is an appropriate counterexample to assuming more thinking fixes perception. [RadLE preprint](https://arxiv.org/abs/2509.25559).

Another preprint found GPT-5 around 44% on BraTS-derived brain-tumor VQA using triplanar mosaics, with GPT-5-mini 44.19% and GPT-5 43.71%. Automated report-derived labels, no human comparator and no non-CoT baseline limit interpretation. In contrast, a broader GPT-5 VQA preprint reported high scores on small VQA-RAD/SLAKE items and text-only physics questions. Those exams measure different skills from finding subtle pathology in full studies. [Brain-tumor study](https://arxiv.org/abs/2508.10865), [VQA/physics study](https://arxiv.org/abs/2508.13192).

In a separate 180-case, single-key-image study spanning radiographs/CT/MRI, clinical context improved pooled accuracy from 10.6% to 24.0%; Gemini 2.0 had the highest overall model accuracy of 29.2%. It selected diagnostic images from real PACS cases and evaluated a broad pathology spectrum, rather than easy forced-choice questions. [Life paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12842777/).

## Techniques worth testing, with endpoint boundaries

### Frontier model plus deterministic local imaging tools

An April 2026 preprint evaluated GPT-5.4, Claude Sonnet 4.6 and Gemini 3.1 Pro as orchestrators of local MRI skull stripping, registration, tumor segmentation and volume measurements. Images were not sent to commercial LLM servers; agents saw textual tool results and pointers. In the handoff architecture, GPT-5.4 human-evaluated response accuracy was 95.8% on single-timepoint measurements (150 cases/769 queries) and 91.3% on longitudinal questions (75 cases/809 queries). On 30 RANO cases, GPT-5.4 and Claude reached 86.7% in their best configurations; two of 18 progressive-disease cases were missed. [Agentic neuro-radiology preprint](https://arxiv.org/abs/2604.16729).

This is successful frontier-assisted quantitative imaging, not direct visual diagnosis. Tools were selected for already described pathologies; automatic differential diagnosis before tool selection remains unsupported. Many source scans were preprocessed, human review covered 30% of runs, and segmentation errors bounded final answers. Do not generalize these results to undifferentiated brain MRI. It is nevertheless a practical prototype route when reliable tools already exist for the stated anatomy and disease.

### Tool augmentation needs an ablation against direct inference

MedRAX combines GPT-4o with specialist CXR classification, segmentation, grounding and reporting tools. On ChestAgentBench, a 2,500-question, six-choice benchmark generated from public Eurorad case material, overall accuracy was 63.1% versus GPT-4o 56.4%. A second benchmark showed 68.1% versus GPT-4o 63.5%. The reference implementation used an NVIDIA RTX 6000; full-suite fit on our 8 GB GPU is not demonstrated. Public case exposure and GPT-generated question construction matter. [MedRAX preprint](https://arxiv.org/abs/2502.02673).

Evo-MedAgent reports GPT-5-mini .68→.79 and Gemini 3 Flash .76→.87 with evolving episodic/procedural memory. Crucially, ground-truth answer feedback is revealed after each evaluation case before memory updates. This is sequential supervised test-time learning, not a frozen, unlabeled hospital inference condition. A defensible replication would learn rules from development cases, freeze the memory, and evaluate unique patient-held-out cases without answer feedback. [Evo-MedAgent preprint](https://arxiv.org/abs/2604.14475).

### Zoom, grounding and iterative inspection: plausible, not uniformly solved

RadDiff increased top-1 accuracy on 57 expert-validated differences from 1.75% for a general-domain baseline to 47.37% with medical encoders, image-plus-text reasoning, iterative refinement and targeted visual search. The final visual-search step improved 45.61→47.37%; a separate condition using ground-truth reports reached 50.88%. This is cohort/image-set difference description with domain encoders, not standalone patient diagnosis. [RadDiff preprint](https://arxiv.org/abs/2601.03733).

MedReason-R1 learns local-zoom CT diagnosis with reinforcement learning on CT-RATE-VQA, while MedVistaGym trains tool-interleaved visual reasoning. Both support the broader mechanism that spatial inspection can matter; neither proves that attaching an untrained crop tool to any frontier model will solve clinical radiology. Their public, synthetic-QA benchmarks and trained model weights need separate verification. [MedReason-R1](https://arxiv.org/abs/2510.19626), [MedVistaGym](https://arxiv.org/abs/2601.07107).

## Open radiology models: more faithful inputs and stronger task specialization

### MedGemma 1.5: the optimized volume path still has modest CT performance

Google's protocol passes up to 85 individual axial slices, resized individually to 896×896, with slice indices and per-condition binary queries. CT HU is mapped to RGB windows: red −1024 to 1024, green −135 to 215, blue 0 to 80. MRI is normalized per volume. Multiple sequences/reconstruction kernels can be stacked, with equidistant sampling above 85 slices. The slice budget is 21,760 visual tokens, under a 32k total context. [Technical report](https://arxiv.org/abs/2604.05081), [official CT notebook](https://github.com/Google-Health/medgemma/blob/main/notebooks/high_dimensional_ct_hugging_face.ipynb).

With this method, official MedGemma 1.5 4B results are internal balanced CT macro accuracy 61.1%, MRI 64.7%, and CT-RATE validation macro F1 27.0%, precision 34.2%, recall 42.0%. CT-RATE is out of distribution for MedGemma; internal sets are not independent institutional deployment tests. These absolute figures are far less reassuring than headlines emphasizing relative improvement. [Official model card](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card).

The original MedGemma 4B fine-tuning demonstration raised SIIM-ACR pneumothorax F1 59.7→71.5 and accuracy 85.9→87.8. This was full-parameter supervised fine-tuning, not evidence that an 8 GB QLoRA run or quantized 1.5 will reproduce the same endpoint. [Technical report Table 13](https://arxiv.org/html/2507.05201#S5.T13).

Our pinned NF4 evaluation supplied up to four montage images and distorted wide CT/MRI montages through square resizing. It therefore did not test Google's volume protocol. That mismatch should be corrected in a new study. It does not explain the observed misses causally: we did not isolate quantization, resolution, slice coverage, prompting or model weights. Full 85-slice long-context inference and fine-tuning are not established to fit our 8 GB GPU. A first engineering check should measure peak VRAM, tokens, slice coverage and inference behavior before making that commitment.

### CT-CLIP / CT-CHAT: real volumes, open code, noncommercial license

CT-RATE pairs 25,692 noncontrast chest CT scans from 21,304 patients with reports; multiple reconstructions yield 50,188 volumes. CT-CLIP classifies 18 abnormalities from volumetric embeddings; CT-CHAT adds a language model trained on over 2.7 million derived QA pairs. The paper's zero-shot CT-CLIP improves average AUROC by .102 over its supervised baseline internally; the first external dataset gain is .085. These are model-comparator differences, not hospital outcome improvements. [Paper](https://arxiv.org/abs/2403.17834).

Official code says training uses A100 80 GB at batch eight; inference can use smaller GPUs but gives no verified 8 GB requirement. Enlarging patches to save memory can hurt small-pathology detection. The release is CC-BY-NC-SA 4.0, so noncommercial research availability does not establish commercial hospital-use rights. Reported 1.5-second volume classification is not a local 8 GB latency promise. [Official repository](https://github.com/ibrahimethemhamamci/CT-CLIP).

### Merlin: externally validated abdominal CT encoder

The 2026 Nature paper validates Merlin on 5,137 internal CTs and 44,098 external CTs from three sites and two public datasets, across several different downstream tasks. The current arXiv body reports 30-finding zero-shot mean F1 .741 internally and .647 externally. Do not treat the entire 44,098-scan total as the denominator for that one finding-classification endpoint. [Nature publication](https://www.nature.com/articles/s41586-026-10181-8), [arXiv results](https://arxiv.org/html/2406.06512).

Weights and code are available, with repository MIT license; specific pretrained-backbone and dataset rights still need checking. The public abdominal dataset contains 25,494 CT/report pairs from 18,317 patients and requires a data-use agreement. Training was about 160 hours on an NVIDIA A6000. An 8 GB inference fit has not been established here. This is a serious abdomen-specific representation-learning baseline, not an off-the-shelf general radiologist. [Repository](https://github.com/StanfordMIMI/Merlin), [weights](https://huggingface.co/stanfordmimi/Merlin).

### Pillar-0 and nnFoundation: promising recent research, not deployment evidence

Pillar-0 explicitly models 3D structure and multichannel CT windows. It reports internal mean AUROCs 86.4 abdomen/pelvis, 88.0 chest, 90.1 head CT and 82.9 breast MRI across 366 findings. External Stanford abdominal CT AUROC is 82.2 versus Merlin 80.6. These are findings-specific rankings with report-extracted RATE labels, not proof of report completeness, clinical sensitivity thresholds or hospital approval. The verified release has modality-specific checkpoints, including a 94.1M-parameter chest CT encoder. The actual pretraining repository uses Educational Community License 2.0. Hugging Face weight access is gated, and its exact access agreement needs review before claiming hospital-use rights; the arXiv manuscript license is not the code or weight license. No 8 GB inference measurement was obtained. [Pillar-0 preprint](https://arxiv.org/abs/2511.17803), [checkpoint collection](https://huggingface.co/collections/YalaLab/pillar-0), [code license](https://raw.githubusercontent.com/YalaLab/pillar-pretrain/main/LICENSE).

The September 2026 nnFoundation preprint covers 2.1 million volumes and 108 downstream tasks. CNN and ViT variants support different local/spatial versus global/semantic tasks. The actual repository is `MIC-DKFZ/nnssl`, with its `nnFoundation` branch and links to 102M-parameter CNN and 674M-parameter ViT checkpoints; there is no need to assume a repository named nnFoundation exists. The CNN checkpoint is approximately 410 MB according to its model card, making an 8 GB inference engineering check plausible, but memory depends on 3D input/patch size and adaptation; no fit is promised. The code uses CC-BY-SA 4.0 and checkpoint-specific licensing remains to be reviewed. These are encoders to adapt in nnU-Net/nnDetection, not turnkey diagnostic chatbots. Very recent preprint and no local reproduction yet. [Paper](https://arxiv.org/abs/2609.26924), [actual repository](https://github.com/MIC-DKFZ/nnssl).

### TotalSegmentator / nnU-Net: practical 3D quantitative path

TotalSegmentator provides CT and MRI anatomy segmentation with CPU/GPU inference and lower-memory options including fast mode, ROI subsets and volume splitting. Default anatomical tasks are Apache-2.0; other specialized tasks have distinct commercial/noncommercial licenses. This makes the standard tool a plausible first 8 GB engineering test, with CPU fallback, without assuming every task shares the same license. Reducing resolution can sacrifice small-structure accuracy. [Official repository](https://github.com/wasserth/TotalSegmentator).

The MRI study reports internal Dice .839 and two external test sets of 20 MRIs each. Dice measures boundary overlap, not disease diagnosis. The 80-structure research model should not be confused with the current repository's default 50-class MRI task. [MRI paper](https://arxiv.org/abs/2405.19492).

### MAIRA-2: grounding helps auditability, not perfect reporting

MAIRA-2 uses current frontal/lateral radiographs, prior study and clinical indication/context to generate findings with localized boxes. In the paper, only 52.9% of generated MIMIC sentences are logically supported under RadFact. Grounding precision is about 68.8% on GR-Bench and 80.2% on PadChest-GR; correct localization conditional on a correct sentence is not overall report accuracy. External datasets, ablations and qualitative review make it informative, but the authors explicitly identify a gap to practical clinical performance. [MAIRA-2 paper](https://arxiv.org/abs/2406.04449).

## Bounded next experiments suggested by this evidence

1. Compare direct frontier models on a report-grounded, patient-held-out cohort: fixed high-resolution individual views, automated study coverage, series/window metadata, anatomical checklist, binary per-finding output, and a bounded crop/reinspection loop. Keep reports hidden from inference. Compare image-plus-safe-pre-imaging context against image-only and context-only controls.
2. Add a development-only calibration lane. Estimate sensitivity/specificity and decision thresholds from report-supported positive and explicit-negative labels. Freeze thresholds before independent evaluation; report abstentions and missing negatives rather than filling them from silence.
3. Separate key-image classification from full-study discovery. A model interpreting a doctor-selected lesion slice answers an easier, clinically useful but different question. Never label that result autonomous radiology.
4. For local open models, first correct MedGemma volume preprocessing and measure resource feasibility. Compare a dedicated CXR classifier and a native 3D CT encoder where modality/licensing match. A frontier model may format or contextualize validated tool measurements, while each measurement remains traceable to its image and tool.
5. Retain existing doctor's reports as reference standards as requested, but distinguish report-mentioned assertions from comprehensive image truth. Without fresh image review, unsupported localization, omitted findings and clinical significance cannot be adjudicated. That limits what a retrospective report-only study can prove; it does not prevent useful model comparison.

No new patient data or model inference was performed for these notes. No model purchases, GPU rentals, fine-tuning, account access, commit or push was performed by this research contributor.
