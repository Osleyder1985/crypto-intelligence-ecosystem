import unittest

from scripts.stack_poc.sensitivity_analysis import analyze


class SensitivityAnalysisTests(unittest.TestCase):
    def test_missing_score_or_evidence_blocks_ranking(self):
        result = analyze({
            'weights': {'contracts': 50, 'charts': 50},
            'candidates': [{'name': 'Flutter', 'scores': {'contracts': 4, 'charts': None}, 'evidence': {'contracts': 'run-1'}}],
        })
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['ranking'], [])
        self.assertEqual(len(result['missing']), 1)

    def test_incomplete_evidence_reports_partial_scores_without_ranking(self):
        result = analyze({
            'weights': {'contracts': 70, 'charts': 30},
            'candidates': [
                {'name': 'A', 'scores': {'contracts': 4, 'charts': None}, 'evidence': {'contracts': 'run-a'}},
                {'name': 'B', 'scores': {'contracts': None, 'charts': 5}, 'evidence': {'charts': 'run-b'}},
            ],
        })
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['ranking'], [])
        self.assertEqual(result['sensitivity'], [])
        self.assertEqual(result['partial_scores'][0]['weight_coverage_percent'], 70)
        self.assertEqual(result['partial_scores'][0]['partial_score_out_of_100'], 80)
        self.assertEqual(result['partial_scores'][1]['weight_coverage_percent'], 30)
        self.assertEqual(result['partial_scores'][1]['partial_score_out_of_100'], 100)
        self.assertIn('different evidence coverage', result['partial_score_warning'])

    def test_complete_evidence_computes_baseline_and_all_sensitivity_scenarios(self):
        result = analyze({
            'weights': {'contracts': 50, 'charts': 50},
            'candidates': [
                {'name': 'A', 'scores': {'contracts': 5, 'charts': 2}, 'evidence': {'contracts': 'run-a', 'charts': 'run-b'}},
                {'name': 'B', 'scores': {'contracts': 3, 'charts': 4}, 'evidence': {'contracts': 'run-c', 'charts': 'run-d'}},
            ],
        })
        self.assertEqual(result['status'], 'complete')
        self.assertEqual([row['candidate'] for row in result['ranking']], ['A', 'B'])
        self.assertEqual(len(result['sensitivity']), 4)
        self.assertEqual([row['score_out_of_100'] for row in result['ranking']], [70.0, 70.0])
        self.assertTrue(all('ranking_changed' in row for row in result['sensitivity']))

    def test_weights_must_sum_to_one_hundred(self):
        with self.assertRaisesRegex(ValueError, 'sum to 100'):
            analyze({'weights': {'contracts': 40}, 'candidates': [{'name': 'A'}]})

    def test_boolean_is_not_a_valid_numeric_weight_or_score(self):
        with self.assertRaisesRegex(ValueError, 'weights must be positive'):
            analyze({'weights': {'contracts': True, 'charts': 99}, 'candidates': [{'name': 'A'}]})
        result = analyze({
            'weights': {'contracts': 100},
            'candidates': [{'name': 'A', 'scores': {'contracts': True}, 'evidence': {'contracts': 'run-1'}}],
        })
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['ranking'], [])

    def test_candidate_names_must_be_unique_and_non_empty(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            analyze({'weights': {'contracts': 100}, 'candidates': [{'name': 'A'}, {'name': 'A'}]})
        with self.assertRaisesRegex(ValueError, 'non-empty name'):
            analyze({'weights': {'contracts': 100}, 'candidates': [{'name': '  '}] })


if __name__ == '__main__':
    unittest.main()
