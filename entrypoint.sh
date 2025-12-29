#!/bin/sh
set -e

# Fix ownership only if needed (safe + fast)
if [ "$(stat -c '%u' /web/storage)" != "$(id -u botuser)" ]; then
  chown -R botuser:botuser /web/storage
fi

if [ "$(stat -c '%u' /app/bot/logs)" != "$(id -u botuser)" ]; then
  chown -R botuser:botuser /app/bot/logs
fi

exec "$@"
