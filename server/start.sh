#!/bin/bash
celery -A src.infrastructure.celery.app worker --beat --loglevel=info &
uvicorn main:app --host 0.0.0.0 --port $PORT