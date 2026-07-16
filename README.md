# Supply Chain Traceability Matrix

A local Streamlit application for assessing product categories and plotting their
criticality, strategic value, and implementation cost on a bubble matrix.

## Quick start

On Windows with `make` available:

```powershell
make setup
make run
```

Without `make`:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The application stores local data in `data/app.db`. Back up this file to preserve
assessments. It is intentionally excluded from Git.

See [the user guide](docs/user-guide.md) for operating instructions and
[the technical guide](docs/technical-guide.md) for architecture, configuration,
testing, and maintenance.

## Licence

The methodology, question framework, scoring model, scenario logic, and related
assessment content require prior written permission before reuse.

Any approved reuse must cite Gaelle Sannia as the source of the methodology.
See [LICENSE](LICENSE) for details.
