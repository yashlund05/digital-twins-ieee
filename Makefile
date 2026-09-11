# =============================================================================
# Makefile — Digital Twin Power Grid Research Repository
# =============================================================================

.PHONY: help install install-dev validate-env test test-unit test-integration \
        test-validation test-regression format lint type-check \
        validate-dt prepare-data check-secrets clean

# Default target
help:
	@echo "Digital Twin Power Grid Research Repository"
	@echo "=========================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install package (production deps)"
	@echo "  make install-dev      Install package with dev deps"
	@echo "  make validate-env     Validate environment setup"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-validation  Run physical validation tests"
	@echo "  make test-regression  Run regression tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           Format code with black + ruff"
	@echo "  make lint             Lint code with ruff"
	@echo "  make type-check       Run mypy type checking"
	@echo ""
	@echo "Research:"
	@echo "  make validate-dt      Validate IEEE 33-bus Digital Twin"
	@echo "  make prepare-data     Run data preparation pipeline"
	@echo ""
	@echo "Safety:"
	@echo "  make check-secrets    Scan for accidentally committed secrets"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Remove generated files"

# =============================================================================
# Setup
# =============================================================================

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,notebooks]"

validate-env:
	@echo "Validating environment..."
	@python -c "import sys; assert sys.version_info >= (3, 10), f'Python 3.10+ required, got {sys.version}'"
	@python -c "import opendssdirect; print('[OK] opendssdirect')"
	@python -c "import numpy; print('[OK] numpy', numpy.__version__)"
	@python -c "import pandas; print('[OK] pandas', pandas.__version__)"
	@python -c "import sklearn; print('[OK] scikit-learn', sklearn.__version__)"
	@python -c "import xgboost; print('[OK] xgboost', xgboost.__version__)"
	@python -c "import pydantic; print('[OK] pydantic', pydantic.__version__)"
	@python -c "import yaml; print('[OK] PyYAML')"
	@python -c "import matplotlib; print('[OK] matplotlib', matplotlib.__version__)"
	@python -c "import click; print('[OK] click', click.__version__)"
	@echo "Environment validation complete."

# =============================================================================
# Testing
# =============================================================================

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short -m unit

test-integration:
	pytest tests/integration/ -v --tb=short -m integration

test-validation:
	pytest tests/validation/ -v --tb=short -m validation

test-regression:
	pytest tests/regression/ -v --tb=short -m regression

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# =============================================================================
# Code Quality
# =============================================================================

format:
	black src/ tests/
	ruff check --fix src/ tests/

lint:
	ruff check src/ tests/

type-check:
	mypy src/

# =============================================================================
# Research Commands
# =============================================================================

validate-dt:
	python -m src.cli validate-dt

prepare-data:
	python -m src.cli prepare-data

# =============================================================================
# Safety
# =============================================================================

check-secrets:
	@echo "Scanning for accidentally staged secrets..."
	@git diff --cached --name-only | xargs grep -l "password\|api_key\|secret\|token" 2>/dev/null && \
		(echo "WARNING: Potential secrets found in staged files!"; exit 1) || \
		echo "[OK] No obvious secrets found in staged files."

# =============================================================================
# Maintenance
# =============================================================================

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned generated files."
