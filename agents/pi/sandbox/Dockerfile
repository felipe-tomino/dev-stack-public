FROM node:24.21.0-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates chromium git python3 ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.5.2 \
    && mkdir -p /home/node/.pi/agent /home/node/.agents \
    && ln -s /opt/dev-stack/skills /home/node/.agents/skills \
    && ln -s /opt/dev-stack/workflows /home/node/.agents/workflows \
    && chown -R node:node /home/node/.pi /home/node/.agents

COPY entrypoint.py /usr/local/bin/pi-sandbox-entrypoint
COPY agent-chromium /usr/local/bin/agent-chromium
RUN chmod 755 /usr/local/bin/pi-sandbox-entrypoint /usr/local/bin/agent-chromium

ENV PUPPETEER_EXECUTABLE_PATH=/usr/local/bin/agent-chromium \
    PI_BROWSER_RELAY=0 PI_BROWSER_TERN=0 npm_config_cache=/tmp/npm-cache
USER node
ENTRYPOINT ["/usr/local/bin/pi-sandbox-entrypoint"]
