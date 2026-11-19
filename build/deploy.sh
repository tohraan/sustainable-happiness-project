#!/bin/sh
# Manual deploy from this Mac. Pushing to main does the same thing automatically (.github/workflows/deploy.yml).
set -e
cd "$(dirname "$0")/.."
python3 build/game.py
build/site.sh
cd deploy && vercel deploy --prod --yes 2>&1 | grep -E 'Production|Aliased'
