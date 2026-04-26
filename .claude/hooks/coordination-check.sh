#!/usr/bin/env bash
# Reads shared coordination state on every turn.
# Prints active worktree summaries and delivers+clears inbox messages.

FEATURE=$(basename "$PWD")
GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null) || exit 0
MAIN_REPO=$(dirname "$GIT_COMMON")
COORD="$MAIN_REPO/.claude/coordination"

[ -d "$COORD" ] || exit 0

# Print other teams' active files
FOUND_ACTIVE=0
while IFS= read -r -d '' f; do
    name=$(basename "$f" .md)
    [ "$name" = "$FEATURE" ] && continue
    [ "$FOUND_ACTIVE" -eq 0 ] && echo "=== Active worktrees ===" && FOUND_ACTIVE=1
    echo "--- $name ---"
    cat "$f"
done < <(find "$COORD/active" -name "*.md" -print0 2>/dev/null)

# Deliver and clear inbox
INBOX="$COORD/inbox/$FEATURE"
if [ -d "$INBOX" ]; then
    FOUND_MSG=0
    while IFS= read -r -d '' msg; do
        [ "$FOUND_MSG" -eq 0 ] && echo "=== INBOX ===" && FOUND_MSG=1
        cat "$msg"
        rm "$msg"
    done < <(find "$INBOX" -name "*.md" -print0 2>/dev/null | sort -z)
fi
