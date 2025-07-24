# pull base image
FROM python:3.11-slim

RUN apt-get update -y && apt-get install -y cron ca-certificates

RUN pip install poetry==1.6.1
RUN poetry config virtualenvs.create false

WORKDIR /code

COPY ./pyproject.toml ./README.md ./poetry.lock* ./

ARG DOCKER_COMPOSE_WAIT_VERSION
ENV DOCKER_COMPOSE_WAIT_VERSION=${DOCKER_COMPOSE_WAIT_VERSION:-2.12.1}
ARG DOCKER_COMPOSE_WAIT_PLATFORM_SUFFIX
ENV DOCKER_COMPOSE_WAIT_PLATFORM_SUFFIX=${DOCKER_COMPOSE_WAIT_PLATFORM_SUFFIX:-}

# Install docker-compose wait
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$DOCKER_COMPOSE_WAIT_VERSION/wait${DOCKER_COMPOSE_WAIT_PLATFORM_SUFFIX} /wait
RUN chown $UID:$GID /wait &&  chmod +x /wait

RUN poetry install  --no-interaction --no-ansi --no-root

COPY ./dgrehydro ./dgrehydro

RUN ls -lah
RUN poetry install --no-interaction --no-ansi

EXPOSE 8001

CMD exec gunicorn -b 0.0.0.0:8001 dgrehydro:app
