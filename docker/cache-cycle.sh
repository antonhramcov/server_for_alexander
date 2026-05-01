#!/bin/sh
set -eu

python /app/cache.py
sleep "${CACHE_RESTART_DELAY:-300}"
