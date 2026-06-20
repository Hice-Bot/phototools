const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8093'
  : `http://${window.location.hostname}:8093`;

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