#!/usr/bin/env bash
# SessionStart hook — make the GSD toolchain available in ephemeral containers.
#
# Why this exists: GSD is not part of this repo. It installs into ~/.claude/
# (skills, agents, hooks) plus the global npm prefix (gsd-sdk / gsd-tools).
# A Claude Code cloud session gets a fresh container that clones only the repo,
# so ~/.claude/ starts empty and every /gsd-* skill is missing. This hook
# reinstalls it there, and does nothing at all on a machine that already has it.
#
# NEVER clobbers an existing install. If any GSD is already present -- any
# version -- this hook reports it and exits. That keeps it a no-op on a local
# machine whose GSD version may differ from the pin below.
#
# Wired in .claude/settings.json. Stdout lands in every agent's context at
# session start, so keep it to a few short lines. Always exits 0: a failed
# install must degrade the session, never block it.
set -uo pipefail

# Pin. Change this (or export GSD_VERSION) to match the version you run
# locally, so cloud and local sessions drive .planning/ with the same tool.
GSD_VERSION="${GSD_VERSION:-1.42.3}"
PKG="get-shit-done-cc"
SKILLS_DIR="$HOME/.claude/skills"
LOG="${TMPDIR:-/tmp}/gsd-install.log"

installed_version() {
  command -v gsd-sdk >/dev/null 2>&1 || return 1
  gsd-sdk --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1
}

# Present = a working CLI, or skills (v1.4x packaging), or commands (older
# colon-namespaced packaging). Any one of these means hands off.
gsd_present() {
  command -v gsd-sdk >/dev/null 2>&1 && return 0
  command -v gsd-tools >/dev/null 2>&1 && return 0
  [ -d "$SKILLS_DIR/gsd-execute-phase" ] && return 0
  [ -d "$HOME/.claude/commands/gsd" ] && return 0
  return 1
}

if gsd_present; then
  have=$(installed_version || echo "unknown")
  echo "[gsd] READY — v${have} already installed; leaving it untouched."
  exit 0
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[gsd] MISSING — no npm on PATH, cannot install. /gsd-* skills unavailable."
  exit 0
fi

echo "[gsd] MISSING — installing ${PKG}@${GSD_VERSION} (fresh container; ~20s)…"

if ! npm install -g "${PKG}@${GSD_VERSION}" >"$LOG" 2>&1; then
  echo "[gsd] FAILED — npm install did not succeed. See $LOG"
  echo "[gsd] Session continues without /gsd-* skills."
  exit 0
fi

# --claude selects the Claude Code target, --global writes to ~/.claude,
# --yes keeps the installer non-interactive (it prompts otherwise).
if ! get-shit-done-cc --claude --global --yes >>"$LOG" 2>&1; then
  echo "[gsd] FAILED — installer did not complete. See $LOG"
  echo "[gsd] Session continues without /gsd-* skills."
  exit 0
fi

count=$(ls "$SKILLS_DIR" 2>/dev/null | grep -c '^gsd-' || echo 0)
echo "[gsd] INSTALLED v${GSD_VERSION} — ${count} /gsd-* skills available."
echo "[gsd] Skills use the hyphen form: /gsd-plan-phase, /gsd-execute-phase 4."
exit 0
