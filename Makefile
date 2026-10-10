.PHONY: lock build up up-gpu test lint down tex tex-review

# Update uv.lock with uv in a throwaway container, without the project image
# or a host Python environment. Needed after renaming the project in
# pyproject.toml, before the first build (the build installs uv.lock frozen).
lock:
	docker run --rm -u "$$(id -u):$$(id -g)" -e UV_CACHE_DIR=/tmp/uv-cache \
		-v "$(CURDIR)":/work -w /work ghcr.io/astral-sh/uv:python3.11-bookworm uv lock

build:
	docker compose build

up:
	docker compose up -d

up-gpu:
	docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

test:
	docker compose exec research-template uv run pytest

lint:
	docker compose exec research-template uv run ruff check .

down:
	docker compose down --remove-orphans

tex:
	bash draft/compile.sh

tex-review:
	bash draft/compile.sh --review
