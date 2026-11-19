(() => {
  const params = new URLSearchParams(location.search);
  const slides = [...document.querySelectorAll('.slide')], N = slides.length;
  const TARGET = {Tohraan: 170, Vedansh: 170};
  const LV = {1: {name: 'Blood camp', hrs: 2, c: 'var(--blood)', t: 'var(--cream)'}, 2: {name: 'Langar seva', hrs: 1, c: 'var(--saffron)', t: 'var(--ink)'},
              3: {name: 'Unity Run', hrs: 8, c: 'var(--green)', t: 'var(--cream)'}, 4: {name: 'Class vs reality', hrs: 0, c: 'var(--ink)', t: 'var(--cream)'}};
  const STEPS = ['Start', 'Did', 'Impact', 'Learned', 'Research', 'Evidence', 'Summary'];
  const lvOf = s => +s.dataset.level || 0, stOf = s => +s.dataset.step || 0;
  const idx = (l, st) => slides.findIndex(s => lvOf(s) === l && stOf(s) === st);
  const groups = s => [...new Set([...s.querySelectorAll('[data-tap]')].map(e => +e.dataset.tap))].sort((a, b) => a - b);
  const pending = s => groups(s).filter(g => !s.classList.contains('t' + g));
  const reveal = (s, g) => { s.classList.add('t' + g); s.querySelectorAll(`[data-tap="${g}"]`).forEach(e => e.classList.add('on')); };

  // ---- unity run: place stations on the route ----
  const route = document.getElementById('route');
  if (route) {
    const box = route.ownerSVGElement, ox = parseFloat(box.style.left), oy = parseFloat(box.style.top), L = route.getTotalLength();
    document.querySelectorAll('.station').forEach(st => {
      const f = +st.dataset.at, p = route.getPointAtLength(L * f);
      st.style.left = (ox + p.x - 50) + 'px'; st.style.top = (oy + p.y - 50) + 'px';
      const r = document.createElement('div');   // pulse as the lapping runner passes
      r.className = 'loop ripple'; if (st.dataset.tap) r.dataset.tap = st.dataset.tap;
      r.style.cssText = `left:${st.style.left};top:${st.style.top};width:100px;height:100px;--lp:6s;--ld:${(f * 6).toFixed(2)}s`;
      st.before(r);
    });
  }

  // ---- tap groups: each group's delays start from its own first move ----
  slides.forEach(s => groups(s).forEach(g => {
    const els = [...s.querySelectorAll(`[data-tap="${g}"]`)].flatMap(e => [e, ...e.querySelectorAll('[style*="--d"]')])
      .filter(e => e.style.getPropertyValue('--d'));
    if (!els.length) return;
    const ds = els.map(e => parseFloat(e.style.getPropertyValue('--d')) || 0), m = Math.min(...ds);
    els.forEach((e, i) => e.style.setProperty('--d', (ds[i] - m).toFixed(2) + 's'));
  }));

  // ---- motion v2: kinetic headline characters, photo curtains, odometer digits ----
  document.querySelectorAll('.m2 .ln>span').forEach(line => {
    let i = 0;
    const split = node => [...node.childNodes].forEach(n => {
      if (n.nodeType !== 3) return split(n);
      const f = document.createDocumentFragment();
      [...n.textContent].forEach(c => {
        const ch = document.createElement('span');
        ch.className = 'ch'; ch.textContent = c === ' ' ? ' ' : c; ch.style.setProperty('--i', i++);
        f.appendChild(ch);
      });
      n.replaceWith(f);
    });
    split(line);
  });
  document.querySelectorAll('.m2 .frame .ph').forEach(ph => ph.insertAdjacentHTML('afterbegin', '<i class="cv"></i><i class="curtain"></i>'));
  document.querySelectorAll('[data-odo]').forEach(el => {
    el.innerHTML = [...el.textContent].map((c, j) =>
      `<span class="odo"><span style="--n:${+c + 10};--j:${j}">${[...Array(20)].map((_, k) => k % 10).join('<br>')}</span></span>`).join('');
  });

  // ---- layers for parallax + speaker chip ----
  slides.forEach(s => {
    const bg = document.createElement('div'), fg = document.createElement('div');
    bg.className = 'bg'; fg.className = 'fg';
    [...s.children].forEach(c => { if (c.tagName === 'ASIDE') return; (c.classList.contains('blk') ? bg : fg).appendChild(c); });
    s.prepend(bg, fg);
    const c = s.dataset.speaker === 'Tohraan' ? 'var(--saffron)' : 'var(--green)';
    s.insertAdjacentHTML('beforeend', `<div class="speaker" style="--c:${c}"><b class="dot"></b>${s.dataset.speaker.toUpperCase()}</div>`);
  });

  // ---- photos: browser-saved (edit mode) > images/<slot>.jpg > data-src default ----
  const DB = (() => {
    let p = null;
    const open = () => p || (p = new Promise((res, rej) => {
      const r = indexedDB.open('happiness-deck', 1);
      r.onupgradeneeded = () => r.result.createObjectStore('slots');
      r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
    }));
    const run = (mode, fn) => open().then(db => new Promise((res, rej) => {
      const t = db.transaction('slots', mode), q = fn(t.objectStore('slots'));
      t.oncomplete = () => res(q && q.result); t.onerror = () => rej(t.error);
    }));
    return {
      all: () => open().then(db => new Promise(res => {
        const out = {}, c = db.transaction('slots').objectStore('slots').openCursor();
        c.onsuccess = () => { const k = c.result; if (k) { out[k.key] = k.value; k.continue(); } else res(out); };
        c.onerror = () => res(out);
      })).catch(() => ({})),
      get: k => run('readonly', st => st.get(k)).catch(() => null),
      put: (k, v) => run('readwrite', st => st.put(v, k)),
      del: k => run('readwrite', st => st.delete(k)),
    };
  })();
  const EXT = ['jpg', 'jpeg', 'png', 'webp', 'JPG', 'JPEG', 'PNG'];
  const firstOk = list => new Promise(res => {
    let i = 0; const img = new Image();
    img.onload = () => res(list[i]); img.onerror = () => (++i < list.length ? img.src = list[i] : res(null));
    img.src = list[0];
  });
  const XP = params.has('export');
  const fileList = ph => { const sl = ph.dataset.slot, src = ph.dataset.src;
    return [...EXT.map(x => `images/${sl}.${x}`),                                   // real photo saved for this slot
            ...(XP ? [] : [`images/placeholders/${sl}.jpg`]),                        // AI placeholder: live deck only, never exported
            ...(src && src !== `images/${sl}` ? EXT.map(x => `${src}.${x}`) : [])]; };   // genuine default
  const show = (ph, src, pos) => new Promise(res => {
    ph.querySelector('.kb')?.remove();
    if (!src) { ph.classList.add(ph.hasAttribute('data-panel') ? 'nophoto' : 'missing'); return res(); }
    ph.classList.remove('nophoto');
    const kb = document.createElement('div'), img = new Image();
    kb.className = 'kb loop'; img.draggable = false; if (pos) img.style.objectPosition = pos;
    img.onload = () => { ph.classList.remove('missing'); res(); };
    img.onerror = () => { kb.remove(); ph.classList.add('missing'); res('bad'); };
    img.src = src; kb.appendChild(img); ph.insertBefore(kb, ph.querySelector('.eov'));
  });
  const phs = [...document.querySelectorAll('.ph[data-slot]')];
  const POS = window.__POS || {};
  const recsP = params.has('export') ? Promise.resolve({}) : DB.all();
  const loadPh = (ph, recs) => {
    const r = recs[ph.dataset.slot], pos = (r && r.pos) || POS[ph.dataset.slot];
    return r && r.blob ? (ph.classList.remove('ai'), show(ph, URL.createObjectURL(r.blob), pos)) : firstOk(fileList(ph)).then(src => (ph.classList.toggle('ai', !!src && src.includes('/placeholders/')), show(ph, src, pos)));
  };
  const loads = phs.map(ph => recsP.then(recs => loadPh(ph, recs)));

  // ---- presenter sync ----
  let ch = null; try { ch = new BroadcastChannel('happiness-deck'); } catch (e) {}
  const send = m => { try { ch && ch.postMessage(m); } catch (e) {} try { localStorage.setItem('happiness-deck', JSON.stringify({...m, t: Date.now()})); } catch (e) {} };
  const listen = fn => { if (ch) ch.onmessage = e => fn(e.data); addEventListener('storage', e => { if (e.key === 'happiness-deck' && e.newValue) { try { fn(JSON.parse(e.newValue)); } catch (_) {} } }); };

  if (params.has('presenter')) {
    document.body.classList.add('presenter');
    let spk = null, spkStart = Date.now(), totStart = null;
    const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
    const show = (i, left) => {
      const s = slides[i];
      if (s.dataset.speaker !== spk) { spk = s.dataset.speaker; spkStart = Date.now(); }
      if (totStart === null && i > 0) totStart = Date.now();
      document.getElementById('pnow').textContent = `Step ${i + 1} / ${N} · ${spk} speaking` + (left ? ` · ${left} tap${left > 1 ? 's' : ''} left` : '');
      document.getElementById('ptitle').textContent = s.dataset.title;
      document.getElementById('pnotes').textContent = s.querySelector('.notes')?.textContent || '';
      document.getElementById('pnext').textContent = slides[i + 1] ? `${slides[i + 1].dataset.title} (${slides[i + 1].dataset.speaker})` : 'End';
      document.getElementById('ptarget').textContent = `target ${fmt(TARGET[spk])}`;
    };
    listen(m => m.type === 'at' && show(m.i, m.left));
    setInterval(() => { const e = (Date.now() - spkStart) / 1000, el = document.getElementById('ptimer');
      el.textContent = fmt(e); el.classList.toggle('over', e > TARGET[spk]);
      document.getElementById('ptotal').textContent = totStart ? fmt((Date.now() - totStart) / 1000) : '0:00'; }, 250);
    addEventListener('keydown', e => {
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) send({type: 'go', d: 1});
      if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) send({type: 'go', d: -1});
    });
    show(0); send({type: 'hello'});
    return;
  }

  const stage = document.getElementById('stage');
  const fit = () => stage.style.transform = `translate(-50%,-50%) scale(${Math.min(innerWidth / 1920, innerHeight / 1080)})`;
  addEventListener('resize', () => { fit(); placeCue(0); }); fit();

  // ---- HUD: level chip, step buttons, hours meter, NEXT ----
  const hud = document.createElement('div'); hud.id = 'hud';
  const ck = '<svg class="hck" viewBox="0 0 64 64"><use href="#i-check"/></svg>', lk = '<svg class="hlk" viewBox="0 0 64 64"><use href="#i-lock"/></svg>';
  hud.innerHTML = `<div class="hlvl"><b id="hlv"></b><span id="hst"></span></div>
    <div class="hsteps">${STEPS.slice(1).map((n, i) => `<button class="hbtn" data-s="${i + 1}" tabindex="-1">${ck}${lk}${n}</button>`).join('')}</div>
    <div class="hmeter">${[1, 2, 3].map(l => `<i data-l="${l}" style="--c:${LV[l].c};flex:${LV[l].hrs}"></i>`).join('')}<span><b id="hhrs"></b></span></div>
    <button class="hbtn hnext" id="hnext" data-act="next" tabindex="-1"></button>`;
  stage.appendChild(hud);
  const btns = [...hud.querySelectorAll('.hsteps button')], segs = [...hud.querySelectorAll('.hmeter i')];
  const maxStep = {1: -1, 2: -1, 3: -1};
  const SUMI = {1: idx(1, 6), 2: idx(2, 6), 3: idx(3, 6)};
  const earnedAt = i => [1, 2, 3].filter(l => SUMI[l] >= 0 && SUMI[l] <= i);
  const meterOn = new Set();
  const renderHud = (i, instant) => {
    const s = slides[i], l = lvOf(s), st = stOf(s), map = s.dataset.map != null;
    if (l && l < 4) maxStep[l] = Math.max(maxStep[l], st);
    hud.dataset.mode = l && l < 4 ? 'full' : (l === 4 || map) ? 'lite' : 'off';
    hud.style.setProperty('--lc', LV[l] ? LV[l].c : 'var(--ink)'); hud.style.setProperty('--lt', LV[l] ? LV[l].t : 'var(--cream)');
    const e = earnedAt(i);
    document.getElementById('hlv').textContent = map ? 'Overview' : l === 4 ? 'Reflection' : l ? `Activity ${l} of 3` : '';
    document.getElementById('hst').textContent = map ? `${e.length} of 3 activities done` : l === 4 ? 'Class vs reality' : l ? `${LV[l].name} · ${STEPS[st]}` : '';
    if (l && l < 4) btns.forEach(b => { const k = +b.dataset.s;
      b.className = 'hbtn ' + (k === st ? 'on' : k <= maxStep[l] ? 'done' : k === Math.max(maxStep[l], st) + 1 ? 'next' : 'lock'); });
    document.getElementById('hnext').textContent = st === 6 ? 'Overview ▶' : (l && l < 4 && st === 0) ? 'Start ▶' : map ? 'Begin ▶' : i === N - 1 ? 'End' : 'Next ▶';
    document.getElementById('hhrs').textContent = `${e.reduce((a, k) => a + LV[k].hrs, 0)} / 11 hrs`;
    segs.forEach(sg => { const k = +sg.dataset.l, on = e.includes(k);
      if (on && !meterOn.has(k)) { meterOn.add(k); sg.style.transform = 'scaleX(1)';
        if (!instant) sg.animate([{transform: 'scaleX(0)'}, {transform: 'scaleX(1)'}], {duration: 1100, delay: 600, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards'}); }
      if (!on && meterOn.has(k)) { meterOn.delete(k); sg.style.transform = 'scaleX(0)'; } });
  };
  const shake = el => el.animate([{translate: '0'}, {translate: '-10px'}, {translate: '10px'}, {translate: '-6px'}, {translate: '4px'}, {translate: '0'}], {duration: 380, easing: 'ease-out'});

  // ---- the TAP cue sits on the next thing to reveal ----
  const cue = document.createElement('button'); cue.id = 'cue'; cue.tabIndex = -1; cue.hidden = true; cue.innerHTML = '<b></b>'; stage.appendChild(cue);
  let cur = 0, busy = false, auto = [];
  const GAP = .8;   // seconds between auto-revealed groups
  const clearAuto = () => { auto.forEach(clearTimeout); auto = []; };
  const autoPlay = first => { clearAuto(); const s = slides[cur];
    pending(s).forEach((g, i) => auto.push(setTimeout(() => { if (slides[cur] === s) { reveal(s, g); at(); } }, (first + i * GAP) * 1000))); };
  function placeCue(delay) { cue.hidden = true; return;
    const s = slides[cur], all = groups(s), p = pending(s);
    if (!p.length || busy || document.body.classList.contains('static')) { cue.hidden = true; return; }
    const els = [...s.querySelectorAll(`[data-tap="${p[0]}"]`)];
    const t = els.find(e => e.dataset.cue) || els.find(e => e.classList.contains('badge')) || els[0];
    let x, y;
    if (t.dataset.cue) [x, y] = t.dataset.cue.split(',').map(Number);
    else { const r = t.getBoundingClientRect(), sr = stage.getBoundingClientRect(), k = sr.width / 1920;
      x = (r.left + r.width / 2 - sr.left) / k; y = (r.top + Math.min(r.height / 2, 130) - sr.top) / k; }
    cue.style.left = x + 'px'; cue.style.top = y + 'px';
    cue.querySelector('b').textContent = `Tap ${all.length - p.length + 1}/${all.length}`;
    cue.hidden = false; cue.classList.remove('show'); void cue.offsetWidth;
    cue.style.setProperty('--cd', (delay ?? 1) + 's'); cue.classList.add('show');
  }

  // ---- export: one page per step, every tap revealed ----
  if (params.has('export')) {
    document.body.classList.add('static');
    cur = Math.max(0, Math.min(N - 1, (+params.get('export') || 1) - 1));
    for (let j = 0; j <= cur; j++) renderHud(j, true);
    const s = slides[cur]; groups(s).forEach(g => reveal(s, g));
    s.classList.add('active');
    Promise.all([document.fonts.ready, ...loads]).then(() => setTimeout(() => window.__ready = true, 400));
    return;
  }

  const sweep = document.createElement('div'); sweep.id = 'sweep'; sweep.innerHTML = '<i class="sa"></i><i class="sb"></i>'; stage.appendChild(sweep);
  cur = Math.max(0, Math.min(N - 1, (parseInt(location.hash.slice(1)) || 1) - 1));
  const seen = new Set();
  const enter = s => { const was = seen.has(s); s.classList.toggle('seen', was); seen.add(s); };
  const at = () => send({type: 'at', i: cur, left: pending(slides[cur]).length});
  for (let j = 0; j <= cur; j++) renderHud(j, true);
  slides[cur].classList.add('active'); enter(slides[cur]);
  document.fonts.ready.then(() => autoPlay(1.2));

  const go = to => {
    if (busy || to < 0 || to >= N || to === cur) return;
    busy = true; cue.hidden = true; clearAuto();
    const from = slides[cur], next = slides[to], fwd = to > cur;
    const same = lvOf(from) && lvOf(from) === lvOf(next) && lvOf(from) < 4;
    const done = () => { pending(from).forEach(g => reveal(from, g)); busy = false; autoPlay(same ? .5 : .7); };
    if (same) {   // same board: content swaps, frame + HUD stay
      from.classList.add('moving', 'st-out'); next.classList.add('moving', 'st-in');
      next.style.setProperty('--b', '.22s'); next.classList.add('active'); enter(next);
      setTimeout(() => { from.classList.remove('active', 'moving', 'st-out'); next.classList.remove('moving', 'st-in'); done(); }, 400);
    } else {      // new place: the colour band sweeps across
      const cc = getComputedStyle(next).getPropertyValue('--cc').trim() || '#1C1814';
      sweep.style.setProperty('--sc', cc);
      sweep.style.setProperty('--sd', /^#1c1814$/i.test(cc) ? 'var(--gold)' : 'var(--ink)');
      sweep.className = ''; void sweep.offsetWidth; sweep.className = fwd ? 'fwd' : 'back';
      from.classList.add('moving', fwd ? 'out-l' : 'out-r');
      next.classList.add('moving', fwd ? 'in-r' : 'in-l');
      next.style.setProperty('--b', '.5s'); next.classList.add('active'); enter(next);
      setTimeout(() => {
        from.classList.remove('active', 'moving', 'out-l', 'out-r'); next.classList.remove('moving', 'in-r', 'in-l');
        sweep.className = ''; done();
      }, 1000);
    }
    cur = to; renderHud(cur); history.replaceState(null, '', '#' + (cur + 1)); at();
  };
  const advance = () => {
    if (busy) return;
    go(cur + 1);   // one press per slide; tap groups reveal on their own
  };

  addEventListener('keydown', e => {
    if (e.target.closest && e.target.closest('input,textarea')) return;
    const k = e.key;
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); advance(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); go(cur - 1); }
    else if (k === 'Home') go(0); else if (k === 'End') go(N - 1);
    else if (k === 'f' || k === 'F') document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
    else if (k === 'p' || k === 'P') { window.open(location.pathname + '?presenter', 'presenter', 'width=1200,height=760'); setTimeout(at, 700); }
    else if (k === 'e' || k === 'E') toggleEdit();
  });
  stage.addEventListener('click', e => {
    const t = e.target.closest('[data-act],#cue,.hsteps button'); if (!t) return;
    document.activeElement && document.activeElement.blur && document.activeElement.blur();
    if (t === cue) return advance();
    if (t.matches('.hsteps button')) {
      if (t.classList.contains('lock')) return shake(t);
      return go(idx(lvOf(slides[cur]), +t.dataset.s));
    }
    if (t.dataset.act === 'next') return advance();
    if (t.dataset.act === 'enter') return t.classList.contains('locked') ? shake(t) : go(idx(+t.dataset.lv, 0));
  });
  listen(m => { if (m.type === 'go') m.d > 0 ? advance() : go(cur - 1); if (m.type === 'hello') at(); });
  setTimeout(() => document.getElementById('hint').style.opacity = 0, 5000);

  // ---- edit mode: E toggles; Replace or drop a photo on any frame; drag to reframe ----
  let editing = false;
  const emsg = document.getElementById('emsg'), say = t => emsg.textContent = t;
  const toggleEdit = () => { editing = !editing; document.body.classList.toggle('editing', editing); say(''); };
  document.getElementById('edone').onclick = toggleEdit;
  phs.forEach(ph => ph.insertAdjacentHTML('beforeend', `<span class="eov"><button data-e="pick">+ Replace</button><button data-e="reset">Reset</button><em>${ph.dataset.slot}</em></span>`));
  const picker = Object.assign(document.createElement('input'), {type: 'file', accept: 'image/*'});
  let target = null;
  const setSlot = async (ph, file) => {
    if (!file || !/^image\//.test(file.type)) return say('That file is not an image.');
    const old = await DB.get(ph.dataset.slot);
    ph.classList.remove('ai');
    const bad = await show(ph, URL.createObjectURL(file), old && old.pos);
    if (bad) return say(`Chrome can't open ${file.name} (HEIC?). Export it as JPG and try again.`);
    await DB.put(ph.dataset.slot, {blob: file, pos: (old && old.pos) || null});
    say(`${ph.dataset.slot} updated and kept in this browser. Click "Save to images folder" so the PDF export gets it too.`);
  };
  picker.onchange = () => { if (target && picker.files[0]) setSlot(target, picker.files[0]); picker.value = ''; };
  stage.addEventListener('click', e => {
    const b = e.target.closest('.eov button'); if (!b || !editing) return;
    e.stopPropagation(); const ph = b.closest('.ph');
    if (b.dataset.e === 'pick') { target = ph; picker.click(); }
    else DB.del(ph.dataset.slot).then(() => loadPh(ph, {})).then(() => say(`${ph.dataset.slot} reset to the file in images/.`));
  }, true);
  addEventListener('dragover', e => { e.preventDefault(); const ph = e.target.closest && e.target.closest('.ph[data-slot]');
    document.querySelectorAll('.ph.drop').forEach(p => p !== ph && p.classList.remove('drop')); if (ph) ph.classList.add('drop'); });
  addEventListener('dragleave', e => { if (!e.relatedTarget) document.querySelectorAll('.ph.drop').forEach(p => p.classList.remove('drop')); });
  addEventListener('drop', e => {
    e.preventDefault(); document.querySelectorAll('.ph.drop').forEach(p => p.classList.remove('drop'));
    const ph = e.target.closest && e.target.closest('.ph[data-slot]'), f = e.dataTransfer.files[0];
    if (!ph || !f) return;
    if (!editing) toggleEdit();
    setSlot(ph, f);
  });
  stage.addEventListener('pointerdown', e => {
    if (!editing || e.target.closest('.eov')) return;
    const ph = e.target.closest('.ph[data-slot]'), img = ph && ph.querySelector('.kb img'); if (!img) return;
    e.preventDefault(); e.stopPropagation();
    const r = ph.getBoundingClientRect(), x0 = e.clientX, y0 = e.clientY;
    const [px, py] = (img.style.objectPosition || '50% 50%').split(' ').map(parseFloat);
    const cl = v => Math.max(0, Math.min(100, v));
    const mv = ev => img.style.objectPosition = `${cl(px - (ev.clientX - x0) / r.width * 160).toFixed(1)}% ${cl(py - (ev.clientY - y0) / r.height * 160).toFixed(1)}%`;
    const up = async () => {
      removeEventListener('pointermove', mv); removeEventListener('pointerup', up);
      const old = (await DB.get(ph.dataset.slot)) || {};
      await DB.put(ph.dataset.slot, {...old, pos: img.style.objectPosition});
      say(`Reframed ${ph.dataset.slot}.`);
    };
    addEventListener('pointermove', mv); addEventListener('pointerup', up);
  }, true);
  document.getElementById('esave').onclick = async () => {
    const recs = await DB.all(), keys = Object.keys(recs);
    if (!keys.length) return say('Nothing to save yet: replace or reframe a photo first.');
    const pos = {...POS}; keys.forEach(k => { if (recs[k].pos) pos[k] = recs[k].pos; });
    const js = `window.__POS = ${JSON.stringify(pos, null, 1)};\n`;
    if (window.showDirectoryPicker) {
      try {
        const dir = await showDirectoryPicker({id: 'happiness-images', mode: 'readwrite'});
        if (dir.name !== 'images') return say(`That folder is "${dir.name}". Pick the "images" folder inside sustainable-happiness-project.`);
        const write = async (name, data) => { const w = await (await dir.getFileHandle(name, {create: true})).createWritable(); await w.write(data); await w.close(); };
        let n = 0;
        for (const k of keys) if (recs[k].blob) { await write(`${k}.jpg`, recs[k].blob); n++; }
        await write('positions.js', js);
        return say(`Saved ${n} photo${n === 1 ? '' : 's'} and the framing to images/. The PDF export will use them.`);
      } catch (err) { if (err.name === 'AbortError') return say('Save cancelled.'); say(`Couldn't write there (${err.message}). Downloading the files instead.`); }
    }
    const dl = (name, blob) => { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click(); };
    keys.forEach(k => recs[k].blob && dl(`${k}.jpg`, recs[k].blob)); dl('positions.js', new Blob([js], {type: 'text/javascript'}));
    say('Downloaded. Move these files into the project\'s images folder.');
  };
})();
