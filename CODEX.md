# Supply Chain Traceability Matrix

## Product Context

This is a local product-category assessment tool for progressively answering questions and visualizing the results as a bubble chart.

The user has 10 to 20 product categories, and categories can be added or removed over time. Each category has two groups of questions. Questions may be dropdown/categorical or numeric. Answers do not need to be completed in one sitting, so progress must be saved locally and clearly shown.

Core mental model:

```text
Product category -> answers -> calculated X/Y/Size values -> bubble chart
```

## Preferred Stack

- Python
- Streamlit
- SQLite for local persistence
- Plotly for charts

Keep the app local-first and simple to run.

## UX Direction

Use a two-column layout:

- Left sidebar: product categories, completion status, add/remove category controls, chart navigation.
- Main pane: selected category questionnaire with two tabs, one per question group.

Category completion should be visible in the sidebar:

- Complete: green/tick-style status
- Partial: amber status
- Not started: neutral/grey status
- Also show answered count, for example `12 / 20 answered`

Use color mainly for status. Keep the question forms calm, readable, and work-focused.

Expected controls:

- Clear save behavior or auto-save
- Last updated timestamp per category
- Validation warnings for missing required answers
- Export to CSV or Excel
- A small admin/config area for categories and questions
- A way to show the bubble chart from the sidebar

## Data Model Guidance

Questions are defined in a YAML configuration file. SQLite stores product categories and answers only.

SQLite tables:

```text
categories
- id
- name
- description
- is_active
- created_at
- updated_at

answers
- id
- category_id
- question_id
- value
- updated_at
```

Question IDs in YAML must be stable because `answers.question_id` references them. If a question label changes, keep the same ID. If a question is replaced with a different meaning, create a new ID.

Questions YAML shape:

```yaml
sections:
  - id: supply_risk
    label: Supply Risk
    questions:
      - id: supplier_concentration
        label: Supplier concentration
        type: dropdown
        options:
          - label: Low
            value: 1
          - label: Medium
            value: 3
          - label: High
            value: 5
        required: true
        contributes_to:
          x: 0.4
          y: 0.0
          size: 0.2

      - id: annual_spend
        label: Annual spend
        type: number
        required: true
        contributes_to:
          x: 0.0
          y: 0.0
          size: 0.8
```

Supported question metadata:

- `id`: stable machine-readable ID
- `label`: display text
- `type`: `dropdown` or `number`
- `options`: required for dropdown questions
- `required`: whether the answer counts toward completion
- `contributes_to`: weights for the chart calculations: `x`, `y`, and `size`

## Chart Guidance

The bubble chart should use one bubble per product category.

- X axis: calculated score from answers
- Y axis: calculated score from answers
- Bubble size: calculated value from answers

The exact scoring formulas should be kept in a small, testable layer rather than embedded directly inside Streamlit UI code.

## Implementation Preferences

- Keep Streamlit UI code separate from persistence and scoring logic where practical.
- Prefer small modules over one large file once the app grows beyond a prototype.
- Keep local data files such as `data/app.db` out of git.
- Avoid adding heavy frameworks unless the app clearly needs them.
