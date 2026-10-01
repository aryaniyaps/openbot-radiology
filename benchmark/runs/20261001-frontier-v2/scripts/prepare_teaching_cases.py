#!/usr/bin/env python3
"""Separate physician-authored reference reports from neutral image packets."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
PRIVATE = ROOT / '.private/frontier-v2'
CACHE = ROOT / '.firecrawl/frontier-v2'
PATTERNS = {
    'CBCT': r'CBCT|cone.beam|mental foram|mandib|three-dimensional reconstruction',
    'FL': r'fluorosc|barium|oesophagogra|esophagogra|contrast swallow|upper gastro|gastrograf|angiogra',
    'NM': r'PET|positron|scintigra|SPECT|FDG|radiotracer|nuclear',
    'MG': r'mammogra|tomosynth|craniocaudal|medio.?lateral oblique|\bCC\b|\bMLO\b',
    'US': r'ultrasound|sonogra|doppler|B.mode',
    'DX': r'radiograph|X.ray|plain film',
    'MR': r'\bMR\b|\bMRI\b|magnetic resonance|T1.weighted|T2.weighted|FLAIR|ADC|diffusion.weighted',
    'CT': r'\bCT\b|computed tomography',
}
DEV = {'19554','19716','19680','19695','19577','9014','19696','11444'}


def read_source(id):
    choices = list(CACHE.glob('case-' + id + '*.json'))
    for path in sorted(choices, key=lambda p: ('-cli' not in p.name, '-recovered' not in p.name)):
        d = json.loads(path.read_text())
        if 'value' in d:
            d = d['value']
        d = d.get('structuredContent', d)
        if d.get('markdown'):
            return d['markdown'], path
    return None, None


def section(md, start, end):
    m = re.search(re.escape(start) + r'\s+(.+?)(?=' + re.escape(end) + r')', md, re.S)
    return m.group(1).strip() if m else ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--development-only', action='store_true')
    a = ap.parse_args()
    candidates = json.loads((PRIVATE / 'candidate-sources.json').read_text())
    eligible, excluded = [], []
    for id, source_categories in sorted(candidates.items()):
        if a.development_only and id not in DEV:
            continue
        md, source_path = read_source(id)
        if not md:
            excluded.append({'source_id': id, 'reason': 'source acquisition pending'}); continue
        typ = re.search(r'\*\*Case Type\*\*\s+([^\n]+)', md)
        if typ and 'Series' in typ.group(1):
            excluded.append({'source_id': id, 'reason': 'multiple-patient case series'}); continue
        if re.search(r'\bCase [12]:', section(md,'Clinical History','Imaging Findings')):
            excluded.append({'source_id': id, 'reason': 'multiple patients in case history'}); continue
        diagnosis = section(md,'Final Diagnosis','[References]')
        if not diagnosis:
            diagnosis = section(md,'Final Diagnosis','Case information')
        diagnosis = diagnosis.strip().split('\n\n')[0].strip()
        findings = section(md,'Imaging Findings','Discussion')
        history = section(md,'Clinical History','Imaging Findings')
        if not diagnosis or not findings or not history:
            excluded.append({'source_id': id, 'reason': 'missing explicit existing physician interpretation'}); continue
        if 'creativecommons.org/licenses' not in md:
            excluded.append({'source_id': id, 'reason': 'image reuse license not verified'}); continue
        images = list(dict.fromkeys(re.findall(r'!\[([^\]]*)\]\((https?://[^)]+figure_image/[^)]+)\)', md)))
        matches = {}
        for modality,pattern in PATTERNS.items():
            group = [(caption,url) for caption,url in images if re.search(pattern,caption,re.I)]
            if modality in source_categories and group:
                matches[modality] = group
        # CBCT figures can carry only neutral plane labels; the physician's
        # declared technique establishes the source modality, not its diagnosis.
        if 'CBCT' in source_categories and not matches and images:
            matches['CBCT'] = images
        if not matches:
            excluded.append({'source_id': id, 'reason': 'no modality-matched diagnostic figure'}); continue
        modality = next(k for k in PATTERNS if k in matches)
        figures = matches[modality]
        case_id = 'TEACH-' + hashlib.sha256(('frontier-v2-source-' + id).encode()).hexdigest()[:12].upper()
        out = PRIVATE / 'agent-visible' / case_id
        out.mkdir(parents=True, exist_ok=True)
        view_records = []
        for i,(caption,url) in enumerate(figures,1):
            filename = f'view-{i:03}.png'
            path = out / filename
            if not path.exists():
                request = urllib.request.Request(url, headers={'User-Agent': 'RadiologyResearch/1.0'})
                with urllib.request.urlopen(request, timeout=35) as f:
                    data = f.read(10*1024*1024+1)
                assert len(data) <= 10*1024*1024
                im = Image.open(io.BytesIO(data)).convert('RGB')
                # PNG removes URL-bearing EXIF while preserving the supplied
                # raster. No lesion crops, edits or fabricated image content.
                original_size = im.size
                im.save(path)
            else:
                original_size = Image.open(path).size
            view_records.append({'file': filename,'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'pixels': list(original_size),'source_url':url,'source_caption':caption})
        patient = re.search(r'\*\*Patient\*\*\s+([^\n]+)',md)
        # Clinical history is a separate contextual input, never figure labels,
        # source titles, findings, discussion, final diagnosis or outcomes.
        context = ((patient.group(1)+'\n') if patient else '') + history
        packet = {'case_id':case_id,'stage':'development' if id in DEV else 'evaluation',
            'modality':modality,'clinical_context':context,
            'image_files':[x['file'] for x in view_records],
            'coverage':'Selected published teaching-case images; not a complete examination. Original annotations retained.',
            'input_limitations':['No calibrated original DICOM','Physician-selected images and annotations','Public teaching case: memorization risk'],
            'source_type':'peer-reviewed physician-authored teaching case'}
        (out/'input.json').write_text(json.dumps(packet,indent=2)+'\n')
        reference = dict(packet,source_id=id,source_url='https://www.eurorad.org/case/'+id,
            source_document_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
            reference_diagnosis=diagnosis,reference_findings=findings,
            physician_authorship=section(md,'**Authors**','**Connected authors**')[:1600],
            figures=view_records,license='Source-linked Creative Commons; research only, verify commercial rights separately')
        refs=PRIVATE/'references';refs.mkdir(exist_ok=True)
        (refs/(case_id+'.json')).write_text(json.dumps(reference,indent=2)+'\n')
        eligible.append({'case_id':case_id,'stage':packet['stage'],'modality':modality,
            'source_id':id,'source_url':reference['source_url'],'image_count':len(figures)})
    manifest=PRIVATE/('development-manifest.json' if a.development_only else 'teaching-manifest.json')
    manifest.write_text(json.dumps({'cases':eligible,'exclusions':excluded},indent=2)+'\n')
    from collections import Counter
    print(json.dumps({'eligible':len(eligible),'modalities':dict(Counter(x['modality'] for x in eligible)),
                      'excluded':len(excluded),'manifest':str(manifest)}))


if __name__ == '__main__':
    main()
