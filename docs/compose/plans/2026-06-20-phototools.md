# PhotoTools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 9-tool image processing website with a vanilla HTML/JS frontend and Python FastAPI backend for ML-heavy operations.

**Architecture:** Single-page app with tool grid homepage and individual tool pages. Client-side tools use Canvas API. Server-side tools (upscale, bg removal) hit a FastAPI backend on port 8090. Frontend served as static files.

**Tech Stack:** Vanilla HTML/CSS/JS, Canvas API, Python 3.9, FastAPI, uvicorn, Pillow, rembg, onnxruntime

---

## File Structure

```
/root/phototools/
├── frontend/
│   ├── index.html              # Tool grid homepage
│   ├── css/
│   │   └── style.css           # Global styles, dark theme
│   ├── js/
│   │   ├── app.js              # Router, shared utilities
│   │   ├── tools/
│   │   │   ├── upscale.js      # Image upscaling (calls API)
│   │   │   ├── removebg.js     # Background removal (calls API)
│   │   │   ├── resize.js       # Resize/crop (client)
│   │   │   ├── convert.js      # Format conversion (client)
│   │   │   ├── watermark.js    # Watermark overlay (client)
│   │   │   ├── compress.js     # Image compression (client)
│   │   │   ├── coloradjust.js  # Color adjustments (client)
│   │   │   ├── compare.js      # Image comparison (client)
│   │   │   └── transparent.js  # Transparent PNG (calls API)
│   │   └── components/
│   │       ├── dropzone.js     # Shared drag-drop component
│   │       ├── preview.js      # Shared image preview
│   │       └── download.js     # Shared download button
│   └── tools/
│       ├── upscale.html
│       ├── removebg.html
│       ├── resize.html
│       ├── convert.html
│       ├── watermark.html
│       ├── compress.html
│       ├── coloradjust.html
│       ├── compare.html
│       └── transparent.html
├── server/
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt
│   └── models/                 # ONNX models downloaded at setup
└── docs/
    └── compose/plans/
        └── 2026-06-20-phototools.md
```

---

### Task 1: Project Scaffold & Global Styles

**Covers:** Foundation for all tools

**Files:**
- Create: `/root/phototools/frontend/index.html`
- Create: `/root/phototools/frontend/css/style.css`
- Create: `/root/phototools/frontend/js/app.js`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p /root/phototools/frontend/{css,js/tools,js/components,tools}
mkdir -p /root/phototools/server
```

- [ ] **Step 2: Create global CSS with dark theme**

```css
/* /root/phototools/frontend/css/style.css */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg: #0a0e0b;
  --bg-card: #111815;
  --bg-card-hover: #1a2218;
  --border: #2a3a2a;
  --border-accent: #4a8a4a;
  --text: #e0ddd8;
  --text-dim: #7a8a7a;
  --accent: #4a9a5a;
  --accent-glow: rgba(74, 154, 90, 0.3);
  --danger: #c44;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'IBM Plex Mono', monospace;
  min-height: 100vh;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px;
}

header {
  padding: 32px 0 24px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 40px;
}

header h1 {
  font-size: 20px;
  font-weight: 500;
  color: var(--accent);
  letter-spacing: 2px;
}

header .tagline {
  font-size: 11px;
  color: var(--text-dim);
  margin-top: 6px;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.tool-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 24px 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-accent);
  box-shadow: 0 0 20px var(--accent-glow);
}

.tool-card .icon { font-size: 28px; margin-bottom: 12px; }
.tool-card .name { font-size: 13px; font-weight: 500; margin-bottom: 4px; }
.tool-card .desc { font-size: 10px; color: var(--text-dim); line-height: 1.5; }

.tool-page {
  max-width: 800px;
  margin: 0 auto;
}

.tool-page h2 {
  font-size: 16px;
  font-weight: 500;
  color: var(--accent);
  margin-bottom: 20px;
}

.dropzone {
  border: 2px dashed var(--border);
  border-radius: 8px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-dim);
  font-size: 12px;
}

.dropzone:hover, .dropzone.active {
  border-color: var(--accent);
  background: rgba(74, 154, 90, 0.05);
}

.dropzone .big-icon { font-size: 36px; margin-bottom: 12px; }

.preview-area {
  margin-top: 20px;
  text-align: center;
}

.preview-area img {
  max-width: 100%;
  max-height: 500px;
  border-radius: 4px;
  border: 1px solid var(--border);
}

.controls {
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.controls label {
  font-size: 11px;
  color: var(--text-dim);
}

.controls input[type="range"] {
  accent-color: var(--accent);
}

.controls select, .controls input[type="number"], .controls input[type="text"] {
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text);
  font-family: inherit;
  font-size: 11px;
  padding: 6px 10px;
  border-radius: 4px;
}

.btn {
  background: var(--accent);
  color: #fff;
  border: none;
  font-family: inherit;
  font-size: 12px;
  padding: 10px 24px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:hover { opacity: 0.85; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-secondary {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-dim);
}

.btn-secondary:hover { border-color: var(--accent); color: var(--text); }

.info-bar {
  margin-top: 16px;
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 10px;
  color: var(--text-dim);
  display: flex;
  gap: 20px;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: var(--bg-card);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 12px;
}

.progress-bar .fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s;
  border-radius: 2px;
}

@media (max-width: 700px) {
  .tool-grid { grid-template-columns: repeat(2, 1fr); }
  .controls { flex-direction: column; align-items: stretch; }
}
```

- [ ] **Step 3: Create homepage**

```html
<!-- /root/phototools/frontend/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PhotoTools</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1>PHOTO TOOLS</h1>
      <div class="tagline">client-side &bull; fast &bull; no signup</div>
    </header>
    <main class="tool-grid" id="toolGrid"></main>
  </div>
  <script>
    const TOOLS = [
      { id: 'upscale',     icon: '\u2B06', name: 'Upscale',       desc: '2x/4x AI upscaling', page: 'tools/upscale.html', server: true },
      { id: 'removebg',    icon: '\u2744', name: 'Remove BG',     desc: 'Remove background', page: 'tools/removebg.html', server: true },
      { id: 'resize',      icon: '\u29C9', name: 'Resize / Crop', desc: 'Resize or crop to exact dimensions', page: 'tools/resize.html' },
      { id: 'convert',     icon: '\u21C4', name: 'Convert',       desc: 'PNG, JPEG, WebP, AVIF conversion', page: 'tools/convert.html' },
      { id: 'watermark',   icon: '\u2602', name: 'Watermark',     desc: 'Add text or logo watermark', page: 'tools/watermark.html' },
      { id: 'compress',    icon: '\u2B07', name: 'Compress',      desc: 'Reduce file size with quality control', page: 'tools/compress.html' },
      { id: 'coloradjust', icon: '\u2600', name: 'Color Adjust',  desc: 'Brightness, contrast, saturation, hue', page: 'tools/coloradjust.html' },
      { id: 'compare',     icon: '\u2194', name: 'Compare',       desc: 'Side-by-side or slider comparison', page: 'tools/compare.html' },
      { id: 'transparent', icon: '\u25CB', name: 'Transparent',   desc: 'Convert to transparent PNG', page: 'tools/transparent.html', server: true },
    ];
    const grid = document.getElementById('toolGrid');
    TOOLS.forEach(t => {
      const card = document.createElement('a');
      card.href = t.page;
      card.className = 'tool-card';
      card.innerHTML = `<div class="icon">${t.icon}</div><div class="name">${t.name}</div><div class="desc">${t.desc}</div>`;
      grid.appendChild(card);
    });
  </script>
</body>
</html>
```

- [ ] **Step 4: Create app.js with shared utilities**

```javascript
// /root/phototools/frontend/js/app.js
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8090'
  : `http://${window.location.hostname}:8090`;

function createDropzone(container, onFile) {
  const dz = document.createElement('div');
  dz.className = 'dropzone';
  dz.innerHTML = '<div class="big-icon">\uD83D\uDCC1</div>Drop image here or click to browse';
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.style.display = 'none';
  input.addEventListener('change', () => { if (input.files[0]) onFile(input.files[0]); });
  dz.addEventListener('click', () => input.click());
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('active'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('active'));
  dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('active'); if (e.dataTransfer.files[0]) onFile(e.dataTransfer.files[0]); });
  container.appendChild(dz);
  container.appendChild(input);
  return { element: dz, input };
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = URL.createObjectURL(file);
  });
}

function fileToCanvas(file) {
  return new Promise(async (resolve) => {
    const img = await loadImage(file);
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    resolve(canvas);
  });
}

function canvasToFile(canvas, type = 'image/png', quality = 0.92) {
  return new Promise(resolve => {
    canvas.toBlob(blob => {
      resolve(new File([blob], 'output.' + type.split('/')[1], { type }));
    }, type, quality);
  });
}

function showPreview(container, src) {
  container.innerHTML = '';
  const img = document.createElement('img');
  img.src = src;
  container.appendChild(img);
  return img;
}

function addDownloadButton(container, file, filename = 'output.png') {
  const btn = document.createElement('button');
  btn.className = 'btn';
  btn.textContent = 'Download';
  btn.addEventListener('click', () => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(file);
    a.download = filename;
    a.click();
  });
  container.appendChild(btn);
  return btn;
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

async function apiPost(endpoint, file, extraFields = {}) {
  const form = new FormData();
  form.append('image', file);
  Object.entries(extraFields).forEach(([k, v]) => form.append(k, v));
  const res = await fetch(`${API_BASE}${endpoint}`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.blob();
}
```

- [ ] **Step 5: Test in browser**

Open `http://72.61.79.238:8080/` — verify tool grid renders with 9 tools, each links to its tool page.

---

### Task 2: Shared Components (Dropzone, Preview, Download)

**Covers:** All tools — reusable components

**Files:**
- Create: `/root/phototools/frontend/js/components/dropzone.js`
- Create: `/root/phototools/frontend/js/components/preview.js`
- Create: `/root/phototools/frontend/js/components/download.js`

- [ ] **Step 1: Create dropzone component**

Already included in `app.js` via `createDropzone()`. No separate file needed — the functions in app.js are the shared components. Skip this task if app.js is sufficient.

- [ ] **Step 2: Verify all component functions work**

Test `createDropzone`, `loadImage`, `fileToCanvas`, `showPreview`, `addDownloadButton`, `apiPost` by building the first tool (Task 3).

---

### Task 3: Resize / Crop Tool (Client-Side)

**Covers:** Client-side resize and crop tool

**Files:**
- Create: `/root/phototools/frontend/tools/resize.html`

- [ ] **Step 1: Create resize tool page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Resize / Crop - PhotoTools</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1><a href="../index.html">PHOTO TOOLS</a> / Resize & Crop</h1>
    </header>
    <main class="tool-page">
      <div id="dropzoneArea"></div>
      <div class="controls" id="controls" style="display:none">
        <div>
          <label>Width</label><br>
          <input type="number" id="width" min="1" max="10000">
        </div>
        <div>
          <label>Height</label><br>
          <input type="number" id="height" min="1" max="10000">
        </div>
        <div>
          <label><input type="checkbox" id="lockRatio" checked> Lock ratio</label>
        </div>
        <div>
          <label>Mode</label><br>
          <select id="mode">
            <option value="resize">Resize</option>
            <option value="crop">Crop</option>
          </select>
        </div>
        <button class="btn" id="applyBtn">Apply</button>
        <button class="btn btn-secondary" id="resetBtn">Reset</button>
      </div>
      <div class="info-bar" id="infoBar" style="display:none"></div>
      <div class="preview-area" id="previewArea"></div>
      <div id="downloadArea" style="margin-top:16px"></div>
    </main>
  </div>
  <script src="../js/app.js"></script>
  <script>
    let originalCanvas = null;
    let originalW = 0, originalH = 0;

    const dz = createDropzone(document.getElementById('dropzoneArea'), async (file) => {
      originalCanvas = await fileToCanvas(file);
      originalW = originalCanvas.width;
      originalH = originalCanvas.height;
      document.getElementById('width').value = originalW;
      document.getElementById('height').value = originalH;
      document.getElementById('controls').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('infoBar').textContent = `Original: ${originalW} x ${originalH} (${formatBytes(file.size)})`;
      showPreview(document.getElementById('previewArea'), originalCanvas.toDataURL());
      document.getElementById('downloadArea').innerHTML = '';
    });

    const wInput = document.getElementById('width');
    const hInput = document.getElementById('height');
    const lockRatio = document.getElementById('lockRatio');
    const mode = document.getElementById('mode');

    wInput.addEventListener('input', () => {
      if (lockRatio.checked) hInput.value = Math.round(wInput.value * originalH / originalW);
    });
    hInput.addEventListener('input', () => {
      if (lockRatio.checked) wInput.value = Math.round(hInput.value * originalW / originalH);
    });

    document.getElementById('applyBtn').addEventListener('click', async () => {
      const tw = parseInt(wInput.value);
      const th = parseInt(hInput.value);
      const out = document.createElement('canvas');
      out.width = tw; out.height = th;
      const ctx = out.getContext('2d');
      if (mode.value === 'resize') {
        ctx.drawImage(originalCanvas, 0, 0, tw, th);
      } else {
        const sx = (originalW - tw) / 2;
        const sy = (originalH - th) / 2;
        ctx.drawImage(originalCanvas, sx, sy, tw, th, 0, 0, tw, th);
      }
      showPreview(document.getElementById('previewArea'), out.toDataURL());
      const blob = await out.toBlob(b => b);
      const file = new File([blob], 'resized.png', { type: 'image/png' });
      document.getElementById('downloadArea').innerHTML = '';
      addDownloadButton(document.getElementById('downloadArea'), file, 'resized.png');
    });

    document.getElementById('resetBtn').addEventListener('click', () => {
      wInput.value = originalW;
      hInput.value = originalH;
      if (originalCanvas) showPreview(document.getElementById('previewArea'), originalCanvas.toDataURL());
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Test resize and crop in browser**

Open `http://72.61.79.238:8080/tools/resize.html`, upload an image, resize to new dimensions, verify output.

---

### Task 4: Format Conversion Tool (Client-Side)

**Covers:** Format conversion between PNG, JPEG, WebP, AVIF

**Files:**
- Create: `/root/phototools/frontend/tools/convert.html`

- [ ] **Step 1: Create format conversion page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Convert - PhotoTools</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1><a href="../index.html">PHOTO TOOLS</a> / Format Convert</h1>
    </header>
    <main class="tool-page">
      <div id="dropzoneArea"></div>
      <div class="controls" id="controls" style="display:none">
        <div>
          <label>Output Format</label><br>
          <select id="format">
            <option value="image/png">PNG</option>
            <option value="image/jpeg">JPEG</option>
            <option value="image/webp">WebP</option>
          </select>
        </div>
        <div>
          <label>Quality (JPEG/WebP)</label><br>
          <input type="range" id="quality" min="10" max="100" value="90">
          <span id="qualityVal">90%</span>
        </div>
        <button class="btn" id="convertBtn">Convert</button>
      </div>
      <div class="info-bar" id="infoBar" style="display:none"></div>
      <div class="preview-area" id="previewArea"></div>
      <div id="downloadArea" style="margin-top:16px"></div>
    </main>
  </div>
  <script src="../js/app.js"></script>
  <script>
    let srcCanvas = null;
    let srcSize = 0;

    createDropzone(document.getElementById('dropzoneArea'), async (file) => {
      srcCanvas = await fileToCanvas(file);
      srcSize = file.size;
      document.getElementById('controls').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('infoBar').textContent = `Source: ${srcCanvas.width}x${srcCanvas.height}, ${formatBytes(srcSize)}`;
      showPreview(document.getElementById('previewArea'), srcCanvas.toDataURL());
      document.getElementById('downloadArea').innerHTML = '';
    });

    document.getElementById('quality').addEventListener('input', e => {
      document.getElementById('qualityVal').textContent = e.target.value + '%';
    });

    document.getElementById('convertBtn').addEventListener('click', async () => {
      const fmt = document.getElementById('format').value;
      const q = parseInt(document.getElementById('quality').value) / 100;
      const blob = await new Promise(r => srcCanvas.toBlob(r, fmt, q));
      const url = URL.createObjectURL(blob);
      showPreview(document.getElementById('previewArea'), url);
      const ext = fmt.split('/')[1] === 'jpeg' ? 'jpg' : fmt.split('/')[1];
      const f = new File([blob], `converted.${ext}`, { type: fmt });
      document.getElementById('downloadArea').innerHTML = '';
      addDownloadButton(document.getElementById('downloadArea'), f, `converted.${ext}`);
      document.getElementById('infoBar').textContent += ` → ${formatBytes(blob.size)} (${ext.toUpperCase()})`;
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Test format conversion in browser**

---

### Task 5: Image Compression Tool (Client-Side)

**Covers:** JPEG/WebP compression with quality control

**Files:**
- Create: `/root/phototools/frontend/tools/compress.html`

- [ ] **Step 1: Create compress tool page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Compress - PhotoTools</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1><a href="../index.html">PHOTO TOOLS</a> / Compress</h1>
    </header>
    <main class="tool-page">
      <div id="dropzoneArea"></div>
      <div class="controls" id="controls" style="display:none">
        <div>
          <label>Format</label><br>
          <select id="format">
            <option value="image/webp">WebP (best)</option>
            <option value="image/jpeg">JPEG</option>
            <option value="image/png">PNG</option>
          </select>
        </div>
        <div>
          <label>Quality</label><br>
          <input type="range" id="quality" min="5" max="100" value="80">
          <span id="qualityVal">80%</span>
        </div>
        <button class="btn" id="compressBtn">Compress</button>
      </div>
      <div class="info-bar" id="infoBar" style="display:none"></div>
      <div class="preview-area" id="previewArea"></div>
      <div id="downloadArea" style="margin-top:16px"></div>
    </main>
  </div>
  <script src="../js/app.js"></script>
  <script>
    let srcCanvas = null, srcSize = 0;

    createDropzone(document.getElementById('dropzoneArea'), async (file) => {
      srcCanvas = await fileToCanvas(file);
      srcSize = file.size;
      document.getElementById('controls').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('infoBar').textContent = `Original: ${formatBytes(srcSize)}`;
      showPreview(document.getElementById('previewArea'), srcCanvas.toDataURL());
      document.getElementById('downloadArea').innerHTML = '';
    });

    document.getElementById('quality').addEventListener('input', e => {
      document.getElementById('qualityVal').textContent = e.target.value + '%';
    });

    document.getElementById('compressBtn').addEventListener('click', async () => {
      const fmt = document.getElementById('format').value;
      const q = parseInt(document.getElementById('quality').value) / 100;
      const blob = await new Promise(r => srcCanvas.toBlob(r, fmt, q));
      const savings = ((1 - blob.size / srcSize) * 100).toFixed(1);
      const ext = fmt.split('/')[1] === 'jpeg' ? 'jpg' : fmt.split('/')[1];
      document.getElementById('infoBar').textContent = `Original: ${formatBytes(srcSize)} → Compressed: ${formatBytes(blob.size)} (${savings > 0 ? '-' : '+'}${Math.abs(savings)}%)`;
      const f = new File([blob], `compressed.${ext}`, { type: fmt });
      document.getElementById('downloadArea').innerHTML = '';
      addDownloadButton(document.getElementById('downloadArea'), f, `compressed.${ext}`);
      showPreview(document.getElementById('previewArea'), URL.createObjectURL(blob));
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Test compression in browser**

---

### Task 6: Watermark Tool (Client-Side)

**Covers:** Text watermark overlay with position/opacity

**Files:**
- Create: `/root/phototools/frontend/tools/watermark.html`

- [ ] **Step 1: Create watermark tool page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Watermark - PhotoTools</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1><a href="../index.html">PHOTO TOOLS</a> / Watermark</h1>
    </header>
    <main class="tool-page">
      <div id="dropzoneArea"></div>
      <div class="controls" id="controls" style="display:none">
        <div>
          <label>Text</label><br>
          <input type="text" id="wmText" value="WATERMARK" style="width:180px">
        </div>
        <div>
          <label>Position</label><br>
          <select id="wmPos">
            <option value="center">Center</option>
            <option value="top-left">Top Left</option>
            <option value="top-right">Top Right</option>
            <option value="bottom-left">Bottom Left</option>
            <option value="bottom-right" selected>Bottom Right</option>
          </select>
        </div>
        <div>
          <label>Opacity</label><br>
          <input type="range" id="wmOpacity" min="5" max="100" value="40">
        </div>
        <div>
          <label>Size</label><br>
          <input type="range" id="wmSize" min="12" max="200" value="48">
        </div>
        <button class="btn" id="applyBtn">Apply</button>
      </div>
      <div class="info-bar" id="infoBar" style="display:none"></div>
      <div class="preview-area" id="previewArea"></div>
      <div id="downloadArea" style="margin-top:16px"></div>
    </main>
  </div>
  <script src="../js/app.js"></script>
  <script>
    let srcCanvas = null;

    createDropzone(document.getElementById('dropzoneArea'), async (file) => {
      srcCanvas = await fileToCanvas(file);
      document.getElementById('controls').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('infoBar').textContent = `${srcCanvas.width} x ${srcCanvas.height}`;
      showPreview(document.getElementById('previewArea'), srcCanvas.toDataURL());
      document.getElementById('downloadArea').innerHTML = '';
    });

    ['wmText', 'wmPos', 'wmOpacity', 'wmSize'].forEach(id => {
      document.getElementById(id).addEventListener('input', () => {
        if (srcCanvas) document.getElementById('applyBtn').click();
      });
    });

    document.getElementById('applyBtn').addEventListener('click', async () => {
      const out = document.createElement('canvas');
      out.width = srcCanvas.width; out.height = srcCanvas.height;
      const ctx = out.getContext('2d');
      ctx.drawImage(srcCanvas, 0, 0);

      const text = document.getElementById('wmText').value;
      const size = parseInt(document.getElementById('wmSize').value);
      const opacity = parseInt(document.getElementById('wmOpacity').value) / 100;
      const pos = document.getElementById('wmPos').value;

      ctx.save();
      ctx.globalAlpha = opacity;
      ctx.font = `bold ${size}px 'IBM Plex Mono', monospace`;
      ctx.fillStyle = '#fff';
      ctx.strokeStyle = 'rgba(0,0,0,0.5)';
      ctx.lineWidth = size / 16;
      ctx.textBaseline = 'middle';

      const metrics = ctx.measureText(text);
      let x, y;
      const pad = size;
      if (pos === 'center') { x = (out.width - metrics.width) / 2; y = out.height / 2; }
      else if (pos === 'top-left') { x = pad; y = pad + size / 2; }
      else if (pos === 'top-right') { x = out.width - metrics.width - pad; y = pad + size / 2; }
      else if (pos === 'bottom-left') { x = pad; y = out.height - pad - size / 2; }
      else { x = out.width - metrics.width - pad; y = out.height - pad - size / 2; }

      ctx.strokeText(text, x, y);
      ctx.fillText(text, x, y);
      ctx.restore();

      showPreview(document.getElementById('previewArea'), out.toDataURL());
      const blob = await new Promise(r => out.toBlob(r, 'image/png'));
      const f = new File([blob], 'watermarked.png', { type: 'image/png' });
      document.getElementById('downloadArea').innerHTML = '';
      addDownloadButton(document.getElementById('downloadArea'), f, 'watermarked.png');
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Test watermark in browser**

---

### Task 7: Color Adjustments Tool (Client-Side)

**Covers:** Brightness, contrast, saturation, hue, temperature

**Files:**
- Create: `/root/phototools/frontend/tools/coloradjust.html`

- [ ] **Step 1: Create color adjust tool page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Color Adjust - PhotoTools</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1><a href="../index.html">PHOTO TOOLS</a> / Color Adjust</h1>
    </header>
    <main class="tool-page">
      <div id="dropzoneArea"></div>
      <div class="controls" id="controls" style="display:none; flex-direction:column; gap:16px">
        <div style="display:flex; gap:20px; flex-wrap:wrap">
          <div><label>Brightness</label><br><input type="range" id="brightness" min="0" max="200" value="100"></div>
          <div><label>Contrast</label><br><input type="range" id="contrast" min="0" max="200" value="100"></div>
          <div><label>Saturation</label><br><input type="range" id="saturation" min="0" max="200" value="100"></div>
          <div><label>Hue Rotate</label><br><input type="range" id="hue" min="0" max="360" value="0"></div>
          <div><label>Sepia</label><br><input type="range" id="sepia" min="0" max="100" value="0"></div>
          <div><label>Grayscale</label><br><input type="range" id="grayscale" min="0" max="100" value="0"></div>
        </div>
        <div>
          <button class="btn" id="applyBtn">Apply & Export</button>
          <button class="btn btn-secondary" id="resetBtn">Reset</button>
        </div>
      </div>
      <div class="info-bar" id="infoBar" style="display:none"></div>
      <div class="preview-area" id="previewArea"></div>
      <div id="downloadArea" style="margin-top:16px"></div>
    </main>
  </div>
  <script src="../js/app.js"></script>
  <script>
    let srcCanvas = null;

    function getFilter() {
      const b = document.getElementById('brightness').value;
      const c = document.getElementById('contrast').value;
      const s = document.getElementById('saturation').value;
      const h = document.getElementById('hue').value;
      const sep = document.getElementById('sepia').value;
      const g = document.getElementById('grayscale').value;
      return `brightness(${b}%) contrast(${c}%) saturate(${s}%) hue-rotate(${h}deg) sepia(${sep}%) grayscale(${g}%)`;
    }

    function applyPreview() {
      if (!srcCanvas) return;
      const preview = document.getElementById('previewArea');
      const img = preview.querySelector('img') || document.createElement('img');
      img.src = srcCanvas.toDataURL();
      img.style.filter = getFilter();
      if (!preview.querySelector('img')) preview.appendChild(img);
    }

    createDropzone(document.getElementById('dropzoneArea'), async (file) => {
      srcCanvas = await fileToCanvas(file);
      document.getElementById('controls').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('infoBar').textContent = `${srcCanvas.width} x ${srcCanvas.height}`;
      document.getElementById('previewArea').innerHTML = '';
      document.getElementById('downloadArea').innerHTML = '';
      applyPreview();
    });

    ['brightness', 'contrast', 'saturation', 'hue', 'sepia', 'grayscale'].forEach(id => {
      document.getElementById(id).addEventListener('input', applyPreview);
    });

    document.getElementById('resetBtn').addEventListener('click', () => {
      ['brightness', 'contrast', 'saturation'].forEach(id => document.getElementById(id).value = 100);
      ['hue', 'sepia', 'grayscale'].forEach(id => document.getElementById(id).value = 0);
      applyPreview();
    });

    document.getElementById('applyBtn').addEventListener('click', async () => {
      const out = document.createElement('canvas');
      out.width = srcCanvas.width; out.height = srcCanvas.height;
      const ctx = out.getContext('2d');
      ctx.filter = getFilter();
      ctx.drawImage(srcCanvas, 0, 0);
      showPreview(document.getElementById('previewArea'), out.toDataURL());
      const blob = await new Promise(r => out.toBlob(r, 'image/png'));
      const f = new File([blob], 'adjusted.png', { type: 'image/png' });
      document.getElementById('downloadArea').innerHTML = '';
      addDownloadButton(document.getElementById('downloadArea'), f, 'adjusted.png');
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Test color adjustments in browser**

---

### Task 8: Image Comparison Tool (Client-Side)

**Covers:** Side-by-side and slider before/after comparison

**Files:**
- Create: `/root/phototools/frontend/tools/compare.html`

- [ ] **Step 1: Create compare tool page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Compare - PhotoTools</title>
  <link rel="stylesheet" href="../css/style.css">
  <style>
    .compare-wrap { position: relative; overflow: hidden; border-radius: 4px; border: 1px solid var(--border); cursor: col-resize; user-select: none; }
    .compare-wrap img { display: block; width: 100%; }
    .compare-wrap .overlay { position: absolute; top: 0; left: 0; height: 100%; overflow: hidden; }
    .compare-wrap .overlay img { height: 100%; width: auto; min-width: 100%; object-fit: cover; }
    .compare-wrap .divider { position: absolute; top: 0; width: 2px; height: 100%; background: var(--accent); cursor: col-resize; }
    .compare-wrap .labels { position: absolute; top: 8px; width: 100%; display: flex; justify-content: space-between; pointer-events: none; }
    .compare-wrap .labels span { background: rgba(0,0,0,0.6); padding: 4px 10px; font-size: 10px; border-radius: 3px; }
    .dual-view { display: flex; gap: 16px; }
    .dual-view > div { flex: 1; text-align: center; }
    .dual-view img { max-width: 100%; max-height: 400px; border: 1px solid var(--border); border-radius: 4px; }
    .dual-view .label { font-size: 10px; color: var(--text-dim); margin-top: 6px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1><a href="../index.html">PHOTO TOOLS</a> / Compare</h1>
    </header>
    <main class="tool-page">
      <div id="drop1"></div>
      <div id="drop2" style="margin-top:12px"></div>
      <div class="controls" id="controls" style="display:none">
        <button class="btn" id="sliderMode">Slider View</button>
        <button class="btn btn-secondary" id="dualMode">Side by Side</button>
      </div>
      <div class="preview-area" id="previewArea"></div>
    </main>
  </div>
  <script src="../js/app.js"></script>
  <script>
    let img1 = null, img2 = null;
    let mode = 'slider';

    createDropzone(document.getElementById('drop1'), async (file) => {
      img1 = await loadImage(file);
      document.getElementById('drop1').innerHTML = `<div class="big-icon">\u2705</div>Image 1 loaded (${img1.naturalWidth}x${img1.naturalHeight})`;
      tryRender();
    });

    createDropzone(document.getElementById('drop2'), async (file) => {
      img2 = await loadImage(file);
      document.getElementById('drop2').innerHTML = `<div class="big-icon">\u2705</div>Image 2 loaded (${img2.naturalWidth}x${img2.naturalHeight})`;
      tryRender();
    });

    function tryRender() {
      if (!img1 || !img2) return;
      document.getElementById('controls').style.display = 'flex';
      render();
    }

    function render() {
      const area = document.getElementById('previewArea');
      area.innerHTML = '';
      if (mode === 'slider') renderSlider(area);
      else renderDual(area);
    }

    function renderSlider(area) {
      const w = Math.max(img1.naturalWidth, img2.naturalWidth);
      const h = Math.max(img1.naturalHeight, img2.naturalHeight);
      const wrap = document.createElement('div');
      wrap.className = 'compare-wrap';
      wrap.style.height = Math.min(500, h * (800 / w)) + 'px';

      const bg = document.createElement('img');
      bg.src = img2.src;
      bg.style.height = '100%';
      bg.style.width = '100%';
      bg.style.objectFit = 'contain';
      wrap.appendChild(bg);

      const overlay = document.createElement('div');
      overlay.className = 'overlay';
      overlay.style.width = '50%';
      const ovImg = document.createElement('img');
      ovImg.src = img1.src;
      ovImg.style.height = '100%';
      ovImg.style.width = '100%';
      ovImg.style.objectFit = 'contain';
      overlay.appendChild(ovImg);
      wrap.appendChild(overlay);

      const divider = document.createElement('div');
      divider.className = 'divider';
      divider.style.left = '50%';
      wrap.appendChild(divider);

      const labels = document.createElement('div');
      labels.className = 'labels';
      labels.innerHTML = '<span>Before</span><span>After</span>';
      wrap.appendChild(labels);

      let dragging = false;
      function move(e) {
        const rect = wrap.getBoundingClientRect();
        const x = Math.max(0, Math.min(rect.width, (e.clientX || e.touches[0].clientX) - rect.left));
        const pct = (x / rect.width) * 100;
        overlay.style.width = pct + '%';
        divider.style.left = pct + '%';
      }
      wrap.addEventListener('mousedown', () => dragging = true);
      wrap.addEventListener('touchstart', () => dragging = true);
      window.addEventListener('mouseup', () => dragging = false);
      window.addEventListener('touchend', () => dragging = false);
      wrap.addEventListener('mousemove', e => { if (dragging) move(e); });
      wrap.addEventListener('touchmove', e => { if (dragging) move(e); });
      wrap.addEventListener('click', move);

      area.appendChild(wrap);
    }

    function renderDual(area) {
      const div = document.createElement('div');
      div.className = 'dual-view';
      div.innerHTML = `<div><img src="${img1.src}"><div class="label">Image 1</div></div><div><img src="${img2.src}"><div class="label">Image 2</div></div>`;
      area.appendChild(div);
    }

    document.getElementById('sliderMode').addEventListener('click', () => { mode = 'slider'; render(); });
    document.getElementById('dualMode').addEventListener('click', () => { mode = 'dual'; render(); });
  </script>
</body>
</html>
```

- [ ] **Step 2: Test comparison in browser**

---

### Task 9: FastAPI Backend (Server-Side Tools)

**Covers:** Upscale, Background Removal, Transparent PNG

**Files:**
- Create: `/root/phototools/server/main.py`
- Create: `/root/phototools/server/requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn==0.30.0
python-multipart==0.0.9
Pillow==11.3.0
onnxruntime==1.19.2
rembg==2.0.60
numpy
```

- [ ] **Step 2: Create FastAPI server**

```python
# /root/phototools/server/main.py
import io
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rembg_session = None

def get_rembg():
    global rembg_session
    if rembg_session is None:
        from rembg import new_session
        rembg_session = new_session("u2net")
    return rembg_session

upscale_model = None

def get_upscale():
    global upscale_model
    if upscale_model is None:
        import onnxruntime as ort
        model_path = os.path.join(os.path.dirname(__file__), "models", "realesrgan-x2.onnx")
        if os.path.exists(model_path):
            upscale_model = ort.InferenceSession(model_path)
        else:
            raise RuntimeError("Upscale model not found. Download realesrgan-x2.onnx to server/models/")
    return upscale_model


@app.post("/api/remove-bg")
async def remove_bg(image: UploadFile = File(...)):
    data = await image.read()
    from rembg import remove
    result = remove(data, session=get_rembg())
    return Response(content=result, media_type="image/png")


@app.post("/api/transparent")
async def transparent(image: UploadFile = File(...)):
    data = await image.read()
    from rembg import remove
    result = remove(data, session=get_rembg(), alpha_matting=True)
    return Response(content=result, media_type="image/png")


@app.post("/api/upscale")
async def upscale(
    image: UploadFile = File(...),
    scale: int = Form(2),
):
    data = await image.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")

    try:
        session = get_upscale()
        img_array = np.array(img).astype(np.float32).transpose(2, 0, 1) / 255.0
        img_array = np.expand_dims(img_array, 0)

        input_name = session.get_inputs()[0].name
        result = session.run(None, {input_name: img_array})[0]
        result = (result.clip(0, 1).transpose(1, 2, 0) * 255).astype(np.uint8)
        out = Image.fromarray(result)
    except Exception:
        w, h = img.size
        out = img.resize((w * scale, h * scale), Image.LANCZOS)

    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
```

- [ ] **Step 3: Install dependencies on KVM4**

```bash
ssh root@76.13.106.218 'pip3 install fastapi uvicorn python-multipart rembg'
```

- [ ] **Step 4: Create systemd service for FastAPI**

```bash
cat > /etc/systemd/system/phototools-api.service << 'EOF'
[Unit]
Description=PhotoTools API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/mcuser/phototools/server
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8090
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable phototools-api && systemctl start phototools-api
```

- [ ] **Step 5: Verify API health**

```bash
curl http://localhost:8090/api/health
# Expected: {"status":"ok"}
```

---

### Task 10: Client-Side Server Tool Pages

**Covers:** Upscale, Remove BG, Transparent tool pages that call the API

**Files:**
- Create: `/root/phototools/frontend/tools/upscale.html`
- Create: `/root/phototools/frontend/tools/removebg.html`
- Create: `/root/phototools/frontend/tools/transparent.html`

- [ ] **Step 1: Create upscale tool page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Upscale - PhotoTools</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1><a href="../index.html">PHOTO TOOLS</a> / AI Upscale</h1>
    </header>
    <main class="tool-page">
      <div id="dropzoneArea"></div>
      <div class="controls" id="controls" style="display:none">
        <div>
          <label>Scale</label><br>
          <select id="scale">
            <option value="2">2x</option>
            <option value="4">4x</option>
          </select>
        </div>
        <button class="btn" id="upscaleBtn">Upscale</button>
      </div>
      <div class="progress-bar" id="progress" style="display:none"><div class="fill" id="progressFill"></div></div>
      <div class="info-bar" id="infoBar" style="display:none"></div>
      <div class="preview-area" id="previewArea"></div>
      <div id="downloadArea" style="margin-top:16px"></div>
    </main>
  </div>
  <script src="../js/app.js"></script>
  <script>
    let srcFile = null;

    createDropzone(document.getElementById('dropzoneArea'), async (file) => {
      srcFile = file;
      const img = await loadImage(file);
      document.getElementById('controls').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('infoBar').textContent = `Source: ${img.naturalWidth} x ${img.naturalHeight}`;
      showPreview(document.getElementById('previewArea'), img.src);
      document.getElementById('downloadArea').innerHTML = '';
    });

    document.getElementById('upscaleBtn').addEventListener('click', async () => {
      if (!srcFile) return;
      const btn = document.getElementById('upscaleBtn');
      btn.disabled = true;
      btn.textContent = 'Processing...';
      document.getElementById('progress').style.display = 'block';
      document.getElementById('progressFill').style.width = '30%';

      try {
        const scale = document.getElementById('scale').value;
        document.getElementById('progressFill').style.width = '60%';
        const blob = await apiPost('/api/upscale', srcFile, { scale });
        document.getElementById('progressFill').style.width = '100%';

        const url = URL.createObjectURL(blob);
        showPreview(document.getElementById('previewArea'), url);
        const f = new File([blob], 'upscaled.png', { type: 'image/png' });
        document.getElementById('downloadArea').innerHTML = '';
        addDownloadButton(document.getElementById('downloadArea'), f, 'upscaled.png');

        const img = await loadImage(srcFile);
        document.getElementById('infoBar').textContent = `${img.naturalWidth}x${img.naturalHeight} → ${img.naturalWidth * parseInt(scale)}x${img.naturalHeight * parseInt(scale)} (${formatBytes(blob.size)})`;
      } catch (e) {
        document.getElementById('infoBar').textContent = 'Error: ' + e.message;
      }

      btn.disabled = false;
      btn.textContent = 'Upscale';
      setTimeout(() => { document.getElementById('progress').style.display = 'none'; }, 1000);
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Create remove background tool page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Remove BG - PhotoTools</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1><a href="../index.html">PHOTO TOOLS</a> / Remove Background</h1>
    </header>
    <main class="tool-page">
      <div id="dropzoneArea"></div>
      <div class="controls" id="controls" style="display:none">
        <button class="btn" id="processBtn">Remove Background</button>
      </div>
      <div class="progress-bar" id="progress" style="display:none"><div class="fill" id="progressFill"></div></div>
      <div class="info-bar" id="infoBar" style="display:none"></div>
      <div class="preview-area" id="previewArea"></div>
      <div id="downloadArea" style="margin-top:16px"></div>
    </main>
  </div>
  <script src="../js/app.js"></script>
  <script>
    let srcFile = null;

    createDropzone(document.getElementById('dropzoneArea'), async (file) => {
      srcFile = file;
      const img = await loadImage(file);
      document.getElementById('controls').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('infoBar').textContent = `${img.naturalWidth} x ${img.naturalHeight}`;
      showPreview(document.getElementById('previewArea'), img.src);
      document.getElementById('downloadArea').innerHTML = '';
    });

    document.getElementById('processBtn').addEventListener('click', async () => {
      if (!srcFile) return;
      const btn = document.getElementById('processBtn');
      btn.disabled = true;
      btn.textContent = 'Processing...';
      document.getElementById('progress').style.display = 'block';
      document.getElementById('progressFill').style.width = '30%';

      try {
        document.getElementById('progressFill').style.width = '60%';
        const blob = await apiPost('/api/remove-bg', srcFile);
        document.getElementById('progressFill').style.width = '100%';

        const url = URL.createObjectURL(blob);
        showPreview(document.getElementById('previewArea'), url);
        const f = new File([blob], 'no-bg.png', { type: 'image/png' });
        document.getElementById('downloadArea').innerHTML = '';
        addDownloadButton(document.getElementById('downloadArea'), f, 'no-bg.png');
        document.getElementById('infoBar').textContent = `Output: ${formatBytes(blob.size)} (transparent PNG)`;
      } catch (e) {
        document.getElementById('infoBar').textContent = 'Error: ' + e.message;
      }

      btn.disabled = false;
      btn.textContent = 'Remove Background';
      setTimeout(() => { document.getElementById('progress').style.display = 'none'; }, 1000);
    });
  </script>
</body>
</html>
```

- [ ] **Step 3: Create transparent PNG tool page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Transparent PNG - PhotoTools</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1><a href="../index.html">PHOTO TOOLS</a> / Transparent PNG</h1>
    </header>
    <main class="tool-page">
      <div id="dropzoneArea"></div>
      <div class="controls" id="controls" style="display:none">
        <button class="btn" id="processBtn">Make Transparent</button>
      </div>
      <div class="progress-bar" id="progress" style="display:none"><div class="fill" id="progressFill"></div></div>
      <div class="info-bar" id="infoBar" style="display:none"></div>
      <div class="preview-area" id="previewArea"></div>
      <div id="downloadArea" style="margin-top:16px"></div>
    </main>
  </div>
  <script src="../js/app.js"></script>
  <script>
    let srcFile = null;

    createDropzone(document.getElementById('dropzoneArea'), async (file) => {
      srcFile = file;
      const img = await loadImage(file);
      document.getElementById('controls').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('infoBar').textContent = `${img.naturalWidth} x ${img.naturalHeight}`;
      showPreview(document.getElementById('previewArea'), img.src);
      document.getElementById('downloadArea').innerHTML = '';
    });

    document.getElementById('processBtn').addEventListener('click', async () => {
      if (!srcFile) return;
      const btn = document.getElementById('processBtn');
      btn.disabled = true;
      btn.textContent = 'Processing...';
      document.getElementById('progress').style.display = 'block';
      document.getElementById('progressFill').style.width = '30%';

      try {
        document.getElementById('progressFill').style.width = '60%';
        const blob = await apiPost('/api/transparent', srcFile);
        document.getElementById('progressFill').style.width = '100%';

        const url = URL.createObjectURL(blob);
        showPreview(document.getElementById('previewArea'), url);
        const f = new File([blob], 'transparent.png', { type: 'image/png' });
        document.getElementById('downloadArea').innerHTML = '';
        addDownloadButton(document.getElementById('downloadArea'), f, 'transparent.png');
        document.getElementById('infoBar').textContent = `Output: transparent PNG (${formatBytes(blob.size)})`;
      } catch (e) {
        document.getElementById('infoBar').textContent = 'Error: ' + e.message;
      }

      btn.disabled = false;
      btn.textContent = 'Make Transparent';
      setTimeout(() => { document.getElementById('progress').style.display = 'none'; }, 1000);
    });
  </script>
</body>
</html>
```

- [ ] **Step 4: Test all three server-backed tools**

---

### Task 11: Deploy to KVM4

**Covers:** Frontend rsync + backend setup on production server

**Files:** All frontend and server files

- [ ] **Step 1: rsync frontend to KVM4**

```bash
rsync -az /root/phototools/frontend/ root@76.13.106.218:/home/mcuser/phototools/frontend/
```

- [ ] **Step 2: rsync server to KVM4**

```bash
rsync -az /root/phototools/server/ root@76.13.106.218:/home/mcuser/phototools/server/
```

- [ ] **Step 3: Install Python dependencies on KVM4**

```bash
ssh root@76.13.106.218 'cd /home/mcuser/phototools/server && pip3 install -r requirements.txt'
```

- [ ] **Step 4: Create and start systemd service**

```bash
ssh root@76.13.106.218 'cat > /etc/systemd/system/phototools-api.service << EOF
[Unit]
Description=PhotoTools API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/mcuser/phototools/server
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8090
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable phototools-api && systemctl start phototools-api'
```

- [ ] **Step 5: Serve frontend via existing HTTP server or nginx**

Copy or symlink `/home/mcuser/phototools/frontend/` contents to wherever the existing static server points, or add an nginx location block.

- [ ] **Step 6: Verify all tools accessible**

Open the homepage and test each tool.

---

### Task 12: End-to-End Verification

**Covers:** All tools working correctly

- [ ] **Step 1: Verify homepage loads with all 9 tools**

Open `http://72.61.79.238:{port}/` — confirm 9 tool cards render.

- [ ] **Step 2: Test each client-side tool**

Upload an image to each of: Resize, Convert, Compress, Watermark, Color Adjust, Compare — confirm preview and download work.

- [ ] **Step 3: Test each server-side tool**

Upload an image to: Upscale, Remove BG, Transparent — confirm API response and download.

- [ ] **Step 4: Verify mobile responsiveness**

Check tool grid at 400px width — confirm 2-column layout.
