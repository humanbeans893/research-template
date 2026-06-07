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

# System dependencies used by common geospatial Python packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev libproj-dev proj-data proj-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN echo 'export PS1="\[\e[01;32m\]\u@\h\[\e[00m\]:\[\e[01;34m\]\w\[\e[00m\]\$ "' >> /root/.bashrc \
    && echo 'alias ls="ls --color=auto"' >> /root/.bashrc \
    && echo 'alias grep="grep --color=auto"' >> /root/.bashrc

RUN npm install -g @anthropic-ai/claude-code

WORKDIR /workspace
