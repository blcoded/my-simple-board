.DEFAULT_GOAL := start

.PHONY: help start dev run test test-integration test-e2e sync clean frontend backend dev-backend dev-frontend build serve docker-build docker-run

PORT ?= 8000
HOST ?= 0.0.0.0

start:
	@$(MAKE) -j 2 backend frontend

dev:
	@$(MAKE) -j 2 backend frontend

backend:
	cd Backend && uv run uvicorn backend.main:app --reload --host $(HOST) --port $(PORT)

dev-backend: backend

frontend:
	cd Frontend && npm run dev

dev-frontend: frontend

build:
	cd Frontend && npm run build

serve: build
	cd Backend && uv run uvicorn backend.main:app --host $(HOST) --port $(PORT)

run:
	cd Backend && uv run uvicorn backend.main:app --host $(HOST) --port $(PORT)

test:
	cd Backend && uv run pytest

test-integration:
	uv run --directory Backend pytest ../tests/integration -v

test-e2e:
	NODE_PATH=Frontend/node_modules node Frontend/node_modules/@playwright/test/cli.js test --config=playwright.config.ts

sync:
	cd Backend && uv sync
	cd Frontend && npm install

clean:
	cd Backend && uv run python -c "import shutil, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + glob.glob('**/.pytest_cache', recursive=True)]"

docker-build:
	docker build -t mini-kanban:latest .

docker-run:
	docker run -p $(PORT):8000 mini-kanban:latest

help:
	@echo "Mini Kanban Board - Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make                  Start backend (serving frontend) and frontend dev servers"
	@echo "  make serve            Build frontend and run backend to serve both API & frontend"
	@echo "  make build            Build frontend production assets"
	@echo "  make backend          Run backend server with auto-reload (port $(PORT))"
	@echo "  make frontend         Run frontend development server (Vite)"
	@echo "  make run              Run backend server directly without auto-reload"
	@echo "  make test             Run full unit pytest test suite"
	@echo "  make test-integration Run integration tests against docker-compose stack"
	@echo "  make test-e2e         Run Playwright E2E browser tests against docker-compose stack"
	@echo "  make sync             Install and synchronize dependencies using uv and npm"
	@echo "  make clean            Remove cache files and temporary artifacts"
	@echo "  make docker-build     Build the multi-stage Docker image"
	@echo "  make docker-run       Run the containerized application on port $(PORT)"
	@echo "  make help             Display this help message"
	@echo ""

