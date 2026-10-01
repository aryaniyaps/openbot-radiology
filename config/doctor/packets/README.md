# Practice imaging packet provenance

These display derivatives come from deidentified public TCIA DICOM images. Patient names, demographics, identifiers and accessions in this deployment are synthetic. The source image pixels are retained in PACS; PNG packets use display windowing, resizing and explicitly disclosed sampling. No collection diagnosis is provided to the assistant.

- PRACTICE001 (DX): [COVID-19-NY-SBU](https://doi.org/10.7937/TCIA.BBAG-2923), [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). 1 supplied source views, rendered for display.
- PRACTICE002 (CT): [COVID-19-NY-SBU](https://doi.org/10.7937/TCIA.BBAG-2923), [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). 16 of 241 axial positions, lung and mediastinal windows.
- PRACTICE003 (MR): [PROSTATEx](https://doi.org/10.7937/K9TCIA.2017.MURS5CL), [Creative Commons Attribution 3.0 Unported License](http://creativecommons.org/licenses/by/3.0/). ep2d_diff_tra_DYNDIST: 16 of 57 instances; t2_tse_tra: 16 of 19 instances; ep2d_diff_tra_DYNDIST_ADC: 16 of 19 instances.
- PRACTICE004 (US): [Prostate-MRI-US-Biopsy](https://doi.org/10.7937/TCIA.2020.A61IOC1A), [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). 16 of 227 spatial frames; not temporal cine.
- PRACTICE005 (MG): [CMMD](https://doi.org/10.7937/tcia.eqde-4b16), [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). 4 supplied source views, rendered for display.

Citation and creator attribution: consult each linked TCIA collection citation record for the dataset authors. Source accession and UIDs are recorded in `config/data/public-manifest.json`; assigned source/pixel hashes and native UID mappings are in `docs/evidence/hospital-deployment/packet-provenance.json`.

Packet orientation follows supplied pixel ordering; this presentation does not supply full DICOM orientation controls, calibrated mammography reading or cine review. Use the native viewer for complete supplied series.

 (carry this file with shared recordings):

- Saltz J., Saltz M., Prasanna P., Moffitt R., Hajagos J., Bremer E., Balsamo J., Kurc T. (2021). *Stony Brook University COVID-19 Positive Cases*. TCIA. [10.7937/TCIA.BBAG-2923](https://doi.org/10.7937/TCIA.BBAG-2923). [Collection citation](https://www.cancerimagingarchive.net/collection/covid-19-ny-sbu/).
- Litjens G., Debats O., Barentsz J., Karssemeijer N., Huisman H. (2017). *SPIE-AAPM PROSTATEx Challenge Data*, version 2. TCIA. [10.7937/K9TCIA.2017.MURS5CL](https://doi.org/10.7937/K9TCIA.2017.MURS5CL). [Collection citation](https://www.cancerimagingarchive.net/collection/prostatex/).
- Natarajan S., Priester A., Margolis D., Huang J., Marks L. (2020). *Prostate-MRI-US-Biopsy*, version 2. TCIA. [10.7937/TCIA.2020.A61IOC1A](https://doi.org/10.7937/TCIA.2020.A61IOC1A). [Collection citation](https://www.cancerimagingarchive.net/collection/prostate-mri-us-biopsy/).
- Cui C., Li L., Cai H., Fan Z., Zhang L., Dan T., Li J., Wang J. (2021). *The Chinese Mammography Database (CMMD)*. TCIA. [10.7937/tcia.eqde-4b16](https://doi.org/10.7937/tcia.eqde-4b16). [Collection citation](https://www.cancerimagingarchive.net/collection/cmmd/).

PROSTATEx publication attribution: Litjens and colleagues (2014), *Computer-Aided Detection of Prostate Cancer in MRI*, [10.1109/TMI.2014.2303821](https://doi.org/10.1109/TMI.2014.2303821). TCIA infrastructure attribution: Clark and colleagues (2013), [10.1007/s10278-013-9622-7](https://doi.org/10.1007/s10278-013-9622-7).

Source projection and laterality labels are displayed as supplied, not independently clinically validated. TCIA's [TOMPEI-CMMD description](https://www.cancerimagingarchive.net/analysis-result/tompei-cmmd/) reports corrections to original CMMD view labels; these demonstrations use the original CMMD images and do not claim corrected clinical labels.
