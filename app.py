import streamlit as st

from src.db import (
    create_category,
    deactivate_category,
    get_active_categories,
    get_answers,
    init_db,
    save_answer,
    update_category,
)
from src.scoring import calculate_completion, load_questions


def required_answer_count(answers: dict, questions: dict) -> tuple[int, int]:
    required_questions = [
        question
        for section in questions.get("sections", [])
        for question in section.get("questions", [])
        if question.get("required", False)
    ]
    answered = sum(
        1
        for question in required_questions
        if answers.get(question["id"]) is not None and answers.get(question["id"]) != ""
    )
    return answered, len(required_questions)


def completion_label(completion: str, answered: int, required: int) -> str:
    labels = {
        "complete": "Complete",
        "partial": "Partial",
        "not_started": "Not started",
    }
    return f"{labels[completion]} - {answered} / {required} required answered"


def category_sidebar_label(category: dict, questions: dict) -> str:
    answers = get_answers(category["id"])
    completion = calculate_completion(answers, questions)
    answered, required = required_answer_count(answers, questions)
    status_labels = {
        "complete": "Complete",
        "partial": "Partial",
        "not_started": "Not started",
    }
    return f"{category['name']} ({status_labels[completion]}, {answered}/{required})"


def render_assessment_page() -> None:
    st.header("Assessment")

    categories = get_active_categories()
    if not categories:
        st.info("Add a category before starting an assessment.")
        return

    questions = load_questions()
    category_by_id = {category["id"]: category for category in categories}

    st.sidebar.divider()
    st.sidebar.subheader("Products")
    selected_category_id = st.sidebar.radio(
        "Product categories",
        [category["id"] for category in categories],
        format_func=lambda category_id: category_sidebar_label(
            category_by_id[category_id],
            questions,
        ),
        label_visibility="collapsed",
    )
    selected_category = category_by_id[selected_category_id]
    answers = get_answers(selected_category["id"])
    completion = calculate_completion(answers, questions)
    answered, required = required_answer_count(answers, questions)

    st.subheader(selected_category["name"])
    if selected_category["description"]:
        st.caption(selected_category["description"])
    st.caption(completion_label(completion, answered, required))

    with st.form(f"assessment_{selected_category['id']}"):
        tabs = st.tabs([section["label"] for section in questions["sections"]])
        pending_answers = {}

        for tab, section in zip(tabs, questions["sections"]):
            with tab:
                for question in section["questions"]:
                    question_id = question["id"]
                    label = question["label"]
                    if question.get("required", False):
                        label = f"{label} *"

                    saved_value = answers.get(question_id)
                    key = f"answer_{selected_category['id']}_{question_id}"

                    if question["type"] == "dropdown":
                        pending_answers[question_id] = render_dropdown_question(
                            label,
                            question["options"],
                            saved_value,
                            key,
                        )
                    elif question["type"] == "number":
                        pending_answers[question_id] = st.number_input(
                            label,
                            value=number_value(saved_value),
                            step=1.0,
                            key=key,
                        )
                    else:
                        st.warning(f"Unsupported question type: {question['type']}")

        submitted = st.form_submit_button("Save assessment")
        if submitted:
            for question_id, value in pending_answers.items():
                save_answer(
                    selected_category["id"],
                    question_id,
                    "" if value is None else value,
                )
            st.success(f"Saved assessment for {selected_category['name']}.")
            st.rerun()


def render_chart_page() -> None:
    st.header("Matrix / Bubble chart")
    st.info("Bubble chart will go here.")


def render_categories_admin_page() -> None:
    st.header("Categories admin")

    with st.form("create_category_form", clear_on_submit=True):
        st.subheader("Add category")
        name = st.text_input("Name")
        description = st.text_area("Description", height=90)
        submitted = st.form_submit_button("Add category")

        if submitted:
            if not name.strip():
                st.warning("Category name is required.")
            else:
                create_category(name, description)
                st.success(f"Added {name.strip()}.")
                st.rerun()

    st.divider()
    st.subheader("Active categories")

    categories = get_active_categories()
    if not categories:
        st.info("No active categories yet.")
        return

    for category in categories:
        label = f"{category['name']} | Last updated {category['updated_at']}"
        with st.expander(label):
            with st.form(f"edit_category_{category['id']}"):
                updated_name = st.text_input(
                    "Name",
                    value=category["name"],
                    key=f"name_{category['id']}",
                )
                updated_description = st.text_area(
                    "Description",
                    value=category["description"],
                    height=90,
                    key=f"description_{category['id']}",
                )

                save_changes = st.form_submit_button("Save changes")
                if save_changes:
                    if not updated_name.strip():
                        st.warning("Category name is required.")
                    else:
                        update_category(
                            category["id"],
                            updated_name,
                            updated_description,
                        )
                        st.success(f"Updated {updated_name.strip()}.")
                        st.rerun()

            if st.button("Deactivate category", key=f"deactivate_{category['id']}"):
                deactivate_category(category["id"])
                st.success(f"Deactivated {category['name']}.")
                st.rerun()


def render_dropdown_question(
    label: str,
    options: list[dict],
    saved_value: object,
    key: str,
) -> object:
    choices = [{"label": "Not answered", "value": None}, *options]
    labels = [choice["label"] for choice in choices]
    values_by_label = {choice["label"]: choice["value"] for choice in choices}
    saved_label = next(
        (
            choice["label"]
            for choice in choices
            if choice["value"] == saved_value
        ),
        "Not answered",
    )
    selected_label = st.selectbox(
        label,
        labels,
        index=labels.index(saved_label),
        key=key,
    )
    return values_by_label[selected_label]


def number_value(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


st.set_page_config(
    page_title="Supply Chain Traceability Matrix",
    layout="wide",
)

init_db()

st.title("Supply Chain Traceability Matrix")

page = st.sidebar.radio(
    "Navigation",
    ("Assessment", "Matrix / Bubble chart", "Categories admin"),
)

if page == "Assessment":
    render_assessment_page()
elif page == "Matrix / Bubble chart":
    render_chart_page()
elif page == "Categories admin":
    render_categories_admin_page()
