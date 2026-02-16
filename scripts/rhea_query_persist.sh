#!/usr/bin/env bash
# rhea_query_persist.sh — Per-query memory persistence
#
# Every Rhea interaction should call this to:
#   1. Log the query/summary to .entire/logs/queries.jsonl
#   2. Detect changed files since last query
#   3. Create a micro-snapshot capturing the delta
#   4. Stage + auto-commit if Entire.io strategy is auto-commit
#
# Usage:
#   scripts/rhea_query_persist.sh "query summary here"
#   scripts/rhea_query_persist.sh "query summary" --no-commit  # log only, skip git
#
# ADR-014 (2026-02-14) — Per-query memory updates

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

QUERY="${1:-unspecified}"
NO_COMMIT=false
[[ "${2:-}" == "--no-commit" ]] && NO_COMMIT=true

LOGS_DIR=".entire/logs"
SNAPSHOTS_DIR=".entire/snapshots"
QUERIES_LOG="$LOGS_DIR/queries.jsonl"
mkdir -p "$LOGS_DIR" "$SNAPSHOTS_DIR"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TS_FILE=$(date -u +%Y-%m-%dT%H-%M-%SZ)
GIT_REV=$(git rev-parse --short HEAD 2>/dev/null || echo "none")

# 1. Detect changed files (staged + unstaged + untracked in tracked dirs)
CHANGED=$(git diff --name-only 2>/dev/null || true)
STAGED=$(git diff --cached --name-only 2>/dev/null || true)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | head -20 || true)
ALL_CHANGED=$(echo -e "${CHANGED}\n${STAGED}\n${UNTRACKED}" | sort -u | grep -v '^$' || true)
CHANGED_COUNT=$(echo "$ALL_CHANGED" | grep -c . || echo 0)

# 2. Log the query + delta to queries.jsonl
python3 -c "
import json, sys
entry = {
    'ts': '$TS',
    'git_rev': '$GIT_REV',
    'query': '''$QUERY''',
    'changed_files': [f for f in '''$ALL_CHANGED'''.strip().split('\n') if f],
    'changed_count': int('$CHANGED_COUNT')
}
with open('$QUERIES_LOG', 'a') as f:
    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
print(f'  📝 Query logged ({entry[\"changed_count\"]} files changed)')
" 2>&1

# 3. Create micro-snapshot (lightweight — just delta, not full state)
SNAP_FILE="$SNAPSHOTS_DIR/QUERY-${TS_FILE}-${GIT_REV}.json"
python3 -c "
import json, glob
snap = {
    'type': 'query',
    'ts': '$TS',
    'git_rev': '$GIT_REV',
    'query_summary': '''$QUERY'''[:200],
    'changed_files': [f for f in '''$ALL_CHANGED'''.strip().split('\n') if f],
    'docs_sizes': {f.split('/')[-1]: __import__('os').path.getsize(f) for f in glob.glob('docs/*.md')},
}
with open('$SNAP_FILE', 'w') as f:
    json.dump(snap, f, indent=2, ensure_ascii=False)
print(f'  📸 Micro-snapshot: QUERY-${TS_FILE}-${GIT_REV}.json')
" 2>&1

# 4. Auto-commit if strategy is auto-commit and there are changes
if [ "$NO_COMMIT" = false ]; then
    STRATEGY=$(python3 -c "import json; print(json.load(open('.entire/settings.local.json')).get('strategy','manual-commit'))" 2>/dev/null || echo "manual-commit")

    if [ "$STRATEGY" = "auto-commit" ] && [ "$CHANGED_COUNT" -gt 0 ]; then
        echo "  🔄 Auto-commit (strategy=auto-commit)..."
        git add docs/*.md metrics/*.json .entire/logs/*.jsonl .entire/snapshots/QUERY-*.json scripts/*.sh 2>/dev/null || true
        git add src/*.py .entire/settings.local.json 2>/dev/null || true

        if ! git diff --cached --quiet 2>/dev/null; then
            COMMIT_MSG="auto: query persist — ${QUERY:0:60}"
            # Use rhea_commit.sh if entire CLI is available, else plain git
            if command -v entire &>/dev/null && [ -x "$REPO_ROOT/scripts/rhea_commit.sh" ]; then
                "$REPO_ROOT/scripts/rhea_commit.sh" -m "$COMMIT_MSG" 2>&1 || git commit -m "$COMMIT_MSG" 2>&1
            else
                git commit -m "$COMMIT_MSG" 2>&1
            fi
            echo "  ✅ Auto-committed: $(git log --oneline -1)"
        else
            echo "  ℹ️  No staged changes to commit"
        fi
    fi
fi

# 5. Prune old QUERY snapshots (keep last 100)
ls -1t "$SNAPSHOTS_DIR"/QUERY-*.json 2>/dev/null | tail -n +101 | xargs rm -f 2>/dev/null || true

echo "  ✅ Query persistence complete"
