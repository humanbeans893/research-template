.PHONY: up up-gpu test lint down tex

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
	cd draft && lualatex -interaction=nonstopmode main.tex
