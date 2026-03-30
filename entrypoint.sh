#!/bin/bash
# Ensure writable directories exist for volume mounts
# Docker volumes mount as root — this fixes permissions at runtime

mkdir -p /app/data/db /app/data/real /app/data/sample

# Fix permissions if running as root (some deployments)
if [ "$(id -u)" = "0" ]; then
    chown -R appuser:appuser /app/data
    exec gosu appuser "$@"
else
    exec "$@"
fi
