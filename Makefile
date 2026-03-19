COMPOSE_FILE = srcs/docker-compose.yml
COMPOSE = docker compose -f $(COMPOSE_FILE)

DATA_DIRS = srcs/data/postgres srcs/data/postgres_mlflow srcs/data/minio srcs/data/artifacts srcs/logs

.PHONY: build up down downv logs stop start clean fclean dirs

build: dirs
	sudo chmod 777 -R ./*
	sudo chown -R $$(whoami):$$(whoami) .venv 2>/dev/null || true
	@bash srcs/scripts/dependencies/dependencies_py.sh
	$(COMPOSE) build
	$(COMPOSE) up -d --remove-orphans
	@bash srcs/scripts/logs/log-finder.sh

re: fclean
	$(MAKE) dirs
	$(COMPOSE) build
	$(COMPOSE) up -d --remove-orphans
	@bash srcs/scripts/logs/log-finder.sh
	@bash srcs/scripts/dependencies/dependencies_py.sh

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


clean: down
	$(COMPOSE) down -v




fclean: clean
	@rm -rf $(DATA_DIRS)
	@echo "fclean: conteneurs, volumes et données supprimés."
