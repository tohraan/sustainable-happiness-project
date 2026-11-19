#!/bin/sh
# Rebuild the public site at https://happiness-through-volunteering.vercel.app from the current deck.
set -e
cd "$(dirname "$0")/.."
mkdir -p deploy && find deploy -mindepth 1 -maxdepth 1 ! -name .vercel -exec rm -rf {} +   # keep the .vercel project link
cp -R index.html fonts fonts.css Sustainable-Happiness-Project.pdf deploy/
rsync -a --exclude unused images/ deploy/images/
printf '{"cleanUrls":true}\n' > deploy/vercel.json
cd deploy && vercel deploy --prod --yes 2>&1 | grep -E 'Production|Aliased'
