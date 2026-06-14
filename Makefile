.PHONY: help db-up db-down migrate ingest backend frontend

help:
	@echo "Week 1 dev commands:"
	@echo "  make db-up       Start Postgres + Redis in Docker"
	@echo "  make db-down     Stop and remove containers"
	@echo "  make migrate     Apply database migrations"
	@echo "  make seed        Load fixture documents (fast, no crawling)"
	@echo "  make ingest      Crawl Citizens Information live (slow)"
	@echo "  make backend     Start the FastAPI backend (hot reload)"
	@echo "  make frontend    Start the Next.js frontend (hot reload)"

db-up:
	docker-compose up -d postgres redis
	@echo "Waiting for Postgres to be ready..."
	@until docker-compose exec postgres pg_isready -U advisor -d advisor; do sleep 1; done
	@echo "Postgres is ready."

db-down:
	docker-compose down

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && .venv/bin/python scripts/seed.py

# Live crawl — requires bot protection bypass or approved access
ingest:
	cd backend && .venv/bin/python scripts/ingest.py --max-pages 50

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev
