// main.js - for Secure File Store (works with the Flask endpoints used in the project)

async function sha256Hex(buf) {
  const hash = await crypto.subtle.digest('SHA-256', buf);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2,'0')).join('');
}

function showAlert(msg) {
  // simple alert fallback; later you can replace with nicer toasts
  alert(msg);
}

async function createFile() {
  try {
    const user = document.getElementById('user').value || 'alice';
    const fileEl = document.getElementById('fileInput');
    const fnameInput = document.getElementById('filename');
    const sensitivity = document.getElementById('sensitivity').value || 1;

    if (!fileEl.files || fileEl.files.length === 0) { showAlert('Choose a file first'); return; }
    const f = fileEl.files[0];
    const filename = fnameInput.value.trim() || f.name;

    const arr = await f.arrayBuffer();
    const sha = await sha256Hex(arr);

    // 1) create metadata & get file_id
    const resp = await fetch(`/files?user=${encodeURIComponent(user)}`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({filename: filename, sha256: sha, sensitivity: sensitivity})
    });

    const j = await resp.json();
    if (!resp.ok) {
      console.error('create metadata failed', j);
      showAlert('Create metadata failed: ' + (j.error || JSON.stringify(j)));
      return;
    }

    if (j.status === 'exists') {
      showAlert('File already exists (id: ' + j.file_id + ')');
      return;
    }

    const fid = j.file_id;
    // 2) upload the blob (raw bytes). In demo server expects ciphertext or raw blob.
    const put = await fetch(`/upload_blob/${fid}?user=${encodeURIComponent(user)}`, {
      method: 'PUT',
      body: arr
    });

    if (!put.ok) {
      const text = await put.text();
      console.error('upload failed', text);
      showAlert('Upload failed');
      return;
    }

    showAlert('Upload successful. File id: ' + fid);
    // clear inputs
    fileEl.value = '';
    fnameInput.value = '';
    document.getElementById('results').innerHTML = '';
  } catch (err) {
    console.error(err);
    showAlert('Error: ' + err.message);
  }
}

async function searchFiles() {
  try {
    const q = document.getElementById('search').value || '';
    const r = await fetch(`/search?q=${encodeURIComponent(q)}`);
    if (!r.ok) {
      const t = await r.text();
      console.error('search failed', t);
      showAlert('Search failed');
      return;
    }
    const j = await r.json();
    const ul = document.getElementById('results');
    ul.innerHTML = '';
    if (!j.matches || j.matches.length === 0) {
      ul.innerHTML = '<li style="color:#999">No matches</li>';
      return;
    }
    for (const m of j.matches) {
      const li = document.createElement('li');
      li.style.margin = '6px 0';
      li.innerHTML = `<strong>${escapeHtml(m.filename)}</strong> <span style="color:#9ad1d4">(${m.id})</span>
        <button style="margin-left:8px" onclick="fillDownload('${m.id}')">Use id</button>`;
      ul.appendChild(li);
    }
  } catch (err) {
    console.error(err);
    showAlert('Search error: ' + err.message);
  }
}

function fillDownload(id) {
  document.getElementById('fileid').value = id;
}

async function downloadFile() {
  try {
    const user = document.getElementById('user').value || 'alice';
    const fid = document.getElementById('fileid').value.trim();
    if (!fid) { showAlert('Enter file id'); return; }

    const r = await fetch(`/download/${encodeURIComponent(fid)}?user=${encodeURIComponent(user)}`);
    if (r.status === 403) { showAlert('Access denied'); return; }
    if (!r.ok) {
      const txt = await r.text();
      console.error('download failed', txt);
      showAlert('Download failed');
      return;
    }

    const blob = await r.blob();
    // get suggested filename from headers if present
    let suggested = 'downloaded';
    const disp = r.headers.get('Content-Disposition');
    if (disp) {
      const match = /filename="?([^"]+)"?/.exec(disp);
      if (match) suggested = match[1];
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = suggested;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error(err);
    showAlert('Download error: ' + err.message);
  }
}

/* small helper */
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

/* expose functions to buttons if needed */
window.createFile = createFile;
window.searchFiles = searchFiles;
window.downloadFile = downloadFile;
