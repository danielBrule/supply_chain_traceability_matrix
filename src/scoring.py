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
    category_answers: dict[str, Any], questions: dict[str, Any]
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
            scores[score_key] += value * float(weights.get(score_key, 0.0))

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


def _has_answer(category_answers: dict[str, Any], question_id: str) -> bool:
    value = category_answers.get(question_id)
    return value is not None and value != ""


def _numeric_answer(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Answer value must be numeric for scoring: {value!r}") from exc
