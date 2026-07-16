"""Shared presentation helpers for the Streamlit interface."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st


def answer_count(answers: dict[str, Any], questions: dict, required_only: bool = False) -> tuple[int, int]:
    configured = [
        question
        for section in questions.get("sections", [])
        for question in section.get("questions", [])
        if not required_only or question.get("required", False)
    ]
    answered = sum(answers.get(question["id"]) not in (None, "") for question in configured)
    return answered, len(configured)


def completion_label(completion: str, answered: int, required: int) -> str:
    labels = {"complete": "Completee", "partial": "Partielle", "not_started": "Non commencee"}
    return f"{labels[completion]} - {answered} / {required} reponses requises completees"


def render_question_prompt(question: dict) -> None:
    marker = " *" if question.get("required", False) else ""
    label = html.escape(f"{question['label']}{marker}")
    description = question.get("description", "")
    body = f"<strong>{label}</strong>"
    if description:
        body += f"<br><em>{html.escape(description)}</em>"
    st.markdown(body, unsafe_allow_html=True)


def render_dropdown_question(options: list[dict], saved_value: object, key: str) -> object:
    choices = [{"label": "Non renseigne", "value": None}, *options]
    values = [choice["value"] for choice in choices]
    selected = st.selectbox(
        "Reponse",
        choices,
        index=values.index(saved_value) if saved_value in values else 0,
        format_func=lambda option: option.get("description") or option["label"],
        key=key,
        label_visibility="collapsed",
    )
    return selected["value"]


def number_value(value: object) -> float | None:
    return None if value in (None, "") else float(value)
