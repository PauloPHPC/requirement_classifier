#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env}"
REQ_CLASSIFIER_DIR="${REQ_CLASSIFIER_DIR:-$APP_DIR/requirements_classifier/distilbert}"

cd "$APP_DIR"

if [ -n "${GDRIVE_FOLDER_URL:-}" ]; then
  mkdir -p "$REQ_CLASSIFIER_DIR"

  BEFORE="$(mktemp)"
  AFTER="$(mktemp)"
  ls -1A "$REQ_CLASSIFIER_DIR" | sort > "$BEFORE"

  echo ">> Baixando pasta do Drive para: $REQ_CLASSIFIER_DIR (mantendo nome)"
  gdown --folder "$GDRIVE_FOLDER_URL" -O "$REQ_CLASSIFIER_DIR"

  ls -1A "$REQ_CLASSIFIER_DIR" | sort > "$AFTER"
  NEW_ITEM="$(comm -13 "$BEFORE" "$AFTER" | head -n 1 || true)"
  rm -f "$BEFORE" "$AFTER"

else
  echo ">> GDRIVE_FOLDER_URL não definido; pulando download do Drive"
fi

touch "$ENV_FILE"

if ! grep -qE '^DJANGO_SECRET_KEY=' "$ENV_FILE"; then
  echo ">> Gerando DJANGO_SECRET_KEY no .env"
  SECRET_KEY="$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")"
  printf "DJANGO_SECRET_KEY='%s'\n" "$SECRET_KEY" >> "$ENV_FILE"
else
  SECRET_KEY="$(grep -E '^DJANGO_SECRET_KEY=' "$ENV_FILE" | head -n1 | cut -d= -f2- | sed -e \"s/^'//\" -e \"s/'$//\")"
fi

export DJANGO_SECRET_KEY="$SECRET_KEY"

python manage.py collectstatic --noinput || true
python manage.py migrate --noinput || true

exec "$@"
