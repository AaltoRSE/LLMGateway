#!/bin/bash

# This is the startup script inside Docker environment

# Check if the DANGEROUS_DO_MIGRATION flag is set
if [ "$DANGEROUS_DO_MIGRATION" = "true" ]; then
    echo "DANGEROUS_DO_MIGRATION is set. Running alembic upgrade head..."
    alembic upgrade head
fi

if [ "$ENV" = "dev" ]; then
    echo "ENV variable MUST NOT be 'dev'. Exiting."
    exit 1
fi

# Check if the current user is root
if [ "$(id -u)" -eq 0 ]; then
  echo "Aalto AI cannot be run as root."
  exit 1
fi

# Start the Uvicorn server
echo "Starting the uvicorn server"
exec uvicorn --no-server-header --host 0.0.0.0 --log-level warning app.main:app
