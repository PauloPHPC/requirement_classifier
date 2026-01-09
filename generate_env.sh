#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env}"

touch "$ENV_FILE"

if grep -qE '^SECRET_KEY=' "$ENV_FILE"; then
  exit 0
fi

SECRET_KEY_VAL="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"

ESCAPED="$(printf '%s' "$SECRET_KEY_VAL" | sed 's/\\/\\\\/g; s/"/\\"/g')"

printf 'SECRET_KEY="%s"\n' "$ESCAPED" >> "$ENV_FILE"