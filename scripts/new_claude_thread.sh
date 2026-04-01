#!/usr/bin/env bash
# Usage: ./scripts/new_claude_thread.sh <slug> 
# Example: ./scripts/new_claude_thread.sh social-repost-blueprint

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <slug>"
  echo "Example: $0 social-repost-blueprint"
  exit 1
fi

SLUG="$1"
PROMPT_FILE="docs/prompts/${SLUG}.md"

mkdir -p docs/prompts

if [ -f "$PROMPT_FILE" ]; then
  echo "Prompt file already exists: $PROMPT_FILE"
else
  cat > "$PROMPT_FILE" << 'PEOF'
# Paste your first-message prompt for the new Claude thread here.

# Instructions:
# 1. Open VS Code, create a NEW Claude/Chat conversation.
# 2. Paste the contents of this file as the FIRST message in that chat.
# 3. Then come back to terminal, stage and commit this file:
#    git add docs/prompts/<slug>.md
#    git commit -m "docs: add <slug> prompt"
#    git push origin <branch>

PEOF
  echo "Created $PROMPT_FILE"
  echo "Open it in VS Code and replace the template with your actual prompt."
fi

echo
echo "Next steps:"
echo "1) In VS Code, open: $PROMPT_FILE"
echo "2) Paste your new-thread prompt into that file and save."
echo "3) Start a NEW Claude chat and paste the same prompt as the first message."
echo "4) Then run:"
echo "   git add $PROMPT_FILE"
echo "   git commit -m \"docs: add ${SLUG} prompt\""
echo "   git push origin foundation   # or your feature branch"
