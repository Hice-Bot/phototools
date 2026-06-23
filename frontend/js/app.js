const API_BASE = window.PHOTOTOOLS_API_BASE
  || (window.location.port === '8091'
    ? `${window.location.protocol}//${window.location.hostname}:8093`
    : `${window.location.origin}`);

const CLERK_PUBLISHABLE_KEY = window.CLERK_PUBLISHABLE_KEY || 'pk_test_dummy_phototools';

function createEl(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}

function enhanceHeader() {
  const header = document.querySelector('header');
  if (!header || header.dataset.enhanced) return;
  header.dataset.enhanced = 'true';
  header.classList.add('site-header');

  const title = header.querySelector('h1');
  const row = createEl('div', 'header-row');
  if (title) row.appendChild(title);

  const nav = createEl('nav', 'site-nav');
  const prefix = window.location.pathname.includes('/tools/') ? '../' : '';
  [
    ['All Tools', `${prefix}index.html`],
    ['MCP', `${prefix}mcp.html`],
    ['Pricing', `${prefix}pricing.html`],
  ].forEach(([label, href]) => {
    const link = createEl('a', '', label);
    link.href = href;
    nav.appendChild(link);
  });

  const auth = createEl('div', 'auth-slot');
  auth.id = 'authSlot';
  const signIn = createEl('button', 'btn btn-secondary btn-small', 'Sign in');
  signIn.type = 'button';
  signIn.addEventListener('click', () => window.PhotoToolsAuth?.openSignIn?.());
  auth.appendChild(signIn);

  row.appendChild(nav);
  row.appendChild(auth);
  header.insertBefore(row, header.firstChild);
}

function createAdBanner(label = 'Ad placeholder') {
  const ad = createEl('div', 'ad-banner');
  ad.setAttribute('role', 'complementary');
  ad.setAttribute('aria-label', label);
  ad.textContent = `${label} (728x90)`;
  return ad;
}

function setupToolPageChrome() {
  enhanceHeader();
  const main = document.querySelector('main.tool-page');
  if (!main || main.dataset.toolChromeReady) return;
  main.dataset.toolChromeReady = 'true';

  const topAd = createAdBanner('Ad placeholder');
  main.insertBefore(topAd, main.firstChild);

  const drop = document.getElementById('dropzoneArea');
  const result = document.getElementById('previewArea');
  if (drop && result && !main.querySelector('.tool-workspace')) {
    const workspace = createEl('div', 'tool-workspace');
    const left = createEl('section', 'tool-column tool-column-original');
    const right = createEl('section', 'tool-column tool-column-result');

    main.insertBefore(workspace, drop);
    workspace.appendChild(left);
    workspace.appendChild(right);

    ['dropzoneArea', 'controls', 'toolbar', 'progress', 'infoBar'].forEach(id => {
      const node = document.getElementById(id);
      if (node) left.appendChild(node);
    });
    ['previewArea', 'metaInfo', 'downloadArea'].forEach(id => {
      const node = document.getElementById(id);
      if (node) right.appendChild(node);
    });
  }

  main.appendChild(createAdBanner('Ad placeholder'));
}

function renderDropzone(container, input, onFile) {
  container.innerHTML = '';
  const dz = createEl('div', 'dropzone');
  const icon = createEl('div', 'big-icon', 'Upload');
  const text = createEl('div', '', 'Drop image here or click to browse');
  dz.appendChild(icon);
  dz.appendChild(text);
  dz.addEventListener('click', () => {
    input.value = '';
    input.click();
  });
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('active'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('active'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('active');
    if (e.dataTransfer.files[0]) onFile(e.dataTransfer.files[0]);
  });
  container.appendChild(dz);
  container.appendChild(input);
}

function showOriginalPreview(container, file, img, input) {
  container.innerHTML = '';
  container.classList.add('original-loaded');
  const panel = createEl('div', 'image-panel original-panel');
  const head = createEl('div', 'panel-head');
  head.appendChild(createEl('span', 'panel-title', 'Original'));
  const meta = createEl('span', 'panel-meta', `${img.naturalWidth} x ${img.naturalHeight} | ${formatBytes(file.size)}`);
  head.appendChild(meta);
  const image = document.createElement('img');
  image.src = img.src;
  image.alt = file.name || 'Original image';
  const change = createEl('button', 'btn btn-secondary btn-small', 'Choose another');
  change.type = 'button';
  change.addEventListener('click', () => {
    input.value = '';
    input.click();
  });
  panel.appendChild(head);
  panel.appendChild(image);
  panel.appendChild(change);
  container.appendChild(panel);
  container.appendChild(input);
}

function createDropzone(container, onFile) {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.style.display = 'none';

  async function handleFile(file) {
    const img = await loadImage(file);
    showOriginalPreview(container, file, img, input);
    clearResult();
    await onFile(file);
  }

  input.addEventListener('change', () => {
    if (input.files[0]) handleFile(input.files[0]);
  });
  renderDropzone(container, input, handleFile);
  return { element: container, input };
}

function loadImage(fileOrUrl) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = typeof fileOrUrl === 'string' ? fileOrUrl : URL.createObjectURL(fileOrUrl);
  });
}

async function fileToCanvas(file) {
  const img = await loadImage(file);
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);
  return canvas;
}

function canvasToFile(canvas, type = 'image/png', quality = 0.92) {
  return new Promise((resolve, reject) => {
    canvas.toBlob(blob => {
      if (!blob) {
        reject(new Error('Could not render image'));
        return;
      }
      resolve(new File([blob], `output.${type.split('/')[1]}`, { type }));
    }, type, quality);
  });
}

function clearResult() {
  const preview = document.getElementById('previewArea');
  const downloads = document.getElementById('downloadArea');
  if (preview) preview.innerHTML = '';
  if (downloads) downloads.innerHTML = '';
}

function showPreview(container, src, label = 'Result') {
  container.innerHTML = '';
  const panel = createEl('div', 'image-panel result-panel');
  const head = createEl('div', 'panel-head');
  head.appendChild(createEl('span', 'panel-title', label));
  const image = document.createElement('img');
  image.src = src;
  image.alt = label;
  panel.appendChild(head);
  panel.appendChild(image);
  container.appendChild(panel);
  return image;
}

function addDownloadButton(container, file, filename = 'output.png') {
  const btn = createEl('button', 'btn download-btn', 'Download');
  btn.type = 'button';
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

async function authHeaders() {
  const headers = {};
  const token = await window.PhotoToolsAuth?.getToken?.();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function apiPost(endpoint, file, extraFields = {}, options = {}) {
  const form = new FormData();
  form.append('image', file);
  Object.entries(extraFields).forEach(([k, v]) => form.append(k, v));
  const headers = options.paid ? await authHeaders() : {};
  const res = await fetch(`${API_BASE}${endpoint}`, { method: 'POST', body: form, headers });
  if (!res.ok) {
    let detail = `API error: ${res.status}`;
    try {
      const json = await res.json();
      if (json.detail) detail = json.detail;
    } catch (_) {}
    throw new Error(detail);
  }
  const blob = await res.blob();
  blob.photoToolsMode = res.headers.get('X-PhotoTools-Mode') || '';
  return blob;
}

document.addEventListener('DOMContentLoaded', setupToolPageChrome);
