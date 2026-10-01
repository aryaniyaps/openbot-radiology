"""Observed resource accounting; no inferred subscription-dollar prices."""
import pathlib, json, collections, statistics, time
R=pathlib.Path(__file__).resolve().parents[1]
groups=collections.defaultdict(list)
for p in (R/'evidence').glob('*/*/*/*/result.json'):
    d=json.loads(p.read_text())
    if d.get('bot_id'):
        groups[(d.get('stage'),d.get('requested_model'))].append(d)
usage=[]
for (stage,model),rs in sorted(groups.items()):
    known=[x for x in rs if (x.get('usage') or {}).get('input') is not None]
    known_output=[x for x in rs if (x.get('usage') or {}).get('output') is not None]
    known_cached=[x for x in rs if (x.get('usage') or {}).get('cachedInput') is not None]
    elapsed=[x['finished_unix']-x['started_unix'] for x in rs if x.get('finished_unix') and x.get('started_unix')]
    usage.append({'stage':stage,'model':model,'recorded_diagnostic_runs':len(rs),'token_measurements':len(known),'missing_token_measurements':len(rs)-len(known),
                  'input_observed_subtotal':sum(x['usage']['input'] for x in known) if known else None,
                  'cached_input_measurements':len(known_cached),'missing_cached_input_measurements':len(rs)-len(known_cached),
                  'cached_input_subset_observed_subtotal':sum(x['usage']['cachedInput'] for x in known_cached) if known_cached else None,
                  'output_measurements':len(known_output),'missing_output_measurements':len(rs)-len(known_output),
                  'output_observed_subtotal':sum(x['usage']['output'] for x in known_output) if known_output else None,
                  'elapsed_measured_count':len(elapsed),'elapsed_observed_sum_seconds':sum(elapsed) if elapsed else None,
                  'dollar_total':None,'dollar_reason':'Subscription allocation and local hardware/electricity prices unavailable; no purchases'})
inference_log=R/'private/medgemma-inferences.jsonl'
all_inferences=[json.loads(line) for line in inference_log.read_text().splitlines()] if inference_log.exists() else []
inferences=[d for d in all_inferences if d.get('inference_seconds') is not None]
guarded=[d for d in all_inferences if d.get('error')=='AssertionError: Visual evidence required; maximum four images' and d.get('inference_seconds') is None]
telemetry=R/'evidence/resource-telemetry.jsonl'
resource_rows=[json.loads(line) for line in telemetry.read_text().splitlines()] if telemetry.exists() else []
gpu_phase=next((d for d in reversed(resource_rows) if 'MainPID=649323' in d.get('own_medgemma','')),None)
preprocessing=[json.loads(p.read_text()) for p in (R/'evidence').glob('preprocess-*.json')]
from native_only_usage import observations, totals
extra=observations(R)
data={'updated_unix':time.time(),'platform_usage_by_stage_model':usage,'native_only_development_dispatches':extra,'native_only_development_observed_usage':totals(R),'native_only_development_measured_count':sum(x.get('native_total_token_usage') is not None for x in extra),'native_only_accounting_note':'Four audited development threads lack framework results. Their native observed totals are additional once; no controller status or clinical score is synthesized. Cached input is a subset.',
      'medgemma_inference_records_with_duration':len(inferences),'medgemma_inference_seconds_observed_sum':sum(x['inference_seconds'] for x in inferences) if inferences else None,
      'medgemma_requests_rejected_before_inference':len(guarded),'medgemma_inference_duration_missing_count':len(all_inferences)-len(inferences)-len(guarded),'medgemma_total_serving_records':len(all_inferences),'medgemma_last_active_resource_checkpoint':gpu_phase,'unique_case_latest_preprocessing_receipts':len(preprocessing),'latest_preprocessing_seconds_observed_sum':sum(d.get('preprocessing_seconds',0) for d in preprocessing),'preprocessing_accounting_note':'Latest per-case export receipt only; repeat DICOM preparations separately logged in batch-events. Do not add overlapping receipts or present this as complete lifecycle cost.',
      'serving_cost_note':'Independent specialist cached reads inferred once physically; role deployment requires specialist compute attribution. Duration sums are compute observations, not wall-clock elapsed, currency or energy.',
      'live_clinician_reviews':0,'currency_prices_available':False,'purchases':0,
      'development_note':'Development and repeat inference included separately. Failed startup/configuration attempts and preprocessing have no dollar allocation; missing measurements are explicit.'}
(R/'report/resource-cost-inventory.json').write_text(json.dumps(data,indent=2)+'\n')
