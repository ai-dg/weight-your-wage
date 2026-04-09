COMPOSE_FILE = srcs/docker-compose.yml
COMPOSE_GPU_FILE = srcs/docker-compose.gpu.yml
# Sans USE_GPU=1 : fastapi démarre sans réservation GPU (pas de toolkit requis).
# USE_GPU=1 : activer après https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
COMPOSE = docker compose -f $(COMPOSE_FILE) $(if $(filter 1,$(USE_GPU)),-f $(COMPOSE_GPU_FILE),)

ifneq (,$(wildcard srcs/.env))
include srcs/.env
export
endif

DATA_DIRS = .venv srcs/.venv srcs/data/postgres srcs/data/postgres_mlflow srcs/data/minio srcs/data/artifacts srcs/data/grafana_data srcs/data/prometheus srcs/logs

.PHONY: build up down downv logs stop start clean fclean dirs fix-perms

build: dirs
	if [ "$(NODE_ENV)" = "PROD" ]; then \
		$(MAKE) dependencies-py; \
		$(COMPOSE) build; \
		$(COMPOSE) up -d --remove-orphans; \
		$(MAKE) logs-finder; \
		sudo chmod -R 777 ./*; \
	else \
		$(MAKE) dependencies-py; \
		$(COMPOSE) build; \
		$(COMPOSE) --profile dev up -d --remove-orphans; \
		$(MAKE) logs-finder; \
		sudo chmod -R 777 ./*; \
	fi

up: dirs
	if [ "$(NODE_ENV)" = "PROD" ]; then \
		$(COMPOSE) up -d --remove-orphans; \
	else \
		$(COMPOSE) --profile dev up -d --remove-orphans; \
	fi

down:
	if [ "$(NODE_ENV)" = "PROD" ]; then \
		$(COMPOSE) down; \
	else \
		$(COMPOSE) --profile dev down; \
	fi

downv:
	$(MAKE) logs-kill-finder
	if [ "$(NODE_ENV)" = "PROD" ]; then \
		$(COMPOSE) down -v; \
	else \
		$(COMPOSE) --profile dev down -v; \
	fi

stop: down


start: down up


logs:
	$(COMPOSE) logs -f


logs-svc:
	$(COMPOSE) logs -f $(SVC)

dirs:
	@mkdir -p $(DATA_DIRS)

fix-perms:
	@sudo chown -R $$(id -u):$$(id -g) .venv srcs/.venv srcs/data srcs/model srcs/logs 2>/dev/null || true
	@sudo chmod -R u+rwX srcs/model 2>/dev/null || true

clean: down
	@echo "Stopping services and removing containers..."
	if [ "$(NODE_ENV)" = "PROD" ]; then \
		$(COMPOSE) down -v; \
	else \
		$(COMPOSE) --profile dev down -v; \
	fi

logs-finder:
	@bash srcs/scripts/logs/log-finder.sh

logs-kill-finder:
	@bash srcs/scripts/logs/kill-finder.sh


dependencies-py:
	@bash srcs/scripts/dependencies/dependencies_py.sh
	@bash srcs/scripts/logs/kill-finder.sh 2>/dev/null || true

fclean: clean
	@echo "Performing factory reset..."
	$(MAKE) fix-perms
	@rm -rf $(DATA_DIRS)
	@echo "fclean: conteneurs, volumes et données supprimés."
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
