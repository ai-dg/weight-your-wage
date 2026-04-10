#!/bin/bash
LOG_DIR=./srcs/logs
PID_FILE="$LOG_DIR/pids.txt"

rm -f "$PID_FILE"
rm -rf ./srcs/logs/*

ACTIVE_SERVICES=$(docker compose -f srcs/docker-compose.yml ps --services --filter "status=running")

for service in $ACTIVE_SERVICES; do
  docker logs --follow "$service" > "$LOG_DIR/$service.log" 2>&1 &
  echo $! >> "$PID_FILE"
done

echo "All followers are started. PID saved at $PID_FILE"