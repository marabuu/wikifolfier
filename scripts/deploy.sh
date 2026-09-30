#!/usr/bin/env bash
# First deploy (or full rebuild) on a clean VPS.
#
#   ./scripts/deploy.sh
#
# Requires: Docker + Docker Compose installed, .env configured.
set -euo pipefail

cd "$(dirname "$0")/.."

BASE="docker-compose.yml"
PROD="docker-compose.prod.yml"

if [[ ! -f .env ]]; then
    echo "ERROR: .env not found. Run: cp .env.example .env" >&2
    exit 1
fi

# shellcheck disable=SC1091
set -a; source .env; set +a

if [[ -z "${DJANGO_SECRET_KEY:-}" || "$DJANGO_SECRET_KEY" == "generate-with-python-secrets-token-urlsafe-50" ]]; then
    echo "==> Generating DJANGO_SECRET_KEY"
    NEW_SECRET="$(docker run --rm python:3.12-slim python -c \
        'import secrets; print(secrets.token_urlsafe(50))')"
    if grep -q '^DJANGO_SECRET_KEY=' .env; then
        sed -i "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=${NEW_SECRET}|" .env
    else
        echo "DJANGO_SECRET_KEY=${NEW_SECRET}" >> .env
    fi
    set -a; source .env; set +a
fi

echo "==> Building images"
docker compose -f "$BASE" -f "$PROD" build

echo "==> Starting services"
docker compose -f "$BASE" -f "$PROD" up -d

echo "==> Waiting for database"
docker compose -f "$BASE" -f "$PROD" exec -T postgres \
    pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"

echo "==> Running migrations"
docker compose -f "$BASE" -f "$PROD" exec -T backend \
    python manage.py migrate --noinput

echo "==> Creating categories"
docker compose -f "$BASE" -f "$PROD" exec -T backend \
    python manage.py seed_categories

echo "==> Collecting static files"
docker compose -f "$BASE" -f "$PROD" exec -T backend \
    python manage.py collectstatic --noinput

echo "==> Status"
docker compose -f "$BASE" -f "$PROD" ps

cat <<EOF

Deploy finished.

Next steps:
  1. Create the GM account:
       docker compose -f $BASE -f $PROD exec backend python manage.py createsuperuser
  2. Optional demo content:
       docker compose -f $BASE -f $PROD exec backend python manage.py seed_demo
  3. Import content from Wikidot:
       docker compose -f $BASE -f $PROD --profile tools run --rm importer import
  4. Issue the TLS certificate (see DEPLOY.md).
EOF