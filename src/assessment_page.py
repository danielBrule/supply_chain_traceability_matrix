"""Product-category assessment page."""

from __future__ import annotations

import streamlit as st

from src.db import deactivate_category, get_answers, save_answer, update_category
from src.scoring import calculate_completion
from src.ui_common import answer_count, completion_label, number_value, render_dropdown_question, render_question_prompt


def render_assessment_page(selected_category_id: int | None, categories: list[dict], questions: dict) -> None:
    if selected_category_id is None:
        st.header("Evaluation")
        st.info("Ajoutez une famille de produit avant de commencer une evaluation.")
        return

    selected = {category["id"]: category for category in categories}[selected_category_id]
    answers = get_answers(selected["id"])
    completion = calculate_completion(answers, questions)
    answered, required = answer_count(answers, questions, required_only=True)

    st.title(selected["name"])
    if selected["description"]:
        st.write(selected["description"])
    st.caption(completion_label(completion, answered, required))

    with st.form(f"assessment_{selected['id']}"):
        tabs = st.tabs([section["label"] for section in questions["sections"]])
        pending = {}
        for tab, section in zip(tabs, questions["sections"]):
            with tab:
                for question in section["questions"]:
                    question_id = question["id"]
                    render_question_prompt(question)
                    saved = answers.get(question_id)
                    key = f"answer_{selected['id']}_{question_id}"
                    if question["type"] == "dropdown":
                        pending[question_id] = render_dropdown_question(question["options"], saved, key)
                    elif question["type"] == "number":
                        pending[question_id] = st.number_input(
                            "Reponse", value=number_value(saved), step=1.0, key=key, label_visibility="collapsed"
                        )
                    else:
                        st.warning(f"Type de question non supporte : {question['type']}")

        if st.form_submit_button("Sauvegarder"):
            for question_id, value in pending.items():
                save_answer(selected["id"], question_id, "" if value is None else value)
            st.success(f"Evaluation sauvegardee pour {selected['name']}.")
            st.rerun()

    _render_category_actions(selected)


def _render_category_actions(category: dict) -> None:
    st.divider()
    edit_key = f"edit_selected_category_{category['id']}"
    edit_col, deactivate_col = st.columns([0.22, 0.78])
    if edit_col.button("Modifier la famille de produit", key=f"toggle_{edit_key}"):
        st.session_state[edit_key] = not st.session_state.get(edit_key, False)
    if deactivate_col.button("Desactiver la famille de produit", key=f"deactivate_{category['id']}"):
        deactivate_category(category["id"])
        st.session_state.pop("selected_category_id", None)
        st.rerun()

    if st.session_state.get(edit_key, False):
        with st.form(f"category_details_{category['id']}"):
            name = st.text_input("Nom de la famille de produit", value=category["name"])
            description = st.text_area("Description de la famille de produit", value=category["description"], height=90)
            if st.form_submit_button("Enregistrer la famille de produit"):
                if not name.strip():
                    st.warning("Le nom de la famille de produit est obligatoire.")
                else:
                    update_category(category["id"], name, description)
                    st.session_state[edit_key] = False
                    st.rerun()
