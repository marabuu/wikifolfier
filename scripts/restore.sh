#!/usr/bin/env bash
# Restore a PostgreSQL dump created by scripts/backup.sh
#
#   ./scripts/restore.sh backups/compendium-20240101-120000.dump.gz
#
# WARNING: this REPLACES the current database contents.
set -euo pipefail

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-compendium}"
DUMP_FILE="${1:-}"

if [[ -z "$DUMP_FILE" || ! -f "$DUMP_FILE" ]]; then
    echo "Usage: $0 <backup-file.dump.gz>" >&2
    exit 1
fi

echo "==> This will DROP and recreate the database. Type 'yes' to confirm."
read -r confirmation
[[ "$confirmation" == "yes" ]] || { echo "Aborted."; exit 1; }

DB_CONTAINER="${PROJECT_NAME}_postgres"

echo "==> Stopping backend to avoid writes during restore"
docker compose -f "$COMPOSE_FILE" stop backend

echo "==> Recreating database"
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U "${POSTGRES_USER:-compendium}" -d postgres \
    -c "DROP DATABASE IF EXISTS \"${POSTGRES_DB:-compendium}\" WITH (FORCE);"
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U "${POSTGRES_USER:-compendium}" -d postgres \
    -c "CREATE DATABASE \"${POSTGRES_DB:-compendium}\" OWNER \"${POSTGRES_USER:-compendium}\";"

echo "==> Restoring dump"
gunzip -c "$DUMP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T postgres \
    pg_restore -U "${POSTGRES_USER:-compendium}" -d "${POSTGRES_DB:-compendium}" \
    --no-owner --no-acl --clean --if-exists

echo "==> Starting backend and applying migrations"
docker compose -f "$COMPOSE_FILE" start backend
docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py migrate --noinput

echo "==> Restore finished. Verify with:"
echo "    docker compose -f $COMPOSE_FILE exec backend python manage.py showmigrations wiki"