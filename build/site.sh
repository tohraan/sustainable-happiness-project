#!/bin/sh
# Assemble the public site into deploy/ (keeps the .vercel project link if present).
set -e
cd "$(dirname "$0")/.."
mkdir -p deploy && find deploy -mindepth 1 -maxdepth 1 ! -name .vercel -exec rm -rf {} +
cp -R index.html fonts fonts.css deploy/
[ -f Sustainable-Happiness-Project.pdf ] && cp Sustainable-Happiness-Project.pdf deploy/
[ -f Sustainable-Happiness-Project-editable.pptx ] && cp Sustainable-Happiness-Project-editable.pptx deploy/
rsync -a --exclude unused images/ deploy/images/
printf '{"cleanUrls":true}\n' > deploy/vercel.json
