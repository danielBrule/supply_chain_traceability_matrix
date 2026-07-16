# Technical guide

## Architecture

The application uses Python, Streamlit, SQLite, Plotly, pandas, and PyYAML.

```text
app.py                    Streamlit entrypoint, navigation, matrix and admin UI
src/assessment_page.py    Assessment form and category actions
src/ui_common.py          Shared form and completion presentation helpers
src/db.py                 SQLite persistence
src/scoring.py            Configuration loading, completion, and scoring
config/questions.yaml     Questions, scenarios, weights, and bubble-size bands
data/app.db               Local runtime data (not tracked)
tests/                    Standard-library unit tests
```

UI modules may call persistence and scoring functions, while persistence and scoring
must remain independent of Streamlit. Scoring rules should not be added directly to
page-rendering code.

## Persistence

`init_db()` creates the database on startup. Categories are soft-deleted through
`is_active`; the administration danger zone performs permanent deletion. Answers
are stored as JSON text and uniquely keyed by category and question. Saving an
answer also updates the owning category's `updated_at` timestamp.

Set `SCTM_DB_PATH` before importing `src.db` to use a different database path.

## Question configuration

Question IDs are persistence keys and must remain stable. Changing a label is safe;
changing a question's meaning requires a new ID. Dropdown option values and numeric
answers must be convertible to numbers for scoring.

Each `contributes_to` entry supplies base weights for `x`, `y`, and `size`.
Scenarios can multiply the `x` and `y` contribution of individual questions. Cost
(`size`) is deliberately scenario-independent.

## Local validation

```powershell
make py_compile
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use temporary SQLite databases and never modify `data/app.db`.

## Continuous integration

`.github/workflows/ci.yml` runs compilation and unit tests on pushes and pull
requests using Python 3.12. Keep local validation commands and CI commands aligned.

## Current scope

The app is local-first and single-user. Authentication, concurrent editing, hosted
deployment, and CSV/Excel export are intentionally outside the current scope.
