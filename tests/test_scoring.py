import unittest

from src.scoring import (
    calculate_completion,
    calculate_scores,
    classify_bubble_size,
    get_scenario_by_id,
    load_questions,
)


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

# Deliberately asymmetric values make every scenario multiplier observable.
# These are valid dropdown values from config/questions.yaml.
CONFIGURED_ANSWERS = {
    "c1_obligation_reglementaire_contractuelle": 1,
    "c2_risque_sanitaire_securite": 4,
    "c3_exposition_incident": 7,
    "c4_risque_operationnel_continuite": 9.5,
    "v1_differenciation_premium": 1,
    "v2_confiance_engagement_client": 4,
    "v3_resilience_proactive": 7,
    "v4_nouveaux_modeles_affaires": 9.5,
    "s1_profondeur_chaine": 1,
    "s2_heterogeneite_parc_fournisseurs": 4,
    "s3_finesse_maille_conservation": 7,
    "s4_ecart_systeme_information": 9.5,
    "s5_impact_organisationnel": 1,
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


class ConfiguredScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions = load_questions()

    def assert_scenario_scores(self, scenario_id, expected_x, expected_y):
        scenario = get_scenario_by_id(self.questions, scenario_id)
        result = calculate_scores(CONFIGURED_ANSWERS, self.questions, scenario)
        self.assertEqual(result["completion"], "complete")
        self.assertEqual(result["x"], expected_x)
        self.assertEqual(result["y"], expected_y)

    def test_socle_expected_scores(self):
        # X = 0.25 * (1*1.2 + 4*1.2 + 7*1.0 + 9.5*0.6)
        # Y = 0.25 * (1*1.4 + 4*1.0 + 7*1.0 + 9.5*0.6)
        self.assert_scenario_scores("socle", expected_x=4.67, expected_y=4.53)

    def test_defensif_conformite_expected_scores(self):
        # X = 0.25 * (1*1.4 + 4*1.4 + 7*0.8 + 9.5*0.4)
        # Y uses the same multipliers as the Socle scenario.
        self.assert_scenario_scores(
            "defensif_conformite", expected_x=4.1, expected_y=4.53
        )

    def test_offensif_differenciation_expected_scores(self):
        # X uses the same multipliers as the Socle scenario.
        # Y = 0.25 * (1*1.6 + 4*1.2 + 7*0.6 + 9.5*0.6)
        self.assert_scenario_scores(
            "offensif_differenciation", expected_x=4.67, expected_y=4.08
        )

    def test_resilience_continuite_expected_scores(self):
        # X = 0.25 * (1*1.0 + 4*1.0 + 7*0.8 + 9.5*1.2)
        # Y = 0.25 * (1*1.0 + 4*0.8 + 7*1.6 + 9.5*0.6)
        self.assert_scenario_scores(
            "resilience_continuite", expected_x=5.5, expected_y=5.28
        )

    def test_cost_is_identical_for_every_configured_scenario(self):
        # Cost = 0.2 * (1 + 4 + 7 + 9.5 + 1) = 4.5.
        expected_cost = 4.5
        for scenario_id in (
            "socle",
            "defensif_conformite",
            "offensif_differenciation",
            "resilience_continuite",
        ):
            with self.subTest(scenario=scenario_id):
                scenario = get_scenario_by_id(self.questions, scenario_id)
                result = calculate_scores(CONFIGURED_ANSWERS, self.questions, scenario)
                self.assertEqual(result["size_score"], expected_cost)


if __name__ == "__main__":
    unittest.main()
