#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = rag
PYTHON_VERSION = 3.12
PYTHON_INTERPRETER = uv run python

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python dependencies
.PHONY: requirements
requirements:
	uv sync

## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using ruff (use `make format` to do formatting)
.PHONY: lint
lint:
	ruff format --check
	ruff check

## Format source code with ruff
.PHONY: format
format:
	ruff check --fix
	ruff format

## Run all tests
.PHONY: test
test:
	$(PYTHON_INTERPRETER) -m pytest tests

## Run unit and API tests only (fast, no external dependencies)
.PHONY: test-fast
test-fast:
	$(PYTHON_INTERPRETER) -m pytest tests/unit/ tests/api/ -v

## Run ALL tests (incl. integration/ragas_ci) with .env loaded into the test process — needs MISTRAL_API_KEY
.PHONY: test-env
test-env:
	@set -a && . ./.env && set +a && $(PYTHON_INTERPRETER) -m pytest tests -v

## Build the Faiss index (fetch + clean + chunk + embed), without starting the API
.PHONY: build-index
build-index:
	$(PYTHON_INTERPRETER) scripts/build_index.py

## Set up Python interpreter environment
.PHONY: create_environment
create_environment:
	uv venv --python $(PYTHON_VERSION)
	@echo ">>> New uv virtual environment created. Activate with:"
	@echo ">>> Windows: .\\\\.venv\\\\Scripts\\\\activate"
	@echo ">>> Unix/macOS: source ./.venv/bin/activate"




#################################################################################
# PROJECT RULES                                                                 #
#################################################################################



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
