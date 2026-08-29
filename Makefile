.PHONY: setup install test lint format typecheck security seed demo api dashboard validate clean

PYTHON ?= python
PIP ?= $(PYTHON) -m pip

setup: install seed
	@echo "Setup complete. Default provider is mock."

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy app

security:
	$(PYTHON) -m bandit -r app -q
	$(PYTHON) -m pip_audit

seed:
	@mkdir -p data
	$(PYTHON) scripts/seed_data.py

demo:
	$(PYTHON) scripts/demo.py

api:
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	$(PYTHON) -m streamlit run dashboard/app.py --server.port 8501

validate:
	$(PYTHON) scripts/validate_repo.py

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
