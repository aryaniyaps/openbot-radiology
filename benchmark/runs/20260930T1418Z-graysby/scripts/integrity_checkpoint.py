"""Curator verifies frozen artifacts without exposing references to diagnostic agents."""
import pathlib,json,hashlib,time,ast
R=pathlib.Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((R/'PROTOCOL.json').read_text());f=json.loads((R/'evidence/protocol-freeze.json').read_text())
records=[]
for name,expected in p['frozen_artifact_hashes'].items():
    path=R/name;actual=sha(path) if path.exists() else None
    records.append({'file':name,'expected_sha256':expected,'current_sha256':actual,'unchanged':actual==expected})
def clinical_strings(path):
    tree=ast.parse(path.read_text())
    return [n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and any(s in n.value for s in ['Interpret the supplied','Independently interpret','Maximum 250 words','Return ONLY one JSON','Your original independent answer','Independent blinded MedGemma read','Before interpreting, call'])]
prompts=[]
for name in ['run_direct_case.py','run_viewer_case.py']:
    original=R/'private/frozen-controller-sources'/name;current=R/'scripts'/name
    prompts.append({'file':name,'frozen_source_exists':original.exists(),'clinical_literal_strings_unchanged':original.exists() and clinical_strings(original)==clinical_strings(current)})
critical=[x for x in records if x['file'].startswith(('agent-visible/','scoring/')) or x['file'] in ['scripts/prepare_volume.py','scripts/response_schema.py','scripts/medgemma_server.py','scripts/benchmark_codex.py']]
out={'updated_unix':time.time(),'protocol_unchanged':sha(R/'PROTOCOL.json')==f['protocol_sha256'],'frozen_artifacts':records,'changed_artifacts':[x['file'] for x in records if not x['unchanged']],'critical_reference_visual_preparation_schema_serving_adapter_unchanged':all(x['unchanged'] for x in critical),'clinical_prompt_literal_audit':prompts,'interpretation':'Changed controller/accounting/curator files require their recorded deviations; frozen source copies are retained. This checkpoint does not certify that every operational prompt is free from platform context.'}
(R/'report/integrity-checkpoint.json').write_text(json.dumps(out,indent=2)+'\n')
assert out['protocol_unchanged'] and out['critical_reference_visual_preparation_schema_serving_adapter_unchanged']
assert all(x['clinical_literal_strings_unchanged'] for x in prompts)
print('Frozen critical assets and clinical prompt literals verified; changes:',out['changed_artifacts'])
