# syntax=docker/dockerfile:1

# Build stage. Its only job is to produce /opt/venv; pip, setuptools, and the
# wheel cache stay behind and never reach the image that ships.
FROM python:3.13-slim AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /src

# pyproject.toml is the only dependency list in the repo, so it is also the one
# the image installs from - a hand-copied requirements.txt would drift the first
# time someone bumps discord.py. Copying nothing else here means that editing a
# cog doesn't invalidate the install layer below.
COPY pyproject.toml ./
RUN python -c "import tomllib; print(*tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies'], sep=chr(10))" > requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip python -m venv /opt/venv && /opt/venv/bin/pip install -r requirements.txt


# Runtime stage.
FROM python:3.13-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Nothing in the bot writes to disk, so it runs as a normal user with no home
# directory. docker-compose.yml mounts the root filesystem read-only to match.
RUN useradd --system --no-create-home --shell /usr/sbin/nologin flyxbot

COPY --from=build /opt/venv /opt/venv

WORKDIR /app
COPY bot.py config.py ./
COPY cogs/ ./cogs/

USER flyxbot

# No .env is copied in - .dockerignore excludes it, and the token arrives from
# the environment at run time, so it never lands in a layer.
CMD ["python", "bot.py"]
