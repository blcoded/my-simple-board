.DEFAULT_GOAL := start

.PHONY: help start dev run test sync clean frontend backend dev-backend dev-frontend

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

run:
	cd Backend && uv run uvicorn backend.main:app --host $(HOST) --port $(PORT)

test:
	cd Backend && uv run pytest

sync:
	cd Backend && uv sync
	cd Frontend && npm install

clean:
	cd Backend && uv run python -c "import shutil, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + glob.glob('**/.pytest_cache', recursive=True)]"

help:
	@echo "Mini Kanban Board - Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make            Start both backend and frontend development servers"
	@echo "  make start      Start both backend and frontend development servers"
	@echo "  make dev        Start both backend and frontend development servers"
	@echo "  make backend    Run backend development server with auto-reload (port $(PORT))"
	@echo "  make frontend   Run frontend development server (Vite)"
	@echo "  make run        Run backend server without auto-reload"
	@echo "  make test       Run full pytest test suite"
	@echo "  make sync       Install and synchronize dependencies using uv and npm"
	@echo "  make clean      Remove cache files and temporary artifacts"
	@echo "  make help       Display this help message"
	@echo ""

