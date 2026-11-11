.PHONY: setup up down dev-api dev-web worker migrate seed check test acceptance e2e fixtures
setup:
	python3.12 -m venv .venv
	.venv/bin/pip install -e './backend[dev]'
	npm --prefix frontend ci
up:
	docker compose up --build -d

down:
	docker compose down
migrate:
	cd backend && ../.venv/bin/alembic upgrade head
seed:
	.venv/bin/python -m app.seed
dev-api:
	.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
worker:
	.venv/bin/python -m app.workers.runner
dev-web:
	npm --prefix frontend run dev -- --port 5173
check:
	.venv/bin/ruff check backend scripts
	.venv/bin/ruff format --check backend scripts
	.venv/bin/mypy backend/app
	npm --prefix frontend run format:check
	npm --prefix frontend run build
test:
	cd backend && ../.venv/bin/pytest -q --cov=app --cov-report=term-missing
acceptance:
	.venv/bin/python scripts/acceptance.py
e2e:
	cd frontend && npm run test:e2e
fixtures:
	.venv/bin/python scripts/generate_fixtures.py
	cp fixtures/atlaspm/snapshot.csv frontend/public/fixtures/atlaspm/snapshot.csv
	cp fixtures/meridianrent/events.json frontend/public/fixtures/meridianrent/events.json
