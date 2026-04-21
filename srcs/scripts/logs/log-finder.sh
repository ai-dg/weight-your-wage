#!/bin/bash
LOG_DIR=./srcs/logs
PID_FILE="$LOG_DIR/pids.txt"

rm -f "$PID_FILE"
rm -rf ./srcs/logs/*

ACTIVE_CONTAINER_IDS=$(docker compose -f srcs/docker-compose.yml ps -q --filter "status=running")

for container_id in $ACTIVE_CONTAINER_IDS; do
  container_name=$(docker inspect --format '{{.Name}}' "$container_id" | sed 's#^/##')
  docker logs --follow "$container_id" > "$LOG_DIR/$container_name.log" 2>&1 &
  echo $! >> "$PID_FILE"
done

echo "All followers are started. PID saved at $PID_FILE"