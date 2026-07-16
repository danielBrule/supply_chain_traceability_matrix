.PHONY: setup venv install py_compile test run init-db activate clean

VENV := .venv
PYTHON := py
VENV_PYTHON := $(VENV)/Scripts/python.exe

setup: install

venv:
	if not exist "$(VENV_PYTHON)" $(PYTHON) -m venv "$(VENV)"

install: venv
	"$(VENV_PYTHON)" -m pip install --upgrade pip
	"$(VENV_PYTHON)" -m pip install -r requirements.txt

py_compile: venv
	"$(VENV_PYTHON)" -m compileall -q app.py src tests

test: py_compile
	"$(VENV_PYTHON)" -m unittest discover -s tests -v

run: py_compile
	"$(VENV_PYTHON)" -m streamlit run app.py

init-db: venv
	"$(VENV_PYTHON)" -c "from src.db import init_db; init_db(); print('Database initialized at data/app.db')"

activate: venv
	@echo PowerShell may block Activate.ps1 by default.
	@echo Run these commands in PowerShell to allow activation for this session only:
	@echo Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
	@echo .\.venv\Scripts\Activate.ps1
	@echo Or skip activation and run Python directly with:
	@echo .\.venv\Scripts\python.exe

clean:
	$(PYTHON) -c "import pathlib, shutil; shutil.rmtree(pathlib.Path('$(VENV)'), ignore_errors=True)"
