FROM python:3.12-slim

RUN apt-get update -qy \
    && apt-get install -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    PYTHONPATH='/backend/app'

WORKDIR /backend

COPY ./pyproject.toml ./poetry.lock /backend/


RUN /usr/local/bin/poetry install --no-root 

COPY ./app ./app
COPY ./entrypoint.sh ./entrypoint.sh

RUN chmod +x /backend/entrypoint.sh

WORKDIR /backend/app

EXPOSE 8000

ENTRYPOINT ["/backend/entrypoint.sh"]
