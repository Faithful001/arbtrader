#!/bin/bash
export PYTHONUNBUFFERED=1
celery -A src.infrastructure.celery.app worker --beat --loglevel=info --pool=solo --without-mingle --without-gossip &
uvicorn main:app --host 0.0.0.0 --port $PORT