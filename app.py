import html

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
    save_setting,
    get_setting,
    update_category,
)
from src.scoring import (
    calculate_completion,
    calculate_scores,
    get_bubble_size_rules,
    get_scenario_by_id,
    get_scenarios,
    load_questions,
)


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
        "complete": "Complétée",
        "partial": "Partielle",
        "not_started": "Non commencee",
    }
    return f"{labels[completion]} - {answered} / {required} reponses requises completees"


def category_sidebar_label(category: dict, questions: dict) -> str:
    answers = get_answers(category["id"])
    completion = calculate_completion(answers, questions)
    status_labels = {
        "complete": "Complétée",
        "partial": "Partielle",
        "not_started": "Non commencee",
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
    selected = (
        category["id"] == selected_category_id
        and st.session_state.get("page") == "Assessment"
    )
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
    st.sidebar.subheader("Famille de produit")

    selected_category_id = ensure_selected_category_id(categories)
    if not categories:
        st.sidebar.caption("Aucune famille de produit active")
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

    with st.sidebar.popover("+ Ajouter une famille"):
        with st.form("sidebar_create_category_form", clear_on_submit=True):
            name = st.text_input("Nom", key="sidebar_new_category_name")
            description = st.text_area(
                "Description",
                height=90,
                key="sidebar_new_category_description",
            )

            if st.form_submit_button("Ajouter"):
                if not name.strip():
                    st.warning("Le nom de la famille de produit est obligatoire.")
                else:
                    category_id = create_category(name, description)
                    st.session_state.selected_category_id = category_id
                    st.session_state.page = "Assessment"
                    st.rerun()

    return ensure_selected_category_id(get_active_categories())


def render_tools_sidebar() -> None:
    with st.sidebar.container():
        st.markdown("<span class='sidebar-tools-marker'></span>", unsafe_allow_html=True)
        st.subheader("Outils")

        if st.button(
            "Matrice",
            type="primary" if st.session_state.get("page") == "Matrix / Bubble chart" else "secondary",
            width="stretch",
        ):
            st.session_state.page = "Matrix / Bubble chart"
            st.rerun()

        if st.button(
            "Administration",
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
        st.header("Evaluation")
        st.info("Ajoutez une famille de produit avant de commencer une evaluation.")
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
                    render_question_prompt(question)

                    saved_value = answers.get(question_id)
                    key = f"answer_{selected_category['id']}_{question_id}"

                    if question["type"] == "dropdown":
                        pending_answers[question_id] = render_dropdown_question(
                            question["options"],
                            saved_value,
                            key,
                        )
                    elif question["type"] == "number":
                        pending_answers[question_id] = st.number_input(
                            "Reponse",
                            value=number_value(saved_value),
                            step=1.0,
                            key=key,
                            label_visibility="collapsed",
                        )
                    else:
                        st.warning(f"Type de question non supporte : {question['type']}")

        submitted = st.form_submit_button("Sauvegarder")
        if submitted:
            for question_id, value in pending_answers.items():
                save_answer(
                    selected_category["id"],
                    question_id,
                    "" if value is None else value,
                )
            st.success(f"Evaluation sauvegardee pour {selected_category['name']}.")
            st.rerun()

    st.divider()
    edit_key = f"edit_selected_category_{selected_category['id']}"
    edit_col, delete_col = st.columns([0.22, 0.78])
    if edit_col.button("Modifier la famille de produit", key=f"toggle_{edit_key}"):
        st.session_state[edit_key] = not st.session_state.get(edit_key, False)

    if delete_col.button(
        "Desactiver la famille de produit",
        key=f"deactivate_selected_category_{selected_category['id']}",
    ):
        deactivate_category(selected_category["id"])
        st.session_state.pop("selected_category_id", None)
        st.rerun()

    if st.session_state.get(edit_key, False):
        with st.form(f"selected_category_details_{selected_category['id']}"):
            updated_name = st.text_input("Nom de la famille de produit", value=selected_category["name"])
            updated_description = st.text_area(
                "Description de la famille de produit",
                value=selected_category["description"],
                height=90,
            )
            if st.form_submit_button("Enregistrer la famille de produit"):
                if not updated_name.strip():
                    st.warning("Le nom de la famille de produit est obligatoire.")
                else:
                    update_category(
                        selected_category["id"],
                        updated_name,
                        updated_description,
                    )
                    st.session_state[edit_key] = False
                    st.success("Famille de produit mise a jour.")
                    st.rerun()


def build_chart_rows(
    categories: list[dict],
    questions: dict,
    scenario: dict,
) -> tuple[list[dict], list[dict]]:
    chart_rows = []
    incomplete_rows = []

    for category in categories:
        answers = get_answers(category["id"])
        scores = calculate_scores(answers, questions, scenario)
        answered, required = required_answer_count(answers, questions)

        if scores["completion"] == "complete":
            chart_rows.append(
                {
                    "category": category["name"],
                    "description": category["description"],
                    "x": scores["x"],
                    "y": scores["y"],
                    "size": scores["size"],
                    "size_score": scores["size_score"],
                    "size_label": scores["size_label"],
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
    st.header("Matrice")

    selected_scenario = get_selected_scenario(questions)
    st.caption(f"Scenario: {selected_scenario['label']}")
    if selected_scenario.get("description"):
        st.caption(selected_scenario["description"])

    chart_rows, incomplete_rows = build_chart_rows(
        categories,
        questions,
        selected_scenario,
    )
    if not chart_rows:
        st.info("Aucune famille de produit complete pour le moment. Completez toutes les reponses obligatoires pour afficher les bulles.")
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
                "size": False,
                "size_score": ":.2f",
                "size_label": True,
                "completion": False,
            },
            labels={
                "x": "Criticite",
                "y": "Valeur",
                "size_score": "Score cout",
                "size_label": "Taille de bulle",
                "category": "Famille de produit",
            },
            size_max=60,
        )
        fig.update_layout(
            height=620,
            margin={"l": 20, "r": 20, "t": 30, "b": 20},
            legend_title_text="Famille de produit",
        )
        add_matrix_quadrants(fig)
        st.plotly_chart(fig, width="stretch")

    render_quadrant_methodology()

    if incomplete_rows:
        st.subheader("Non affichees sur la matrice")
        st.caption("Seules les familles de produit avec toutes les reponses obligatoires completees sont affichees.")
        st.dataframe(
            pd.DataFrame(incomplete_rows),
            width="stretch",
            hide_index=True,
        )


def get_selected_scenario(questions: dict) -> dict:
    scenario_id = get_setting("scenario_id")
    return get_scenario_by_id(questions, scenario_id)


def render_quadrant_methodology() -> None:
    st.subheader("Lecture des quadrants")

    quadrants = [
        {
            "title": "Levier, l'actif stratégique",
            "subtitle": "Criticité haute, valeur haute",
            "body": [
                "Dans ce quadrant, l'obligation et l'opportunité coïncident : la traçabilité est exigée par la réglementation, un client ou la nature du produit, mais permet aussi de créer une famille de produits premium, résiliente, engageante pour le client ou intégrant la circularité.",
                "La recommandation est d'investir pleinement, au-delà du minimum réglementaire, et de faire de la traçabilité un argument. La dépense qui existerait de toute façon au titre de la conformité peut être convertie en avantage concurrentiel.",
                "La taille de la bulle donne l'étalement dans le temps : une petite bulle représente un quick win par lequel commencer, une très grande bulle impose de phaser l'investissement. Dans ce quadrant, le coût ne fait pas renoncer, il fait prioriser.",
            ],
        },
        {
            "title": "Obligatoire, le ticket d'entrée",
            "subtitle": "Criticité haute, valeur basse",
            "body": [
                "Dans ce quadrant, la nécessité seule justifie la mise en place de la traçabilité. Aucune création de valeur n'a été identifiée au scoring : la mise en conformité vise à éviter une sanction ou à ne pas être exclu d'un marché.",
                "La recommandation est de tracer par nécessité et de minimiser le coût total, en calant la granularité sur l'exigence réglementaire ou contractuelle, pas davantage.",
                "La taille de la bulle a une fonction d'alerte : puisque la dépense n'a pas de retour direct en face, chaque euro doit être challengé. Une grande bulle en Obligatoire signale une famille où il faut réutiliser l'existant, adopter des standards ou mutualiser.",
            ],
        },
        {
            "title": "Dormante, l'opportunité de croissance",
            "subtitle": "Criticité basse, valeur haute",
            "body": [
                "Dans ce quadrant, il n'y a pas de caractère obligatoire, mais le scoring identifie une opportunité : premium possible, clientèle sensible à la traçabilité, avantage de résilience ou modèle d'affaires émergent.",
                "La recommandation est d'explorer par pilote ciblé et de prouver la valeur avant de lancer une mise en œuvre large. Le pilote doit être cadré sur une famille ou un marché avec des objectifs précis.",
                "La taille de la bulle aide à décider du moment d'agir : une petite bulle peut justifier un pilote rapide ; une grande bulle appelle plutôt un déclencheur clair, comme une évolution réglementaire annoncée ou un signal client fort.",
            ],
        },
        {
            "title": "Accessoire, le coût évitable",
            "subtitle": "Criticité basse, valeur basse",
            "body": [
                "Dans ce quadrant, il n'y a ni devoir de traçabilité ni opportunité identifiée. L'absence de traçabilité de ces familles ne présente pas de risque significatif.",
                "La recommandation est de ne rien engager, au-delà d'une veille minimale. Savoir ne pas investir est une décision à part entière : chaque euro non dépensé ici finance un Levier ou un pilote en Dormante.",
                "Ici, la bulle ne change pas la décision : quelle que soit sa taille, on n'engage pas. Une petite bulle indique seulement que l'investissement serait faible, pas qu'il serait pertinent.",
            ],
        },
    ]

    for quadrant in quadrants:
        with st.expander(f"{quadrant['title']} ({quadrant['subtitle']})"):
            for paragraph in quadrant["body"]:
                st.write(paragraph)

    with st.expander("Rôle du coût et cas particulier RSE"):
        st.write(
            "La direction stratégique relève d'abord des deux axes, avec en majeure la valeur stratégique. "
            "Le coût règle la temporalité, le rythme et l'ordre de passage : c'est une troisième dimension, "
            "pas un troisième axe."
        )
        st.write(
            "Les familles à enjeu RSE apparaissent principalement en Obligatoire lorsque la réglementation "
            "impose déjà la traçabilité, ou en Dormante lorsqu'aucune obligation n'existe encore mais qu'une "
            "valeur potentielle est identifiée. Cela permet d'anticiper les bascules réglementaires et de "
            "transformer certaines familles en Levier."
        )


def add_matrix_quadrants(fig) -> None:
    quadrant_styles = [
        {
            "name": "Accessoire, le coût évitable",
            "x0": 0,
            "x1": 5,
            "y0": 0,
            "y1": 5,
            "fillcolor": "rgba(148, 163, 184, 0.12)",
            "label_x": 2.5,
            "label_y": 0.35,
        },
        {
            "name": "Obligatoire, le ticket d'entrée",
            "x0": 5,
            "x1": 10,
            "y0": 0,
            "y1": 5,
            "fillcolor": "rgba(239, 68, 68, 0.10)",
            "label_x": 7.5,
            "label_y": 0.35,
        },
        {
            "name": "Dormante, l'opportunité de croissance",
            "x0": 0,
            "x1": 5,
            "y0": 5,
            "y1": 10,
            "fillcolor": "rgba(245, 158, 11, 0.10)",
            "label_x": 2.5,
            "label_y": 9.65,
        },
        {
            "name": "Levier, l'actif stratégique",
            "x0": 5,
            "x1": 10,
            "y0": 5,
            "y1": 10,
            "fillcolor": "rgba(34, 197, 94, 0.10)",
            "label_x": 7.5,
            "label_y": 9.65,
        },
    ]

    shapes = [
        {
            "type": "rect",
            "xref": "x",
            "yref": "y",
            "x0": quadrant["x0"],
            "x1": quadrant["x1"],
            "y0": quadrant["y0"],
            "y1": quadrant["y1"],
            "fillcolor": quadrant["fillcolor"],
            "line": {"color": "rgba(148, 163, 184, 0.35)", "width": 1},
            "layer": "below",
        }
        for quadrant in quadrant_styles
    ]
    shapes.extend(
        [
            {
                "type": "line",
                "xref": "x",
                "yref": "y",
                "x0": 5,
                "x1": 5,
                "y0": 0,
                "y1": 10,
                "line": {"color": "rgba(148, 163, 184, 0.75)", "width": 1, "dash": "dash"},
            },
            {
                "type": "line",
                "xref": "x",
                "yref": "y",
                "x0": 0,
                "x1": 10,
                "y0": 5,
                "y1": 5,
                "line": {"color": "rgba(148, 163, 184, 0.75)", "width": 1, "dash": "dash"},
            },
        ]
    )

    annotations = [
        {
            "x": quadrant["label_x"],
            "y": quadrant["label_y"],
            "xref": "x",
            "yref": "y",
            "text": quadrant["name"],
            "showarrow": False,
            "font": {"size": 13, "color": "rgba(226, 232, 240, 0.86)"},
            "align": "center",
            "bgcolor": "rgba(15, 23, 42, 0.50)",
            "bordercolor": "rgba(148, 163, 184, 0.35)",
            "borderpad": 4,
        }
        for quadrant in quadrant_styles
    ]

    fig.update_layout(shapes=shapes, annotations=annotations)
    fig.update_xaxes(range=[0, 10], zeroline=False)
    fig.update_yaxes(range=[0, 10], zeroline=False)


def render_categories_admin_page(questions: dict) -> None:
    st.header("Administration")

    categories = get_active_categories()
    inactive_categories = get_inactive_categories()

    render_scenario_settings(questions)
    st.divider()
    render_bubble_size_legend(questions)
    st.divider()

    st.subheader("Familles de produit actives")
    if not categories:
        st.info("Aucune famille de produit active.")
    else:
        for category in categories:
            with st.expander(category["name"]):
                if category["description"]:
                    st.write(category["description"])
                answers = get_answers(category["id"])
                answered, total = total_answer_count(answers, questions)
                st.caption(f"Progression {answered} / {total} reponses")
                st.caption(f"Derniere mise a jour {category['updated_at']}")

    st.divider()
    st.subheader("Familles de produit inactives")
    if not inactive_categories:
        st.info("Aucune famille de produit inactive.")
    else:
        for category in inactive_categories:
            category_col, action_col = st.columns([0.75, 0.25])
            with category_col:
                st.write(category["name"])
                if category["description"]:
                    st.caption(category["description"])
                answers = get_answers(category["id"])
                answered, total = total_answer_count(answers, questions)
                st.caption(f"Progression {answered} / {total} reponses")
                st.caption(f"Derniere mise a jour {category['updated_at']}")
            if action_col.button(
                "Reactiver",
                key=f"reactivate_category_{category['id']}",
                width="stretch",
            ):
                reactivate_category(category["id"])
                st.session_state.selected_category_id = category["id"]
                st.session_state.page = "Assessment"
                st.rerun()

    st.divider()
    st.subheader("Zone de danger")
    st.warning("Cette action supprime definitivement toutes les familles de produit et toutes les reponses sauvegardees.")
    with st.form("delete_all_products_form"):
        confirmation = st.text_input("Ecrire DELETE pour confirmer")
        delete_submitted = st.form_submit_button("Supprimer toutes les familles de produit definitivement")

        if delete_submitted:
            if confirmation != "DELETE":
                st.warning("Ecrire DELETE exactement pour confirmer.")
            else:
                delete_all_categories()
                st.session_state.pop("selected_category_id", None)
                st.session_state.page = "Assessment"
                st.success("Toutes les familles de produit et les reponses ont ete supprimees definitivement.")
                st.rerun()


def render_scenario_settings(questions: dict) -> None:
    scenarios = get_scenarios(questions)
    selected_scenario = get_selected_scenario(questions)
    scenario_ids = [scenario["id"] for scenario in scenarios]
    selected_index = scenario_ids.index(selected_scenario["id"])

    st.subheader("Scenario")

    with st.form("project_scenario_form"):
        chosen_scenario = st.radio(
            "Scenario",
            scenarios,
            index=selected_index,
            format_func=scenario_display_text,
        )

        if st.form_submit_button("Sauvegarder le scenario"):
            save_setting("scenario_id", chosen_scenario["id"])
            st.success(f"Scenario sauvegarde : {chosen_scenario['label']}.")
            st.rerun()


def scenario_display_text(scenario: dict) -> str:
    description = scenario.get("description")
    if not description:
        return scenario["label"]
    return f"{scenario['label']} - {description}"


def render_bubble_size_legend(questions: dict) -> None:
    st.subheader("Taille de bulle")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Score cout": f"{rule['min_score']} - {rule['max_score']}",
                    "Taille de bulle": rule["label"],
                    "Lecture": rule["reading"],
                }
                for rule in get_bubble_size_rules(questions)
            ]
        ),
        width="stretch",
        hide_index=True,
    )


def render_dropdown_question(
    options: list[dict],
    saved_value: object,
    key: str,
) -> object:
    choices = [{"label": "Non renseigne", "value": None}, *options]
    values = [choice["value"] for choice in choices]
    selected_index = values.index(saved_value) if saved_value in values else 0
    selected = st.selectbox(
        "Reponse",
        choices,
        index=selected_index,
        format_func=option_display_text,
        key=key,
        label_visibility="collapsed",
    )
    return selected["value"]


def render_question_prompt(question: dict) -> None:
    required_marker = " *" if question.get("required", False) else ""
    label = html.escape(f"{question['label']}{required_marker}")
    description = question.get("description", "")

    if description:
        st.markdown(
            f"<strong>{label}</strong><br><em>{html.escape(description)}</em>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<strong>{label}</strong>", unsafe_allow_html=True)


def option_display_text(option: dict) -> str:
    return option.get("description") or option["label"]


def number_value(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


st.set_page_config(
    page_title="Matrice de tracabilite supply chain",
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
