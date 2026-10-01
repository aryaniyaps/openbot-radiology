"""Same-study specialist versus self-review comparison; no additional inference."""
import pathlib, json, random, hashlib, time
from binary_metrics import paired

R = pathlib.Path(__file__).resolve().parents[1]
protocol = json.loads((R / 'PROTOCOL.json').read_text())
tasks = json.loads((R / 'report/task-results.json').read_text())
metrics = json.loads((R / 'report/task-metrics.json').read_text())
records = []
for modality in ['CXR', 'CT', 'MR']:
    ids = {x['case_id'] for x in protocol['control_and_repeats'] if x['modality'] == modality}
    for model in protocol['models'][:3]:
        labels = sorted({x['task'] for x in metrics if x['modality'] == modality})
        for label in labels:
            for condition in ['delegated', 'second-reader']:
                def select(configuration):
                    return sorted([x for x in tasks if x['stage'] == 'evaluation' and x['modality'] == modality and x['model'] == model and x['arm'] == 'B' and x['configuration'] == configuration and not x['attempt'] and x['task'] == label and x['case_id'] in ids], key=lambda x: x['case_id'])
                a, b = select('self-review'), select(condition)
                assert [x['case_id'] for x in a] == [x['case_id'] for x in b]
                pending = sum(x['status'] == 'not_run' or y['status'] == 'not_run' for x, y in zip(a, b))
                result = paired(a, b)
                result.update(modality=modality, model=model, task=label, comparison='self-review-vs-' + condition,
                              planned_control_studies=len(ids), reference_positive=sum(x['label'] for x in a),
                              reference_negative=sum(x['label'] == 0 for x in a), pending_pairs=pending,
                              case_ids=[x['case_id'] for x in a])
                if pending:
                    for name in ['b_minus_a', 'exact_mcnemar_p', 'a_only_success', 'b_only_success', 'both_success', 'neither_success']:
                        result[name] = None
                    result['inference_status'] = 'Pending control pairs: no effect or gain/loss estimate.'
                elif a:
                    differences = [int(y['end_to_end_success']) - int(x['end_to_end_success']) for x, y in zip(a, b)]
                    seed = int(hashlib.sha256(('graysby-self-review-control-v1' + modality + model + label + condition).encode()).hexdigest()[:16], 16)
                    rng = random.Random(seed)
                    bootstrap = sorted(sum(rng.choices(differences, k=len(differences))) / len(differences) for _ in range(5000))
                    result['ci_for_difference'] = [bootstrap[124], bootstrap[4874]]
                    result['inference_status'] = 'Exploratory same-study paired bootstrap5000; control cases prespecified, added comparison during audit; no multiplicity adjustment or confirmatory claim.'
                    if result['a_only_success'] + result['b_only_success'] == 0:
                        upper = 1 - .05 ** (1 / len(a))
                        result['zero_discordance_exact_upper_probability'] = upper
                        result['conservative_zero_discordance_difference_interval'] = [-upper, upper]
                else:
                    result['inference_status'] = 'Not estimable: no reference-supported control assertions.'
                records.append(result)
out = {'updated_unix': time.time(), 'scope': 'Same ten prespecified control studies, self-review versus each specialist condition; no new diagnostic condition, score change, or model invocation.',
       'analysis_status': 'Exploratory audit refinement added during execution, not a preregistered confirmatory analysis.',
       'limitations': 'Ten controls overall, fewer reference-supported studies per modality/task. Do not compare40-study specialist results against10-study self-review as if cohorts match. OpenI study IDs are patient proxies. Zero discordance is not equivalence.',
       'records': records}
(R / 'report/self-review-controlled-comparisons.json').write_text(json.dumps(out, indent=2) + '\n')
