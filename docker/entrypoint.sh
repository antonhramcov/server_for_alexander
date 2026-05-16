#!/bin/sh
set -eu

mkdir -p /app/files /app/requests

exec "$@"
