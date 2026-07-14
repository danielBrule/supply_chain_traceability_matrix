"""Question loading, completion checks, and chart score calculations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

QUESTIONS_PATH = Path("config/questions.yaml")
SCORE_KEYS = ("x", "y", "size")


def load_questions(path: str | Path = QUESTIONS_PATH) -> dict[str, Any]:
    """Load the question configuration from YAML."""
    with Path(path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if "sections" not in data or not isinstance(data["sections"], list):
        raise ValueError("Question config must contain a 'sections' list.")

    return data


def calculate_completion(
    category_answers: dict[str, Any], questions: dict[str, Any]
) -> str:
    """Return not_started, partial, or complete for required answers."""
    required_questions = [
        question
        for question in _iter_questions(questions)
        if question.get("required", False)
    ]
    answered_count = sum(
        1 for question in required_questions if _has_answer(category_answers, question["id"])
    )

    if answered_count == 0:
        return "not_started"
    if answered_count == len(required_questions):
        return "complete"
    return "partial"


def calculate_scores(
    category_answers: dict[str, Any],
    questions: dict[str, Any],
    scenario: dict[str, Any] | None = None,
) -> dict[str, float | str | None]:
    """Calculate weighted chart scores for a category's answers."""
    completion = calculate_completion(category_answers, questions)
    if completion != "complete":
        return {"x": None, "y": None, "size": None, "completion": completion}

    scores = {key: 0.0 for key in SCORE_KEYS}

    for question in _iter_questions(questions):
        question_id = question["id"]
        if not _has_answer(category_answers, question_id):
            continue

        value = _numeric_answer(category_answers[question_id])
        weights = question.get("contributes_to", {})

        for score_key in SCORE_KEYS:
            question_weight = float(weights.get(score_key, 0.0))
            scenario_weight = _scenario_weight(scenario, question_id, score_key)
            scores[score_key] += value * question_weight * scenario_weight

    return {
        "x": round(scores["x"], 2),
        "y": round(scores["y"], 2),
        "size": round(scores["size"], 2),
        "completion": completion,
    }


def _iter_questions(questions: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        question
        for section in questions.get("sections", [])
        for question in section.get("questions", [])
    ]


def get_scenarios(questions: dict[str, Any]) -> list[dict[str, Any]]:
    """Return configured scenarios, falling back to a neutral scenario."""
    scenarios = questions.get("scenarios", [])
    if scenarios:
        return scenarios

    return [
        {
            "id": "default",
            "label": "Default scenario",
            "description": "Neutral weighting",
            "weights": {},
        }
    ]


def get_scenario_by_id(
    questions: dict[str, Any],
    scenario_id: str | None,
) -> dict[str, Any]:
    """Find a scenario by ID, or return the first configured scenario."""
    scenarios = get_scenarios(questions)
    for scenario in scenarios:
        if scenario["id"] == scenario_id:
            return scenario
    return scenarios[0]


def _has_answer(category_answers: dict[str, Any], question_id: str) -> bool:
    value = category_answers.get(question_id)
    return value is not None and value != ""


def _numeric_answer(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Answer value must be numeric for scoring: {value!r}") from exc


def _scenario_weight(
    scenario: dict[str, Any] | None,
    question_id: str,
    score_key: str,
) -> float:
    if scenario is None or score_key == "size":
        return 1.0

    question_weights = scenario.get("weights", {}).get(question_id, {})
    return float(question_weights.get(score_key, 1.0))
