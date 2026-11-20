FROM node:24.21.0-bookworm-slim

ARG TARGETARCH
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates chromium curl git python3 ripgrep util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && case "$TARGETARCH" in \
        arm64) arch=arm64; sha=82a880ba04d73f1c81a12931447f9f9ed8945581998564eae900c1238f4502e2 ;; \
        amd64) arch=x64; sha=80a692c5adb9c71124bb11e77bd7edb3cf8fbbab6980db3206dcb6a4cb2905b5 ;; \
        *) exit 1 ;; \
    esac \
    && curl -fsSL --retry 2 "https://github.com/can1357/oh-my-pi/releases/download/v18.22.2/omp-linux-$arch" -o /usr/local/bin/omp \
    && echo "$sha  /usr/local/bin/omp" | sha256sum -c - \
    && chmod 755 /usr/local/bin/omp \
    && mkdir -p /workspace /opt/dev-stack /home/node/.agents /home/node/.omp/agent \
    && ln -s /opt/dev-stack/skills /home/node/.agents/skills \
    && ln -s /opt/dev-stack/workflows /home/node/.agents/workflows \
    && chown node:node /workspace /home/node/.omp /home/node/.omp/agent

COPY entrypoint.sh /usr/local/bin/omp-lite-entrypoint
COPY config.yml /etc/omp-lite/config.yml
COPY mcp.json /etc/omp-lite/mcp.json
COPY agent-chromium /usr/local/bin/agent-chromium
RUN chmod 755 /usr/local/bin/omp-lite-entrypoint /usr/local/bin/agent-chromium

ENV PUPPETEER_EXECUTABLE_PATH=/usr/local/bin/agent-chromium \
    PI_BROWSER_RELAY=0 PI_BROWSER_TERN=0 PI_BROWSER_CMUX=0 \
    OMP_WORKTREE_DIR=/workspace/worktrees \
    GIT_TERMINAL_PROMPT=0 npm_config_cache=/tmp/npm-cache
USER node
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/omp-lite-entrypoint"]
