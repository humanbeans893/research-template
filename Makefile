SERVICE := research-template
# The uv image the Dockerfile builds on, so `make lock` resolves with the same Python.
UV_IMAGE := $(shell sed -n 's/^FROM //p' Dockerfile | head -n 1)

.DEFAULT_GOAL := help
.PHONY: help ensure-up lock build up down shell test lint check experiment numbers paper tex tex-review

help: ## List the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-11s %s\n", $$1, $$2}'

ensure-up:
	@docker compose ps --status running --services | grep -qx $(SERVICE) || docker compose up -d

lock: ## Update uv.lock in a throwaway uv container (no host Python)
	docker run --rm -u "$$(id -u):$$(id -g)" -e UV_CACHE_DIR=/tmp/uv-cache \
		-v "$(CURDIR)":/work -w /work $(UV_IMAGE) uv lock

build: ## Rebuild the image after pyproject.toml or uv.lock changes
	docker compose build

up: ## Start the container (GPU: COMPOSE_FILE in .env)
	docker compose up -d

down: ## Stop and remove the container
	docker compose down --remove-orphans

shell: ensure-up ## Open a shell in the container
	docker compose exec $(SERVICE) bash

test: ensure-up ## pytest in the container; options with ARGS="-k name"
	docker compose exec $(SERVICE) uv run pytest $(ARGS)

lint: ensure-up ## ruff check in the container
	docker compose exec $(SERVICE) uv run ruff check .

check: lint test ## Run before every commit: ruff and pytest

experiment: ensure-up ## New experiment: make experiment SLUG=<slug>
	@test -n "$(SLUG)" || { echo "usage: make experiment SLUG=<slug>"; exit 1; }
	docker compose exec $(SERVICE) uv run python scripts/new_experiment.py "$(SLUG)"

numbers: ensure-up ## Write draft/tables/numbers.tex from result/tables/*.csv
	docker compose exec $(SERVICE) uv run python scripts/make_numbers.py

paper: numbers tex ## Numbers, then the PDFs

tex: ## Build draft/main.pdf and draft/supplementary.pdf with host lualatex
	bash draft/compile.sh

tex-review: ## Build the line-numbered draft/main_review.pdf
	bash draft/compile.sh --review
