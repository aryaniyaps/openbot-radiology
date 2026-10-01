import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import build_results
from build_results import recognized,summarize_label,wilson,paired_difference

class ScoringChecks(unittest.TestCase):
    def test_negated_diagnosis_is_not_recognition(self):
        self.assertFalse(recognized('No evidence of pituitary macroadenoma.',r'macroadenoma'))
        self.assertTrue(recognized('No hemorrhage. Pituitary macroadenoma is present.',r'macroadenoma'))
    def test_abstentions_remain_in_assigned_denominator(self):
        rows=[{'reference':'present','prediction':'present'},{'reference':'present','prediction':'unassessable'},{'reference':'absent','prediction':'failure'},{'reference':'unscorable','prediction':'absent'}]
        s=summarize_label(rows);self.assertEqual(s['all_assigned_positive_detection'],.5);self.assertEqual(s['all_assigned_correct_negative'],0);self.assertEqual(s['definite_only_sensitivity'],1);self.assertEqual(s['unresolved_positive'],1)
    def test_small_denominators_do_not_look_certain(self):
        self.assertIsNone(wilson(0,0));self.assertLess(wilson(5,5)[0],.6);self.assertGreater(wilson(0,5)[1],.4)
    def test_paired_patient_difference(self):
        d=paired_difference([1,0,-1,0]);self.assertEqual(d['astra_minus_sol'],0);self.assertEqual(d['n'],4);self.assertLess(d['patient_bootstrap_ci95'][0],0);self.assertGreater(d['patient_bootstrap_ci95'][1],0)
    def test_upload_recovery_preserves_first_attempt(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(build_results,'P',Path(folder)):
            directory=Path(folder)/'results/evaluation/direct/gpt-6-astra/CASE';directory.mkdir(parents=True)
            first={'status':'controller-failure','exception':'HTTPError: HTTP Error 507: Insufficient Storage','turns':[]}
            original=json.dumps(first);(directory/'result.json').write_text(original)
            recovery=directory.parent/'CASE-transport-recovery';recovery.mkdir();(recovery/'result.json').write_text(json.dumps({'status':'succeeded','structured_answer':{'primary_diagnosis':'example'}}))
            result=build_results.load_result('CASE','gpt-6-astra')
            self.assertEqual(result['status'],'succeeded');self.assertEqual(result['first_attempt_status'],'controller-failure');self.assertTrue(result['transport_recovery']);self.assertEqual((directory/'result.json').read_text(),original)
    def test_recovery_cannot_replace_any_started_read(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(build_results,'P',Path(folder)):
            directory=Path(folder)/'results/evaluation/direct/gpt-6-astra/CASE';directory.mkdir(parents=True)
            (directory/'result.json').write_text(json.dumps({'status':'controller-failure','exception':'HTTPError: HTTP Error 507: Insufficient Storage','turns':[]}));(directory/'request-01.json').write_text('{}')
            with self.assertRaises(AssertionError):build_results.load_result('CASE','gpt-6-astra')

if __name__=='__main__':unittest.main()
