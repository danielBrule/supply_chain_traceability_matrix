import streamlit as st

from src.db import (
    create_category,
    deactivate_category,
    get_active_categories,
    get_answers,
    get_inactive_categories,
    init_db,
    reactivate_category,
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


def ensure_selected_category_id(categories: list[dict]) -> int | None:
    if not categories:
        st.session_state.pop("selected_category_id", None)
        return None

    category_ids = [category["id"] for category in categories]
    selected_category_id = st.session_state.get("selected_category_id")
    if selected_category_id not in category_ids:
        selected_category_id = category_ids[0]
        st.session_state.selected_category_id = selected_category_id

    return selected_category_id


def render_products_sidebar(categories: list[dict], questions: dict) -> int | None:
    st.sidebar.subheader("Products")

    selected_category_id = ensure_selected_category_id(categories)
    if not categories:
        st.sidebar.caption("No active products")
    else:
        for category in categories:
            product_col, menu_col = st.sidebar.columns([0.58, 0.42])
            label = category_sidebar_label(category, questions)
            if category["id"] == selected_category_id:
                label = f"Selected - {label}"

            if product_col.button(
                label,
                key=f"select_product_{category['id']}",
                use_container_width=True,
            ):
                st.session_state.selected_category_id = category["id"]
                st.session_state.page = "Assessment"
                st.rerun()

            with menu_col.popover("...", use_container_width=True):
                with st.form(f"sidebar_edit_category_{category['id']}"):
                    updated_name = st.text_input(
                        "Name",
                        value=category["name"],
                        key=f"sidebar_name_{category['id']}",
                    )
                    updated_description = st.text_area(
                        "Description",
                        value=category["description"],
                        height=90,
                        key=f"sidebar_description_{category['id']}",
                    )

                    if st.form_submit_button("Save"):
                        if not updated_name.strip():
                            st.warning("Category name is required.")
                        else:
                            update_category(
                                category["id"],
                                updated_name,
                                updated_description,
                            )
                            st.rerun()

                if st.button("Deactivate", key=f"sidebar_deactivate_{category['id']}"):
                    deactivate_category(category["id"])
                    if st.session_state.get("selected_category_id") == category["id"]:
                        st.session_state.pop("selected_category_id", None)
                    st.rerun()

    with st.sidebar.popover("+ Add category"):
        with st.form("sidebar_create_category_form", clear_on_submit=True):
            name = st.text_input("Name", key="sidebar_new_category_name")
            description = st.text_area(
                "Description",
                height=90,
                key="sidebar_new_category_description",
            )

            if st.form_submit_button("Add"):
                if not name.strip():
                    st.warning("Category name is required.")
                else:
                    category_id = create_category(name, description)
                    st.session_state.selected_category_id = category_id
                    st.session_state.page = "Assessment"
                    st.rerun()

    return ensure_selected_category_id(get_active_categories())


def render_matrix_sidebar() -> None:
    st.sidebar.subheader("Matrix")
    if st.sidebar.button("Bubble chart", use_container_width=True):
        st.session_state.page = "Matrix / Bubble chart"
        st.rerun()


def render_navigation_sidebar() -> None:
    st.sidebar.subheader("Navigation")
    admin_label = "Selected - Categories admin"

    if st.session_state.get("page") != "Categories admin":
        admin_label = "Categories admin"

    if st.sidebar.button(admin_label, use_container_width=True):
        st.session_state.page = "Categories admin"
        st.rerun()


def render_assessment_page(
    selected_category_id: int | None,
    categories: list[dict],
    questions: dict,
) -> None:
    st.header("Assessment")

    if selected_category_id is None:
        st.info("Add a category before starting an assessment.")
        return

    category_by_id = {category["id"]: category for category in categories}
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

    categories = get_active_categories()
    inactive_categories = get_inactive_categories()

    st.subheader("Active categories")
    if not categories:
        st.info("No active categories yet.")
    else:
        for category in categories:
            with st.expander(category["name"]):
                if category["description"]:
                    st.write(category["description"])
                st.caption(f"Last updated {category['updated_at']}")

    st.divider()
    st.subheader("Inactive categories")
    if not inactive_categories:
        st.info("No inactive categories.")
    else:
        for category in inactive_categories:
            category_col, action_col = st.columns([0.75, 0.25])
            with category_col:
                st.write(category["name"])
                if category["description"]:
                    st.caption(category["description"])
                st.caption(f"Last updated {category['updated_at']}")
            if action_col.button(
                "Add back",
                key=f"reactivate_category_{category['id']}",
                use_container_width=True,
            ):
                reactivate_category(category["id"])
                st.session_state.selected_category_id = category["id"]
                st.session_state.page = "Assessment"
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
questions = load_questions()
categories = get_active_categories()

st.title("Supply Chain Traceability Matrix")

selected_category_id = render_products_sidebar(categories, questions)
st.sidebar.divider()
render_matrix_sidebar()
st.sidebar.divider()

if "page" not in st.session_state:
    st.session_state.page = "Assessment"

page = st.session_state.page
render_navigation_sidebar()

if page == "Assessment":
    render_assessment_page(selected_category_id, get_active_categories(), questions)
elif page == "Matrix / Bubble chart":
    render_chart_page()
elif page == "Categories admin":
    render_categories_admin_page()
