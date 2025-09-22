const canvas = document.getElementById('pumpkin');
const ctx = canvas.getContext('2d');

const ASSETS_PATH = 'assets';
let meta = { head: { mouth_anchor: { x: 0.5, y: 0.65 }, mouth_scale: 1, canvas_size: [2048,2048] } };
const assets = { head: null, mouths: {} };
let currentMouth = 'mouth_closed';

// quick toggle to disable blink overlay
const DISABLE_BLINK = true;

// load helpers
async function fetchJson(p) { const r = await fetch(p); if (!r.ok) throw new Error('fetch failed'); return r.json(); }
function loadImg(src){ return new Promise(res=>{ const i=new Image(); i.onload=()=>res(i); i.onerror=()=>res(null); i.src=src; }); }

async function loadAll() {
  try { meta = await fetchJson(`${ASSETS_PATH}/head_meta.json`); } catch(e){ console.warn('head_meta.json missing, using defaults'); }
  assets.head = await loadImg(`${ASSETS_PATH}/plate_head.png`);
  // load any mouth_*.png present
  const mouthNames = ['closed','wide','o','ee','ah','oh','fv','th','smile','smirk'];
  for (const n of mouthNames) {
    const name = `mouth_${n}.png`;
    const img = await loadImg(`${ASSETS_PATH}/${name}`);
    if (img) assets.mouths[`mouth_${n}`] = img;
  }
  // debug: list what loaded
  console.log('Loaded mouth sprites:', Object.keys(assets.mouths));
}

let isBlinking = false;
let lastBlinkAt = 0;
let nextBlinkAt = performance.now() + 2000; // schedule first blink shortly after start
const blinkDuration = 120;

function draw() {
  ctx.clearRect(0,0,canvas.width,canvas.height);

  // bob:
  const t = performance.now()/800;
  const bob = Math.sin(t) * (Number(document.getElementById('bob')?.value || 1));

  if (assets.head) {
    ctx.save();
    ctx.shadowColor = 'rgba(255,150,30,0.6)';
    ctx.shadowBlur = 40 * (parseFloat(document.getElementById('glow')?.value || 1));
    // draw head with vertical bob
    ctx.drawImage(assets.head, 0, bob, canvas.width, canvas.height);
    ctx.restore();
  } else {
    ctx.fillStyle='#111'; ctx.fillRect(0,0,canvas.width,canvas.height);
  }

  // improved blink: timestamp-driven, no startup flash
  if (!DISABLE_BLINK) {
    const now = performance.now();
    const blinkRateVal = Number(document.getElementById('blinkRate')?.value || 3000);
    if (!isBlinking && now >= nextBlinkAt) {
      isBlinking = true;
      lastBlinkAt = now;
      nextBlinkAt = now + blinkRateVal + (Math.random() * 1200);
    }
    if (isBlinking && (now - lastBlinkAt) > blinkDuration) {
      isBlinking = false;
    }

    if (isBlinking) {
      ctx.fillStyle='rgba(10,6,6,0.9)';
      ctx.fillRect(canvas.width*0.28, canvas.height*0.14, canvas.width*0.44, canvas.height*0.12);
    }
  }

  // draw current mouth if available (ensure normal composite mode)
  ctx.globalCompositeOperation = 'source-over';
  const img = assets.mouths[currentMouth];
  if (img) {
    const anchor = meta.head?.mouth_anchor || {x:0.5,y:0.65};
    const scale = meta.head?.mouth_scale || 1.0;
    // apply the same bob offset to the mouth so it moves with the head
    const x = anchor.x * canvas.width;
    const y = (anchor.y * canvas.height) + bob;
    const w = canvas.width * 0.3 * scale;
    const h = canvas.height * 0.18 * scale;
    ctx.drawImage(img, x - w/2, y - h/2, w, h);
  }

  requestAnimationFrame(draw);
}

function mapLevelToSprite(level){
  // map 0..1 -> sprite names (simple)
  const idx = Math.max(0, Math.min(4, Math.round(level*4)));
  const map = ['mouth_closed','mouth_smile','mouth_o','mouth_wide','mouth_wide'];
  const candidate = map[idx];
  return (candidate && assets.mouths[candidate]) ? candidate : (Object.keys(assets.mouths)[0] || 'mouth_closed');
}

// start
loadAll().then(()=>{ requestAnimationFrame(draw); }).catch(e=>{ console.error(e); requestAnimationFrame(draw); });

// --- UI handlers (add this near the end of app.js) ---
document.getElementById('speakBtn').addEventListener('click', async () => {
  const btn = document.getElementById('speakBtn');
  btn.disabled = true;
  try {
    const resp = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}' // server may accept optional payload
    });
    if (!resp.ok) {
      const txt = await resp.text().catch(()=>String(resp.status));
      throw new Error(txt || 'generate failed');
    }
    const j = await resp.json();
    // if server returned playable assets, play them
    if (j.frames && j.audio) {
      const frames = await (await fetch(`/${j.frames}`)).json();
      const audio = new Audio(`/${j.audio}`);
      audio.preload = 'auto';
      await audio.play().catch(()=>{ /* autoplay may block; still proceed */ });
      const start = performance.now();
      for (const f of frames) {
        const t = Math.max(0, f.t * 1000 - (performance.now() - start));
        await new Promise(r => setTimeout(r, t));
        currentMouth = mapLevelToSprite(f.level);
      }
      currentMouth = 'mouth_closed';
    } else {
      // fallback visual if server did not return frames/audio
      currentMouth = 'mouth_smile';
      setTimeout(()=> currentMouth = 'mouth_closed', 1200);
    }
  } catch (err) {
    console.error('Generate failed', err);
    alert('Generate failed: ' + (err && err.message ? err.message : err));
  } finally {
    btn.disabled = false;
  }
});

document.getElementById('playBtn').addEventListener('click', async () => {
  const btn = document.getElementById('playBtn');
  btn.disabled = true;
  try {
    // simple replay fallback (if you later store frames in a variable, replace this)
    currentMouth = 'mouth_smile';
    await new Promise(r => setTimeout(r, 900));
    currentMouth = 'mouth_closed';
  } finally {
    btn.disabled = false;
  }
});
// --- end handlers ---