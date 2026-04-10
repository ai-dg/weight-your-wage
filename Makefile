COMPOSE_FILES = srcs/docker-compose.yml
COMPOSE_GPU_FILE = srcs/docker-compose.gpu.yml

ifneq (,$(wildcard srcs/.env))
include srcs/.env
export
endif

DATA_DIRS = .venv srcs/data/postgres srcs/data/postgres_mlflow srcs/data/minio srcs/data/artifacts srcs/data/grafana_data srcs/data/prometheus srcs/logs

.PHONY: build up down downv logs stop start clean fclean dirs fix-perms


# --- GPU Auto-Detection
HAS_GPU := $(shell nvidia-smi > /dev/null 2>&1 && echo "yes" || echo "no")

ifeq ($(HAS_GPU),yes)
COMPOSE_FILES += -f COMPOSE_GPU_FILE
$(info GPU mode: Enabled)
else
$(info GPU mode: Disabled (CPU only))
endif

# --- Environment profile
PROFILES :=
ifneq ($(NODE_ENV),PROD)
PROFILES += --profile dev
endif

COMPOSE = docker compose -f $(COMPOSE_FILES) $(PROFILES)

build: dirs
	$(MAKE) dependencies-py
	$(COMPOSE) $(PROFILES) build
	$(COMPOSE) $(PROFILES) up -d --remove-orphans
	$(MAKE) logs-finder
	sudo chmod -R 777 ./*

up: dirs
	$(COMPOSE) $(PROFILES) up -d --remove-orphans
	
down:
	$(COMPOSE) $(PROFILES) down

downv:
	$(MAKE) logs-kill-finder
	$(COMPOSE) $(PROFILES) down -v

stop: down


start: down up


logs:
	$(COMPOSE) $(PROFILES) logs -f


logs-svc:
	$(COMPOSE) $(PROFILES) logs -f $(SVC)

dirs:
	@mkdir -p $(DATA_DIRS)

fix-perms:
	@sudo chown -R $$(id -u):$$(id -g) .venv srcs/.venv srcs/data srcs/model srcs/logs 2>/dev/null || true
	@sudo chmod -R u+rwX srcs/model 2>/dev/null || true

clean: down
	@echo "Stopping services and removing containers..."
	$(COMPOSE) $(PROFILES) down -v

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
	$(COMPOSE) $(PROFILES) down -v --rmi all --remove-orphans

	# Remove physical data directories created by 'dirs'
	sudo rm -rf $(DATA_DIRS)

	# Remove the Python virtual environment and lock files
	sudo rm -rf .venv

	# Optional: Clean up dangling docker build cache
	docker builder prune -f
	@echo "fclean: Containers, volumes, images, .venv, and data directories wiped."

re: fclean build
