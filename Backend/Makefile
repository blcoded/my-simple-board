.DEFAULT_GOAL := dev

.PHONY: help dev run test sync clean

PORT ?= 8000
HOST ?= 0.0.0.0

help:
	@echo "Mini Kanban Backend Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make         Run backend development server with auto-reload (port $(PORT))"
	@echo "  make dev     Run backend development server with auto-reload (port $(PORT))"
	@echo "  make run     Run backend server without auto-reload"
	@echo "  make test    Run full pytest test suite"
	@echo "  make sync    Install and synchronize dependencies using uv"
	@echo "  make clean   Remove cache files and temporary artifacts"
	@echo "  make help    Display this help message"
	@echo ""

dev:
	uv run uvicorn backend.main:app --reload --host $(HOST) --port $(PORT)

run:
	uv run uvicorn backend.main:app --host $(HOST) --port $(PORT)

test:
	uv run pytest

sync:
	uv sync

clean:
	uv run python -c "import shutil, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + glob.glob('**/.pytest_cache', recursive=True)]"
