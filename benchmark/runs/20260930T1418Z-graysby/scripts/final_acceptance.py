"""Curator-only delivery checks; never dispatches inference or repairs results."""
import pathlib, json, collections, time, urllib.request, math

R = pathlib.Path(__file__).resolve().parents[1]
protocol = json.loads((R / 'PROTOCOL.json').read_text())
rows = json.loads((R / 'report/assignment-results.json').read_text())
fields = ['stage', 'case_id', 'arm', 'configuration', 'model', 'attempt']
key = lambda x: tuple(x.get(k, '') for k in fields)
checks = {}
checks['frozen_assignment_count_970'] = len(protocol['assignments']) == len(rows) == 970
checks['exact_assignment_set'] = collections.Counter(map(key, rows)) == collections.Counter(map(key, protocol['assignments']))
checks['no_pending_assignments'] = all(x['execution_status'] != 'not_run' for x in rows)
missing = []
identity_failures = []
unclosed = []
for row in rows:
    path = R / row['result_path'] if row.get('result_path') else None
    if not path or not path.exists():
        missing.append(key(row))
        continue
    result = json.loads(path.read_text())
    start, finish = result.get('started_unix'), result.get('finished_unix')
    terminal = result.get('status') in {'succeeded', 'failed', 'timeout', 'quarantined', 'controller_failure'}
    timestamps = all(isinstance(v, (int, float)) and math.isfinite(v) for v in [start, finish]) and finish >= start
    metadata = all(result.get(k) == row[k] for k in ['case_id', 'stage', 'arm', 'modality']) and result.get('requested_model') == row['model'] and result.get('configuration', 'primary') == row['configuration']
    if not terminal or not timestamps or not metadata:
        unclosed.append(key(row))
    if row['valid_structured'] and row['model'].startswith('gpt-'):
        native = result.get('native_identity', {})
        if native.get('status') != 'verified' or native.get('reported_model') != row['model'] or native.get('prior_conversation_context_detected'):
            identity_failures.append(key(row))
checks['every_terminal_result_preserved'] = not missing and not unclosed
checks['qualified_GPT_identity_and_context'] = not identity_failures
checks['context_quarantine_18'] = sum(x['prior_conversation_context_detected'] for x in rows) == 18
results = []
for path in (R / 'evidence').glob('*/*/*/*/result.json'):
    results.append(json.loads(path.read_text()))
usage_input = sum((x.get('usage') or {}).get('input', 0) or 0 for x in results)
usage_output = sum((x.get('usage') or {}).get('output', 0) or 0 for x in results)
from native_only_usage import totals
supplement = totals(R)
usage_input += supplement['input_tokens']
usage_output += supplement['output_tokens']
assignments_created = len(list((R / 'evidence').rglob('assignment.json')))
checks['observed_diagnostic_token_and_conversation_ceiling'] = usage_input <= 100_000_000 and usage_output <= 1_000_000 and assignments_created <= 1002
allowance = json.loads((R / 'evidence/provider-allowance-current.json').read_text())['limits']
checks['credit_balance_unchanged'] = allowance['rateLimits'].get('credits', {}).get('balance') == '62500'
checks['authorized_free_reset_receipt'] = (R / 'evidence/free-banked-reset-receipt.json').exists()
integrity = json.loads((R / 'report/integrity-checkpoint.json').read_text())
checks['frozen_critical_assets_and_prompts'] = integrity['protocol_unchanged'] and integrity['critical_reference_visual_preparation_schema_serving_adapter_unchanged'] and all(x['clinical_literal_strings_unchanged'] for x in integrity['clinical_prompt_literal_audit'])
with urllib.request.urlopen('http://127.0.0.1:18899/api/bots', timeout=20) as response:
    bots = json.load(response)['bots']
busy = [x['id'] for x in bots if x.get('busy')]
checks['own_workspace_idle'] = not busy
events = [json.loads(x) for x in (R / 'evidence/batch-events.jsonl').read_text().splitlines()]
terminal_events = [x for x in events if x.get('batch_complete')]
checks['latest_batch_finished_without_safety_stop'] = bool(terminal_events) and not terminal_events[-1].get('stopped_by_budget_or_safety')
checks['reports_and_figures_present'] = all((R / name).exists() for name in ['DECISION-REPORT.md', 'REPORT.md', 'REQUIREMENT-AUDIT.md', 'report/finding-resolution.png', 'report/finding-resolution.svg', 'report/execution-progress.png'])
out = dict(updated_unix=time.time(), passed=all(checks.values()), checks=checks,
           assignment_status_counts=dict(collections.Counter(x['execution_status'] for x in rows)),
           diagnostic_assignments_created=assignments_created, original_conversation_cap=1000, corrected_conversation_cap=1002,
           observed_input_tokens=usage_input, observed_output_tokens=usage_output,
           missing_results=missing, unclosed_results=unclosed,
           qualified_identity_failures=identity_failures, busy_own_bots=busy,
           scope='Delivery consistency, identity, frozen inputs and budget checks; independent audit and clinical limitations remain separate. Token sums are observed subtotals, not whole investigation cost.')
(R / 'report/final-acceptance.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'passed': out['passed'], 'checks': checks, 'assignments_created': assignments_created}))
raise SystemExit(0 if out['passed'] else 2)
