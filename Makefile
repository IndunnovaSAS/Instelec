# TransMaint - Makefile
# Commands for development, testing, and deployment

.PHONY: help install test test-unit test-integration test-e2e coverage lint format migrate shell run clean

# Default target
help:
	@echo "TransMaint - Available commands:"
	@echo ""
	@echo "  Development:"
	@echo "    install        Install dependencies"
	@echo "    migrate        Run database migrations"
	@echo "    shell          Start Django shell"
	@echo "    run            Start development server"
	@echo ""
	@echo "  Testing:"
	@echo "    test           Run all tests"
	@echo "    test-unit      Run unit tests only"
	@echo "    test-int       Run integration tests only"
	@echo "    test-e2e       Run E2E tests only"
	@echo "    test-fast      Run tests without slow tests"
	@echo "    coverage       Run tests with coverage report"
	@echo "    coverage-html  Generate HTML coverage report"
	@echo ""
	@echo "  Code Quality:"
	@echo "    lint           Run linter (ruff)"
	@echo "    format         Format code (ruff)"
	@echo "    check          Run all quality checks"
	@echo ""
	@echo "  Cleanup:"
	@echo "    clean          Remove cache and temporary files"

# Development
install:
	pip install -e ".[dev]"
	pip install -r requirements/local.txt

migrate:
	python manage.py migrate

shell:
	python manage.py shell_plus

run:
	python manage.py runserver

# Testing
test:
	pytest

test-unit:
	pytest tests/unit -v

test-int:
	pytest tests/integration -v

test-e2e:
	pytest tests/e2e -v

test-fast:
	pytest -m "not slow" -v

test-verbose:
	pytest -v --tb=long

# Coverage
coverage:
	pytest --cov=apps --cov-report=term-missing

coverage-html:
	pytest --cov=apps --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

coverage-xml:
	pytest --cov=apps --cov-report=xml

# Code Quality
lint:
	ruff check .

lint-fix:
	ruff check --fix .

format:
	ruff format .

format-check:
	ruff format --check .

check: lint format-check
	@echo "All quality checks passed!"

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@echo "Cleanup complete!"

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database
db-reset:
	python manage.py reset_db --noinput
	python manage.py migrate
	python manage.py createsuperuser --noinput || true

db-seed:
	python manage.py loaddata fixtures/*.json

# Celery
celery-worker:
	celery -A config worker -l info

celery-beat:
	celery -A config beat -l info

celery-flower:
	celery -A config flower
