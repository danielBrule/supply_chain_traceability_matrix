.PHONY: setup venv install clean

VENV := .venv
PYTHON := python
VENV_PYTHON := $(VENV)/Scripts/python.exe

setup: install

venv:
	$(PYTHON) -c "import pathlib, subprocess, sys; venv = pathlib.Path('$(VENV)'); subprocess.check_call([sys.executable, '-m', 'venv', str(venv)]) if not venv.exists() else None"

install: venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt

clean:
	$(PYTHON) -c "import pathlib, shutil; shutil.rmtree(pathlib.Path('$(VENV)'), ignore_errors=True)"
