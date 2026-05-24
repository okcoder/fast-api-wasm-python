# Node.js/npm をベースにし、Python は mise で管理します。
FROM mcr.microsoft.com/devcontainers/javascript-node:1-22-bookworm

USER node

# mise は公式インストーラで導入します。
RUN curl https://mise.run | sh

ENV NPM_CONFIG_PREFIX="/home/node/.npm-global"
ENV PATH="/home/node/.local/bin:/home/node/.local/share/mise/shims:/home/node/.npm-global/bin:${PATH}"

RUN mkdir -p /home/node/.npm-global \
    && npm config set prefix /home/node/.npm-global \
    && npm install -g @openai/codex
