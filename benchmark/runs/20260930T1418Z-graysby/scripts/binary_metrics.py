#!/usr/bin/env python3
"""Development scoring functions for reference-supported binary tasks.

Not clinical adjudication. One primary attempt per patient/configuration/task.
References must be passed by the separate curator, never diagnostic agents.
"""
import math
from collections import Counter

STATUSES = {'completed', 'abstained', 'timeout', 'tool_failure', 'access_failure',
            'input_insufficient', 'context_contamination', 'budget_exhausted', 'invalid_output', 'not_run'}


def proportion(k, n):
    assert isinstance(k, int) and isinstance(n, int) and 0 <= k <= n
    if n == 0:
        return {'numerator': k, 'denominator': n, 'estimate': None, 'ci95': None}
    z = 1.959963984540054
    p = k / n
    divisor = 1 + z*z/n
    middle = (p + z*z/(2*n)) / divisor
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / divisor
    return {'numerator': k, 'denominator': n, 'estimate': p,
            'ci95': [max(0., middle-half), min(1., middle+half)], 'method': 'Wilson two-sided 95%'}


def exact_mcnemar(a_only, b_only):
    assert all(type(x) is int and x >= 0 for x in [a_only, b_only])
    n = a_only + b_only
    if not n:
        return 1.
    # Symmetric binomial p=0.5: two-sided probability, capped at 1.
    return min(1., 2 * sum(math.comb(n, i) for i in range(min(a_only, b_only)+1)) / (2**n))


def reconcile(references, outputs):
    """Missing assigned outputs remain explicit not_run outcomes."""
    refs = {x['case_id']: x for x in references}
    if len(refs) != len(references):
        raise ValueError('Duplicate assigned case ID')
    if len({x['patient_id'] for x in references}) != len(references):
        raise ValueError('Repeated patient: analyze repeats separately, never inflate primary N')
    if any(type(x['label']) is not int or x['label'] not in [0, 1] for x in references):
        raise ValueError('Binary reference must be integer 0 or 1')
    seen = {}
    for row in outputs:
        case = row['case_id']
        if case not in refs or case in seen:
            raise ValueError('Unassigned or repeated output; retries must be separate')
        status = row['status']
        if status not in STATUSES:
            raise ValueError('Unknown execution status')
        prediction = row.get('prediction')
        if status == 'completed':
            if type(prediction) is not int or prediction not in [0, 1]:
                raise ValueError('Completed requires a binary task conclusion')
        elif prediction is not None:
            raise ValueError('Non-completed row cannot carry a scored diagnostic conclusion')
        for key in ['latency_ms', 'cost_usd']:
            value = row.get(key)
            if value is not None and (type(value) not in [int, float] or not math.isfinite(value) or value < 0):
                raise ValueError('Invalid resource measurement')
        seen[case] = dict(row)
    reconciled = []
    for case, ref in refs.items():
        row = seen.get(case, {'case_id': case, 'status': 'not_run', 'prediction': None})
        row.update(label=ref['label'], patient_id=ref['patient_id'])
        row['scorable'] = row['status'] == 'completed'
        row['correct'] = row['prediction'] == ref['label'] if row['scorable'] else None
        row['end_to_end_success'] = row['correct'] is True
        reconciled.append(row)
    return reconciled


def summarize(rows):
    n = len(rows)
    completed = [x for x in rows if x['scorable']]
    positive = [x for x in completed if x['label'] == 1]
    negative = [x for x in completed if x['label'] == 0]
    tp = sum(x['prediction'] == 1 for x in positive)
    tn = sum(x['prediction'] == 0 for x in negative)
    counts = Counter(x['status'] for x in rows)
    sensitivity = proportion(tp, len(positive))
    specificity = proportion(tn, len(negative))
    missing_bounds = {}
    for label, name, successes in [(1,'sensitivity',tp),(0,'specificity',tn)]:
        assigned = sum(x['label'] == label for x in rows)
        missing = sum(x['label'] == label and not x['scorable'] for x in rows)
        missing_bounds[name] = {'assigned_class_count': assigned, 'unscored_class_count': missing,
                                'identification_bounds': [successes/assigned, (successes+missing)/assigned] if assigned else None,
                                'meaning': 'Best/worst missing-outcome bounds, not confidence intervals; failures are not diagnostic FN/FP'}
    measured_cost = [x['cost_usd'] for x in rows if x.get('cost_usd') is not None]
    return {'assigned_patients': n, 'status_counts': dict(counts), 'completed_patients': len(completed),
            'completion': proportion(len(completed), n),
            'end_to_end_label_success': proportion(sum(x['end_to_end_success'] for x in rows), n),
            'completed_only_label_agreement': proportion(sum(x['correct'] for x in completed), len(completed)),
            'sensitivity_completed_only': sensitivity, 'specificity_completed_only': specificity,
            'false_negative_rate_completed_only': proportion(len(positive)-tp, len(positive)),
            'false_positive_rate_completed_only': proportion(len(negative)-tn, len(negative)),
            'diagnostic_confusion_counts': {'TP': tp, 'FN': len(positive)-tp, 'TN': tn, 'FP': len(negative)-tn},
            'missing_outcome_bounds': missing_bounds,
            'cost_usd': {'measured_patients': len(measured_cost), 'missing_patients': n-len(measured_cost),
                         'measured_subtotal': sum(measured_cost) if measured_cost else None,
                         'total': sum(measured_cost) if measured_cost and len(measured_cost)==n else None}}


def paired(a, b, completed_only=False):
    aa = {x['case_id']: x for x in a}; bb = {x['case_id']: x for x in b}
    if aa.keys() != bb.keys():
        raise ValueError('Paired configurations must have identical assigned cases')
    pairs = []
    for case in aa:
        x, y = aa[case], bb[case]
        if (x['patient_id'], x['label']) != (y['patient_id'], y['label']):
            raise ValueError('Patient or reference mismatch')
        if completed_only and not (x['scorable'] and y['scorable']):
            continue
        pairs.append((x['end_to_end_success'], y['end_to_end_success']))
    both = sum(x and y for x,y in pairs)
    a_only = sum(x and not y for x,y in pairs)
    b_only = sum(y and not x for x,y in pairs)
    neither = len(pairs)-both-a_only-b_only
    return {'endpoint': 'completed-only paired label correctness' if completed_only else 'all-assigned paired end-to-end label success',
            'paired_patients': len(pairs), 'both_success': both, 'a_only_success': a_only,
            'b_only_success': b_only, 'neither_success': neither,
            'b_minus_a': (b_only-a_only)/len(pairs) if pairs else None,
            'exact_mcnemar_p': exact_mcnemar(a_only,b_only) if pairs else None,
            'ci_for_difference': None, 'inference_status': 'CI and stratified design analysis required before comparative conclusion'}
