
(() => {
  const params = new URLSearchParams(location.search);
  const slides = [...document.querySelectorAll('.slide')];
  const N = slides.length;
  const TARGET = {Tohraan: 145, Vedansh: 215}; // seconds (40 / 60 split of a 6-min pair slot)

  // folio + speaker tags
  slides.forEach((s, i) => {
    const sp = s.dataset.speaker, c = sp === 'Tohraan' ? 'var(--saffron)' : 'var(--green)';
    s.insertAdjacentHTML('beforeend', `<div class="speaker" style="--c:${c}"><i></i>${sp}</div><div class="folio">${String(i+1).padStart(2,'0')} / ${N}</div>`);
  });

  // ---- strategy map (slide 9) ----
  const acts = [
    {k:'blood', label:'Blood camp', c:'var(--blood)', y:390},
    {k:'langar', label:'Langar seva', c:'var(--saffron)', y:610},
    {k:'run', label:'Unity Run', c:'var(--green)', y:830},
  ];
  const strats = [
    {t:'Practicing Acts of Kindness', n:'every stop, every hour', on:['blood','langar','run']},
    {t:'Nurturing Social Relationships', n:'together, always, with strangers too', on:['blood','langar','run']},
    {t:'Expressing Gratitude', n:'seva is service as thanks', on:['langar','blood']},
    {t:'Taking Care of Body & Soul', n:'a run at dawn · a prayer hall', on:['run','langar']},
    {t:'Living in the Present', n:'one runner, one bottle, now', on:['run','langar']},
    {t:'Managing Stress', n:'calming our own nerves to donate', on:['blood']},
  ];
  const map = document.getElementById('map');
  if (map) {
    const X1 = 560, X2 = 1180, y0 = 330, gap = 112;
    let svg = '', d = .5;
    strats.forEach((s, j) => {
      const y2 = y0 + j*gap;
      s.on.forEach(k => {
        const a = acts.find(a => a.k === k);
        svg += `<path class="draw rough" pathLength="1" style="--d:${(d+=.16).toFixed(2)}s;--t:1.1s" d="M${X1} ${a.y}C${X1+300} ${a.y} ${X2-300} ${y2} ${X2} ${y2}" fill="none" stroke="${a.c}" stroke-width="4.5" stroke-linecap="round" opacity=".9"/>`;
      });
    });
    acts.forEach((a, i) => {
      svg += `<g class="a pop" style="--d:${.3+i*.12}s;transform-origin:${X1-160}px ${a.y}px"><rect x="${X1-330}" y="${a.y-46}" width="330" height="92" rx="46" fill="var(--card)" stroke="${a.c}" stroke-width="4" filter="url(#rough)"/><text x="${X1-165}" y="${a.y+12}" text-anchor="middle" style="font:600 36px var(--serif);fill:var(--ink)">${a.label}</text></g>`;
    });
    strats.forEach((s, j) => {
      const y2 = y0 + j*gap;
      svg += `<g class="a rise" style="--d:${(1.0+j*.28).toFixed(2)}s"><circle cx="${X2}" cy="${y2}" r="11" fill="var(--ink)"/><text x="${X2+34}" y="${y2+4}" style="font:600 37px var(--serif);fill:var(--ink)">${s.t.replace('&','&amp;')}</text><text x="${X2+36}" y="${y2+42}" style="font:600 30px var(--hand);fill:var(--ink-soft)">${s.n}</text></g>`;
    });
    map.innerHTML = svg;
  }

  // ---- photos: try several extensions, else show labelled placeholder ----
  const exts = ['jpg','jpeg','png','webp','JPG','JPEG','PNG'];
  const loads = [];
  document.querySelectorAll('.ph[data-src]').forEach(ph => {
    loads.push(new Promise(res => {
      let i = 0; const img = new Image();
      img.onload = () => { ph.appendChild(img); res(); };
      img.onerror = () => { if (++i < exts.length) img.src = `${ph.dataset.src}.${exts[i]}`; else { ph.classList.add('missing'); res(); } };
      img.src = `${ph.dataset.src}.${exts[0]}`;
    }));
  });
  document.querySelectorAll('.ph[data-video]').forEach(ph => {
    loads.push(new Promise(res => {
      const v = document.createElement('video');
      Object.assign(v, {muted:true, loop:true, autoplay:true, playsInline:true, src: ph.dataset.video});
      v.onloadeddata = () => { ph.appendChild(v); res(); };
      v.onerror = () => { ph.classList.add('missing'); res(); };
      setTimeout(res, 3000);
    }));
  });

  // ---- presenter mode ----
  let ch = null; try { ch = new BroadcastChannel('happiness-deck'); } catch(e) {}
  const send = msg => { try { ch && ch.postMessage(msg); } catch(e) {} try { localStorage.setItem('happiness-deck', JSON.stringify({...msg, t: Date.now()})); } catch(e) {} };
  const listen = fn => { if (ch) ch.onmessage = e => fn(e.data); window.addEventListener('storage', e => { if (e.key === 'happiness-deck' && e.newValue) { try { fn(JSON.parse(e.newValue)); } catch(_) {} } }); };

  if (params.has('presenter')) {
    document.body.classList.add('presenter');
    let cur = 0, spk = null, spkStart = Date.now(), totStart = null;
    const fmt = s => `${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
    const show = i => {
      cur = i; const s = slides[i];
      if (s.dataset.speaker !== spk) { spk = s.dataset.speaker; spkStart = Date.now(); }
      if (totStart === null && i > 0) totStart = Date.now();
      document.getElementById('pnow').textContent = `Slide ${i+1} / ${N} · ${spk} speaking`;
      document.getElementById('ptitle').textContent = s.dataset.title;
      document.getElementById('pnotes').textContent = s.querySelector('.notes')?.textContent || '';
      document.getElementById('pnext').textContent = slides[i+1] ? `${slides[i+1].dataset.title} (${slides[i+1].dataset.speaker})` : 'End';
      document.getElementById('ptarget').textContent = `target ${fmt(TARGET[spk])}`;
    };
    listen(m => m.type === 'at' && show(m.i));
    setInterval(() => {
      const e = (Date.now() - spkStart)/1000, el = document.getElementById('ptimer');
      el.textContent = fmt(e); el.classList.toggle('over', e > TARGET[spk]);
      document.getElementById('ptotal').textContent = totStart ? fmt((Date.now()-totStart)/1000) : '0:00';
    }, 250);
    addEventListener('keydown', e => {
      if (['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)) send({type:'go', d:1});
      if (['ArrowLeft','ArrowUp','PageUp'].includes(e.key)) send({type:'go', d:-1});
    });
    show(0); send({type:'hello'});
    return;
  }

  // ---- fit stage ----
  const stage = document.getElementById('stage');
  const fit = () => { const s = Math.min(innerWidth/1920, innerHeight/1080); stage.style.transform = `scale(${s})`; };
  addEventListener('resize', fit); fit();

  // ---- export mode: one slide, final state ----
  if (params.has('export')) {
    document.body.classList.add('static');
    const i = Math.max(0, Math.min(N-1, (+params.get('export')||1) - 1));
    slides[i].classList.add('active');
    Promise.all([document.fonts.ready, ...loads]).then(() => setTimeout(() => window.__ready = true, 300));
    return;
  }

  // ---- navigation with page-turn ----
  let cur = Math.max(0, Math.min(N-1, (parseInt(location.hash.slice(1))||1) - 1)), busy = false;
  slides[cur].classList.add('active');
  const go = to => {
    if (busy || to < 0 || to >= N || to === cur) return;
    busy = true;
    const from = slides[cur], next = slides[to];
    if (to > cur) {
      next.classList.add('active');
      from.classList.add('leaving');
      from.addEventListener('animationend', function h(e){ if (e.target !== from) return; from.removeEventListener('animationend', h); from.classList.remove('active','leaving'); busy = false; });
    } else {
      next.style.setProperty('--b', '1.0s');
      next.classList.add('active','arriving-back');
      next.addEventListener('animationend', function h(e){ if (e.target !== next) return; next.removeEventListener('animationend', h); next.classList.remove('arriving-back'); from.classList.remove('active'); next.style.removeProperty('--b'); busy = false; });
    }
    cur = to; history.replaceState(null, '', '#' + (cur+1)); send({type:'at', i:cur});
  };
  addEventListener('keydown', e => {
    if (['ArrowRight','ArrowDown','PageDown',' ','Enter'].includes(e.key)) { e.preventDefault(); go(cur+1); }
    else if (['ArrowLeft','ArrowUp','PageUp','Backspace'].includes(e.key)) { e.preventDefault(); go(cur-1); }
    else if (e.key === 'Home') go(0);
    else if (e.key === 'End') go(N-1);
    else if (e.key === 'f' || e.key === 'F') { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); }
    else if (e.key === 'p' || e.key === 'P') { window.open(location.pathname + '?presenter', 'presenter', 'width=1200,height=760'); setTimeout(() => send({type:'at', i:cur}), 600); }
  });
  addEventListener('click', e => { if (e.clientX > innerWidth/2) go(cur+1); else go(cur-1); });
  listen(m => { if (m.type === 'go') go(cur + m.d); if (m.type === 'hello') send({type:'at', i:cur}); });
  setTimeout(() => { const h = document.getElementById('hint'); if (h) h.style.opacity = 0; }, 4000);
})();
