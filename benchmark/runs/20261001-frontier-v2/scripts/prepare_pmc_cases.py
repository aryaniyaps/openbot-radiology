#!/usr/bin/env python3
"""Acquire licensed clinical case reports and figures; keep answers out of packets."""
import argparse, hashlib, html, io, json, re, time, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from prepare_teaching_cases import PATTERNS
ROOT=Path(__file__).resolve().parents[4];P=ROOT/'.private/frontier-v2';CACHE=P/'pmc-sources';CACHE.mkdir(exist_ok=True)
XL='{http://www.w3.org/1999/xlink}href'

def fetch(url,path):
    if path.exists():return path.read_bytes()
    time.sleep(1)
    req=urllib.request.Request(url,headers={'User-Agent':'RadiologyResearch/1.0 (public noncommercial academic case comparison)'})
    with urllib.request.urlopen(req,timeout=35) as f:b=f.read(20*1024**2)
    path.write_bytes(b);return b

def text(el):return ' '.join(''.join(el.itertext()).split()) if el is not None else ''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--modalities',nargs='+',default=['CBCT','FL','NM','MG','US','DX','MR','CT']);a=ap.parse_args()
    previous=json.loads((P/'pmc-manifest.json').read_text()) if (P/'pmc-manifest.json').exists() else {'cases':[],'exclusions':[]}
    cases=[x for x in previous['cases'] if x['modality'] not in a.modalities];excluded=[x for x in previous['exclusions'] if x['modality'] not in a.modalities];used={x['source_id'] for x in cases}
    # Rare modalities first; no patient is counted twice across modality groups.
    for modality in a.modalities:
        results=json.loads((P/('pmc-search-'+modality+'.json')).read_text())['resultList']['result'];count=0
        for item in results:
            id=item.get('pmcid')
            if not id or id in used or count>=6:continue
            try:
                xml=fetch('https://www.ebi.ac.uk/europepmc/webservices/rest/'+id+'/fullTextXML',CACHE/(id+'.xml'));root=ET.fromstring(xml)
                license=text(root.find('.//license'))
                if not re.search(r'creativecommons|CC BY|Creative Commons',license,re.I):raise ValueError('No verified Creative Commons license')
                body=root.find('body'); sections=body.findall('.//sec') if body is not None else []
                clinical=next((s for s in sections if re.search(r'case|clinical|patient',text(s.find('title')),re.I)),None)
                if clinical is None:raise ValueError('No patient case section')
                paras=[text(x) for x in clinical.findall('p') if text(x)]
                if not paras:raise ValueError('No clinical case narrative')
                narrative='\n'.join(paras)
                if re.search(r'\b(?:two|three|four|five) patients\b|Case 2|Patient 2',narrative,re.I):raise ValueError('Multiple patients')
                figs=[]
                pattern=r'\bCBCT\b|cone.beam' if modality=='CBCT' else PATTERNS[modality]
                for f in root.findall('.//fig'):
                    caption=text(f.find('caption'))
                    if not re.search(pattern,caption,re.I):continue
                    if re.search(r'\btimeline\b|schematic|anatomical structure|flow.?chart|study design',caption,re.I):continue
                    if re.search(r'another.{0,30}patient|other.{0,30}patient',caption,re.I):raise ValueError('Figure includes a different patient')
                    if re.search(r'histolog|histopath|hematoxylin|immunohisto|gross specimen|macroscopic|surgical photograph',caption,re.I):continue
                    g=next((x for x in f.findall('.//graphic') if x.get('content-type')!='thumb'),None)
                    if g is None:continue
                    figs.append({'caption':caption,'graphic':g.get(XL),'figure_id':f.get('id')})
                if not figs:raise ValueError('No modality-matched diagnostic imaging figure')
                if all(re.match(r'post[- ]?operative|post[- ]?treatment|on a 12.month review',f['caption'],re.I) for f in figs):raise ValueError('Only post-treatment figures; primary presenting diagnosis not assessable')
                page=fetch('https://pmc.ncbi.nlm.nih.gov/articles/'+id+'/',CACHE/(id+'.html')).decode()
                urls=[html.unescape(u) for u in re.findall(r'(?:src|href)="([^"]+)"',page) if '/pmc/blobs/' in u]
                case_id='PUB-'+hashlib.sha256(('frontier-v2-'+id).encode()).hexdigest()[:12].upper();out=P/'agent-visible'/case_id;out.mkdir(parents=True,exist_ok=True)
                views=[]
                for i,fig in enumerate(figs,1):
                    name=Path(fig['graphic']).name
                    choices=[u for u in urls if Path(u.split('?')[0]).name==name]
                    if not choices:raise ValueError('Published original figure URL unavailable: '+name)
                    url=choices[0];data=fetch(url,CACHE/(id+'-'+name));im=Image.open(io.BytesIO(data)).convert('RGB')
                    if min(im.size)<180:raise ValueError('Diagnostic figure too small')
                    filename=f'view-{i:03}.png';im.save(out/filename)
                    if (out/filename).stat().st_size>10*1024**2:raise ValueError('Native per-image size limit exceeded')
                    views.append(dict(fig,file=filename,source_url=url,pixels=list(im.size),sha256=hashlib.sha256((out/filename).read_bytes()).hexdigest()))
                # Stop context before the first investigation/result sentence.
                # No source title, figure caption, clinical outcome or diagnosis.
                sentences=re.split(r'(?<=[.!?])\s+',paras[0]);history=[]
                for sentence in sentences:
                    if re.search(r'ultrasound|sonogra|\bCT\b|\bMRI?\b|radiograph|mammogra|scintigra|PET|CBCT|imaging|diagnos|biopsy|histolog',sentence,re.I):break
                    if len(' '.join(history))+len(sentence)>850:break
                    history.append(sentence)
                context=' '.join(history) or 'Pre-imaging history could not be separated reliably; none supplied.'
                packet={'case_id':case_id,'stage':'development' if count==0 else 'evaluation','modality':modality,
                        'clinical_context':context,'image_files':[v['file'] for v in views],
                    'coverage':'Published figures whose captions mention this modality; composites may also contain other modalities or time points. Not a complete examination. Original annotations retained.',
                        'input_limitations':['Selected clinical case-report figures','Uncalibrated publication rasters; missing original series','Public case: memorization risk'],
                        'source_type':'Published clinician-authored case report with existing imaging interpretation'}
                (out/'input.json').write_text(json.dumps(packet,indent=2)+'\n')
                reference=dict(packet,source_id=id,source_url='https://pmc.ncbi.nlm.nih.gov/articles/'+id+'/',
                        source_title=text(root.find('.//article-title')),source_authors=[text(a) for a in root.findall('.//contrib[@contrib-type="author"]')],
                        affiliations=[text(a) for a in root.findall('.//aff')],license=license,
                        clinical_report_narrative=narrative,figures=views,
                        source_xml_sha256=hashlib.sha256(xml).hexdigest(),
                        reference_type='Published case-report interpretation, not a routine signed radiology report; no new clinical adjudication')
                (P/'references'/(case_id+'.json')).write_text(json.dumps(reference,indent=2)+'\n')
                row={'case_id':case_id,'stage':packet['stage'],'modality':modality,'source_id':id,'source_title':reference['source_title'],'source_url':reference['source_url'],'images':len(views)}
                cases.append(row);used.add(id);count+=1;print(json.dumps(row),flush=True)
            except Exception as e:
                excluded.append({'source_id':id,'modality':modality,'reason':str(e)[:200]});print(json.dumps(excluded[-1]),flush=True)
            (P/'pmc-manifest.json').write_text(json.dumps({'cases':cases,'exclusions':excluded},indent=2)+'\n')

if __name__=='__main__':main()
