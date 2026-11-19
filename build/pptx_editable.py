"""Editable PowerPoint of the deck: every text is a real text box, every photo a real picture,
every card / icon / badge its own movable picture, background colour blocks as the slide background.

It renders each slide in its final (export) state, then takes it apart:
  background  = slide colour + .bg blocks              -> one JPEG
  units       = each child of .fg, the HUD and speaker -> transparent PNG (text and photos hidden)
  photos      = each .ph image                          -> picture, cropped like CSS object-fit: cover
  texts       = each text block                         -> text box (font, size, colour, spacing, rotation)

Usage:  python3 build/pptx_editable.py        (needs playwright + python-pptx + pillow + fonttools + brotli)
Output: Sustainable-Happiness-Project-editable.pptx and build/pptx/fonts/*.ttf (install these to edit)
"""
import io, json, math, pathlib, re, shutil, sys
from playwright.sync_api import sync_playwright
from PIL import Image
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from lxml import etree

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORK = ROOT / "build" / "pptx"
shutil.rmtree(WORK, ignore_errors=True)
(WORK / "u").mkdir(parents=True)
DECK = (ROOT / "index.html").as_uri()
SCALE = 2                       # device pixels per CSS px for pictures
EMU = 12192000 / 1920           # EMU per CSS px (slide is 1920 px wide)
ONLY = [int(a) for a in sys.argv[1:] if a.isdigit()]

JS_PREP = r"""
() => {
  // undo the per-character headline split and the odometer columns, so text reads normally
  document.querySelectorAll('[data-odo]').forEach(el => {
    const d = [...el.querySelectorAll('.odo>span')].map(s => +s.style.getPropertyValue('--n') - 10);
    if (d.length && d.every(n => n >= 0 && n <= 9)) el.textContent = d.join('');
  });
  document.querySelectorAll('.ch').forEach(c => c.replaceWith(document.createTextNode(c.textContent)));
  document.querySelectorAll('.ln').forEach(e => e.normalize());
  const css = document.createElement('style');
  css.textContent = `
    html,body{background:transparent!important}
    *,*::before,*::after{animation-play-state:paused!important;transition:none!important;caret-color:transparent}
    body.__x *:not(.__t, .__t *, .__o){visibility:hidden!important}
    body.__x .__t, body.__x .__o{visibility:visible!important}
    body.__x .__o *{visibility:hidden!important}
    body.__x .__tx, body.__x .__tx *{color:transparent!important;-webkit-text-stroke-color:transparent!important;text-shadow:none!important;text-decoration-color:transparent!important}
    body.__x .ph .kb, body.__x .ph img{visibility:hidden!important}
    body.__bg .fg, body.__bg #hud, body.__bg .speaker, body.__bg #hint, body.__bg #cue{visibility:hidden!important}
    #hint, #cue, .eov, aside.notes{display:none!important}`;
  document.head.appendChild(css);
  const stage = document.getElementById('stage'), sr = stage.getBoundingClientRect(), k = sr.width / 1920;
  window.__k = k; window.__sr = sr;
  return {k, x: sr.left, y: sr.top};
}
"""

JS_COLLECT = r"""
() => {
  const sr = window.__sr, k = window.__k;
  const P = r => ({x: (r.left - sr.left) / k, y: (r.top - sr.top) / k, w: r.width / k, h: r.height / k});
  const vis = e => { const c = getComputedStyle(e); if (c.display === 'none' || c.visibility === 'hidden') return false;
    let o = 1; for (let a = e; a; a = a.parentElement) o *= +getComputedStyle(a).opacity; return o > 0.02; };
  const shown = e => { for (let a = e; a && a !== document.body; a = a.parentElement) if (!vis(a)) return false; return true; };
  const angle = e => { let t = 0;
    for (let a = e; a && a !== document.body; a = a.parentElement) {
      const c = getComputedStyle(a);
      if (c.transform && c.transform !== 'none') { const m = new DOMMatrix(c.transform); t += Math.atan2(m.b, m.a) * 180 / Math.PI; }
      if (c.rotate && c.rotate !== 'none') t += parseFloat(c.rotate) || 0;
    } return t; };
  const isPh = e => e.classList && e.classList.contains('ph');
  const hasPh = e => !!e.querySelector('.ph');
  const blockish = e => { const d = getComputedStyle(e).display; return d !== 'inline' && d !== 'contents'; };

  // translucent text colour -> opaque colour blended over the nearest solid background (LibreOffice drops the last glyph of alpha runs)
  const rgbaOf = s => { const m = (s || '').match(/[\d.]+/g); return m ? [+m[0], +m[1], +m[2], m[3] === undefined ? 1 : +m[3]] : null; };
  const mix = (col, e) => {
    const c = rgbaOf(col); if (!c || c[3] >= .99) return col;
    let bg = [240, 232, 216];
    for (let a = e; a; a = a.parentElement) { const b = rgbaOf(getComputedStyle(a).backgroundColor); if (b && b[3] > .5) { bg = b; break; } }
    const k = c[3], f = i => Math.round(c[i] * k + bg[i] * (1 - k));
    return `rgb(${f(0)}, ${f(1)}, ${f(2)})`;
  };
  // ---- text blocks: deepest non-inline elements whose own inline content has text ----
  const blocks = [];
  const inlineText = el => {        // runs from el's inline content (stops at block children)
    const runs = [];
    const walk = n => {
      if (n.nodeType === 3) {
        const t = n.textContent; if (!t) return;
        const p = n.parentElement, c = getComputedStyle(p);
        runs.push({t, ff: c.fontFamily, fs: parseFloat(c.fontSize), fw: +c.fontWeight || 400, it: c.fontStyle === 'italic',
                   col: mix(c.color, p), tt: c.textTransform, ls: parseFloat(c.letterSpacing) || 0, ul: c.textDecorationLine.includes('underline'),
                   ws: c.whiteSpace});
        return;
      }
      if (n.nodeType !== 1) return;
      if (n.tagName === 'BR') { runs.push({br: 1}); return; }
      if (['SVG', 'svg', 'IMG', 'STYLE', 'SCRIPT', 'ASIDE'].includes(n.tagName) || isPh(n)) return;
      if (n !== el && blockish(n)) return;
      if (!vis(n)) return;
      const cs = getComputedStyle(n), gap = e => (parseFloat(cs['margin' + e]) || 0) + (parseFloat(cs['padding' + e]) || 0);
      const sp = () => runs.push({t: ' ', ff: cs.fontFamily, fs: parseFloat(cs.fontSize), fw: +cs.fontWeight || 400, it: false, col: mix(cs.color, n), tt: 'none', ls: 0, ul: false, ws: 'pre', gap: 1});
      if (n !== el && gap('Left') > 3) sp();
      n.childNodes.forEach(walk);
      if (n !== el && gap('Right') > 3) sp();
    };
    el.childNodes.forEach(walk);
    return runs;
  };
  const textNodesOf = el => { const out = [];
    const walk = n => { if (n.nodeType === 3) { if (n.textContent.trim()) out.push(n); return; }
      if (n.nodeType !== 1 || (n !== el && blockish(n)) || n.tagName.toLowerCase() === 'svg' || isPh(n)) return;
      n.childNodes.forEach(walk); };
    el.childNodes.forEach(walk); return out; };
  const visit = el => {
    if (!vis(el) || isPh(el) || el.tagName.toLowerCase() === 'svg' || el.tagName === 'ASIDE') return;
    const tns = textNodesOf(el);
    if (tns.length) {
      const c = getComputedStyle(el), runs = inlineText(el);
      const range = document.createRange(); range.setStartBefore(tns[0]); range.setEndAfter(tns[tns.length - 1]);
      const rr = P(range.getBoundingClientRect()), er = P(el.getBoundingClientRect());
      const t0 = tns[0], i0 = Math.max(0, t0.textContent.search(/\S/)), r1 = document.createRange();
      r1.setStart(t0, i0); r1.setEnd(t0, i0 + 1); const fr = P(r1.getBoundingClientRect());
      const pl = parseFloat(c.paddingLeft) + parseFloat(c.borderLeftWidth), pr = parseFloat(c.paddingRight) + parseFloat(c.borderRightWidth);
      const pt = parseFloat(c.paddingTop) + parseFloat(c.borderTopWidth);
      const lh = c.lineHeight === 'normal' ? parseFloat(c.fontSize) * 1.2 : parseFloat(c.lineHeight);
      el.classList.add('__txc');
      blocks.push({el, runs, rr, er, fy: fr.y, fh: fr.h, ow: el.offsetWidth, oh: el.offsetHeight, pl, pr, pt, lh, ta: c.textAlign, ang: angle(el),
                   jc: c.justifyContent, disp: c.display, ws: c.whiteSpace});
    }
    [...el.children].forEach(ch => { if (blockish(ch)) visit(ch); });
  };

  // ---- units ----
  const s = document.querySelector('.slide.active');
  const roots = [...s.querySelector('.fg').children, ...document.getElementById('hud').children, ...s.querySelectorAll(':scope > .speaker')];
  const units = [];
  let uid = 0;
  const addUnit = (el, own) => {
    const id = 'u' + (uid++); el.dataset.u = id;
    const rs = [el, ...(own ? [] : el.querySelectorAll('*'))].filter(e => !isPh(e) && !e.closest('.ph')).map(e => e.getBoundingClientRect()).filter(r => r.width && r.height);
    if (!rs.length) return;
    const L = Math.min(...rs.map(r => r.left)), T = Math.min(...rs.map(r => r.top)), R = Math.max(...rs.map(r => r.right)), B = Math.max(...rs.map(r => r.bottom));
    units.push({kind: 'pic', id, own, box: P({left: L - 40 * k, top: T - 40 * k, width: R - L + 80 * k, height: B - T + 80 * k})});
  };
  const photos = [];
  const addPhoto = ph => {
    const img = ph.querySelector('.kb img, img'); if (!img || !img.naturalWidth || !shown(ph)) return;
    const r = P(ph.getBoundingClientRect()), ang = angle(ph);
    const c = getComputedStyle(img), op = c.objectPosition.split(' ');
    units.push({kind: 'photo', src: img.src, nw: img.naturalWidth, nh: img.naturalHeight, w: ph.offsetWidth, h: ph.offsetHeight,
                cx: r.x + r.w / 2, cy: r.y + r.h / 2, ang, fit: c.objectFit, op});
  };
  const split = el => {
    if (!vis(el)) return;
    if (isPh(el)) return addPhoto(el);
    if (!hasPh(el)) { addUnit(el, false); visit(el); unitsText(el); return; }
    addUnit(el, true);          // its own box (frame mat), then children in order
    const c = getComputedStyle(el);
    [...el.children].forEach(split);
  };
  const unitsText = el => {
    blocks.filter(b => !b.done && (b.el === el || el.contains(b.el))).forEach(b => { b.done = 1; units.push({kind: 'text', b}); });
  };
  roots.forEach(split);
  // serialisable
  return units.map(u => u.kind !== 'text' ? u : (() => { const b = u.b; const o = {...b}; delete o.el; o.kind = 'text'; o.id = (b.el.dataset.tx = 't' + (uid++)); return o; })());
}
"""


def rgba(s):
    m = re.match(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)", s or "")
    if not m:
        return None
    r, g, b = (int(float(m.group(i))) for i in (1, 2, 3))
    a = float(m.group(4)) if m.group(4) is not None else 1.0
    return r, g, b, a


FAMS = {}   # (family, weight) -> (pptx font name, bold)
_MET = {}


def metrics(ff):
    """(ascent, descent) in em from the font's hhea table."""
    fam = ff.split(",")[0].strip().strip('"\'')
    if fam not in _MET:
        from fontTools.ttLib import TTFont
        f = ROOT / "fonts" / f"{fam}.woff2"
        if f.exists():
            t = TTFont(f); u = t["head"].unitsPerEm
            _MET[fam] = (t["hhea"].ascent / u, -t["hhea"].descent / u)
        else:
            _MET[fam] = (0.9, 0.25)
    return _MET[fam]


def font_name(ff, fw):
    fam = ff.split(",")[0].strip().strip('"\'')
    if fam == "Anton":
        return "Anton", False
    if fam in ("Geist", "Archivo"):
        w = 400 if fw <= 450 else 500 if fw <= 550 else 600 if fw <= 650 else 700 if fw <= 750 else 800 if fw <= 850 else 900
        if w in (400, 700):
            FAMS[(fam, 400)] = 1; FAMS[(fam, 700)] = 1
            return fam, w == 700
        FAMS[(fam, w)] = 1
        return f"{fam} {WNAME[w]}", False
    return fam, fw >= 700


WNAME = {500: "Medium", 600: "SemiBold", 800: "ExtraBold", 900: "Black"}


def norm_text(runs, tt_block):
    """Collapse whitespace like CSS white-space:normal across runs; returns list of paragraphs of runs."""
    paras, cur = [], []
    for r in runs:
        if r.get("br"):
            paras.append(cur); cur = []
            continue
        t = r["t"]
        if r["ws"] not in ("pre", "pre-wrap", "pre-line", "break-spaces"):
            t = re.sub(r"[ \t\n\r\f]+", " ", t)
        t = t.replace(" ", " ")
        if r["tt"] == "uppercase":
            t = t.upper()
        elif r["tt"] == "lowercase":
            t = t.lower()
        cur.append({**r, "t": t})
    paras.append(cur)
    out = []
    for p in paras:
        # trim leading/trailing spaces of the paragraph, merge double spaces across run borders
        s = "".join(r["t"] for r in p)
        if not s.strip():
            out.append([])
            continue
        prev_space = True
        q = []
        for r in p:
            t = r["t"]
            if prev_space and not r.get("gap"):
                t = t.lstrip(" ")
            if r.get("gap") and prev_space:
                t = ""
            if t:
                q.append({**r, "t": t}); prev_space = t.endswith(" ")
        if q:
            q[-1]["t"] = q[-1]["t"].rstrip(" ")
        out.append([r for r in q if r["t"]])
    while out and not out[-1]:
        out.pop()
    while out and not out[0]:
        out.pop(0)
    return out


def add_text(slide, b):
    paras = norm_text(b["runs"], None)
    if not paras:
        return
    ang = b["ang"]
    rr, er = b["rr"], b["er"]
    ta = b["ta"]
    if b["disp"] in ("flex", "inline-flex") and b["jc"] == "center":
        ta = "center"
    if abs(ang) > 0.5:      # rotated: unrotated layout box around the element centre
        w, h = b["ow"] - b["pl"] - b["pr"], b["oh"]
        cx, cy = er["x"] + er["w"] / 2, er["y"] + er["h"] / 2
        x, y = cx - w / 2 + (b["pl"] - b["pr"]) / 2, cy - h / 2 + b["pt"]
    else:
        y = b["fy"] - (b["lh"] - b["fh"]) / 2      # top of the first CSS line box
        cl, cr = er["x"] + b["pl"], er["x"] + er["w"] - b["pr"]
        if ta in ("center", "-webkit-center"):
            x, w = cl, cr - cl
        elif ta in ("right", "end"):
            x, w = cl, rr["x"] + rr["w"] - cl
        else:
            x, w = rr["x"], max(cr - rr["x"], rr["w"])
        h = max(rr["y"] + rr["h"] - y, b["lh"])
    lines = round(max(0, rr["h"] - b["fh"]) / max(b["lh"], 1)) + 1      # CSS line boxes actually used
    nowrap = b["ws"] in ("nowrap", "pre") or lines <= len(paras)
    if nowrap and abs(ang) <= 0.5:   # one line per paragraph: anchor on the text itself, with room to spare
        slack = max(14, rr["w"] * 0.08)
        w = rr["w"] + slack
        x = rr["x"] - (slack / 2 if ta in ("center", "-webkit-center") else slack if ta in ("right", "end") else 0)
    elif nowrap:
        x, w = x - 10, w + 20
    # PowerPoint puts the baseline of an exactly-spaced line at lh*A/(A+D); CSS at half-leading + A
    r0 = paras[0][0]
    A, D = metrics(r0["ff"])
    y += (b["lh"] - (A + D) * r0["fs"]) * (0.5 - A / (A + D))
    tb = slide.shapes.add_textbox(Emu(int(x * EMU)), Emu(int(y * EMU)), Emu(int(w * EMU)), Emu(int(h * EMU)))
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = not nowrap
    tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.TOP
    if abs(ang) > 0.5:
        tb.rotation = ang
    for i, pr in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"center": PP_ALIGN.CENTER, "-webkit-center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT, "end": PP_ALIGN.RIGHT,
                       "justify": PP_ALIGN.JUSTIFY}.get(ta, PP_ALIGN.LEFT)
        p.line_spacing = Pt(b["lh"] * 0.5 * 1.0)
        for r in pr:
            run = p.add_run()
            run.text = r["t"].replace("\u25b6", "\u25b6\ufe0e")   # text-style triangle, not the emoji
            f = run.font
            name, bold = font_name(r["ff"], r["fw"])
            f.name = name
            f.size = Pt(round(r["fs"] * 0.5 * 2) / 2)
            f.bold = bold
            f.italic = r["it"]
            f.underline = r["ul"]
            c = rgba(r["col"])
            if c:
                f.color.rgb = RGBColor(*c[:3])
                if c[3] < 0.99:
                    sf = f.color._xFill if hasattr(f.color, "_xFill") else None
                    srgb = run._r.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
                    if srgb is not None:
                        a = etree.SubElement(srgb, "{http://schemas.openxmlformats.org/drawingml/2006/main}alpha")
                        a.set("val", str(int(c[3] * 100000)))
            rpr = run._r.get_or_add_rPr()
            if r["ls"]:
                rpr.set("spc", str(int(round(r["ls"] * 0.5 * 100))))
            for tag in ("latin", "ea", "cs"):
                el = rpr.find(f"{{http://schemas.openxmlformats.org/drawingml/2006/main}}{tag}")
                if el is None:
                    el = etree.SubElement(rpr, f"{{http://schemas.openxmlformats.org/drawingml/2006/main}}{tag}")
                el.set("typeface", name)


def add_photo(slide, u, cache):
    src = u["src"]
    path = pathlib.Path(re.sub(r"^file://", "", src).split("?")[0])
    from urllib.parse import unquote
    path = pathlib.Path(unquote(str(path)))
    W, H, nw, nh = u["w"], u["h"], u["nw"], u["nh"]
    pic = slide.shapes.add_picture(str(path), Emu(int((u["cx"] - W / 2) * EMU)), Emu(int((u["cy"] - H / 2) * EMU)),
                                   Emu(int(W * EMU)), Emu(int(H * EMU)))
    if u["fit"] in ("cover", "fill", ""):
        s = max(W / nw, H / nh)
        dw, dh = nw * s, nh * s

        def pos(v, free):
            v = v.strip()
            if v.endswith("%"):
                return free * float(v[:-1]) / 100
            if v.endswith("px"):
                return float(v[:-2])
            return {"left": 0, "top": 0, "center": free / 2, "right": free, "bottom": free}.get(v, free / 2)
        ox = pos(u["op"][0] if u["op"] else "50%", W - dw)
        oy = pos(u["op"][1] if len(u["op"]) > 1 else "50%", H - dh)
        pic.crop_left = -ox / dw
        pic.crop_right = (dw + ox - W) / dw
        pic.crop_top = -oy / dh
        pic.crop_bottom = (dh + oy - H) / dh
    if abs(u["ang"]) > 0.3:
        pic.rotation = u["ang"]


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    blank = prs.slide_layouts[6]
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=SCALE)
        pg.goto(DECK + "?export=1")
        meta = pg.evaluate("""() => [...document.querySelectorAll('.slide')].map(s => ({
            speaker: s.dataset.speaker, notes: (s.querySelector('.notes')?.textContent || '').trim().replace(/\\s+/g, ' ')}))""")
        for i in range(1, len(meta) + 1):
            if ONLY and i not in ONLY:
                continue
            pg.goto(f"{DECK}?export={i}")
            pg.wait_for_function("window.__ready === true", timeout=20000)
            st = pg.evaluate(JS_PREP)
            pg.wait_for_timeout(150)
            units = pg.evaluate(JS_COLLECT)
            clip0 = {"x": st["x"], "y": st["y"], "width": 1920 * st["k"], "height": 1080 * st["k"]}
            slide = prs.slides.add_slide(blank)
            # background
            pg.evaluate("document.body.classList.add('__bg')")
            bgp = WORK / f"bg{i:02d}.jpg"
            Image.open(io.BytesIO(pg.screenshot(clip=clip0))).convert("RGB").resize((1920, 1080), Image.LANCZOS).save(bgp, quality=88)
            pg.evaluate("document.body.classList.remove('__bg')")
            slide.shapes.add_picture(str(bgp), 0, 0, prs.slide_width, prs.slide_height)
            # hide every text block's glyphs for the unit renders
            pg.evaluate("""() => { document.querySelectorAll('.__txc').forEach(e => {
                e.querySelectorAll('svg').forEach(s => { const c = getComputedStyle(s).color; [s, ...s.querySelectorAll('*')].forEach(k => k.style.setProperty('color', c, 'important')); }); e.classList.add('__tx'); });
                document.body.classList.add('__x'); }""")
            n_pic = n_txt = n_ph = 0
            for u in units:
                if u["kind"] == "pic":
                    cls = "__o" if u["own"] else "__t"
                    pg.evaluate(f"""() => {{ document.querySelectorAll('.__t,.__o').forEach(e => e.classList.remove('__t','__o'));
                        document.querySelector('[data-u="{u['id']}"]').classList.add('{cls}'); }}""")
                    bx = u["box"]
                    x0, y0 = max(0, bx["x"]), max(0, bx["y"])
                    x1, y1 = min(1920, bx["x"] + bx["w"]), min(1080, bx["y"] + bx["h"])
                    if x1 - x0 < 1 or y1 - y0 < 1:
                        continue
                    clip = {"x": st["x"] + x0 * st["k"], "y": st["y"] + y0 * st["k"], "width": (x1 - x0) * st["k"], "height": (y1 - y0) * st["k"]}
                    im = Image.open(io.BytesIO(pg.screenshot(clip=clip, omit_background=True))).convert("RGBA")
                    bb = im.getchannel("A").point(lambda a: 255 if a > 6 else 0).getbbox()
                    if not bb:
                        continue
                    im = im.crop(bb)
                    f = WORK / "u" / f"{i:02d}-{u['id']}.png"
                    im.save(f, optimize=True)
                    px = x0 + bb[0] / SCALE
                    py = y0 + bb[1] / SCALE
                    slide.shapes.add_picture(str(f), Emu(int(px * EMU)), Emu(int(py * EMU)),
                                             Emu(int(im.width / SCALE * EMU)), Emu(int(im.height / SCALE * EMU)))
                    n_pic += 1
                elif u["kind"] == "photo":
                    add_photo(slide, u, None); n_ph += 1
                else:
                    add_text(slide, u); n_txt += 1
            pg.evaluate("document.body.classList.remove('__x')")
            m = meta[i - 1]
            slide.notes_slide.notes_text_frame.text = f"[{m['speaker']}] {m['notes']}"
            trans = etree.fromstring('<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" spd="med"><p:fade/></p:transition>')
            slide._element.insert(2, trans)
            print(f"slide {i:02d}: {n_txt} text boxes, {n_ph} photos, {n_pic} pictures", flush=True)
        b.close()
    out = ROOT / ("Sustainable-Happiness-Project-editable.pptx" if not ONLY else "build/pptx/test.pptx")
    prs.save(out)
    print("saved", out, f"{out.stat().st_size / 1e6:.1f} MB")
    fonts()


def fonts():
    """Static TTFs PowerPoint can use: Anton, plus Geist/Archivo at each weight the deck uses."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    out = WORK / "fonts"
    out.mkdir(exist_ok=True)
    t = TTFont(ROOT / "fonts" / "Anton.woff2"); t.flavor = None; t.save(out / "Anton-Regular.ttf")
    for fam, w in sorted(FAMS) or [("Geist", 400), ("Geist", 700)]:
        v = TTFont(ROOT / "fonts" / f"{fam}.woff2")
        axes = {"wght": w}
        if fam == "Archivo":
            axes["wdth"] = 100
        f = instantiateVariableFont(v, axes)
        f.flavor = None
        if w in (400, 700):
            family, sub = fam, ("Regular" if w == 400 else "Bold")
        else:
            family, sub = f"{fam} {WNAME[w]}", "Regular"
        nm = f["name"]
        for rec in list(nm.names):
            if rec.nameID in (16, 17, 21, 22, 25):
                nm.removeNames(nameID=rec.nameID)
        nm.setName(family, 1, 3, 1, 0x409); nm.setName(sub, 2, 3, 1, 0x409)
        nm.setName(f"{family} {sub}".replace(" Regular", "") if sub == "Regular" else f"{family} {sub}", 4, 3, 1, 0x409)
        nm.setName(f"{family}-{sub}".replace(" ", ""), 6, 3, 1, 0x409)
        nm.setName(f"{family} {sub}", 3, 3, 1, 0x409)
        f["OS/2"].usWeightClass = w if w in (400, 700) else 400
        f["OS/2"].fsSelection = (f["OS/2"].fsSelection & ~0b1100001) | (0b100000 if w == 700 else 0b1000000)
        f["head"].macStyle = 1 if w == 700 else 0
        f.save(out / f"{family.replace(' ', '')}-{sub}.ttf")
    print("fonts:", ", ".join(sorted(x.name for x in out.glob("*.ttf"))))


if __name__ == "__main__":
    build()
