import unittest

from src.scoring import calculate_completion, calculate_scores, classify_bubble_size


QUESTIONS = {
    "sections": [{"id": "main", "label": "Main", "questions": [
        {"id": "risk", "required": True, "contributes_to": {"x": 1, "y": 0, "size": 0}},
        {"id": "value", "required": True, "contributes_to": {"x": 0, "y": 1, "size": 0}},
        {"id": "cost", "required": False, "contributes_to": {"x": 0, "y": 0, "size": 1}},
    ]}],
    "bubble_sizes": [
        {"min_score": 0, "max_score": 2, "label": "Small", "plot_size": 20},
        {"min_score": 3, "max_score": 10, "label": "Large", "plot_size": 60},
    ],
}


class ScoringTests(unittest.TestCase):
    def test_completion_uses_required_questions_only(self):
        self.assertEqual(calculate_completion({}, QUESTIONS), "not_started")
        self.assertEqual(calculate_completion({"risk": 4}, QUESTIONS), "partial")
        self.assertEqual(calculate_completion({"risk": 4, "value": 7}, QUESTIONS), "complete")

    def test_scores_complete_answers(self):
        result = calculate_scores({"risk": 4, "value": 7, "cost": 2}, QUESTIONS)
        self.assertEqual((result["x"], result["y"], result["size_score"]), (4, 7, 2))
        self.assertEqual(result["size_label"], "Small")

    def test_incomplete_answers_are_not_scored(self):
        result = calculate_scores({"risk": 4}, QUESTIONS)
        self.assertIsNone(result["x"])

    def test_scenario_weights_do_not_change_cost(self):
        scenario = {"weights": {"risk": {"x": 0.5}, "cost": {"size": 0.1}}}
        result = calculate_scores({"risk": 4, "value": 7, "cost": 4}, QUESTIONS, scenario)
        self.assertEqual(result["x"], 2)
        self.assertEqual(result["size_score"], 4)

    def test_bubble_size_above_ranges_uses_last_rule(self):
        self.assertEqual(classify_bubble_size(11, QUESTIONS)["label"], "Large")


if __name__ == "__main__":
    unittest.main()
