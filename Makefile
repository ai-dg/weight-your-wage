COMPOSE_FILE = srcs/docker-compose.yml
COMPOSE = docker compose -f $(COMPOSE_FILE)

ifneq (,$(wildcard srcs/.env))
include srcs/.env
export
endif

DATA_DIRS = .venv srcs/data/postgres srcs/data/postgres_mlflow srcs/data/minio srcs/data/artifacts srcs/data/grafana_data srcs/data/prometheus srcs/logs

.PHONY: build up down downv logs stop start clean fclean dirs fix-perms


# --- GPU Auto-Detection
HAS_GPU := $(shell nvidia-smi > /dev/null 2>&1 && echo "yes" || echo "no")

PROFILES_CMD :=

ifeq ($(HAS_GPU),yes)
PROFILES_CMD += --profile gpu
$(info NVIDIA GPU detected! Activating GPU profile...)
else
PROFILES_CMD += --profile cpu
$(info No NVIDIA GPU found. Activating CPU profile...)
endif

ifneq ($(NODE_ENV),PROD)
PROFILES_CMD += --profile dev
endif

build: dirs
	$(MAKE) dependencies-py
	$(COMPOSE) $(PROFILES_CMD) build
	$(COMPOSE) $(PROFILES_CMD) up -d --remove-orphans
	$(MAKE) logs-finder
	sudo chmod -R 777 ./*

up: dirs
	$(COMPOSE) $(PROFILES_CMD) up -d --remove-orphans
	
down:
	$(COMPOSE) $(PROFILES_CMD) down

downv:
	$(MAKE) logs-kill-finder
	$(COMPOSE) $(PROFILES_CMD) down -v

stop: down


start: down up


logs:
	$(COMPOSE) $(PROFILES_CMD) logs -f


logs-svc:
	$(COMPOSE) $(PROFILES_CMD) logs -f $(SVC)

dirs:
	@mkdir -p $(DATA_DIRS)

fix-perms:
	@sudo chown -R $$(id -u):$$(id -g) .venv srcs/.venv srcs/data srcs/model srcs/logs 2>/dev/null || true
	@sudo chmod -R u+rwX srcs/model 2>/dev/null || true

clean: down
	@echo "Stopping services and removing containers..."
	$(COMPOSE) $(PROFILES_CMD) down -v

logs-finder:
	@bash srcs/scripts/logs/log-finder.sh $(HAS_GPU)

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
	$(COMPOSE) $(PROFILES_CMD) down -v --rmi all --remove-orphans

	# Remove physical data directories created by 'dirs'
	sudo rm -rf $(DATA_DIRS)

	# Remove the Python virtual environment and lock files
	sudo rm -rf .venv

	# Optional: Clean up dangling docker build cache
	docker builder prune -f
	@echo "fclean: Containers, volumes, images, .venv, and data directories wiped."

re: fclean build
