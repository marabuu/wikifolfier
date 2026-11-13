#!/usr/bin/env bash
# Backup the PostgreSQL database and the media volume.
#
#   ./scripts/backup.sh            -> ./backups/compendium-<timestamp>.dump
#   ./scripts/backup.sh --media    -> also archive /app/media
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-compendium}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$(pwd)/backups"
mkdir -p "$BACKUP_DIR"

DUMP_FILE="${BACKUP_DIR}/compendium-${TIMESTAMP}.dump"

echo "==> Dumping PostgreSQL to ${DUMP_FILE}"
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    sh -c 'pg_dump -U "${POSTGRES_USER:-compendium}" -d "${POSTGRES_DB:-compendium}" --format=custom --no-owner --no-acl' \
    < /dev/null > "$DUMP_FILE"

gzip -9 "$DUMP_FILE"
echo "==> Created ${DUMP_FILE}.gz"

if [[ "${1:-}" == "--media" ]]; then
    MEDIA_FILE="${BACKUP_DIR}/media-${TIMESTAMP}.tar.gz"
    echo "==> Archiving media volume to ${MEDIA_FILE}"
    docker run --rm \
        --user "$(id -u):$(id -g)" \
        -v "${PROJECT_NAME}_media_data:/data:ro" \
        -v "${BACKUP_DIR}:/backup" \
        alpine tar czf "/backup/$(basename "$MEDIA_FILE")" -C /data .
    echo "==> Created ${MEDIA_FILE}"
fi

# Keep the 15 most recent dumps and media archives.
ls -1t "${BACKUP_DIR}"/compendium-*.dump.gz 2>/dev/null | tail -n +16 | xargs -r rm -f --
ls -1t "${BACKUP_DIR}"/media-*.tar.gz 2>/dev/null | tail -n +16 | xargs -r rm -f --
echo "==> Backup finished"