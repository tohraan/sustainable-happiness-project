"""Render every slide (final animation state) to PNG, then build slides.pdf and slides.pptx.

Usage:  python3 build/export.py            # all outputs
        python3 build/export.py --png      # screenshots + contact sheet only
"""
import sys, pathlib, json
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "slides"
OUT.mkdir(parents=True, exist_ok=True)
deck = (ROOT / "index.html").as_uri()

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto(deck + "?export=1")
    meta = pg.evaluate("""() => [...document.querySelectorAll('.slide')].map(s => ({
        title: s.dataset.title, speaker: s.dataset.speaker,
        notes: (s.querySelector('.notes')?.textContent || '').trim()}))""")
    for i in range(1, len(meta) + 1):
        pg.goto(f"{deck}?export={i}")
        pg.wait_for_function("window.__ready === true", timeout=15000)
        pg.screenshot(path=str(OUT / f"{i:02d}.png"))
    b.close()

pngs = sorted(OUT.glob("*.png"))
# contact sheet for quick review
thumbs = [Image.open(f).convert("RGB").resize((640, 360)) for f in pngs]
cols = 3; rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 650, rows * 370), "#1d1611")
for k, t in enumerate(thumbs):
    sheet.paste(t, ((k % cols) * 650 + 5, (k // cols) * 370 + 5))
sheet.save(ROOT / "build" / "contact-sheet.jpg", quality=85)
(ROOT / "build" / "notes.json").write_text(json.dumps(meta, indent=2))

if "--png" in sys.argv:
    sys.exit()

# PDF
imgs = [Image.open(f).convert("RGB") for f in pngs]
imgs[0].save(ROOT / "Sustainable-Happiness-Project.pdf", save_all=True, append_images=imgs[1:], resolution=144)

# PPTX: one full-bleed image per slide, speaker notes, fade transition
from pptx import Presentation
from pptx.util import Emu
from lxml import etree

prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
blank = prs.slide_layouts[6]
for f, m in zip(pngs, meta):
    s = prs.slides.add_slide(blank)
    s.shapes.add_picture(str(f), 0, 0, prs.slide_width, prs.slide_height)
    s.notes_slide.notes_text_frame.text = f"[{m['speaker']}] {m['notes']}"
    trans = etree.fromstring(
        '<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" spd="slow">'
        '<p:fade/></p:transition>')
    s._element.insert(2, trans)
prs.save(ROOT / "Sustainable-Happiness-Project.pptx")
print("built", len(pngs), "slides")
