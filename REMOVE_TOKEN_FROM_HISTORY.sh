#!/bin/bash
# Script to remove GitHub token from git history
# This rewrites git history - use with caution!

set -e

TOKEN="ghp_... (redacted for security)"
REPLACEMENT="ghp_... (redacted for security)"
FILE="TOKEN_SCOPE_UPDATE.md"

echo "Removing token from git history..."
echo "Token: ${TOKEN:0:10}..."
echo "File: $FILE"
echo ""

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Check for unstaged changes
if ! git diff-index --quiet HEAD --; then
    echo "Warning: You have unstaged changes. Stashing them..."
    git stash push -m "Stashing before token removal from history"
    STASHED=1
fi

# Use git filter-branch to replace token in all commits
echo "Rewriting git history (this may take a while)..."
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force \
    --env-filter 'export GIT_AUTHOR_DATE="$GIT_AUTHOR_DATE" GIT_COMMITTER_DATE="$GIT_COMMITTER_DATE"' \
    --tree-filter "
        if [ -f $FILE ]; then
            sed -i '' 's|$TOKEN|$REPLACEMENT|g' $FILE 2>/dev/null || \
            sed -i 's|$TOKEN|$REPLACEMENT|g' $FILE 2>/dev/null || true
        fi
    " \
    --prune-empty \
    --tag-name-filter cat \
    -- --all

echo ""
echo "History rewrite complete!"
echo ""
echo "Next steps:"
echo "1. Verify the token is removed: git show 878de09c:$FILE | grep -i token"
echo "2. Force push to remote: git push origin --force --all"
echo "3. Warn your team about the history rewrite"
echo ""
echo "⚠️  WARNING: This rewrites history. All team members will need to:"
echo "   git fetch origin"
echo "   git reset --hard origin/main"
echo ""

# Restore stashed changes if any
if [ "$STASHED" = "1" ]; then
    echo "Restoring stashed changes..."
    git stash pop || true
fi
