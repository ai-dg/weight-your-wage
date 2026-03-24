#!/bin/bash

LOG_DIR=./srcs/logs
PID_FILE="$LOG_DIR/pids.txt"

rm -f "$PID_FILE"
rm -rf ./srcs/logs/*

SERVICES=(
  grafana
  minio
  mlflow-server
  fastapi
  nginx
  postgres_db
  pgadmin_contain
  frontend
)

for service in "${SERVICES[@]}"; do
  echo "Starting follower logs for : $service"
  docker logs --follow "$service" > "$LOG_DIR/$service.log" 2>&1 &
  echo $! >> "$PID_FILE"
done

echo "All followers are started. PID saved at $PID_FILE"