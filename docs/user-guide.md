# User guide

## Purpose

The application helps compare product categories using three dimensions:

- criticality on the horizontal axis;
- strategic value on the vertical axis;
- expected implementation cost represented by bubble size.

## Start the application

Run `make run`, or run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit displays the local address to open in a browser.

## Assess a product category

1. Select **+ Ajouter une famille** in the sidebar.
2. Enter a name and optional description.
3. Complete the questions in each assessment tab.
4. Select **Sauvegarder**.

The sidebar indicates whether each category is not started, partial, or complete.
Only categories with every required answer appear on the matrix.

## Read the matrix

Open **Matrice** in the sidebar. Position is determined by criticality and strategic
value. Bubble size represents the implementation-cost band. Expand the guidance
below the chart for the recommended interpretation of each quadrant.

## Choose a scenario

Open **Administration**, select the appropriate strategic scenario, and save it.
The selected scenario changes the relative weighting of criticality and value
questions for every category. It does not change the cost score.

## Manage categories

From an assessment, a category can be renamed, described, or deactivated.
Administration lists active and inactive categories and permits reactivation.
The danger zone permanently deletes all categories and their answers after an
explicit `DELETE` confirmation.

## Data and backup

All application data is stored locally in `data/app.db`. Close the application and
copy that file to create a backup. Restoring the file restores categories, answers,
and the selected scenario. CSV and Excel export are not part of the current scope.
