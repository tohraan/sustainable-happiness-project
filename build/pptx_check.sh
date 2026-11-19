#!/bin/sh
# Render a pptx with LibreOffice (headless) into PNGs: build/pptx_check.sh file.pptx outprefix
set -e
d=$(mktemp -d); /Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir "$d" "$1" >/dev/null 2>&1
pdftoppm -r 144 -png "$d"/*.pdf "$2"
