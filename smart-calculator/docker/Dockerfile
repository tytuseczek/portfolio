FROM europe-west3-docker.pkg.dev/virtual-teacher-apps/docker-base/python:3.9

ARG UID=1000
ARG GID=1000
ARG UNAME=dev
ARG POETRY_INSTALL_EXTRA_ARGS="--no-dev"

RUN /entrypoint.sh ensure_user
USER ${UNAME}

COPY --chown=dev:dev ./poetry.lock ./pyproject.toml ./
RUN poetry install --no-interaction $POETRY_INSTALL_EXTRA_ARGS
COPY --chown=dev:dev ./ ./
