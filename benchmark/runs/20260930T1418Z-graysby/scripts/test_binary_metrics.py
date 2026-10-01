"""Synthetic validation fixtures; these are NOT diagnostic experiment results."""
import unittest
from binary_metrics import reconcile, summarize, paired, proportion, exact_mcnemar


class MetricsValidation(unittest.TestCase):
    def setUp(self):
        self.refs = [{'case_id':str(i),'patient_id':f'fixture-{i}','label':y}
                     for i,y in enumerate([1,1,0,0,1,0])]
        self.a = [
            {'case_id':'0','status':'completed','prediction':1},
            {'case_id':'1','status':'completed','prediction':0},
            {'case_id':'2','status':'completed','prediction':0},
            {'case_id':'3','status':'abstained'},
            {'case_id':'4','status':'tool_failure'},
        ]  # Sixth assigned patient has no output and must remain in N.

    def test_denominators_and_failure_categories(self):
        s = summarize(reconcile(self.refs,self.a))
        self.assertEqual(s['assigned_patients'],6)
        self.assertEqual(s['completed_patients'],3)
        self.assertEqual(s['status_counts']['not_run'],1)
        self.assertEqual(s['end_to_end_label_success']['estimate'],2/6)
        self.assertEqual(s['completed_only_label_agreement']['estimate'],2/3)
        self.assertEqual(s['diagnostic_confusion_counts'],{'TP':1,'FN':1,'TN':1,'FP':0})
        self.assertEqual(s['missing_outcome_bounds']['sensitivity']['identification_bounds'],[1/3,2/3])
        self.assertEqual(s['missing_outcome_bounds']['specificity']['identification_bounds'],[1/3,1.])
        self.assertIsNone(s['cost_usd']['total'])
        self.assertIsNone(s['cost_usd']['measured_subtotal'])

    def test_missing_cost_is_not_zero(self):
        outputs=[dict(x) for x in self.a];outputs[0]['cost_usd']=0.25
        s=summarize(reconcile(self.refs,outputs))
        self.assertEqual(s['cost_usd']['measured_subtotal'],0.25)
        self.assertEqual(s['cost_usd']['missing_patients'],5)
        self.assertIsNone(s['cost_usd']['total'])

    def test_pairs_include_harms_and_successful_recovery(self):
        b=[{'case_id':str(i),'status':'completed','prediction':p} for i,p in enumerate([0,1,0,1,1,0])]
        arows=reconcile(self.refs,self.a);brows=reconcile(self.refs,b)
        p=paired(arows,brows)
        self.assertEqual((p['both_success'],p['a_only_success'],p['b_only_success'],p['neither_success']),(1,1,3,1))
        self.assertEqual(p['paired_patients'],6)
        self.assertEqual(p['b_minus_a'],2/6)
        self.assertEqual(p['exact_mcnemar_p'],0.625)
        self.assertEqual(paired(arows,brows,completed_only=True)['paired_patients'],3)

    def test_wilson_known_values_and_empty(self):
        ci=proportion(50,100)['ci95']
        self.assertAlmostEqual(ci[0],0.4038315303659956)
        self.assertAlmostEqual(ci[1],0.5961684696340044)
        self.assertGreater(proportion(0,40)['ci95'][1],0.08)
        self.assertLess(proportion(40,40)['ci95'][0],0.92)
        self.assertIsNone(proportion(0,0)['estimate'])
        self.assertIsNone(proportion(0,0)['ci95'])

    def test_exact_discordance_known_values(self):
        self.assertEqual(exact_mcnemar(0,6),0.03125)
        self.assertEqual(exact_mcnemar(6,0),0.03125)
        self.assertEqual(exact_mcnemar(3,3),1.)
        self.assertEqual(exact_mcnemar(0,0),1.)

    def test_rejects_repeat_and_unassigned_patient(self):
        with self.assertRaises(ValueError):reconcile(self.refs,self.a+[self.a[0]])
        with self.assertRaises(ValueError):reconcile(self.refs,[{'case_id':'outside','status':'not_run'}])
        refs=[dict(x) for x in self.refs];refs[1]['patient_id']=refs[0]['patient_id']
        with self.assertRaises(ValueError):reconcile(refs,[])

    def test_rejects_ambiguous_conclusion_and_bad_usage(self):
        for prediction in ['malignant',True,None,2]:
            with self.assertRaises(ValueError):reconcile(self.refs,[{'case_id':'0','status':'completed','prediction':prediction}])
        for value in [-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):reconcile(self.refs,[{'case_id':'0','status':'timeout','cost_usd':value}])
        with self.assertRaises(ValueError):reconcile(self.refs,[{'case_id':'0','status':'abstained','prediction':0}])


if __name__ == '__main__':unittest.main(verbosity=2)
