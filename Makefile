COMPOSE_FILE = srcs/docker-compose.yml
COMPOSE = docker compose -f $(COMPOSE_FILE)

DATA_DIRS = srcs/data/postgres srcs/data/postgres_mlflow srcs/data/minio srcs/data/artifacts srcs/data/grafana_data srcs/data/prometheus srcs/logs

.PHONY: build up down downv logs stop start clean fclean dirs

build: dirs
	sudo chmod 777 -R ./*
	sudo chown -R $$(whoami):$$(whoami) .venv 2>/dev/null || true
	@bash srcs/scripts/dependencies/dependencies_py.sh
	$(COMPOSE) build
	$(COMPOSE) up -d --remove-orphans
	@bash srcs/scripts/logs/log-finder.sh

up: dirs
	$(COMPOSE) up -d --remove-orphans

down:
	@bash srcs/scripts/logs/kill-finder.sh
	$(COMPOSE) down

downv:
	@bash srcs/scripts/logs/kill-finder.sh
	$(COMPOSE) down -v

stop: down


start: down up


logs:
	$(COMPOSE) logs -f


logs-svc:
	$(COMPOSE) logs -f $(SVC)

dirs:
	@mkdir -p $(DATA_DIRS)

clean:
	@echo "Stopping services and removing containers..."

	@bash srcs/scripts/logs/kill-finder.sh 2>/dev/null || true

	$(COMPOSE) down --remove-orphans

	@echo "clean: Containers, .venv, and data directories wiped."

fclean:
	@echo "Performing factory reset..."

	@bash srcs/scripts/logs/kill-finder.sh 2>/dev/null || true

	# Remove volumes and all images associated with this project
	$(COMPOSE) down -v --rmi all --remove-orphans

	# Remove physical data directories created by 'dirs'
	sudo rm -rf $(DATA_DIRS)

	# Remove the Python virtual environment and lock files
	sudo rm -rf .venv

	# Optional: Clean up dangling docker build cache
	docker builder prune -f
	@echo "fclean: Containers, volumes, images, .venv, and data directories wiped."

re: fclean build
