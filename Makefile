# Makefile for theobroma-geo-api
# Docker-based commands for local development

# Variables
IMAGE_NAME = theobroma-geo-api
CONTAINER_NAME = theobroma-geo-api-container
PORT = 8000
HOST_PORT = 8000

# Default target
.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Build commands
.PHONY: build
build: ## Build the Docker image
	docker build -t $(IMAGE_NAME) .

.PHONY: build-no-cache
build-no-cache: ## Build the Docker image without cache
	docker build --no-cache -t $(IMAGE_NAME) .

# Run commands
.PHONY: run
run: ## Run the service in a new container
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(HOST_PORT):$(PORT) \
		--env-file .env \
		$(IMAGE_NAME)

.PHONY: run-it
run-it: ## Run the service interactively (foreground)
	docker run -it --rm \
		--name $(CONTAINER_NAME) \
		-p $(HOST_PORT):$(PORT) \
		--env-file .env \
		$(IMAGE_NAME)

.PHONY: run-dev
run-dev: ## Run the service with volume mount for development
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(HOST_PORT):$(PORT) \
		-v $(PWD):/app \
		$(IMAGE_NAME)

# Container management
.PHONY: start
start: ## Start an existing container
	docker start $(CONTAINER_NAME)

.PHONY: stop
stop: ## Stop the running container
	docker stop $(CONTAINER_NAME)

.PHONY: restart
restart: ## Restart the container
	docker restart $(CONTAINER_NAME)

.PHONY: rm
rm: ## Remove the container
	docker rm -f $(CONTAINER_NAME)

# Utility commands
.PHONY: logs
logs: ## Show container logs
	docker logs -f $(CONTAINER_NAME)

.PHONY: shell
shell: ## Open a shell in the running container
	docker exec -it $(CONTAINER_NAME) /bin/bash

.PHONY: status
status: ## Show container status
	docker ps -a --filter name=$(CONTAINER_NAME)

.PHONY: health
health: ## Check service health
	curl -f http://localhost:$(HOST_PORT)/health || echo "Service not responding"

# Development workflow
.PHONY: dev
dev: build run logs ## Build, run, and show logs (full development cycle)

.PHONY: redeploy
redeploy: stop rm build run ## Stop, remove, rebuild, and run (complete redeploy)

# Cleanup commands
.PHONY: clean
clean: ## Remove container and image
	docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME) 2>/dev/null || true

.PHONY: clean-all
clean-all: ## Remove all unused Docker resources
	docker system prune -f

# Quick commands
.PHONY: up
up: build run ## Quick start: build and run
	@echo "Service starting at http://localhost:$(HOST_PORT)"
	@echo "Health check: http://localhost:$(HOST_PORT)/health"

.PHONY: down
down: stop rm ## Quick stop: stop and remove container
