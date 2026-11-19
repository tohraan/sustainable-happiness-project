"""Build the game version of the deck from build/index.before-game.html -> index.html."""
import pathlib, re
ROOT = pathlib.Path.home() / "sustainable-happiness-project"
old = (ROOT / "build/index.before-game.html").read_text()

# ---------------------------------------------------------------- old pieces
css_old = old[old.index("<style>") + 7: old.index("</style>")]
css_old = css_old.replace(".k{font:800 15px/1.2", ".slide .k{font:800 15px/1.2")
css_old = css_old.replace(".orbit{position:absolute;left:740px;top:480px", ".orbit{position:absolute;left:120px;top:440px")
symbols = old[old.index('<svg width="0" height="0"'): old.index("</defs></svg>")]
symbols += '''  <symbol id="i-scale" viewBox="0 0 64 64"><path d="M32 8v48M20 58h24M8 16h48"/><path d="M8 16L2 34M8 16l6 18M56 16l-6 18M56 16l6 18"/><path d="M1 34h14a7 6 0 0 1-14 0z" style="fill:var(--gold)"/><path d="M49 34h14a7 6 0 0 1-14 0z" style="fill:var(--sky)"/><circle cx="32" cy="9" r="4" style="fill:var(--ink)"/></symbol>
  <symbol id="i-lock" viewBox="0 0 64 64"><path d="M20 30v-9a12 12 0 0 1 24 0v9"/><rect x="12" y="29" width="40" height="29" rx="4" style="fill:var(--ink)"/><circle cx="32" cy="42" r="4" style="fill:var(--cream);stroke:none"/></symbol>
  <symbol id="i-check" viewBox="0 0 64 64"><path d="M12 34l13 13 27-29" style="stroke-width:9"/></symbol>
</defs></svg>'''
presenter = old[old.index('<div id="presenter">'): old.index("<script>")]


def sec(name):
    """Inner markup of an old section, found by its comment banner."""
    i = old.index(name)
    a = old.index(">", old.index("<section", i)) + 1
    return old[a: old.index("</section>", a)]


# ---------------------------------------------------------------- helpers
LV = {
    1: dict(key="blood", name="Blood camp", c="var(--blood)", t="var(--cream)", icon="i-drop", hrs=2, cu="cuUp", spk="Vedansh",
            date="01 Oct 2026", org="MAD Club, BITS Pilani Dubai × Dubai Health"),
    2: dict(key="langar", name="Langar seva", c="var(--saffron)", t="var(--ink)", icon="i-bowl", hrs=1, cu="cuCirc", spk="Vedansh",
            date="14 Nov 2026", org="Guru Nanak Darbar Gurudwara, Jebel Ali"),
    3: dict(key="run", name="Unity Run", c="var(--green)", t="var(--cream)", icon="i-medal", hrs=8, cu="cuSide", spk="Tohraan",
            date="15 Nov 2026", org="FittGROUP · Dubai Design District"),
}
STEPN = ["Start", "Did", "Impact", "Learned", "Research", "Evidence", "Summary"]


def open_sec(l, st, title=None, extra=""):
    L = LV[l]
    return (f'<section class="slide m2" data-speaker="{L["spk"]}" data-title="{title or L["name"] + " · " + STEPN[st]}" '
            f'data-level="{l}" data-step="{st}" style="--cc:{L["c"]};--cu:{L["cu"]}{extra}">')


# Every photo frame holds a pair: Vedansh's genuine photo on top, Tohraan's geotagged image below.
# Blood has no images of Tohraan, so both halves there are Vedansh's.
T = "placeholders/t-"
PAIRS = {
    "blood-intro": ("blood-4", "blood-2"),   "blood-did": ("blood-1", "blood-3"),
    "blood-impact": ("blood-2", "blood-4"),  "blood-learned": ("blood-3", "blood-1"),
    "blood-research": ("blood-4", "blood-2"),
    "langar-intro": ("langar-3", T + "langar-4"), "langar-did": ("langar-1", T + "langar-2"),
    "langar-impact": ("langar-2", T + "langar-3"), "langar-learned": ("langar-3", T + "langar-1"),
    "langar-research": ("langar-1", T + "langar-2"),
    "run-intro": ("run-1", T + "run-1"), "run-did": ("run-6", T + "run-4"), "run-impact": ("run-8", T + "run-2"),
    "run-learned": ("run-7", T + "run-5"), "run-research": ("run-9", T + "run-3"),
}


def pair(slot, top, bot, w, h, gap=10):
    hh = (h - gap) // 2
    return (f'<div class="ph" data-slot="{slot}" data-src="images/{top}" data-label="images/{slot}.jpg" style="width:{w}px;height:{hh}px"></div>'
            f'<div class="ph" data-slot="{slot}-t" data-src="images/{bot}" data-label="images/{slot}-t.jpg" style="width:{w}px;height:{hh}px;margin-top:{gap}px"></div>')


def frame(slot, src, tag, anim, d=".3s", more="", tagst=""):
    return (f'<div class="frame a {anim}" style="left:1272px;top:44px;--d:{d}{more}">{pair(slot, *PAIRS[slot], 486, 864)}'
            f'<div class="tag" style="{tagst}">{tag}</div></div>')


def notes(t):
    return f'  <aside class="notes">{t}</aside>\n</section>\n'


def strip_old(body):
    """Remove the old per-slide tracker and old frame; content is reused."""
    body = re.sub(r'\s*<div class="tracker"[^>]*></div>', "", body)
    body = re.sub(r'\s*<div class="frame a [^"]*" style="left:(110|1272)px;top:44px;[^"]*"><div class="ph".*?</div></div>', "", body, count=1)
    body = re.sub(r'\s*<aside class="notes">.*?</aside>', "", body, flags=re.S)
    return body


def shift(body, dx=-620, dy=0, minx=700):
    def f(m):
        x = int(m.group(1))
        return f"left:{x + dx if x >= minx else x}px" if x >= minx else m.group(0)
    body = re.sub(r"left:(\d+)px", f, body)
    if dy:
        body = re.sub(r"top:(\d+)px", lambda m: f"top:{int(m.group(1)) + dy}px", body)
    return body


def tap(body, marker, g, cue=None):
    """Add data-tap to the first tag that contains `marker` (searching from the tag start)."""
    i = body.index(marker)
    s = body.rindex("<", 0, i)
    j = s + 1
    while body[j] not in " >":
        j += 1
    attr = f' data-tap="{g}"' + (f' data-cue="{cue}"' if cue else "")
    return body[:j] + attr + body[j:]


S = []  # sections in play order

# ================================================================ TITLE
t = sec("01 TITLE")
t = re.sub(r'\s*<aside class="notes">.*?</aside>', "", t, flags=re.S)
t = re.sub(r'<h1 class="abs disp" style="left:112px;top:180px;font-size:212px">.*?</h1>',
           '<h1 class="abs disp" style="left:112px;top:190px;font-size:178px">'
           '<span class="ln" style="--d:.1s"><span>Happiness</span></span>'
           '<span class="ln" style="--d:.22s"><span>through</span></span>'
           '<span class="ln" style="--d:.34s"><span style="color:var(--blood)">volunteering.</span></span></h1>', t, flags=re.S)
t = t.replace("A blood drive · a langar kitchen · a pre-dawn unity run", "11 hours · a blood donation camp · langar seva · the Unity Run")
t += '\n  <div class="abs a land" style="left:1590px;top:870px;--d:1.7s"><button class="go" data-act="next" style="background:var(--cream);color:var(--ink);--gc:var(--ink)">Start ▶</button></div>\n'
S.append('<section class="slide m2" data-speaker="Vedansh" data-title="Happiness through volunteering" style="--cc:var(--ink);--cu:cuUp">'
         + t + notes("Good morning. I'm Vedansh, and this is Tohraan. Our project: happiness through volunteering."))

# ================================================================ MAP (4 visits)
NODES = [(330, 690, "i-drop", "Activity 1", "Blood camp", "01 Oct · 2 hrs", "var(--blood)"),
         (770, 520, "i-bowl", "Activity 2", "Langar seva", "14 Nov · 1 hr", "var(--saffron)"),
         (1210, 700, "i-medal", "Activity 3", "Unity Run", "15 Nov · 8 hrs", "var(--green)"),
         (1640, 500, "i-scale", "Reflection", "Class vs reality", "what we re-examined", "var(--ink)")]
SEGS = ["M40 900C140 900 230 690 330 690", "M330 690C500 690 600 520 770 520",
        "M770 520C940 520 1040 700 1210 700", "M1210 700C1380 700 1470 500 1640 500"]
TAIL = "M1640 500C1740 500 1800 380 1880 380"
MAPS = [
    ("Vedansh", "Three activities.", "Eleven hours.", "var(--blood)", "Overview · where our 11 hours went",
     "Eleven hours across three activities: a blood camp, langar seva and a community run."),
    ("Vedansh", "Blood camp", "done.", "var(--blood)", "2 of 11 hours · next: langar seva", "That's two hours. Next, langar seva."),
    ("Vedansh", "Langar seva", "done.", "var(--saffron)", "3 of 11 hours · next: Unity Run",
     "Three hours so far. Over to Tohraan for the Unity Run."),
    ("Tohraan", "Eleven hours", "complete.", "var(--green)", "11 of 11 hours · next: class vs reality",
     "That's all three activities. Finally, where class and reality disagreed."),
]


def map_sec(k):
    spk, h1, h2, hc, lbl, note = MAPS[k]
    o = [f'<section class="slide m2" data-speaker="{spk}" data-title="Overview · {"start" if k == 0 else h1 + " " + h2}" data-map="{k}" style="--cc:var(--ink);--cu:cuUp">']
    o.append(f'  <div class="abs lbl a fade" style="left:120px;top:150px;color:var(--ink-2);--d:.05s">{lbl}</div>')
    o.append(f'  <h2 class="abs disp" style="left:116px;top:196px;font-size:116px"><span class="ln" style="--d:.1s"><span>{h1}</span></span>'
             f'<span class="ln" style="--d:.22s"><span style="color:{hc}">{h2}</span></span></h2>')
    p = ['  <svg class="abs" style="left:0;top:0;width:1920px;height:1080px" viewBox="0 0 1920 1080" fill="none" stroke-linecap="round">']
    for d in SEGS + [TAIL]:
        p.append(f'    <path d="{d}" stroke="rgba(28,24,20,.35)" stroke-width="7" stroke-dasharray="1 22"/>')
    for i, d in enumerate(SEGS):
        if i < k:
            p.append(f'    <path d="{d}" stroke="var(--ink)" stroke-width="12"/>')
        elif i == k:
            p.append(f'    <path class="draw" pathLength="1" style="--d:.5s;--t:1.3s" d="{d}" stroke="var(--ink)" stroke-width="12"/>')
    p.append("  </svg>")
    o += p
    o.append(f'  <div class="mtrav" style="offset-path:path(\'{SEGS[k]}\');--d:.5s"></div>')
    for i, (x, y, ic, l1, l2, l3, c) in enumerate(NODES):
        st = "done" if i < k else "cur" if i == k else "locked"
        d = 1.2 + i * .12 if i != k else 1.15
        if i == k:
            o.append(f'  <div class="loop ripple" style="left:{x - 90}px;top:{y - 90}px;width:180px;height:180px;--rc:{c};--lp:2.2s"></div>')
        inner = f'<div class="badge"><svg viewBox="0 0 64 64"><use href="#{ic}"/></svg></div>'
        if st == "done":
            inner += f'<b class="ok" style="--nc:{c}"><svg viewBox="0 0 64 64"><use href="#i-check"/></svg></b>'
        if st == "locked":
            inner += '<b class="lk"><svg viewBox="0 0 64 64"><use href="#i-lock"/></svg></b>'
        o.append(f'  <div class="node a land {st}" data-act="enter" data-lv="{i + 1}" style="left:{x}px;top:{y}px;--d:{.3 + i * .1 if i != k else 2.6}s">{inner}</div>')
        o.append(f'  <div class="nlab a fade" style="left:{x}px;top:{y + 112}px;--d:{.5 + i * .1}s"><div class="lbl" style="color:{c if st != "locked" else "rgba(28,24,20,.45)"}">{l1}</div>'
                 f'<div class="disp" style="font-size:44px;margin-top:6px;{"color:rgba(28,24,20,.45)" if st == "locked" else ""}">{l2}</div><div class="cite">{l3}</div></div>')
        if i == k:
            o.append(f'  <div class="abs a hang" style="left:{x - 110}px;top:{y - 178}px;--d:3s"><span class="flag">Up next ▼</span></div>')
    o.append(notes(note))
    return "\n".join(o)


# ================================================================ LEVEL STEPS
def intro(l, lines, fs, mission, sub, photo, tag):
    L = LV[l]
    o = [open_sec(l, 0)]
    o.append(f'  <div class="blk a wipe-l" style="left:-20px;top:-20px;width:1250px;height:1120px;background:{L["c"]}"></div>')
    o.append("  " + frame(f'{L["key"]}-intro', photo, tag, "zoom", ".45s", tagst="--tc:var(--ink)"))
    o.append(f'  <div class="abs lbl a fade" style="left:120px;top:150px;color:{L["t"]};--d:.1s">Activity {l} of 3</div>')
    o.append(f'  <h1 class="abs disp" style="left:112px;top:200px;font-size:{fs}px;color:{L["t"]}">'
             + "".join(f'<span class="ln" style="--d:{.15 + i * .12:.2f}s"><span>{x}</span></span>' for i, x in enumerate(lines)) + "</h1>")
    chip = 'class="pb" style="--c:var(--cream);color:var(--ink);padding:12px 18px 10px"'
    o.append(f'  <div class="abs a rise" style="left:120px;top:690px;display:flex;gap:12px;--d:.75s"><span {chip}><span class="lbl" style="font-size:20px">{L["date"]}</span></span>'
             f'<span {chip}><span class="lbl" style="font-size:20px">{L["hrs"]} hour{"s" if L["hrs"] > 1 else ""}</span></span>'
             f'<span {chip}><span class="lbl" style="font-size:20px">{L["org"]}</span></span></div>')
    o.append(f'  <p class="abs body a fade" style="left:120px;top:{770 if sub else 772}px;width:1040px;font-size:30px;font-weight:500;color:{L["t"]};--d:.95s"><b>Our role:</b> {mission}</p>')
    if sub:
        o.append(f'  <p class="abs body a fade" style="left:120px;top:826px;width:1040px;font-size:21px;color:{L["t"]};--d:1.05s">{sub}</p>')
    o.append(f'  <div class="abs a land" style="left:120px;top:{900 if sub else 885}px;--d:1.2s"><button class="go" data-act="next" style="background:var(--ink);color:var(--cream);--gc:var(--cream)">What we did ▶</button></div>')
    return "\n".join(o) + "\n"


def evidence(l, n, photos, head, ph_w, ph_h, top, x0, gap, certs=None):
    """Photos (and, only when certs are given, the genuine certificates in an envelope)."""
    L = LV[l]
    o = [open_sec(l, 5)]
    pg = 2 if certs else 1  # tap group of the photo pile
    o.append(f'  <div class="abs lbl a fade" style="left:120px;top:150px;color:var(--ink-2);--d:.05s">Evidence · {"certificates &amp; photos" if certs else "photos from the day"}</div>')
    o.append(f'  <h2 class="abs disp" style="left:116px;top:196px;font-size:96px"><span class="ln" style="--d:.1s"><span>{head[0]} <span style="color:{L["c"]}">{head[1]}</span></span></span></h2>')
    if certs:
        o.append(f'  <div class="abs a deal" style="left:120px;top:470px;--d:.35s;--fx:0px;--fr:-8deg"><div class="env" data-untap="1" style="--ec:{L["c"]}">'
                 f'<svg class="flap" viewBox="0 0 400 150" preserveAspectRatio="none"><path d="M0 0H400L200 140Z" fill="#B48E55" stroke="var(--ink)" stroke-width="5" stroke-linejoin="round"/></svg>'
                 f'<b class="seal"><svg viewBox="0 0 64 64"><use href="#{L["icon"]}"/></svg></b><div class="disp" style="font-size:44px">Certificates</div><small>Tap to open</small></div></div>')
        for k, (slot, lab, w, h, top_c, *src) in enumerate(certs):
            o.append(f'  <div class="frame a from-b" data-tap="1" style="left:120px;top:{top_c}px;--d:{.15 + k * .15:.2f}s"><div class="ph contain cert" data-slot="{slot}" data-src="images/{src[0] if src else slot}" '
                     f'data-label="{lab} · images/{slot}.jpg" style="width:{w}px;height:{h}px"></div></div>')
    # photo pile -> dealt grid
    fw, fh = ph_w + 34, ph_h + 34
    total = n * fw + (n - 1) * gap
    cx, cy = x0 + total / 2, top + fh / 2
    o.append(f'  <div class="abs a deal" style="left:{cx - 150:.0f}px;top:{cy - 210:.0f}px;--d:.5s;--fx:200px;--fr:10deg"><div class="pile" data-untap="{pg}">'
             f'<i></i><i></i><i><span class="badge rel" style="--s:110px;--sh:5px"><svg viewBox="0 0 64 64"><use href="#{L["icon"]}"/></svg></span>'
             f'<span class="disp" style="font-size:64px;margin-top:22px">{2 * n} photos</span><small>Tap to show</small></i></div></div>')
    for i, src in enumerate(photos):
        x = x0 + i * (fw + gap)
        fx, fy = cx - (x + fw / 2), cy - (top + fh / 2)
        r = [-2.5, 1.5, -1, 2, -1.5][i]
        o.append(f'  <div class="frame a corner" data-tap="{pg}"{f' data-cue="{cx:.0f},{cy:.0f}"' if i == 0 else ''} style="left:{x:.0f}px;top:{top}px;--d:{i * .12:.2f}s;--fx:{fx:.0f}px;--fy:{fy:.0f}px;--fr:{r * 4}deg;rotate:{r}deg">'
                 + pair(f'{L["key"]}-ev{i + 1}', *src, ph_w, ph_h) + '</div>')
    return "\n".join(o) + "\n"


def summary(l, rows):
    L = LV[l]
    tot = sum(LV[k]["hrs"] for k in range(1, l + 1))
    o = [open_sec(l, 6, f'{L["name"]} · Summary')]
    o.append(f'  <div class="blk a wipe-l" style="left:1240px;top:-20px;width:700px;height:1120px;background:{L["c"]}"></div>')
    o.append(f'  <div class="abs lbl a fade" style="left:120px;top:150px;color:var(--ink-2);--d:.05s">Activity {l} of 3 · summary</div>')
    o.append(f'  <h2 class="abs disp" style="left:116px;top:196px;font-size:120px"><span class="ln" style="--d:.1s"><span>{L["name"]},</span></span>'
             f'<span class="ln" style="--d:.22s"><span style="color:{L["c"]}">at a glance.</span></span></h2>')
    o.append('  <div class="abs" style="left:120px;top:448px;width:1060px">')
    for i, (k, v, cite) in enumerate(rows):
        c = f"<small>{cite}</small>" if cite else ""
        o.append(f'    <div class="srow a from-l" style="--d:{.55 + i * .14:.2f}s;--rc:{L["c"] if i % 2 == 0 else "var(--ink)"}"><b>{k}</b><span>{v}{c}</span></div>')
    o.append("  </div>")
    o.append(f'  <div class="loop ripple" style="left:1440px;top:150px;width:300px;height:300px;--rc:{L["t"]};--lp:3s"></div>')
    o.append(f'  <div class="badge a stamp" style="--s:300px;left:1440px;top:150px;--d:.45s;--r:-6deg"><svg viewBox="0 0 64 64"><use href="#{L["icon"]}"/></svg></div>')
    o.append(f'  <b class="ok a stamp" style="left:1680px;top:130px;width:110px;height:110px;--nc:var(--ink);--d:.9s;--r:-10deg"><svg viewBox="0 0 64 64"><use href="#i-check"/></svg></b>')
    o.append(f'  <div class="abs disp a land" style="left:1240px;width:700px;text-align:center;top:500px;font-size:170px;color:{L["t"]};--d:1.1s">{L["hrs"]} hr{"s" if L["hrs"] > 1 else ""}</div>')
    o.append(f'  <div class="abs lbl a fade" style="left:1240px;width:700px;text-align:center;top:680px;color:{L["t"]};--d:1.3s">Running total · {tot} of 11 hours</div>')
    o.append('  <div class="abs a land" style="left:1415px;top:790px;--d:1.5s"><button class="go" data-act="next" style="background:var(--ink);color:var(--cream);--gc:var(--cream)">Overview ▶</button></div>')
    return "\n".join(o) + "\n"


def cardback(left, top, w, h, label, g, tall=False, qc="var(--gold)"):
    cls = "cardback tall" if tall else "cardback"
    return (f'  <div class="abs a flip" style="left:{left}px;top:{top}px;--d:{.5 + g * .15:.2f}s"><div class="{cls}" data-untap="{g}" style="width:{w}px;height:{h}px">'
            f'<span class="q" style="color:{qc}">?</span><div><div class="lbl">{label}</div><small>Tap to reveal</small></div></div></div>\n')


def slot(left, top, w, h, label, g):
    return f'  <div class="abs a fade" style="left:{left}px;top:{top}px;--d:.6s"><div class="slotb" data-untap="{g}" style="width:{w}px;height:{h}px"><b>?</b>{label}</div></div>\n'


# ---------------- BLOOD
def blood_did():
    o = [open_sec(1, 1)]
    o.append('''  <div class="blk a wipe-u" style="left:1180px;top:-20px;width:760px;height:1120px;background:var(--blood)"></div>''')
    o.append("  " + frame("blood-did", "blood-2", "At the camp", "from-b", ".45s", tagst="--tc:var(--ink)"))
    o.append('''  <div class="abs lbl a fade" style="left:120px;top:150px;color:var(--ink-2);--d:.1s">What did we do?</div>
  <h2 class="abs disp" style="left:116px;top:196px;font-size:112px">
    <span class="ln sd" style="--d:.15s"><span>Every donor,</span></span>
    <span class="ln sd" style="--d:.27s"><span style="color:var(--blood)">form to refreshments.</span></span>
  </h2>
  <div class="abs lbl a fade" style="left:120px;top:470px;color:var(--ink-2);font-size:20px;--d:.5s">The donor's path · we helped fellow volunteers donate, step by step</div>
  <svg class="abs" style="left:120px;top:520px;width:1060px;height:120px" viewBox="0 0 1060 120"><g fill="none" stroke="var(--ink)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
    <path data-tap="2" class="draw" pathLength="1" style="--d:0s;--t:.35s" d="M140 60h100m-16-14 16 14-16 14"/>
    <path data-tap="3" class="draw" pathLength="1" style="--d:0s;--t:.35s" d="M405 60h100m-16-14 16 14-16 14"/>
    <path data-tap="4" class="draw" pathLength="1" style="--d:0s;--t:.35s" d="M670 60h100m-16-14 16 14-16 14"/></g></svg>
  <div class="loop cell" data-tap="4" style="left:166px;top:566px"></div>
  <div class="loop ripple" data-tap="1" style="left:120px;top:520px;width:120px;height:120px;--ld:0s"></div>
  <div class="loop ripple" data-tap="2" style="left:385px;top:520px;width:120px;height:120px;--ld:1.07s"></div>
  <div class="loop ripple" data-tap="3" style="left:650px;top:520px;width:120px;height:120px;--ld:2.13s;--rc:var(--blood)"></div>
  <div class="loop ripple" data-tap="4" style="left:915px;top:520px;width:120px;height:120px;--ld:3.2s"></div>
  <div class="badge a land" data-tap="1" style="--s:120px;left:120px;top:520px;--d:0s"><svg viewBox="0 0 64 64"><use href="#i-form"/></svg></div>
  <div class="badge a land" data-tap="2" style="--s:120px;left:385px;top:520px;--d:.3s"><svg viewBox="0 0 64 64"><use href="#i-vitals"/></svg><svg class="ecg" viewBox="0 0 64 64"><path class="loop" pathLength="1" style="--ld:.3s" d="M8 31h13l4-8 6 16 5-12 3 4h17"/></svg></div>
  <div class="badge a land" data-tap="3" style="--s:120px;left:650px;top:520px;--d:.3s;background:var(--blood)"><svg viewBox="0 0 64 64" style="--blood:#F8F1E2;--cream:#C9302C"><use href="#i-drop"/></svg></div>
  <div class="badge a land" data-tap="4" style="--s:120px;left:915px;top:520px;--d:.3s"><svg viewBox="0 0 64 64"><use href="#i-cup"/></svg></div>
  <div class="abs a rise" data-tap="1" style="left:120px;top:670px;width:236px;--d:.2s"><div class="disp" style="font-size:34px">1 · Forms</div><p class="body" style="font-size:20px;margin-top:6px">helped donors fill in the registration and screening forms</p></div>
  <div class="abs a rise" data-tap="2" style="left:385px;top:670px;width:236px;--d:.5s"><div class="disp" style="font-size:34px">2 · Vitals</div><p class="body" style="font-size:20px;margin-top:6px">guided them between the check-up and vitals booths</p></div>
  <div class="abs a rise" data-tap="3" style="left:650px;top:670px;width:236px;--d:.5s"><div class="disp" style="font-size:34px;color:var(--blood)">3 · Donate</div><p class="body" style="font-size:20px;margin-top:6px">we <b>donated too</b>, both of us, between shifts</p></div>
  <div class="abs a rise" data-tap="4" style="left:915px;top:670px;width:236px;--d:.5s"><div class="disp" style="font-size:34px">4 · Refuel</div><p class="body" style="font-size:20px;margin-top:6px">ran post-donation refreshments while donors rested</p></div>
  <p class="abs body a fade" data-tap="4" style="left:120px;top:850px;width:1040px;font-size:22px;color:var(--ink-2);--d:.9s">Dubai Health's blood service runs on <b style="color:var(--ink)">voluntary, unpaid donors</b>, like every one we walked through.</p>''')
    o.append(notes("Our job was the donor's whole journey. We helped donors fill in the forms, guided them to the check-up booths, and looked after them with refreshments afterwards. We both donated as well."))
    return "\n".join(o)


def blood_impact():
    b = strip_old(sec("04 BLOOD · 02 IMPACT"))
    b = tap(b, 'd="M200 140C330 140 330 40 450 40"/>', 1, "560,560")
    b = b.replace('<path class="draw" pathLength="1" style="--d:1.1s', '<path data-tap="1" class="draw" pathLength="1" style="--d:1.1s')
    b = b.replace('<path class="draw" pathLength="1" style="--d:1.2s', '<path data-tap="1" class="draw" pathLength="1" style="--d:1.2s')
    b = b.replace('<g class="a land"', '<g data-tap="1" class="a land"').replace('<g class="a fade"', '<g data-tap="1" class="a fade"')
    b = b.replace('<div class="loop flow"', '<div data-tap="1" class="loop flow"')
    b = b.replace('<div class="abs a rise" style="left:120px;top:760px', '<div class="abs a rise" data-tap="2" style="left:120px;top:760px')
    b = b.replace('<div class="abs a rise" style="left:680px;top:760px', '<div class="abs a rise" data-tap="2" style="left:680px;top:760px')
    b = b.replace('<span data-odo style="--d:1.9s">', '<span data-odo style="--d:2.95s">')
    b = b.replace('<span>1 donation.</span>', '<span>Every donor.</span>')
    b = b.replace('<span>Up to <span style="color:var(--blood)">3 patients.</span></span>', '<span>Up to <span style="color:var(--blood)">3 patients each.</span></span>')
    b = b.replace('<div class="k">Our 2 donations</div><div class="disp" style="font-size:96px;margin-top:6px;color:var(--blood)">Up to 6</div><p class="body" style="font-size:21px;margin-top:6px">patients helped, since each unit splits three ways.</p>',
                  '<div class="k">Every donor we helped through</div><div class="disp" style="font-size:96px;margin-top:6px;color:var(--blood)">&times;3</div><p class="body" style="font-size:21px;margin-top:6px">Each unit splits three ways, so a smoother camp means more patients helped, not just our 2 donations.</p>')
    return (open_sec(1, 2) + "\n  " + frame("blood-impact", "blood-3", "Dubai Health", "fall", ".25s", ";--r:1.5deg", "--tc:var(--blood)") + b
            + notes("One donation splits into red cells, plasma and platelets, helping up to three patients. That counts for every donor we helped, not just our two. And the WHO calls unpaid volunteers the safest source."))


def blood_learned():
    b = strip_old(sec("05 BLOOD · 03 LEARNED"))
    b = shift(b)
    b = b[: b.index('<div class="lcard')]  # keep label + headline, rebuild the cards
    C = [("var(--gold)", "ic-spark", "i-spark", "Most surprising", "Honest reassurance",
          "First-timers were nervous at the forms desk. Having just donated ourselves, we could tell them exactly what it felt like, and that calmed them more than any leaflet."),
         ("var(--ink)", "ic-breathe", "i-mountain", "Most challenging", "Our own nerves",
          "We had to settle our own nerves about the needle, then go straight back to guiding donors between the forms desk and the check-up booths."),
         ("var(--blood)", "ic-sway", "i-sprout", "Most rewarding", "The whole journey",
          "Seeing donors we had helped with their forms reach the refreshments table. Our 2 donations counted, and so did every donor we helped get there.")]
    Y = [410, 592, 774]
    for g, (pc, ic, use, k, big, tk) in enumerate(C, 1):
        b += (f'  <div class="lcard a flip" data-tap="{g}" style="left:120px;top:{Y[g - 1]}px;height:168px;--pc:{pc};--d:.15s"><div class="badge rel" style="--s:96px;--sh:5px">'
              f'<svg class="loop {ic}" viewBox="0 0 64 64"><use href="#{use}"/></svg></div><div><div class="k">{k}</div><div class="big">{big}</div><p class="tk">{tk}</p></div></div>\n')
    backs = "".join(cardback(120, y, 1060, 168, lab, g) for g, (y, lab) in enumerate(zip(Y, ["Most surprising", "Most challenging", "Most rewarding"]), 1))
    return (open_sec(1, 3) + "\n  " + frame("blood-learned", "blood-1", "At the camp", "wipe", ".2s") + "\n" + backs + b
            + notes("The surprise: because we had just donated, we could reassure nervous first-timers honestly. The challenge was settling our own nerves and going straight back to guiding donors. The reward was the whole journey: our two donations, and every donor we helped from form to refreshments."))


def scard(left, top, g, pc, ic, use, hd, big, tk, cite, us, uc="", fx="300px", fr="-10deg"):
    u = f' style="--uc:{uc}"' if uc else ""
    return (f'  <div class="scard a deal" data-tap="{g}" style="left:{left}px;top:{top}px;height:470px;--pc:{pc};--fx:{fx};--fr:{fr};--d:.15s"><div class="hd"><svg class="loop {ic}" viewBox="0 0 64 64"><use href="#{use}"/></svg>{hd}</div>'
            f'<div class="bd"><div class="big">{big}</div><div class="cite">{cite}</div><p class="tk">{tk}</p><p class="us"{u}><b>Us</b>{us}</p></div></div>\n')


def blood_research():
    b = strip_old(sec("06 BLOOD · 04 RESEARCH"))
    b = b[: b.index('<div class="loop warm"')]
    b += '  <div data-tap="1" class="loop warm" style="left:30px;top:350px;width:695px;height:620px"></div>\n'
    b += scard(120, 425, 1, "var(--blood)", "ic-beat", "i-kind", "Acts of kindness", "Warm glow",
               "In a study of blood donors, the good feeling of giving (the warm glow) explained why people donate better than pure concern for others did.",
               "<b>Ferguson et al. (2012)</b> · Transfusion",
               "We donated, then spent two hours helping others donate. The glow lasted the whole session, not just our minutes in the chair.")
    b += scard(665, 425, 2, "var(--ink)", "ic-breathe", "i-breath", "Managing stress", "Stress buffer",
               "In a 14-day diary study, on days people helped others more, everyday stress hit their mood less.",
               "<b>Raposa, Laws &amp; Ansell (2016)</b> · Clin. Psych. Science",
               "Guiding nervous donors gave our own pre-needle nerves somewhere to go. Helping turned waiting into calm.", "var(--blood)", "-100px", "8deg")
    slots = slot(120, 425, 515, 470, "Study 1 · Acts of kindness", 1) + slot(665, 425, 515, 470, "Study 2 · Managing stress", 2)
    return (open_sec(1, 4) + "\n  " + frame("blood-research", "blood-2", "Dubai Health camp", "deal", ".15s", ";--fx:-260px;--fr:12deg", "--tc:var(--blood)") + "\n" + slots + b
            + notes("Acts of kindness: Ferguson found blood donors give for the warm glow of giving, more than pure altruism; we felt it all session. Managing stress: Raposa found that on days people help more, stress hurts their mood less. Guiding nervous donors calmed our own nerves."))


# ---------------- LANGAR
def langar_did():
    o = [open_sec(2, 1)]
    o.append('''  <div class="blk a iris" style="left:-20px;top:-20px;width:1250px;height:1120px;background:var(--saffron);--ix:30%;--iy:62%"></div>''')
    o.append("  " + frame("langar-did", "langar-2", "Behind the counter", "zoom", ".45s", tagst="--tc:var(--ink)"))
    o.append('''  <div class="abs lbl a fade" style="left:120px;top:150px;color:var(--ink);--d:.1s">Langar = free kitchen · seva = selfless service</div>
  <h2 class="abs disp" style="left:116px;top:196px;font-size:112px">
    <span class="ln" style="--d:.15s"><span>Behind the</span></span>
    <span class="ln" style="--d:.27s"><span style="color:var(--cream)">counter.</span></span>
  </h2>
  <svg class="abs" style="left:120px;top:440px;width:560px;height:500px" viewBox="0 0 560 500"><path class="draw" pathLength="1" style="--d:.5s;--t:1.4s" d="M270 80A170 170 0 1 1 269.9 80" fill="none" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"/></svg>
  <div class="loop orbit" data-tap="4"></div>
  <div class="loop ripple" data-tap="1" style="left:340px;top:470px;width:100px;height:100px;--lp:8s;--ld:0s"></div>
  <div class="loop ripple" data-tap="2" style="left:510px;top:640px;width:100px;height:100px;--lp:8s;--ld:2s"></div>
  <div class="loop ripple" data-tap="3" style="left:340px;top:810px;width:100px;height:100px;--lp:8s;--ld:4s"></div>
  <div class="loop ripple" data-tap="4" style="left:170px;top:640px;width:100px;height:100px;--lp:8s;--ld:6s"></div>
  <div class="badge a land" data-tap="1" style="--s:100px;left:340px;top:470px;--d:0s"><svg viewBox="0 0 64 64"><use href="#i-pot"/></svg></div>
  <div class="badge a land" data-tap="2" style="--s:100px;left:510px;top:640px;--d:0s"><svg viewBox="0 0 64 64"><use href="#i-ladle"/></svg></div>
  <div class="badge a land" data-tap="3" style="--s:100px;left:340px;top:810px;--d:0s"><svg viewBox="0 0 64 64"><use href="#i-pangat"/></svg></div>
  <div class="badge a land" data-tap="4" style="--s:100px;left:170px;top:640px;--d:0s"><svg viewBox="0 0 64 64"><use href="#i-heart"/></svg></div>
  <div class="loop steam" data-tap="1" style="left:367px;top:612px;--ld:0s"><svg viewBox="0 0 14 34" width="14" height="34" style="overflow:visible"><path d="M7 32c-6-6 6-9 0-15s6-9 0-15" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linecap="round"/></svg></div>
  <div class="loop steam" data-tap="1" style="left:383px;top:612px;--ld:0.8s"><svg viewBox="0 0 14 34" width="14" height="34" style="overflow:visible"><path d="M7 32c-6-6 6-9 0-15s6-9 0-15" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linecap="round"/></svg></div>
  <div class="loop steam" data-tap="1" style="left:399px;top:612px;--ld:1.6s"><svg viewBox="0 0 14 34" width="14" height="34" style="overflow:visible"><path d="M7 32c-6-6 6-9 0-15s6-9 0-15" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linecap="round"/></svg></div>
  <div class="abs a land" style="left:340px;top:640px;--d:1s;width:100px"><svg viewBox="0 0 64 64" width="100" height="100" style="fill:none;stroke:var(--ink);stroke-width:4;stroke-linecap:round;stroke-linejoin:round;overflow:visible"><use href="#i-bowl" style="--saffron:var(--cream)"/></svg></div>
  <div class="abs a fade" data-tap="1" style="left:690px;top:480px;width:500px;--d:.2s"><div class="disp" style="font-size:38px">1 · We organised</div><div class="body" style="font-size:22px">dal, roti, chawal &amp; meethe chawal</div></div>
  <div class="abs a fade" data-tap="2" style="left:690px;top:585px;width:500px;--d:.2s"><div class="disp" style="font-size:38px">2 · Served</div><div class="body" style="font-size:22px">everyone who came, of every faith</div></div>
  <div class="abs a fade" data-tap="3" style="left:690px;top:690px;width:500px;--d:.2s"><div class="disp" style="font-size:38px">3 · Sat in pangat</div><div class="body" style="font-size:22px">side by side on the floor, same level</div></div>
  <div class="abs a fade" data-tap="4" style="left:690px;top:795px;width:500px;--d:.2s"><div class="disp" style="font-size:38px">4 · Were served</div><div class="body" style="font-size:22px">and ate langar ourselves</div></div>''')
    o.append(notes("Langar is the free community kitchen; seva is selfless service. We organised and served the meal, then sat in pangat and were served ourselves."))
    return "\n".join(o)


def langar_impact():
    b = strip_old(sec("08 LANGAR · 02 IMPACT"))
    b = b.replace('<svg class="a land"', '<svg data-tap="1" class="a land"', 1)
    b = b.replace('<svg class="a land"', '<svg data-tap="1" class="a land"')
    b = b.replace('<div class="loop server"', '<div data-tap="1" class="loop server"')
    b = b.replace('<div class="pb a rise"', '<div data-tap="2" class="pb a rise"')
    return (open_sec(2, 2) + "\n  " + frame("langar-impact", "langar-1", "Serving in pangat", "from-t", ".2s", tagst="--tc:var(--saffron);color:var(--ink)") + b
            + notes("A free meal for anyone, of any faith, eaten side by side. This gurudwara once fed a hundred and one nationalities at one breakfast."))


def langar_learned():
    b = strip_old(sec("09 LANGAR · 03 LEARNED"))
    b = shift(b)
    cards = re.findall(r'<div class="pb a corner lq" style="[^"]*">', b)
    for g, c in enumerate(cards, 1):
        n = c.replace('class="pb a corner lq"', f'class="pb a flip lq" data-tap="{g}"')
        n = re.sub(r"--d:[\d.]+s", "--d:.15s", n)
        b = b.replace(c, n)
    b = b.replace('<div class="badge a land" style="--s:100px;--sh:6px;left:600px;top:650px;--d:1.5s', '<div class="badge a land" data-tap="1" style="--s:100px;--sh:6px;left:600px;top:650px;--d:.6s')
    for a_, b_ in [("Served langar minutes after serving it.", "Minutes after ladling out dal and roti, we sat down in pangat and were served the same meal. Giver and receiver swapped places."),
                   ("To learn the kitchen's rhythm, on the spot.", "No briefing, no rehearsal. We learned the kitchen's rhythm on the spot, by following the sevadars around us."),
                   ("Eating the same food as the people we'd served.", "Eating the same food, on the same floor, as the people we had just served. No one sat above anyone."),
                   ("Nobody asked who we were. We wanted to earn it.", "Nobody asked who we were or why we came. We were handed a ladle and trusted, and we wanted to earn it.")]:
        assert a_ in b, a_
        b = b.replace(a_, b_)
    backs = "".join(cardback(x, y, 520, 250, lab, g, True) for g, (x, y, lab) in enumerate(
        [(120, 440, "Most surprising"), (660, 440, "Most challenging"), (120, 710, "Most rewarding"), (660, 710, "About us")], 1))
    return (open_sec(2, 3) + "\n  " + frame("langar-learned", "langar-3", "Seva", "behind", ".2s", tagst="--tc:var(--saffron);color:var(--ink)") + "\n" + backs + b
            + notes("The surprise: minutes after serving, we were served; giver and receiver swapped places. The challenge was learning the kitchen's rhythm on the spot. The reward was eating as equals, and nobody asked who we were."))


def rrow(top, g, pc, use, strat, cite, big, tk, us, tc="var(--cream)"):
    return (f'  <div class="rrow a from-r" data-tap="{g}" style="top:{top}px;--pc:{pc};--tc:{tc};--d:.15s"><div class="st"><div class="badge rel" style="--s:58px;--sh:4px;border-width:4px">'
            f'<svg viewBox="0 0 64 64"><use href="#{use}"/></svg></div><span class="disp">{strat}</span></div>'
            f'<div class="tx"><div class="cite">{cite}</div><div class="big">{big}</div><p class="tk">{tk}</p><p class="us"><b>Us</b>{us}</p></div></div>\n')


def langar_research():
    b = strip_old(sec("10 LANGAR · 04 RESEARCH"))
    b = b[: b.index("</h2>") + 5] + "\n"
    Y = [394, 582, 770]
    b += rrow(Y[0], 1, "var(--saffron)", "i-people", "Social<br>relationships", "<b>Dunbar (2017)</b> · Adaptive Human Behavior &amp; Physiology", "Eat together, bond more",
              "People who eat with others more often are happier, trust others more and feel closer to their community.",
              "Pangat seats everyone on the same floor, in one row. After serving, we sat in it too.", "var(--ink)")
    b += rrow(Y[1], 2, "var(--ink)", "i-thanks", "Expressing<br>gratitude", "<b>Emmons &amp; McCullough (2003)</b> · JPSP", "Gratitude lifts outlook",
              "People who listed what they were grateful for each week felt better about their lives and more optimistic.",
              "Seva is gratitude acted out: thanks given as a free meal, and we joined in.")
    b += rrow(Y[2], 3, "var(--green)", "i-kind", "Acts of<br>kindness", "<b>Dunn, Aknin &amp; Norton (2008)</b> · Science", "Giving beats getting",
              "People given money to spend on others were happier by evening than those told to spend it on themselves.",
              "Our hour went to strangers of every faith, and we left happier than we arrived.")
    slots = "".join(slot(120, y, 1060, 178, lab, g) for g, (y, lab) in enumerate(zip(Y, ["Social relationships", "Expressing gratitude", "Acts of kindness"]), 1))
    return (open_sec(2, 4) + "\n  " + frame("langar-research", "langar-2", "14 Nov · Jebel Ali", "tile", ".2s", ";--ty:-90deg", "--tc:var(--saffron);color:var(--ink)") + "\n" + slots + b
            + notes("Social relationships: Dunbar found people who eat together feel closer, and pangat seats everyone in one row. Gratitude: Emmons showed it lifts outlook; seva acts it out. Kindness: Dunn found spending on others beats spending on yourself."))


# ---------------- RUN
def run_did():
    o = [open_sec(3, 1)]
    o.append('''  <div class="blk a wipe-d" style="left:-20px;top:-20px;width:1960px;height:450px;background:var(--green)"></div>
  <div class="blk loop glint" style="left:0;top:-20px;width:700px;height:450px;--ld:.4s"></div>''')
    o.append("  " + frame("run-did", "run-2", "~80 flags", "from-r", ".45s", tagst="--tc:var(--ink)"))
    o.append('''  <div class="abs lbl a fade" style="left:120px;top:150px;color:rgba(248,241,226,.8);--d:.1s">What did we do?</div>
  <h2 class="abs disp" style="left:116px;top:196px;font-size:112px;color:var(--cream)">
    <span class="ln dn" style="--d:.15s"><span>Jackets on,</span></span>
    <span class="ln dn" style="--d:.27s"><span style="color:var(--gold)">before dawn.</span></span>
  </h2>
  <svg class="abs" style="left:120px;top:470px;width:1060px;height:200px" viewBox="0 0 1060 200">
    <path d="M20 150C150 150 180 60 280 60S440 150 560 130 720 40 820 60 980 150 1040 110" fill="none" stroke="rgba(28,24,20,.12)" stroke-width="40" stroke-linecap="round"/>
    <path id="route" class="draw" pathLength="1" style="--d:.4s;--t:1.6s;animation-timing-function:linear" d="M20 150C150 150 180 60 280 60S440 150 560 130 720 40 820 60 980 150 1040 110" fill="none" stroke="var(--ink)" stroke-width="7" stroke-linecap="round"/>
  </svg>
  <div class="abs runner loop" style="left:120px;top:470px;width:30px;height:30px;border-radius:50%;background:var(--blood);border:5px solid var(--ink);offset-path:path('M20 150C150 150 180 60 280 60S440 150 560 130 720 40 820 60 980 150 1040 110');offset-rotate:0deg;offset-anchor:50% 50%;offset-distance:0%;opacity:0"></div>
  <div class="badge a land station" data-tap="1" data-at=".14" style="--s:100px"><svg viewBox="0 0 64 64"><use href="#i-sign"/></svg></div>
  <div class="badge a land station" data-tap="2" data-at=".4" style="--s:100px"><span class="loop wave"><svg viewBox="0 0 64 64"><use href="#i-flag"/></svg></span></div>
  <div class="badge a land station" data-tap="3" data-at=".66" style="--s:100px"><svg viewBox="0 0 64 64"><use href="#i-water"/></svg></div>
  <div class="badge a land station" data-tap="4" data-at=".92" style="--s:100px"><svg viewBox="0 0 64 64"><use href="#i-medal"/></svg></div>
  <div class="abs a rise" data-tap="1" style="left:120px;top:705px;width:240px;--d:.25s"><div class="disp" style="font-size:34px">1 · Guide</div><p class="body" style="font-size:20px;margin-top:4px">showed runners the start line and where everything was</p></div>
  <div class="abs a rise" data-tap="2" style="left:385px;top:705px;width:240px;--d:.25s"><div class="disp" style="font-size:34px">2 · Flags</div><p class="body" style="font-size:20px;margin-top:4px">~40 UAE flags each, about <b>80</b> handed out</p></div>
  <div class="abs a rise" data-tap="3" style="left:650px;top:705px;width:240px;--d:.25s"><div class="disp" style="font-size:34px">3 · Water</div><p class="body" style="font-size:20px;margin-top:4px">water for every runner at the finish</p></div>
  <div class="abs a rise" data-tap="4" style="left:915px;top:705px;width:250px;--d:.25s"><div class="disp" style="font-size:34px">4 · Medals</div><p class="body" style="font-size:20px;margin-top:4px">a medal around every finisher's neck</p></div>''')
    o.append(notes("We started before dawn in volunteer jackets. We guided runners to the start, handed out about eighty UAE flags, gave out water and put a medal on every finisher."))
    return "\n".join(o)


def run_impact():
    b = strip_old(sec("12 RUN · 02 IMPACT"))
    b = b.replace('<g class="a from-l"', '<g data-tap="1" class="a from-l"')
    b = b.replace('<div class="a rise" style="--d:1.6s">', '<div data-tap="2" class="a rise" style="--d:1.6s">')
    b = b.replace('<div class="a rise" style="--d:1.8s">', '<div data-tap="2" class="a rise" style="--d:1.8s">')
    b = b.replace('<div class="a rise" style="--d:2s">', '<div data-tap="2" class="a rise" style="--d:2s">')
    b = b.replace('<p class="abs body a fade" style="left:120px;top:888px', '<p class="abs body a fade" data-tap="3" style="left:120px;top:888px')
    return (open_sec(3, 2) + "\n  " + frame("run-impact", "run-1", "One finish line", "wipe-d", ".2s", tagst="--tc:var(--green)") + b
            + notes("The run is built for inclusion: People of Determination run beside every age group. Pettigrew and Tropp's review of 515 studies shows contact between groups cuts prejudice, and a shared finish line is that contact."))


def run_learned():
    b = strip_old(sec("13 RUN · 03 LEARNED"))
    b = shift(b)
    cols = re.findall(r'<div class="col a from-[tb]" style="[^"]*">', b)
    for g, c in enumerate(cols, 1):
        n = re.sub(r'class="col a from-[tb]"', f'class="col a flip" data-tap="{g}"', c)
        n = re.sub(r"--d:[\d.]+s", "--d:.15s", n)
        b = b.replace(c, n)
    for a_, b_ in [("Volunteers set up in the dark, before a single runner arrived.", "Volunteers were setting up in the dark long before the first runner arrived. A race that looks effortless runs on hours of unseen work."),
                   ("The morning after seva, with the same energy for the last runner.", "It came the morning after langar seva. Keeping the same energy for the last runner as for the first was the hardest part."),
                   ("A medal for each, loudest for People of Determination.", "Hanging a medal on every finisher, of every age and ability. The loudest cheers were for People of Determination.")]:
        assert a_ in b, a_
        b = b.replace(a_, b_)
    backs = "".join(cardback(x, 430, 330, 510, lab, g, True) for g, (x, lab) in enumerate([(120, "Surprising"), (485, "Challenging"), (850, "Rewarding")], 1))
    return (open_sec(3, 3) + "\n  " + frame("run-learned", "run-4", "8 hours", "from-l", ".2s", tagst="--tc:var(--green)") + "\n" + backs + b
            + notes("What surprised us: a race starts hours before the gun, with volunteers setting up in the dark. The challenge was eight hours on our feet the morning after seva, keeping the same energy for the last runner. The reward was a medal around every finisher's neck."))


def run_research():
    b = strip_old(sec("14 RUN · 04 RESEARCH"))
    b = b.replace('<div class="rblock a fade" style="top:470px;--pc:var(--gold);--uc:var(--green);--d:.6s"', '<div class="rblock a from-r" data-tap="1" style="top:470px;--pc:var(--gold);--uc:var(--green);--d:0s"')
    b = b.replace('<span class="mark" style="--d:1.2s">', '<span class="mark" style="--d:.6s">')
    b = b.replace('<div class="rblock a fade" style="top:715px;--pc:var(--green);--d:1.3s"', '<div class="rblock a from-r" data-tap="2" style="top:715px;--pc:var(--green);--d:0s"')
    b = b.replace('<span class="mark" style="--d:1.9s;', '<span class="mark" style="--d:.6s;')
    for a_, b_ in [("we're less happy when they do</span>.", "we're less happy when they do</span>, whatever we're doing."),
                   ("Water for runner after runner left no room to wander.", "Handing water and medals to runner after runner for eight hours kept us fully in the moment; there was no room to wander."),
                   ("Five kind acts <span", "Students who did five kind acts <span"),
                   ("lifted happiness; spread over a week, they didn't.", "each week got happier; spreading the same five across the week made no difference."),
                   ("Langar, then the run at dawn the next day: kindness in one burst.", "Langar seva one evening, the run at dawn the next day: our kindness came in one concentrated burst.")]:
        assert a_ in b, a_
        b = b.replace(a_, b_)
    slots = slot(120, 470, 1060, 215, "Study 1 · Living in the present", 1) + slot(120, 715, 1060, 215, "Study 2 · Acts of kindness", 2)
    return (open_sec(3, 4) + "\n  " + frame("run-research", "run-3", "Every finisher", "hang", ".2s", tagst="--tc:var(--green)") + "\n" + slots + b
            + notes("Two strategies. Living in the present: Killingsworth and Gilbert found our minds wander almost half the time, and we're less happy when they do; eight hours of water and medals left no room for that. Acts of kindness: Lyubomirsky found five kind acts in one day lift happiness more than five spread across a week. Langar, then the run: kindness in one burst."))


# ================================================================ ASSEMBLE
S.append(map_sec(0))
S.append(intro(1, ["Blood", "Donation", "Camp"], 160, "help donors through the whole process, from forms and check-up booths to refreshments, and donate ourselves.", "", "blood-1", "01 Oct 2026")
         + notes("First, two hours at a blood donation camp on the first of October, run by our MAD Club with Dubai Health."))
S += [blood_did(), blood_impact(), blood_learned(), blood_research()]
S.append(evidence(1, 2, [("blood-1", "blood-2"), ("blood-3", "blood-4")], ("The camp,", "in photos."), 460, 533, 360, 120, 40)
         + notes("A few photos from the camp."))
S.append(summary(1, [("Did", "Helped donors with forms, booths and refreshments; we donated too.", ""), ("Impact", "Every donation can help up to 3 patients.", ""),
                     ("Learned", "Going first made our reassurance honest.", ""), ("Research", "Warm glow · stress buffer", "Ferguson et al. 2012 · Raposa et al. 2016"),
                     ("Evidence", "3 photos from the camp", "")])
         + notes("So: two hours helping donors through the camp, and two donations of our own."))
S.append(map_sec(1))
S.append(intro(2, ["Langar", "Seva"], 200, "cook, serve and sit down with whoever walks in, as equals.", "", "langar-3", "Guru Nanak Darbar")
         + notes("Next, one hour of langar seva at Guru Nanak Darbar Gurudwara in Jebel Ali, on the fourteenth of November."))
S += [langar_did(), langar_impact(), langar_learned(), langar_research()]
S.append(evidence(2, 3, [("langar-1", T + "langar-1"), ("langar-2", T + "langar-3"), ("langar-3", T + "langar-4")], ("The gurudwara,", "in photos."), 300, 533, 360, 120, 24)
         + notes("And some photos from the gurudwara."))
S.append(summary(2, [("Did", "Organised, served, sat in pangat, were served.", ""), ("Impact", "A free meal for every faith, in one row.", ""),
                     ("Learned", "Giver became receiver.", ""), ("Research", "Gratitude · eating together · giving", "Emmons &amp; McCullough 2003 · Dunbar 2017 · Dunn et al. 2008"),
                     ("Evidence", "3 photos from the gurudwara", "")])
         + notes("In one hour, giver became receiver."))
S.append(map_sec(2))
S.append(intro(3, ["Emirates NBD", "Unity Run"], 150, "eight hours, from pre-dawn set-up to the last runner's medal.",
               "3, 5 &amp; 10 km · open to <b>People of Determination</b> · Hamdan bin Mohammed Community Sports Initiative · <b>“Walk, Run for Unity in Diversity”</b>", "run-5", "d3 · Dubai")
         + notes("Thanks, Vedansh. Our third activity: eight hours at the Emirates NBD Unity Run the very next day, organised by FittGROUP at Dubai Design District."))
S += [run_did(), run_impact(), run_learned(), run_research()]
S.append(evidence(3, 4, [("run-2", T + "run-4"), ("run-3", T + "run-2"), ("run-4", T + "run-3"), ("run-5", T + "run-1")], ("The run,", "on record."), 250, 444, 400, 592, 20,
                 certs=[("cert-run", "Unity Run certificate of completion", 400, 224, 330, "cert-run-photo"), ("cert-run2", "Volunteers.ae certificate", 400, 283, 618)])
         + notes("Here are our two certificates and the photos from d3."))
S.append(summary(3, [("Did", "Guided runners, ~80 flags, water, a medal for every finisher.", ""), ("Impact", "Every ability, one finish line.", ""),
                     ("Learned", "Logistics is kindness no one sees.", ""), ("Research", "Presence · kindness in one burst", "Killingsworth &amp; Gilbert 2010 · Lyubomirsky et al. 2005"),
                     ("Evidence", "2 certificates + 4 photos from d3", "")])
         + notes("Eight hours at the run, eleven in total."))
S.append(map_sec(3))

# ---------------- BOSS (contradictions)
b = sec("15 CONTRADICTIONS")
b = re.sub(r'\s*<aside class="notes">.*?</aside>', "", b, flags=re.S)
b = b.replace('<div class="abs lbl a fade" style="left:120px;top:84px;color:var(--ink-2)">Contradictions · re-examined positions</div>',
              '<div class="abs lbl a fade" style="left:120px;top:244px;color:var(--ink-2);font-size:19px;--d:.3s">Contradictions · 3 claims from class, and what we found</div>')
b = b.replace('style="left:116px;top:126px;font-size:96px"', 'style="left:116px;top:136px;font-size:96px"')
b = b.replace('<div class="abs a stamp" style="right:120px;top:120px;--r:6deg;--d:3.2s;border:6px solid var(--blood);color:var(--blood);padding:14px 20px 12px"><span class="lbl" style="font-size:28px">Position re-examined</span></div>',
              '<div class="abs a stamp" data-tap="3" style="right:120px;top:120px;--r:6deg;--d:.9s;border:6px solid var(--blood);color:var(--blood);background:var(--paper);padding:14px 20px 12px"><span class="lbl" style="font-size:26px">Position re-examined</span></div>')
b = b.replace("left:120px;top:270px;width:1680px;display:grid;grid-template-columns:600px 1fr;row-gap:32px", "left:120px;top:296px;width:1680px;display:grid;grid-template-columns:600px 1fr;row-gap:22px")
for g, d in enumerate(["--d:.4s", "--d:1.3s", "--d:2.2s"], 1):
    b = b.replace(f'<div class="a fade row-c" style="{d}">', f'<div class="a fade row-c" style="--d:{.3 + g * .12:.2f}s">')
rows_f = re.findall(r'<div class="a behind row-f" style="--d:[\d.]+s">.*', b)
for g, r in enumerate(rows_f, 1):
    n = re.sub(r'<div class="a behind row-f" style="--d:[\d.]+s">', f'<div class="a behind row-f" data-tap="{g}" style="--d:0s;height:100%">', r)
    b = b.replace(r, f'<div style="position:relative"><div class="slotb" data-untap="{g}" style="position:absolute;inset:0"><b>?</b>What we found</div>{n}</div>')
b = b.replace("min-height:196px", "min-height:176px")
S.append('<section class="slide m2" data-speaker="Tohraan" data-title="Contradictions · Class vs reality" data-level="4" data-step="0" style="--cc:var(--ink);--cu:cuUp">' + b
         + notes("We also found contradictions. Weinstein and Ryan show helping lifts well-being most when it's freely chosen, and honestly, we started for a grade; by the medals, the motivation was our own. The forty percent happiness pie felt too neat: we could help only because we were healthy, free and in a city that makes it easy. And at langar, the people we served then served us. Kindness felt less like charity, more like belonging."))

# ---------------- CLOSE (4 badges collected)
c = sec("18 CLOSE")
c = re.sub(r'\s*<aside class="notes">.*?</aside>', "", c, flags=re.S)
c = re.sub(r'\s*<div class="hold loop float".*?</div></div>', "", c, flags=re.S)
badges = ""
for i, (ic, x) in enumerate([("i-drop", 1250), ("i-bowl", 1400), ("i-medal", 1550), ("i-scale", 1700)]):
    badges += (f'\n  <div class="hold loop float" style="left:{x}px;top:{480 + (i % 2) * 40}px;transform-origin:60px 60px;--ld:{i * .4:.1f}s"><div class="badge a pop" style="--s:120px;left:0;top:0;--d:{2.5 + i * .1:.1f}s;box-shadow:8px 8px 0 #000">'
               f'<svg viewBox="0 0 64 64"><use href="#{ic}"/></svg></div></div>')
c = c.replace('<div class="abs disp a rise" style="left:1300px;top:720px', badges + '\n  <div class="abs disp a rise" style="left:1250px;top:720px')
c = c.replace('style="left:1306px;top:850px;color:var(--gold)', 'style="left:1256px;top:850px;color:var(--gold)')
S.append('<section class="slide m2" data-speaker="Tohraan" data-title="Sustainable happiness is served" style="--fc:#cbbfa9;--cc:var(--ink);--cu:cuUp">' + c
         + notes("So here's our conclusion. Sustainable happiness isn't something you find; it's something you serve. It's happiness that helps others without costing anyone else. Thank you. We're happy to take questions."))

# frames on Learned/Research slides used 504x896 in reused bodies? (frames were stripped; all new frames are 486x864)
body = "\n\n".join(S)
for i in range(1, 7):
    pass

css_new = (pathlib.Path(__file__).parent / "game.css").read_text()
js_new = (pathlib.Path(__file__).parent / "game.js").read_text()
untap = "\n".join(f'.slide.t{i} [data-untap="{i}"]' + "{opacity:0;transform:translateY(16px) scale(.96);pointer-events:none}" for i in range(1, 7))
untap_cb = "\n".join(f'.slide.t{i} .cardback[data-untap="{i}"]' + "{transform:perspective(1200px) rotateX(90deg);opacity:0}" for i in range(1, 7))
untap_env = '.slide.t1 .env[data-untap="1"]{transform:translateY(140px) rotate(6deg);opacity:0} .slide.t1 .env .flap{transform:perspective(600px) rotateX(180deg)}'

html = (old[: old.index("<style>")].replace("<title>Eleven Hours, Three Ways</title>", "<title>Happiness Through Volunteering</title>") + "<style>" + css_old + css_new + untap + "\n" + untap_cb + "\n" + untap_env + "\n</style>\n</head>\n<body>\n"
        + symbols + '\n\n<div id="viewport"><div id="stage">\n\n' + body + "\n</div></div>\n"
        + '<div id="hint">→ / Space: next · ← back · F fullscreen · P presenter · E edit photos</div>\n'
        + '<div id="editbar"><b>EDIT PHOTOS</b><span>Click "Replace" on any frame, or drop a photo onto it · drag a photo to reframe it · → / ← still move between steps</span>'
          '<button id="esave">Save to images folder</button><button id="edone">Done (E)</button><span id="emsg"></span></div>\n'
        + presenter + '<script src="images/positions.js"></script>\n<script>\n' + js_new + "\n</script>\n</body>\n</html>\n")
(ROOT / "index.html").write_text(html)
print("sections:", html.count('<section class="slide'))
