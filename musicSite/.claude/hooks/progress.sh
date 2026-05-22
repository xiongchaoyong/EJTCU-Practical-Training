#!/usr/bin/env bash
# Stop hook: record progress, commit, and push
set -euo pipefail

TODAY=$(date +%Y-%m-%d)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

# 1. Ensure PROGRESS.md exists
if [ ! -f PROGRESS.md ]; then
  cat > PROGRESS.md <<HEADER
# 项目进度记录

> 最后更新：${TODAY}
> 本项目进度由 Claude Code Stop hook 自动维护

---

## 变更记录

HEADER
fi

# 2. Check for substantive changes
DIFF_STAT=$(git diff --stat 2>/dev/null || true)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null || true)

if [ -z "$DIFF_STAT" ] && [ -z "$UNTRACKED" ]; then
  # No changes — just update the timestamp
  sed -i '' "s/^> 最后更新：.*/> 最后更新：${TODAY}/" PROGRESS.md
  exit 0
fi

# 3. Get today's commit messages for description (exclude auto-progress commits)
TODAY_COMMITS=$(git log --since="today 00:00" --format="%s" 2>/dev/null | grep -v "自动记录项目进度" || true)

# 4. Get changed file names as fallback
FILES=$(git diff --cached --name-only 2>/dev/null | head -5 | tr '\n' ', ' | sed 's/,$//')
if [ -z "$FILES" ]; then
  FILES=$(git diff --name-only 2>/dev/null | head -5 | tr '\n' ', ' | sed 's/,$//')
fi
if [ -z "$FILES" ]; then
  FILES="untracked files"
fi

# 5. Build description: prefer commit messages, fall back to filenames
if [ -n "$TODAY_COMMITS" ]; then
  DESCRIPTION=$(echo "$TODAY_COMMITS" | tr '\n' '; ' | sed 's/; $//')
else
  DESCRIPTION="$FILES"
fi

# 6. Append to PROGRESS.md (avoid duplicate entries)
NEW_ENTRY="- **${TODAY}**：${DESCRIPTION}"
if ! grep -qF "${DESCRIPTION}" PROGRESS.md 2>/dev/null; then
  echo "$NEW_ENTRY" >> PROGRESS.md
fi

# Update timestamp
sed -i '' "s/^> 最后更新：.*/> 最后更新：${TODAY}/" PROGRESS.md

# 7. Commit and push
git add .
if git diff --cached --quiet 2>/dev/null; then
  exit 0  # Nothing to commit
fi

git commit -m "chore: 自动记录项目进度 — ${DESCRIPTION}" 2>/dev/null || true
git push 2>/dev/null || true
