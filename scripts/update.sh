#!/usr/bin/env bash
# Update an existing deployment after a git pull.
# Takes a backup first, then rebuilds and migrates.
#
#   ./scripts/update.sh
set -euo pipefail

cd "$(dirname "$0")/.."

BASE="docker-compose.yml"
PROD="docker-compose.prod.yml"
COMPOSE="docker compose -f $BASE -f $PROD"

echo "==> Backing up before update"
./scripts/backup.sh

echo "==> Rebuilding and restarting"
$COMPOSE build
$COMPOSE up -d

echo "==> Applying migrations"
$COMPOSE exec -T backend python manage.py migrate --noinput

echo "==> Rebuilding search index"
$COMPOSE exec -T backend python manage.py reindex

echo "==> Status"
$COMPOSE ps
echo "==> Update complete"