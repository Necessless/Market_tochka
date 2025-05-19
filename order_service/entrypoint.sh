#!/bin/sh

cd /backend/app
echo "Выполняются миграции..."
alembic  upgrade head

echo "Миграции применены, запускается сервер..."
poetry run uvicorn main:main_app --host 0.0.0.0 --port 8000 --reload

