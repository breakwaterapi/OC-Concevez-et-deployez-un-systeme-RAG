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

## Build Docker images
.PHONY: docker-build
docker-build:
	docker compose build

## Start services in background (API on :8001, UI on :8502)
.PHONY: docker-up
docker-up:
	docker compose up -d

## Stop and remove containers
.PHONY: docker-down
docker-down:
	docker compose down

## Full startup: build images, seed the index if missing (progress bar shown live via a one-off
## container running scripts/build_index.py — same code path as /rebuild, but not through the
## API/HTTP), then start API + UI. The "one command" demo entry point. Only needs Docker on the
## host, not uv/Python. Because seeding runs and completes before `api` starts, the freshly built
## index (written to the shared ./models bind mount) is guaranteed to be picked up at API startup.
.PHONY: up
up:
	docker compose build
	@if [ ! -f models/faiss_index/index.faiss ]; then \
		echo "No index found — building it now via a one-off container (real OpenAgenda + Mistral API calls, may take a few minutes, progress bar below)..."; \
		docker compose run --rm api uv run python scripts/build_index.py; \
	else \
		echo "Index already present at models/faiss_index/ — skipping seed."; \
	fi
	docker compose up -d --wait

## Force a rebuild against the already-running API (e.g. to refresh with new OpenAgenda events) —
## distinct from initial seeding done by `make up`; the UI's "Reconstruire l'index" button does
## the same thing over HTTP.
.PHONY: rebuild
rebuild:
	@set -a && . ./.env && set +a && \
	curl -sf -X POST http://localhost:8001/rebuild -H "X-API-Key: $$REBUILD_API_KEY" && echo

## Full shutdown: stop and remove all containers
.PHONY: down
down:
	docker compose down

## Print .env as export statements — a bare `make env` can't touch your shell, run: eval "$(make env)"
.PHONY: env
env:
	@grep -v '^#' .env | grep -v '^$$' | sed 's/^/export /'

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
