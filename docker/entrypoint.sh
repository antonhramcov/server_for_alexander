#!/bin/sh
set -eu

GOOGLE_AUTH_PATH="${GOOGLE_AUTH_PATH:-/app/files/auth.json}"
GOOGLE_AUTH_DIR="$(dirname "$GOOGLE_AUTH_PATH")"

mkdir -p "$GOOGLE_AUTH_DIR" /app/files /app/requests

if [ -n "${GOOGLE_AUTH_JSON:-}" ]; then
  printf '%s' "$GOOGLE_AUTH_JSON" > "$GOOGLE_AUTH_PATH"
elif [ -n "${GOOGLE_AUTH_JSON_BASE64:-}" ]; then
  printf '%s' "$GOOGLE_AUTH_JSON_BASE64" | python3 -c 'import base64, sys; sys.stdout.buffer.write(base64.b64decode(sys.stdin.read()))' > "$GOOGLE_AUTH_PATH"
fi

exec "$@"
