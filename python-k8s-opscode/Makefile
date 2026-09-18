.PHONY: help install install-dev test lint format clean docker-up docker-down docker-build k8s-apply k8s-delete migrate-up migrate-down

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linting (ruff)"
	@echo "  make format        - Format code (black)"
	@echo "  make typecheck     - Run type checking (mypy)"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make docker-up     - Start Docker Compose services"
	@echo "  make docker-down   - Stop Docker Compose services"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make k8s-apply     - Apply Kubernetes manifests"
	@echo "  make k8s-delete   - Delete Kubernetes resources"
	@echo "  make migrate-up    - Run database migrations"
	@echo "  make migrate-down  - Rollback database migrations"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install ruff black mypy pytest pytest-asyncio pytest-cov pytest-mock

# Testing
test:
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Code quality
lint:
	ruff check app/
	ruff check tests/

format:
	black app/ tests/

typecheck:
	mypy app/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker build -t python-k8s-opscode:latest .

docker-rebuild:
	docker-compose down
	docker build -t python-k8s-opscode:latest .
	docker-compose up -d

# Kubernetes
k8s-apply:
	kubectl apply -f kubernetes/namespace.yaml
	kubectl apply -f kubernetes/serviceaccount.yaml
	kubectl apply -f kubernetes/rbac.yaml
	kubectl apply -f kubernetes/configmap.yaml
	kubectl apply -f kubernetes/secret.yaml
	kubectl apply -f kubernetes/deployment.yaml
	kubectl apply -f kubernetes/service.yaml

k8s-delete:
	kubectl delete -f kubernetes/service.yaml
	kubectl delete -f kubernetes/deployment.yaml
	kubectl delete -f kubernetes/secret.yaml
	kubectl delete -f kubernetes/configmap.yaml
	kubectl delete -f kubernetes/rbac.yaml
	kubectl delete -f kubernetes/serviceaccount.yaml
	kubectl delete -f kubernetes/namespace.yaml

k8s-logs:
	kubectl logs -n opscode -l app=opscode --tail=100 -f

# Database migrations
migrate-up:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-create:
	alembic revision --autogenerate -m "$(message)"

# Development
run:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-prod:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Helm
helm-install:
	helm install opscode ./helm/opscode

helm-upgrade:
	helm upgrade opscode ./helm/opscode

helm-uninstall:
	helm uninstall opscode

# Demo
demo-up:
	kubectl apply -f k8s-demo/demo-app.yaml

demo-down:
	kubectl delete -f k8s-demo/demo-app.yaml

demo-crash:
	kubectl delete pod -l app=demo-app -n default

demo-scale:
	kubectl scale deployment demo-app --replicas=1 -n default
