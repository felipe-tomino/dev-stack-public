#!/bin/bash
set -euo pipefail
umask 077

case "${1:-}" in
  --ready)
    test -d /workspace/repo/.git || exit 42
    exit 0
    ;;
  --seed|--refresh-base)
    mode=$1
    branch=${2:-sandbox-base}
    # Serialize concurrent first launches; publish only a complete checkout.
    exec 9>/workspace/.seed.lock
    flock 9
    if [[ "$mode" == --seed && -d /workspace/repo/.git ]]; then
      # Drain the caller's bundle even if another first launch seeded this volume.
      cat >/dev/null
      exit 0
    fi
    stage=$(mktemp -d /workspace/.seed.XXXXXX)
    trap 'rm -rf -- "$stage"' EXIT
    cat >"$stage/source.bundle"
    if [[ "$mode" == --refresh-base ]]; then
      cd /workspace/repo
      if [[ -n "$(git status --porcelain)" ]]; then
        echo 'Sandbox base checkout is dirty; refusing to refresh it.' >&2
        exit 1
      fi
      git fetch -q "$stage/source.bundle" HEAD
      git merge --ff-only FETCH_HEAD
      exit 0
    fi
    git init -q --initial-branch="$branch" "$stage/repo"
    git -C "$stage/repo" fetch -q "$stage/source.bundle" HEAD
    git -C "$stage/repo" reset -q --hard FETCH_HEAD
    mkdir -p /workspace/worktrees
    mv "$stage/repo" /workspace/repo
    exit 0
    ;;
esac

cd /workspace/repo
if [[ "${1:-}" == --git ]]; then
  shift
  exec git "$@"
fi
# State is Linux-only and shares logins across projects, not with the host OMP.
# Publish the initial MCP file atomically without replacing an existing file.
agent=$HOME/.omp/agent
if [[ ! -e "$agent/mcp.json" ]]; then
  initial=$(mktemp "$agent/.mcp.XXXXXX")
  cp /etc/omp-lite/mcp.json "$initial"
  ln "$initial" "$agent/mcp.json" 2>/dev/null || test -f "$agent/mcp.json"
  rm -- "$initial"
fi
ln -sf /opt/dev-stack/AGENTS.md "$agent/RULES.md"
# All base checkouts use /workspace/repo; keep resume histories project-specific.
session_dir="$HOME/.omp/lite-sessions/${OMP_LITE_PROJECT_ID:?Missing project ID}"
mkdir -p "$session_dir"
exec omp --config /etc/omp-lite/config.yml --no-extensions --no-lsp \
  --tools=read,edit,write,bash,grep,glob,eval --session-dir "$session_dir" \
  --system-prompt-template /opt/dev-stack/SYSTEM_TEMPLATE.md "$@"
