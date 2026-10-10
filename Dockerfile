FROM ghcr.io/astral-sh/uv:python3.11-bookworm

# Install locale, Node.js (required for Claude Code), and common dev tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    curl \
    git \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN echo 'export PS1="\[\e[01;32m\]\u@\h\[\e[00m\]:\[\e[01;34m\]\w\[\e[00m\]\$ "' >> /root/.bashrc \
    && echo 'alias ls="ls --color=auto"' >> /root/.bashrc \
    && echo 'alias grep="grep --color=auto"' >> /root/.bashrc

RUN npm install -g @anthropic-ai/claude-code

# The container runs as the host user (docker-compose.yml `user:`), so give that
# UID/GID a real account with a home outside the bind-mounted /workspace.
ARG UID=1000
ARG GID=1000
RUN (getent group "${GID}" >/dev/null || groupadd -g "${GID}" app) \
    && useradd -m -u "${UID}" -g "${GID}" -s /bin/bash app

# The project environment lives in the image at /opt/venv, never in
# /workspace/.venv: /workspace is the bind-mounted repository, and an
# environment there would be written back to the host.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    VIRTUAL_ENV=/opt/venv \
    UV_CACHE_DIR=/opt/uv-cache \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONPYCACHEPREFIX=/home/app/.cache/pycache \
    PATH=/opt/venv/bin:$PATH
RUN mkdir -p /opt/venv /opt/uv-cache /opt/project \
    && chown "${UID}:${GID}" /opt/venv /opt/uv-cache /opt/project

# Bake the locked dependencies (all groups) into the image. Rebuild with
# `docker compose build` whenever pyproject.toml or uv.lock changes.
USER app
COPY --chown=${UID}:${GID} pyproject.toml uv.lock .python-version /opt/project/
RUN cd /opt/project && uv sync --frozen --no-install-project --all-groups
USER root

WORKDIR /workspace
