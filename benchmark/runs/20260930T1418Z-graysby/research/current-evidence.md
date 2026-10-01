## Published evidence, separate from this benchmark

The historical premise needs qualification. A 2024 study of GPT-4V (`gpt-4-1106-vision-preview`, tested February–March 2024) already examined CT, MRI and radiographs: 515 selected images from 470 patients. Modality/anatomy recognition was strong, while diagnostic classification and exclusion of abnormalities were unreliable. These were representative individual images chosen from studies, with diagnosis confirmation and human comparisons; they were not autonomous complete-volume viewer examinations. Thus, historical evidence was broader than chest radiography, while useful clinical interpretation remained unestablished. Our requested GPT configurations have no matched historical-model control and cannot measure improvement or regression against that study. [Strotzer et al., Radiology, 2024](https://pubs.rsna.org/doi/10.1148/radiol.240955).

Official sources checked on 2026-10-01 still identify MedGemma 1.5 as the 4B multimodal update, with a distinct earlier 27B multimodal model and a 27B text-only model. The model card reports CT/MRI interpretation capability and image normalization to 896×896. Its internal condition-classification results and CT-RATE validation macro-F1 are published evidence, not reproduced results from our four-montage, quantized, no-history protocol. CT-RATE is explicitly listed among public datasets used by the model family; release split labels do not independently prove absence of training exposure. [Official MedGemma model card](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card).

Google’s January 2026 release presents high-dimensional imaging as an imperfect capability intended for developer adaptation. That supports testing beyond chest radiographs, but does not establish full-study diagnostic competence or patient-care readiness. [Google Research release](https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/).

The tested adapter converts a four-image CT montage from 2048×1080 per image to the processor’s 896×896 tensor; MRI montages are 2048×1620. These compress multiple source slices into each encoded image. This is a bounded practical pipeline, not the official per-slice volume example and not a general test of every available MedGemma volume-input strategy. GPT internal image tiling is not independently exposed.

## Coverage matrix

| Modality / study type | Executed scope | Supported endpoint | Unexecuted scope / reason |
|---|---|---|---|
| Chest radiography | OpenI 60 main +10 fresh, released frontal/lateral views | Four explicit report assertions | Other radiographic anatomy not represented |
| Chest CT | CT-RATE 40 main +10 fresh, corrected selected reconstruction; viewer full source volume, direct fixed slice montages | Effusion, nodule, consolidation, emphysema assertions | Other anatomy, dynamic/contrast-phase tasks and adaptive slice requests |
| MRI | MR-RATE 20 main +10 fresh, released multi-series studies with fixed direct sequence selection | Sparse explicit white-matter/atrophy/chronic-infarction/mass assertions | Negative-class estimation, full original protocols, omitted diffusion and broader anatomy |
| Mammography | Development access/rendering investigated separately | No held-out report endpoint | CMMD pathology/class labels did not satisfy the requested existing-doctor-report endpoint; no tomosynthesis evaluation |
| Ultrasound | No held-out execution | None | Still and cine both untested; no selected accessible paired study/report cohort frozen |
| Nuclear medicine | No held-out execution | None | SPECT/PET and whole-study fusion workflows untested |

Non-chest PROSTATEx and CMMD development probes remain technical feasibility evidence, not diagnostic benchmark results. No findings from those probes enter primary scores.
