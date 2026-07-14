import pandas as pd
import plotly.express as px
import streamlit as st

from src.db import (
    create_category,
    delete_all_categories,
    deactivate_category,
    get_active_categories,
    get_answers,
    get_inactive_categories,
    init_db,
    reactivate_category,
    save_answer,
    update_category,
)
from src.scoring import calculate_completion, calculate_scores, load_questions


def apply_sidebar_styles() -> None:
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-size: 17px;
        }

        .stMarkdown, .stCaption, label, [data-testid="stWidgetLabel"] {
            font-size: 1rem;
        }

        div[data-baseweb="select"] {
            font-size: 1rem;
        }

        section[data-testid="stSidebar"] [data-testid="stButton"] button {
            font-size: 1rem;
            min-height: 2.35rem;
        }

        section[data-testid="stSidebar"] h3 {
            font-size: 1.1rem;
        }

        button {
            font-size: 1rem;
        }

        .status-dot {
            display: inline-block;
            width: 0.75rem;
            height: 0.75rem;
            margin-top: 0.8rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.45);
        }

        .status-dot.not-started {
            background-color: #ef4444;
        }

        .status-dot.partial {
            background-color: #f59e0b;
        }

        .status-dot.complete {
            background-color: #22c55e;
        }

        .status-dot.selected {
            box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.25);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div {
            display: flex;
            flex-direction: column;
            min-height: calc(100vh - 4rem);
        }

        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]:has(.sidebar-tools-marker) {
            margin-top: auto;
            padding-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def total_answer_count(answers: dict, questions: dict) -> tuple[int, int]:
    all_questions = [
        question
        for section in questions.get("sections", [])
        for question in section.get("questions", [])
    ]
    answered = sum(
        1
        for question in all_questions
        if answers.get(question["id"]) is not None and answers.get(question["id"]) != ""
    )
    return answered, len(all_questions)


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
    status_labels = {
        "complete": "Complete",
        "partial": "Partial",
        "not_started": "Not started",
    }
    return f"{category['name']} - {status_labels[completion]}"


def product_status_dot(completion: str, selected: bool) -> None:
    selected_class = " selected" if selected else ""
    st.markdown(
        f"<span class='status-dot {completion.replace('_', '-')}{selected_class}'></span>",
        unsafe_allow_html=True,
    )


def render_product_button(
    category: dict,
    questions: dict,
    selected_category_id: int | None,
) -> bool:
    answers = get_answers(category["id"])
    completion = calculate_completion(answers, questions)
    status_label = category_sidebar_label(category, questions)
    selected = category["id"] == selected_category_id
    dot_col, button_col = st.sidebar.columns([0.12, 0.88])
    with dot_col:
        product_status_dot(completion, selected)
    with button_col:
        return st.button(
            status_label,
            key=f"select_product_{category['id']}",
            type="primary" if selected else "secondary",
            width="stretch",
        )


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
    st.sidebar.subheader("Product categories")

    selected_category_id = ensure_selected_category_id(categories)
    if not categories:
        st.sidebar.caption("No active products")
    else:
        for category in categories:
            product_clicked = render_product_button(
                category,
                questions,
                selected_category_id,
            )

            if product_clicked:
                st.session_state.selected_category_id = category["id"]
                st.session_state.page = "Assessment"
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


def render_tools_sidebar() -> None:
    with st.sidebar.container():
        st.markdown("<span class='sidebar-tools-marker'></span>", unsafe_allow_html=True)
        st.subheader("Tools")

        if st.button(
            "Matrix",
            type="primary" if st.session_state.get("page") == "Matrix / Bubble chart" else "secondary",
            width="stretch",
        ):
            st.session_state.page = "Matrix / Bubble chart"
            st.rerun()

        if st.button(
            "Admin",
            type="primary" if st.session_state.get("page") == "Categories admin" else "secondary",
            width="stretch",
        ):
            st.session_state.page = "Categories admin"
            st.rerun()


def render_assessment_page(
    selected_category_id: int | None,
    categories: list[dict],
    questions: dict,
) -> None:
    if selected_category_id is None:
        st.header("Assessment")
        st.info("Add a category before starting an assessment.")
        return

    category_by_id = {category["id"]: category for category in categories}
    selected_category = category_by_id[selected_category_id]
    answers = get_answers(selected_category["id"])
    completion = calculate_completion(answers, questions)
    answered, required = required_answer_count(answers, questions)

    st.title(selected_category["name"])
    if selected_category["description"]:
        st.write(selected_category["description"])
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

    st.divider()
    edit_key = f"edit_selected_category_{selected_category['id']}"
    edit_col, delete_col = st.columns([0.22, 0.78])
    if edit_col.button("Edit category details", key=f"toggle_{edit_key}"):
        st.session_state[edit_key] = not st.session_state.get(edit_key, False)

    if delete_col.button(
        "Deactivate category",
        key=f"deactivate_selected_category_{selected_category['id']}",
    ):
        deactivate_category(selected_category["id"])
        st.session_state.pop("selected_category_id", None)
        st.rerun()

    if st.session_state.get(edit_key, False):
        with st.form(f"selected_category_details_{selected_category['id']}"):
            updated_name = st.text_input("Category name", value=selected_category["name"])
            updated_description = st.text_area(
                "Category description",
                value=selected_category["description"],
                height=90,
            )
            if st.form_submit_button("Save category details"):
                if not updated_name.strip():
                    st.warning("Category name is required.")
                else:
                    update_category(
                        selected_category["id"],
                        updated_name,
                        updated_description,
                    )
                    st.session_state[edit_key] = False
                    st.success("Category details updated.")
                    st.rerun()


def build_chart_rows(categories: list[dict], questions: dict) -> tuple[list[dict], list[dict]]:
    chart_rows = []
    incomplete_rows = []

    for category in categories:
        answers = get_answers(category["id"])
        scores = calculate_scores(answers, questions)
        answered, required = required_answer_count(answers, questions)

        if scores["completion"] == "complete":
            chart_rows.append(
                {
                    "category": category["name"],
                    "description": category["description"],
                    "x": scores["x"],
                    "y": scores["y"],
                    "size": scores["size"],
                    "completion": scores["completion"],
                }
            )
        else:
            incomplete_rows.append(
                {
                    "category": category["name"],
                    "completion": scores["completion"],
                    "answered": answered,
                    "required": required,
                }
            )

    return chart_rows, incomplete_rows


def render_chart_page(categories: list[dict], questions: dict) -> None:
    st.header("Matrix / Bubble chart")

    chart_rows, incomplete_rows = build_chart_rows(categories, questions)
    if not chart_rows:
        st.info("No complete categories yet. Complete all required answers to show bubbles.")
    else:
        chart_data = pd.DataFrame(chart_rows)
        fig = px.scatter(
            chart_data,
            x="x",
            y="y",
            size="size",
            color="category",
            hover_name="category",
            hover_data={
                "description": True,
                "x": ":.2f",
                "y": ":.2f",
                "size": ":.2f",
                "completion": False,
            },
            labels={
                "x": "Supply chain criticality",
                "y": "Traceability maturity",
                "size": "Relative impact",
                "category": "Product category",
            },
            size_max=60,
        )
        fig.update_layout(
            height=620,
            margin={"l": 20, "r": 20, "t": 30, "b": 20},
            legend_title_text="Product category",
        )
        st.plotly_chart(fig, width="stretch")

    if incomplete_rows:
        st.subheader("Not shown on chart")
        st.caption("Only categories with all required answers complete are plotted.")
        st.dataframe(
            pd.DataFrame(incomplete_rows),
            width="stretch",
            hide_index=True,
        )


def render_categories_admin_page(questions: dict) -> None:
    st.header("Admin")

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
                answers = get_answers(category["id"])
                answered, total = total_answer_count(answers, questions)
                st.caption(f"Progress {answered} / {total} questions answered")
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
                answers = get_answers(category["id"])
                answered, total = total_answer_count(answers, questions)
                st.caption(f"Progress {answered} / {total} questions answered")
                st.caption(f"Last updated {category['updated_at']}")
            if action_col.button(
                "Add back",
                key=f"reactivate_category_{category['id']}",
                width="stretch",
            ):
                reactivate_category(category["id"])
                st.session_state.selected_category_id = category["id"]
                st.session_state.page = "Assessment"
                st.rerun()

    st.divider()
    st.subheader("Danger zone")
    st.warning("This permanently deletes all products and all saved answers.")
    with st.form("delete_all_products_form"):
        confirmation = st.text_input("Type DELETE to confirm")
        delete_submitted = st.form_submit_button("Delete all products permanently")

        if delete_submitted:
            if confirmation != "DELETE":
                st.warning("Type DELETE exactly to confirm.")
            else:
                delete_all_categories()
                st.session_state.pop("selected_category_id", None)
                st.session_state.page = "Assessment"
                st.success("All products and answers were permanently deleted.")
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

apply_sidebar_styles()
init_db()
questions = load_questions()
categories = get_active_categories()

if "page" not in st.session_state:
    st.session_state.page = "Assessment"

selected_category_id = render_products_sidebar(categories, questions)
render_tools_sidebar()

page = st.session_state.page

if page == "Assessment":
    render_assessment_page(selected_category_id, get_active_categories(), questions)
elif page == "Matrix / Bubble chart":
    render_chart_page(get_active_categories(), questions)
elif page == "Categories admin":
    render_categories_admin_page(questions)
