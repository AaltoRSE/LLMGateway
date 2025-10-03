#!/bin/bash

# This is the startup script inside Docker environment

if [ "$ENV" = "dev" ]; then
    echo "ENV variable MUST NOT be 'dev'. Exiting."
    exit 1
fi

# Check if the current user is root
if [ "$(id -u)" -eq 0 ]; then
  echo "LLM Server cannot be run as root."
  exit 1
fi

# Start the Uvicorn server
echo "Starting the uvicorn server"
exec uvicorn --no-server-header --host 0.0.0.0 --log-level warning app.main:app
