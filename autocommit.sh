#!/bin/bash
# Auto-commit + push every 2 minutes. Run: nohup ./autocommit.sh > autocommit.log 2>&1 &
cd "$(dirname "$0")"
while true; do
  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -q -m "auto: $(date '+%Y-%m-%d %H:%M:%S')

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WsrVZb94LwbHVAmBvsSTfn" && git push -q origin main 2>&1 | tail -1
  fi
  sleep 120
done
