#!/usr/bin/env bash
gunicorn main:app --bind 0.0.0.0:3000 -k uvicorn.workers.UvicornWorker --workers 1