#!/usr/bin/env bash
# lib_rhea_hooks.sh — Native replacement for Entire.io hook system
# ADR-016: Absorb Entire.io into native scripts
#
# Replaces: entire hooks git session-start/stop/commit-msg/post-commit/pre-push
# Replaces: entire hooks claude-code session-start/end/user-prompt-submit/stop/pre-task/post-task/post-todo
#
# All events logged to .entire/logs/hooks.jsonl (same directory, backward-compatible)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK_LOG="${REPO_ROOT}/.entire/logs/hooks.jsonl"

mkdir -p "$(dirname "$HOOK_LOG")"

_ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
_sha() { git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "none"; }
_branch() { git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "detached"; }

# Log a hook event to JSONL
rhea_hook_log() {
    local event="$1"
    local detail="${2:-}"
    printf '{"ts":"%s","event":"%s","git":"%s","branch":"%s","detail":"%s"}\n' \
        "$(_ts)" "$event" "$(_sha)" "$(_branch)" "$detail" >> "$HOOK_LOG"
}

# Generate a checkpoint ID (replaces Entire-Checkpoint trailer value)
rhea_checkpoint_id() {
    echo "rhea-$(date +%s | shasum | cut -c1-12)"
}

# --- Git hook replacements ---

rhea_git_session_start() {
    rhea_hook_log "git.session-start"
}

rhea_git_session_stop() {
    rhea_hook_log "git.session-stop"
}

rhea_git_commit_msg() {
    # $1 = commit message file
    local msg_file="${1:-}"
    if [ -n "$msg_file" ] && [ -f "$msg_file" ]; then
        # Strip empty commit messages (mirrors entire's behavior)
        local content
        content=$(grep -v '^#' "$msg_file" | tr -d '[:space:]')
        if [ -z "$content" ]; then
            echo "Aborting commit: empty message" >&2
            return 1
        fi
    fi
    rhea_hook_log "git.commit-msg"
}

rhea_git_prepare_commit_msg() {
    # $1 = commit message file, $2 = source (message/merge/squash/commit)
    local msg_file="${1:-}"
    local source="${2:-}"
    if [ -n "$msg_file" ] && [ -f "$msg_file" ]; then
        local ckpt_id
        ckpt_id="$(rhea_checkpoint_id)"
        # Inject trailer (only if not already present)
        if ! grep -q "Rhea-Checkpoint:" "$msg_file" 2>/dev/null; then
            echo "" >> "$msg_file"
            echo "Rhea-Checkpoint: $ckpt_id" >> "$msg_file"
        fi
    fi
    rhea_hook_log "git.prepare-commit-msg" "$source"
}

rhea_git_post_commit() {
    rhea_hook_log "git.post-commit" "$(_sha)"
}

rhea_git_pre_push() {
    local remote="${1:-origin}"
    rhea_hook_log "git.pre-push" "$remote"
}

# --- Claude Code hook replacements ---

rhea_claude_session_start() {
    rhea_hook_log "claude.session-start"
}

rhea_claude_session_end() {
    rhea_hook_log "claude.session-end"
}

rhea_claude_user_prompt_submit() {
    rhea_hook_log "claude.user-prompt-submit"
}

rhea_claude_stop() {
    rhea_hook_log "claude.stop"
}

rhea_claude_pre_task() {
    rhea_hook_log "claude.pre-task"
}

rhea_claude_post_task() {
    rhea_hook_log "claude.post-task"
}

rhea_claude_post_todo() {
    rhea_hook_log "claude.post-todo"
}

# --- Prune old hook logs (keep last 2000 entries) ---

rhea_hooks_prune() {
    if [ -f "$HOOK_LOG" ]; then
        local count
        count=$(wc -l < "$HOOK_LOG" | tr -d ' ')
        if [ "$count" -gt 2000 ]; then
            tail -n 2000 "$HOOK_LOG" > "${HOOK_LOG}.tmp"
            mv "${HOOK_LOG}.tmp" "$HOOK_LOG"
        fi
    fi
}
