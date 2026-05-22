#!/bin/bash
cd /opt/render/project/src  # Render's working directory
celery -A src.infrastructure.celery.app worker --beat --loglevel=info --pool=solo &
uvicorn main:app --host 0.0.0.0 --port $PORT