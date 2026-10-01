"""Audited development usage with no corresponding framework result; count once."""
import pathlib, json

def observations(root):
    path = root / 'evidence/audit/audit-results-development-dispatch-reconciliation.json'
    if not path.exists():
        return []
    records = json.loads(path.read_text())['records']
    assert len({x['thread_id'] for x in records}) == len(records)
    return [x for x in records if x['clinical_dispatch_verified'] and not (root / x['assignment_path']).with_name('result.json').exists()]

def totals(root):
    records = observations(root)
    return {name: sum((x.get('native_total_token_usage') or {}).get(name, 0) or 0 for x in records)
            for name in ['input_tokens', 'cached_input_tokens', 'output_tokens']}
