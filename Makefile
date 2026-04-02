COMPOSE_FILE = srcs/docker-compose.yml
COMPOSE = docker compose -f $(COMPOSE_FILE)

ifneq (,$(wildcard srcs/.env))
include srcs/.env
export
endif

DATA_DIRS = srcs/data/postgres srcs/data/postgres_mlflow srcs/data/minio srcs/data/artifacts srcs/logs

.PHONY: build up down downv logs stop start clean fclean dirs fix-perms


build: dirs
	if [ "$(NODE_ENV)" = "PROD" ]; then \
		$(MAKE) dependencies-py; \
		$(COMPOSE) build; \
		$(COMPOSE) up -d --remove-orphans; \
		$(MAKE) logs-finder; \
	else \
		$(MAKE) dependencies-py; \
		$(COMPOSE) build; \
		$(COMPOSE) --profile dev up -d --remove-orphans; \
		$(MAKE) logs-finder; \
	fi

# fix-perms:
# 	@sudo chown -R $$(id -u):$$(id -g) .venv srcs/data srcs/model srcs/logs 2>/dev/null || true


re: clean build

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


clean: down
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



fclean: clean
	$(MAKE) fix-perms
	@rm -rf $(DATA_DIRS)
	@echo "fclean: conteneurs, volumes et données supprimés."
