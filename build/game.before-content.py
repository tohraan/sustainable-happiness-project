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


def frame(slot, src, tag, anim, d=".3s", more="", tagst=""):
    return (f'<div class="frame a {anim}" style="left:1272px;top:44px;--d:{d}{more}"><div class="ph" data-slot="{slot}" '
            f'data-src="images/{src}" data-label="images/{slot}.jpg" style="width:486px;height:864px"></div>'
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
t += '\n  <div class="abs a land" style="left:1590px;top:870px;--d:1.7s"><button class="go" data-act="next" style="background:var(--cream);color:var(--ink);--gc:var(--ink)">Start ▶</button></div>\n'
S.append('<section class="slide m2" data-speaker="Vedansh" data-title="11 hours, 3 ways to give" style="--cc:var(--ink);--cu:cuUp">'
         + t + notes("Good morning. I'm Vedansh, and this is Tohraan. Our sustainable happiness project is eleven hours of volunteering, and we've built it as a game: three levels, three ways to give."))

# ================================================================ MAP (4 visits)
NODES = [(330, 690, "i-drop", "Level 1", "Blood camp", "01 Oct · 2 hrs", "var(--blood)"),
         (770, 520, "i-bowl", "Level 2", "Langar seva", "14 Nov · 1 hr", "var(--saffron)"),
         (1210, 700, "i-medal", "Level 3", "Unity Run", "15 Nov · 8 hrs", "var(--green)"),
         (1640, 500, "i-scale", "Final level", "Class vs reality", "what we re-examined", "var(--ink)")]
SEGS = ["M40 900C140 900 230 690 330 690", "M330 690C500 690 600 520 770 520",
        "M770 520C940 520 1040 700 1210 700", "M1210 700C1380 700 1470 500 1640 500"]
TAIL = "M1640 500C1740 500 1800 380 1880 380"
MAPS = [
    ("Vedansh", "Three levels.", "Eleven hours.", "var(--blood)", "The map · tap level 1 to play",
     "Here's the map. Level one is a blood donation camp, level two a gurudwara kitchen, level three a community run. Eleven hours to collect."),
    ("Vedansh", "Level 1", "cleared.", "var(--blood)", "2 of 11 hours · level 2 unlocked", "Two hours down. Level two."),
    ("Vedansh", "Level 2", "cleared.", "var(--saffron)", "3 of 11 hours · level 3 unlocked",
     "Three hours down, eight to go. Over to Tohraan for level three."),
    ("Tohraan", "All 3 levels", "cleared.", "var(--green)", "11 of 11 hours · final level unlocked",
     "All three levels cleared. One final level: where class and reality disagreed."),
]


def map_sec(k):
    spk, h1, h2, hc, lbl, note = MAPS[k]
    o = [f'<section class="slide m2" data-speaker="{spk}" data-title="Map · {"start" if k == 0 else h1 + " " + h2}" data-map="{k}" style="--cc:var(--ink);--cu:cuUp">']
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
            o.append(f'  <div class="abs a hang" style="left:{x - 110}px;top:{y - 178}px;--d:3s"><span class="flag">Tap to play ▼</span></div>')
    o.append(notes(note))
    return "\n".join(o)


# ================================================================ LEVEL STEPS
def intro(l, lines, fs, mission, sub, photo, tag):
    L = LV[l]
    o = [open_sec(l, 0)]
    o.append(f'  <div class="blk a wipe-l" style="left:-20px;top:-20px;width:1250px;height:1120px;background:{L["c"]}"></div>')
    o.append("  " + frame(f'{L["key"]}-intro', photo, tag, "zoom", ".45s", tagst="--tc:var(--ink)"))
    o.append(f'  <div class="abs lbl a fade" style="left:120px;top:150px;color:{L["t"]};--d:.1s">Level {l} of 3</div>')
    o.append(f'  <h1 class="abs disp" style="left:112px;top:200px;font-size:{fs}px;color:{L["t"]}">'
             + "".join(f'<span class="ln" style="--d:{.15 + i * .12:.2f}s"><span>{x}</span></span>' for i, x in enumerate(lines)) + "</h1>")
    chip = 'class="pb" style="--c:var(--cream);color:var(--ink);padding:12px 18px 10px"'
    o.append(f'  <div class="abs a rise" style="left:120px;top:690px;display:flex;gap:12px;--d:.75s"><span {chip}><span class="lbl" style="font-size:20px">{L["date"]}</span></span>'
             f'<span {chip}><span class="lbl" style="font-size:20px">{L["hrs"]} hour{"s" if L["hrs"] > 1 else ""}</span></span>'
             f'<span {chip}><span class="lbl" style="font-size:20px">{L["org"]}</span></span></div>')
    o.append(f'  <p class="abs body a fade" style="left:120px;top:{770 if sub else 772}px;width:1040px;font-size:30px;font-weight:500;color:{L["t"]};--d:.95s"><b>Mission:</b> {mission}</p>')
    if sub:
        o.append(f'  <p class="abs body a fade" style="left:120px;top:826px;width:1040px;font-size:21px;color:{L["t"]};--d:1.05s">{sub}</p>')
    o.append(f'  <div class="abs a land" style="left:120px;top:{900 if sub else 885}px;--d:1.2s"><button class="go" data-act="next" style="background:var(--ink);color:var(--cream);--gc:var(--cream)">Start level ▶</button></div>')
    return "\n".join(o) + "\n"


def evidence(l, n, photos, certlabel, ph_w, ph_h, top, x0, gap, certs=None):
    L = LV[l]
    o = [open_sec(l, 5)]
    o.append('  <div class="abs lbl a fade" style="left:120px;top:150px;color:var(--ink-2);--d:.05s">Evidence · certificate &amp; photos</div>')
    o.append(f'  <h2 class="abs disp" style="left:116px;top:196px;font-size:96px"><span class="ln" style="--d:.1s"><span>Proof we were <span style="color:{L["c"]}">there.</span></span></span></h2>')
    # envelope (closed) -> certificate
    o.append(f'  <div class="abs a deal" style="left:120px;top:470px;--d:.35s;--fx:0px;--fr:-8deg"><div class="env" data-untap="1" style="--ec:{L["c"]}">'
             f'<svg class="flap" viewBox="0 0 400 150" preserveAspectRatio="none"><path d="M0 0H400L200 140Z" fill="#B48E55" stroke="var(--ink)" stroke-width="5" stroke-linejoin="round"/></svg>'
             f'<b class="seal"><svg viewBox="0 0 64 64"><use href="#{L["icon"]}"/></svg></b><div class="disp" style="font-size:44px">Certificate</div><small>Tap to open</small></div></div>')
    for k, (slot, lab, w, h, top_c, *src) in enumerate(certs or [(f'cert-{L["key"]}', certlabel, 360, 600, 320)]):
        o.append(f'  <div class="frame a from-b" data-tap="1" style="left:120px;top:{top_c}px;--d:{.15 + k * .15:.2f}s"><div class="ph contain cert" data-slot="{slot}" data-src="images/{src[0] if src else slot}" '
                 f'data-label="{lab} · images/{slot}.jpg" style="width:{w}px;height:{h}px"></div></div>')
    # photo pile -> dealt grid
    fw, fh = ph_w + 34, ph_h + 34
    total = n * fw + (n - 1) * gap
    cx, cy = x0 + total / 2, top + fh / 2
    o.append(f'  <div class="abs a deal" style="left:{cx - 150:.0f}px;top:{cy - 210:.0f}px;--d:.5s;--fx:200px;--fr:10deg"><div class="pile" data-untap="2">'
             f'<i></i><i></i><i><span class="badge rel" style="--s:110px;--sh:5px"><svg viewBox="0 0 64 64"><use href="#{L["icon"]}"/></svg></span>'
             f'<span class="disp" style="font-size:64px;margin-top:22px">{n} photos</span><small>Tap to deal</small></i></div></div>')
    for i, src in enumerate(photos):
        x = x0 + i * (fw + gap)
        fx, fy = cx - (x + fw / 2), cy - (top + fh / 2)
        r = [-2.5, 1.5, -1, 2, -1.5][i]
        o.append(f'  <div class="frame a corner" data-tap="2"{f' data-cue="{cx:.0f},{cy:.0f}"' if i == 0 else ''} style="left:{x:.0f}px;top:{top}px;--d:{i * .12:.2f}s;--fx:{fx:.0f}px;--fy:{fy:.0f}px;--fr:{r * 4}deg;rotate:{r}deg">'
                 f'<div class="ph" data-slot="{L["key"]}-ev{i + 1}" data-src="images/{src}" data-label="images/{L["key"]}-ev{i + 1}.jpg" style="width:{ph_w}px;height:{ph_h}px"></div></div>')
    return "\n".join(o) + "\n"


def summary(l, rows):
    L = LV[l]
    o = [open_sec(l, 6, f'{L["name"]} · Level complete')]
    o.append(f'  <div class="blk a wipe-l" style="left:1240px;top:-20px;width:700px;height:1120px;background:{L["c"]}"></div>')
    o.append(f'  <div class="abs lbl a fade" style="left:120px;top:150px;color:var(--ink-2);--d:.05s">Level {l} · summary</div>')
    o.append(f'  <h2 class="abs disp" style="left:116px;top:196px;font-size:120px"><span class="ln" style="--d:.1s"><span>Level {l}</span></span>'
             f'<span class="ln" style="--d:.22s"><span style="color:{L["c"]}">complete.</span></span></h2>')
    o.append('  <div class="abs" style="left:120px;top:448px;width:1060px">')
    for i, (k, v, cite) in enumerate(rows):
        c = f"<small>{cite}</small>" if cite else ""
        o.append(f'    <div class="srow a from-l" style="--d:{.55 + i * .14:.2f}s;--rc:{L["c"] if i % 2 == 0 else "var(--ink)"}"><b>{k}</b><span>{v}{c}</span></div>')
    o.append("  </div>")
    o.append(f'  <div class="loop ripple" style="left:1440px;top:150px;width:300px;height:300px;--rc:{L["t"]};--lp:3s"></div>')
    o.append(f'  <div class="badge a stamp" style="--s:300px;left:1440px;top:150px;--d:.45s;--r:-6deg"><svg viewBox="0 0 64 64"><use href="#{L["icon"]}"/></svg></div>')
    o.append(f'  <b class="ok a stamp" style="left:1680px;top:130px;width:110px;height:110px;--nc:var(--ink);--d:.9s;--r:-10deg"><svg viewBox="0 0 64 64"><use href="#i-check"/></svg></b>')
    o.append(f'  <div class="abs disp a land" style="left:1240px;width:700px;text-align:center;top:500px;font-size:170px;color:{L["t"]};--d:1.1s">+{L["hrs"]} hr{"s" if L["hrs"] > 1 else ""}</div>')
    o.append(f'  <div class="abs lbl a fade" style="left:1240px;width:700px;text-align:center;top:680px;color:{L["t"]};--d:1.3s">Added to the meter</div>')
    o.append('  <div class="abs a land" style="left:1395px;top:790px;--d:1.5s"><button class="go" data-act="next" style="background:var(--ink);color:var(--cream);--gc:var(--cream)">Back to map ▶</button></div>')
    return "\n".join(o) + "\n"


def cardback(left, top, w, h, label, g, tall=False, qc="var(--gold)"):
    cls = "cardback tall" if tall else "cardback"
    return (f'  <div class="abs a flip" style="left:{left}px;top:{top}px;--d:{.5 + g * .15:.2f}s"><div class="{cls}" data-untap="{g}" style="width:{w}px;height:{h}px">'
            f'<span class="q" style="color:{qc}">?</span><div><div class="lbl">{label}</div><small>Tap to flip</small></div></div></div>\n')


def slot(left, top, w, h, label, g):
    return f'  <div class="abs a fade" style="left:{left}px;top:{top}px;--d:.6s"><div class="slotb" data-untap="{g}" style="width:{w}px;height:{h}px"><b>?</b>{label}</div></div>\n'


# ---------------- BLOOD
def blood_did():
    o = [open_sec(1, 1)]
    o.append('''  <div class="blk a wipe-u" style="left:1180px;top:-20px;width:760px;height:1120px;background:var(--blood)"></div>''')
    o.append("  " + frame("blood-did", "blood-2", "We gave first", "from-b", ".45s", tagst="--tc:var(--ink)"))
    o.append('''  <div class="abs lbl a fade" style="left:120px;top:150px;color:var(--ink-2);--d:.1s">What did we do?</div>
  <h2 class="abs disp" style="left:116px;top:196px;font-size:112px">
    <span class="ln sd" style="--d:.15s"><span>We gave first.</span></span>
    <span class="ln sd" style="--d:.27s"><span style="color:var(--blood)">Then we helped.</span></span>
  </h2>
  <div class="abs lbl a fade" style="left:120px;top:470px;color:var(--ink-2);font-size:20px;--d:.5s">The donor's path · we walked every step with them</div>
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
  <div class="abs a rise" data-tap="1" style="left:120px;top:670px;width:236px;--d:.2s"><div class="disp" style="font-size:34px">1 · Forms</div><p class="body" style="font-size:20px;margin-top:6px">helped donors fill in the procedural forms</p></div>
  <div class="abs a rise" data-tap="2" style="left:385px;top:670px;width:236px;--d:.5s"><div class="disp" style="font-size:34px">2 · Vitals</div><p class="body" style="font-size:20px;margin-top:6px">guided them to the check-up booths</p></div>
  <div class="abs a rise" data-tap="3" style="left:650px;top:670px;width:236px;--d:.5s"><div class="disp" style="font-size:34px;color:var(--blood)">3 · Donate</div><p class="body" style="font-size:20px;margin-top:6px"><b>we gave blood too</b>, both of us</p></div>
  <div class="abs a rise" data-tap="4" style="left:915px;top:670px;width:236px;--d:.5s"><div class="disp" style="font-size:34px">4 · Refuel</div><p class="body" style="font-size:20px;margin-top:6px">handed out refreshments afterwards</p></div>
  <p class="abs body a fade" data-tap="4" style="left:120px;top:850px;width:1040px;font-size:22px;color:var(--ink-2);--d:.9s">Dubai Health's blood service runs on <b style="color:var(--ink)">voluntary, unpaid donors</b>, like every one we walked through.</p>''')
    o.append(notes("We gave first: we both donated. Then we helped donors with their forms, guided them to the vitals booths and handed out refreshments."))
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
    return (open_sec(1, 2) + "\n  " + frame("blood-impact", "blood-3", "Dubai Health", "fall", ".25s", ";--r:1.5deg", "--tc:var(--blood)") + b
            + notes("Each donation splits into red cells, plasma and platelets, so our two could help up to six patients. And the WHO calls unpaid volunteers the safest source of blood."))


def blood_learned():
    b = strip_old(sec("05 BLOOD · 03 LEARNED"))
    b = shift(b)
    # put taps on the lcards and replace their entrance delays
    cards = re.findall(r'<div class="lcard a flip" style="[^"]*">', b)
    for g, c in enumerate(cards, 1):
        b = b.replace(c, c.replace('<div class="lcard a flip"', f'<div class="lcard a flip" data-tap="{g}"').replace(re.search(r"--d:[\d.]+s", c).group(0), "--d:.15s"))
    backs = "".join(cardback(120, y, 1060, 150, lab, g) for g, (y, lab) in enumerate([(420, "Most surprising"), (600, "Most challenging"), (780, "Most rewarding")], 1))
    return (open_sec(1, 3) + "\n  " + frame("blood-learned", "blood-1", "At the camp", "wipe", ".2s") + "\n" + backs + b
            + notes("The surprise: fresh off the chair, we could reassure first-timers honestly. The challenge was our own nerves. The reward: two donations, and every donor we walked through."))


def blood_research():
    b = strip_old(sec("06 BLOOD · 04 RESEARCH"))
    b = b.replace('<div class="loop warm"', '<div data-tap="1" class="loop warm"')
    b = b.replace('<div class="scard a deal" style="left:120px;top:450px;', '<div class="scard a deal" data-tap="1" style="left:120px;top:450px;')
    b = b.replace('<div class="scard a deal" style="left:665px;top:450px;', '<div class="scard a deal" data-tap="2" style="left:665px;top:450px;')
    slots = slot(120, 450, 515, 400, "Study 1 · Acts of kindness", 1) + slot(665, 450, 515, 400, "Study 2 · Managing stress", 2)
    return (open_sec(1, 4) + "\n  " + frame("blood-research", "blood-2", "2 donations", "deal", ".15s", ";--fx:-260px;--fr:12deg", "--tc:var(--blood)") + "\n" + slots + b
            + notes("Acts of kindness: Ferguson found donors give for a warm glow, the good feeling of giving. Managing stress: Raposa found helping others kept mood up on stressful days. Helping turned our nerves into calm."))


# ---------------- LANGAR
def langar_did():
    o = [open_sec(2, 1)]
    o.append('''  <div class="blk a iris" style="left:-20px;top:-20px;width:1250px;height:1120px;background:var(--saffron);--ix:30%;--iy:62%"></div>''')
    o.append("  " + frame("langar-did", "langar-1", "Behind the counter", "zoom", ".45s", tagst="--tc:var(--ink)"))
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
    o.append(notes("Langar is the free community kitchen; seva is selfless service. We organised dal, roti and chawal, served everyone, then sat in pangat and were served ourselves."))
    return "\n".join(o)


def langar_impact():
    b = strip_old(sec("08 LANGAR · 02 IMPACT"))
    b = b.replace('<svg class="a land"', '<svg data-tap="1" class="a land"', 1)
    b = b.replace('<svg class="a land"', '<svg data-tap="1" class="a land"')
    b = b.replace('<div class="loop server"', '<div data-tap="1" class="loop server"')
    b = b.replace('<div class="pb a rise"', '<div data-tap="2" class="pb a rise"')
    return (open_sec(2, 2) + "\n  " + frame("langar-impact", "langar-2", "Inside the langar hall", "from-t", ".2s", tagst="--tc:var(--saffron);color:var(--ink)") + b
            + notes("Langar is a free meal for anyone, of any faith, eaten side by side at the same level. This gurudwara once fed a hundred and one nationalities at one breakfast."))


def langar_learned():
    b = strip_old(sec("09 LANGAR · 03 LEARNED"))
    b = shift(b)
    cards = re.findall(r'<div class="pb a corner lq" style="[^"]*">', b)
    for g, c in enumerate(cards, 1):
        n = c.replace('class="pb a corner lq"', f'class="pb a flip lq" data-tap="{g}"')
        n = re.sub(r"--d:[\d.]+s", "--d:.15s", n)
        b = b.replace(c, n)
    b = b.replace('<div class="badge a land" style="--s:100px;--sh:6px;left:600px;top:650px;--d:1.5s', '<div class="badge a land" data-tap="1" style="--s:100px;--sh:6px;left:600px;top:650px;--d:.6s')
    backs = "".join(cardback(x, y, 520, 250, lab, g, True) for g, (x, y, lab) in enumerate(
        [(120, 440, "Most surprising"), (660, 440, "Most challenging"), (120, 710, "Most rewarding"), (660, 710, "About us")], 1))
    return (open_sec(2, 3) + "\n  " + frame("langar-learned", "langar-1", "Seva", "behind", ".2s", tagst="--tc:var(--saffron);color:var(--ink)") + "\n" + backs + b
            + notes("The surprise: minutes after serving, we were served; giver and receiver swapped seats. The challenge was learning the kitchen's rhythm on the spot. And nobody asked who we were; we were simply trusted."))


def langar_research():
    b = strip_old(sec("10 LANGAR · 04 RESEARCH"))
    # group 1 = relationships -> Dunbar, 2 = gratitude -> Emmons, 3 = kindness -> Dunn
    b = b.replace('<path class="draw" pathLength="1" style="stroke:var(--saffron);--d:1.3s', '<path data-tap="1" class="draw" pathLength="1" style="stroke:var(--saffron);--d:0s')
    b = b.replace('<path class="draw" pathLength="1" style="stroke:var(--ink);--d:1.6s', '<path data-tap="2" class="draw" pathLength="1" style="stroke:var(--ink);--d:0s')
    b = b.replace('<path class="draw" pathLength="1" style="stroke:var(--green);--d:1.9s', '<path data-tap="3" class="draw" pathLength="1" style="stroke:var(--green);--d:0s')
    travs = re.findall(r'<div class="loop trav"', b)
    for g in (1, 2, 3):
        b = b.replace('<div class="loop trav"', f'<div data-tap="{g}" class="loop  trav"', 1)
    b = b.replace('class="loop  trav"', 'class="loop trav"')
    b = b.replace('<div class="rcard a fade" style="top:405px;--pc:var(--ink);--d:2.1s', '<div class="rcard a from-r" data-tap="2" style="top:405px;--pc:var(--ink);--d:.4s')
    b = b.replace('<div class="rcard a fade" style="top:575px;--pc:var(--saffron);--d:1.8s', '<div class="rcard a from-r" data-tap="1" style="top:575px;--pc:var(--saffron);--d:.4s')
    b = b.replace('<div class="rcard a fade" style="top:745px;--pc:var(--green);--d:2.4s', '<div class="rcard a from-r" data-tap="3" style="top:745px;--pc:var(--green);--d:.4s')
    slots = slot(650, 405, 570, 150, "Study", 2) + slot(650, 575, 570, 150, "Study", 1) + slot(650, 745, 570, 150, "Study", 3)
    return (open_sec(2, 4) + "\n  " + frame("langar-research", "langar-3", "14 Nov · Jebel Ali", "tile", ".2s", ";--ty:-90deg", "--tc:var(--saffron);color:var(--ink)") + "\n" + slots + b
            + notes("Three strategies meet here. Dunbar found people who eat together feel closer, and pangat seats everyone in one row. Emmons showed gratitude lifts outlook; seva acts it out. And Dunn found giving beats getting."))


# ---------------- RUN
def run_did():
    o = [open_sec(3, 1)]
    o.append('''  <div class="blk a wipe-d" style="left:-20px;top:-20px;width:1960px;height:450px;background:var(--green)"></div>
  <div class="blk loop glint" style="left:0;top:-20px;width:700px;height:450px;--ld:.4s"></div>''')
    o.append("  " + frame("run-did", "run-1", "Jackets on · pre-dawn", "from-r", ".45s", tagst="--tc:var(--ink)"))
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
    return (open_sec(3, 2) + "\n  " + frame("run-impact", "run-2", "~80 flags", "wipe-d", ".2s", tagst="--tc:var(--green)") + b
            + notes("The run is built for inclusion: People of Determination run beside every age group. Pettigrew and Tropp's review of 515 studies shows contact between groups cuts prejudice, and a shared finish line is that contact."))


def run_learned():
    b = strip_old(sec("13 RUN · 03 LEARNED"))
    b = shift(b)
    cols = re.findall(r'<div class="col a from-[tb]" style="[^"]*">', b)
    for g, c in enumerate(cols, 1):
        n = re.sub(r'class="col a from-[tb]"', f'class="col a flip" data-tap="{g}"', c)
        n = re.sub(r"--d:[\d.]+s", "--d:.15s", n)
        b = b.replace(c, n)
    backs = "".join(cardback(x, 430, 330, 510, lab, g, True) for g, (x, lab) in enumerate([(120, "Surprising"), (485, "Challenging"), (850, "Rewarding")], 1))
    return (open_sec(3, 3) + "\n  " + frame("run-learned", "run-4", "8 hours", "from-l", ".2s", tagst="--tc:var(--green)") + "\n" + backs + b
            + notes("What surprised us: a race starts hours before the gun, with volunteers setting up in the dark. The challenge was eight hours on our feet, the morning after seva. The reward was a medal around every finisher's neck."))


def run_research():
    b = strip_old(sec("14 RUN · 04 RESEARCH"))
    b = b.replace('<div class="rblock a fade" style="top:470px;--pc:var(--gold);--uc:var(--green);--d:.6s"', '<div class="rblock a from-r" data-tap="1" style="top:470px;--pc:var(--gold);--uc:var(--green);--d:0s"')
    b = b.replace('<span class="mark" style="--d:1.2s">', '<span class="mark" style="--d:.6s">')
    b = b.replace('<div class="rblock a fade" style="top:715px;--pc:var(--green);--d:1.3s"', '<div class="rblock a from-r" data-tap="2" style="top:715px;--pc:var(--green);--d:0s"')
    b = b.replace('<span class="mark" style="--d:1.9s;', '<span class="mark" style="--d:.6s;')
    slots = slot(120, 470, 1060, 215, "Study 1 · Living in the present", 1) + slot(120, 715, 1060, 215, "Study 2 · Acts of kindness", 2)
    return (open_sec(3, 4) + "\n  " + frame("run-research", "run-3", "Every finisher", "hang", ".2s", tagst="--tc:var(--green)") + "\n" + slots + b
            + notes("This is living in the present. Killingsworth and Gilbert found our minds wander almost half the time, and we're less happy when they do; handing out water left no room for that. And Lyubomirsky found five kind acts in one day lift happiness more than five spread across a week. Langar, then the run: kindness in one burst."))


# ================================================================ ASSEMBLE
S.append(map_sec(0))
S.append(intro(1, ["Blood", "Donation", "Camp"], 160, "get donors from the form to the refreshments, and give blood ourselves.", "", "blood-1", "01 Oct 2026")
         + notes("Level one: two hours at a blood camp on the first of October, run by our MAD Club with Dubai Health."))
S += [blood_did(), blood_impact(), blood_learned(), blood_research()]
S.append(evidence(1, 3, ["blood-1", "blood-2", "blood-3"], "MAD Club certificate", 300, 533, 360, 665, 24)
         + notes("Here's the certificate and our photos from the camp."))
S.append(summary(1, [("Did", "Forms, vitals, refreshments, and we both donated.", ""), ("Impact", "2 donations, up to 6 patients.", ""),
                     ("Learned", "Going first made our reassurance honest.", ""), ("Research", "Warm glow · stress buffer", "Ferguson et al. 2012 · Raposa et al. 2016"),
                     ("Evidence", "3 photos from the camp", "")])
         + notes("Level one complete: two hours, two donations."))
S.append(map_sec(1))
S.append(intro(2, ["Langar", "Seva"], 200, "cook, serve and sit down with whoever walks in, as equals.", "", "langar-3", "Guru Nanak Darbar")
         + notes("Level two: one hour of langar seva at Guru Nanak Darbar Gurudwara in Jebel Ali, on the fourteenth of November."))
S += [langar_did(), langar_impact(), langar_learned(), langar_research()]
S.append(evidence(2, 3, ["langar-1", "langar-2", "langar-3"], "Gurudwara certificate or letter", 300, 533, 360, 665, 24,
                 certs=[("cert-langar", "Guru Nanak Darbar certificate", 440, 330, 440)])
         + notes("Our certificate from the gurudwara, and the photos."))
S.append(summary(2, [("Did", "Organised, served, sat in pangat, were served.", ""), ("Impact", "A free meal for every faith, in one row.", ""),
                     ("Learned", "Giver became receiver.", ""), ("Research", "Gratitude · eating together · giving", "Emmons &amp; McCullough 2003 · Dunbar 2017 · Dunn et al. 2008"),
                     ("Evidence", "Certificate + 3 photos from the gurudwara", "")])
         + notes("Level two complete: giver became receiver."))
S.append(map_sec(2))
S.append(intro(3, ["Emirates NBD", "Unity Run"], 150, "eight hours, from pre-dawn set-up to the last runner's medal.",
               "3, 5 &amp; 10 km · open to <b>People of Determination</b> · Hamdan bin Mohammed Community Sports Initiative · <b>“Walk, Run for Unity in Diversity”</b>", "run-5", "d3 · Dubai")
         + notes("Thanks, Vedansh. Level three: eight hours at the Emirates NBD Unity Run the very next day, organised by FittGROUP at Dubai Design District."))
S += [run_did(), run_impact(), run_learned(), run_research()]
S.append(evidence(3, 4, ["run-1", "run-2", "run-3", "run-4"], "Unity Run volunteer certificate", 250, 444, 400, 592, 20,
                 certs=[("cert-run", "Unity Run certificate of completion", 400, 224, 330, "cert-run-photo"), ("cert-run2", "Volunteers.ae certificate", 400, 283, 618)])
         + notes("Here's the run certificate and the photos from d3."))
S.append(summary(3, [("Did", "Guided runners, ~80 flags, water, a medal for every finisher.", ""), ("Impact", "Every ability, one finish line.", ""),
                     ("Learned", "Logistics is kindness no one sees.", ""), ("Research", "Presence · kindness in one burst", "Killingsworth &amp; Gilbert 2010 · Lyubomirsky et al. 2005"),
                     ("Evidence", "2 certificates + 4 photos from d3", "")])
         + notes("Level three complete. Eleven hours, and the meter is full."))
S.append(map_sec(3))

# ---------------- BOSS (contradictions)
b = sec("15 CONTRADICTIONS")
b = re.sub(r'\s*<aside class="notes">.*?</aside>', "", b, flags=re.S)
b = b.replace('<div class="abs lbl a fade" style="left:120px;top:84px;color:var(--ink-2)">Contradictions · re-examined positions</div>',
              '<div class="abs lbl a fade" style="left:120px;top:244px;color:var(--ink-2);font-size:19px;--d:.3s">Contradictions · 3 claims from class · tap to see what we found</div>')
b = b.replace('style="left:116px;top:126px;font-size:96px"', 'style="left:116px;top:136px;font-size:96px"')
b = b.replace('<div class="abs a stamp" style="right:120px;top:120px;--r:6deg;--d:3.2s;border:6px solid var(--blood);color:var(--blood);padding:14px 20px 12px"><span class="lbl" style="font-size:28px">Position re-examined</span></div>',
              '<div class="abs a stamp" data-tap="3" style="right:120px;top:120px;--r:6deg;--d:.9s;border:6px solid var(--blood);color:var(--blood);background:var(--paper);padding:14px 20px 12px"><span class="lbl" style="font-size:26px">All levels complete · 11 hrs</span></div>')
b = b.replace("left:120px;top:270px;width:1680px;display:grid;grid-template-columns:600px 1fr;row-gap:32px", "left:120px;top:296px;width:1680px;display:grid;grid-template-columns:600px 1fr;row-gap:22px")
for g, d in enumerate(["--d:.4s", "--d:1.3s", "--d:2.2s"], 1):
    b = b.replace(f'<div class="a fade row-c" style="{d}">', f'<div class="a fade row-c" style="--d:{.3 + g * .12:.2f}s">')
rows_f = re.findall(r'<div class="a behind row-f" style="--d:[\d.]+s">.*', b)
for g, r in enumerate(rows_f, 1):
    n = re.sub(r'<div class="a behind row-f" style="--d:[\d.]+s">', f'<div class="a behind row-f" data-tap="{g}" style="--d:0s;height:100%">', r)
    b = b.replace(r, f'<div style="position:relative"><div class="slotb" data-untap="{g}" style="position:absolute;inset:0"><b>?</b>What we found</div>{n}</div>')
b = b.replace("min-height:196px", "min-height:176px")
S.append('<section class="slide m2" data-speaker="Tohraan" data-title="Final level · Class vs reality" data-level="4" data-step="0" style="--cc:var(--ink);--cu:cuUp">' + b
         + notes("We also found contradictions. Weinstein and Ryan show helping lifts well-being most when it's freely chosen, and honestly, we started for a grade; by the medals, the motivation was our own. The forty percent happiness pie felt too neat: we could help only because we were healthy, free and in a city that makes it easy. And at langar, the people we served then served us. Kindness felt less like charity, more like belonging."))

# ---------------- CLOSE (4 badges collected)
c = sec("18 CLOSE")
c = re.sub(r'\s*<aside class="notes">.*?</aside>', "", c, flags=re.S)
c = re.sub(r'\s*<div class="hold loop float".*?</div></div>', "", c, flags=re.S)
badges = ""
for i, (ic, x) in enumerate([("i-drop", 1250), ("i-bowl", 1400), ("i-medal", 1550), ("i-scale", 1700)]):
    badges += (f'\n  <div class="hold loop float" style="left:{x}px;top:{480 + (i % 2) * 40}px;transform-origin:60px 60px;--ld:{i * .4:.1f}s"><div class="badge a pop" style="--s:120px;left:0;top:0;--d:{2.5 + i * .1:.1f}s;box-shadow:8px 8px 0 #000">'
               f'<svg viewBox="0 0 64 64"><use href="#{ic}"/></svg></div></div>')
c = c.replace('<div class="abs disp a rise" style="left:1300px;top:720px', badges + '\n  <div class="abs lbl a fade" style="left:1252px;top:430px;color:var(--gold);font-size:20px;--d:2.4s">4 / 4 badges collected</div>\n  <div class="abs disp a rise" style="left:1250px;top:720px')
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

html = (old[: old.index("<style>")] + "<style>" + css_old + css_new + untap + "\n" + untap_cb + "\n" + untap_env + "\n</style>\n</head>\n<body>\n"
        + symbols + '\n\n<div id="viewport"><div id="stage">\n\n' + body + "\n</div></div>\n"
        + '<div id="hint">→ / Space: reveal, then next · ← back · click TAP or buttons · F fullscreen · P presenter · E edit photos</div>\n'
        + '<div id="editbar"><b>EDIT PHOTOS</b><span>Click "Replace" on any frame, or drop a photo onto it · drag a photo to reframe it · → / ← still move between steps</span>'
          '<button id="esave">Save to images folder</button><button id="edone">Done (E)</button><span id="emsg"></span></div>\n'
        + presenter + '<script src="images/positions.js"></script>\n<script>\n' + js_new + "\n</script>\n</body>\n</html>\n")
(ROOT / "index.html").write_text(html)
print("sections:", html.count('<section class="slide'))
