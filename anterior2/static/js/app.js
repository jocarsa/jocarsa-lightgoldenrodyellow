/* global bootstrap, marked */
const toastContainer = document.getElementById('toast-container');
function toast(msg, type='info') {
  const id = 't' + Date.now();
  const el = document.createElement('div');
  el.className = `toast align-items-center text-bg-${type} border-0`;
  el.role = 'alert';
  el.id = id;
  el.innerHTML = `<div class="d-flex">
    <div class="toast-body">${msg}</div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
  </div>`;
  toastContainer.appendChild(el);
  new bootstrap.Toast(el, { delay: 2500 }).show();
}

const ctx = document.getElementById('ctx');
const obj = document.getElementById('obj');
const res = document.getElementById('res');
const fmt = document.getElementById('fmt');
const proyecto = document.getElementById('proyecto');
const dbSqlite = document.getElementById('db_sqlite');
const dbMysql = document.getElementById('db_mysql');
const sqlitefile = document.getElementById('sqlitefile');
const mysql_server = document.getElementById('mysql_server');
const mysql_user = document.getElementById('mysql_user');
const mysql_pass = document.getElementById('mysql_pass');
const mysql_db = document.getElementById('mysql_db');
const exts = document.getElementById('exts');
const excs = document.getElementById('excs');
const chkBienvenida = document.getElementById('chk_bienvenida');

const mdRaw = document.getElementById('md-raw');
const mdView = document.getElementById('md-view');
const viewMd = document.getElementById('view_md');
const viewWys = document.getElementById('view_wys');

function switchDB() {
  document.getElementById('sqlite_opts').classList.toggle('d-none', !dbSqlite.checked);
  document.getElementById('mysql_opts').classList.toggle('d-none', !dbMysql.checked);
}
dbSqlite.addEventListener('change', switchDB);
dbMysql.addEventListener('change', switchDB);

viewMd.addEventListener('change', () => {
  mdView.classList.add('d-none');
  mdRaw.classList.remove('d-none');
});
viewWys.addEventListener('change', () => {
  mdRaw.classList.add('d-none');
  mdView.classList.remove('d-none');
  mdView.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
});

async function loadConfig() {
  const r = await fetch('/api/config');
  const cfg = await r.json();
  proyecto.value = cfg.ultima_carpeta_codigo || '';
  sqlitefile.value = cfg.sqlite_file || '';
  const m = cfg.mysql || {};
  mysql_server.value = m.server || '';
  mysql_user.value = m.user || '';
  mysql_pass.value = m.password || '';
  mysql_db.value = m.database || '';
  exts.value = (cfg.extensiones_permitidas || []).join('\\n');
  excs.value = (cfg.carpetas_excluidas || []).join('\\n');
  chkBienvenida.checked = !!cfg.mostrar_bienvenida;
}
loadConfig();

document.getElementById('btn-defaults').addEventListener('click', () => {
  exts.value = [
    '.html','.css','.js','.php','.py','.java','.sql','.c','.cpp','.cu','.h','.json','.xml','.md'
  ].join('\\n');
  excs.value = ['.git','node_modules','vendor','venv','__pycache__','modelo_entrenado','.venv','__pycache__'].join('\\n');
});

document.getElementById('btn-savecfg').addEventListener('click', async () => {
  const cfg = {
    ultima_carpeta_codigo: proyecto.value.trim(),
    ultima_carpeta_sqlite: sqlitefile.value ? require('path') : '',
    sqlite_file: sqlitefile.value.trim(),
    mysql: {
      server: mysql_server.value.trim(),
      user: mysql_user.value.trim(),
      password: mysql_pass.value.trim(),
      database: mysql_db.value.trim(),
    },
    extensiones_permitidas: exts.value.split('\\n').map(s=>s.trim()).filter(Boolean),
    carpetas_excluidas: excs.value.split('\\n').map(s=>s.trim()).filter(Boolean),
    mostrar_bienvenida: chkBienvenida.checked
  };
  await fetch('/api/config', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(cfg)});
  toast('Configuración guardada', 'success');
});

document.getElementById('btn-testdb').addEventListener('click', async () => {
  const mode = dbSqlite.checked ? 'sqlite' : 'mysql';
  const body = { mode };
  if (mode === 'sqlite') body.sqlite_path = sqlitefile.value.trim();
  else body.mysql = {
    server: mysql_server.value.trim(),
    user: mysql_user.value.trim(),
    password: mysql_pass.value.trim(),
    database: mysql_db.value.trim(),
  };
  const r = await fetch('/api/test_db', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const j = await r.json();
  if (j.ok) {
    toast('Conexión OK', 'success');
    mdRaw.textContent = j.report;
    mdView.innerHTML = `<pre><code>${j.report.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}</code></pre>`;
  } else {
    toast(j.error || 'Error de conexión', 'danger');
  }
});

document.getElementById('btn-generate').addEventListener('click', async () => {
  const payload = {
    contexto: ctx.value, objetivo: obj.value, restricciones: res.value, formato: fmt.value,
    carpeta_proyecto: proyecto.value.trim(),
    db_mode: dbSqlite.checked ? 'sqlite' : 'mysql',
    sqlite_path: sqlitefile.value.trim(),
    mysql: {
      server: mysql_server.value.trim(),
      user: mysql_user.value.trim(),
      password: mysql_pass.value.trim(),
      database: mysql_db.value.trim(),
    }
  };
  const r = await fetch('/api/generate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const j = await r.json();
  if (j.ok) {
    mdRaw.textContent = j.markdown;
    mdView.innerHTML = marked.parse(j.markdown);
    mdView.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
    toast('Prompt generado', 'success');
  }
});

document.getElementById('btn-save').addEventListener('click', async () => {
  const r = await fetch('/api/save_report', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({markdown: mdRaw.textContent, carpeta_proyecto: proyecto.value.trim()})});
  const j = await r.json();
  if (j.ok) {
    const link = document.createElement('a');
    link.href = `/download/reports/${encodeURIComponent(j.filename)}`;
    link.textContent = 'Descargar';
    link.className = 'btn btn-sm btn-primary ms-2';
    toast(`Guardado: ${j.filename}`, 'success');
  } else {
    toast('No se pudo guardar', 'danger');
  }
});

document.getElementById('btn-jocarsa').addEventListener('click', async () => {
  const payload = {
    contexto: ctx.value, objetivo: obj.value, restricciones: res.value, formato: fmt.value,
    carpeta_proyecto: proyecto.value.trim(),
    db_mode: dbSqlite.checked ? 'sqlite' : 'mysql',
    sqlite_path: sqlitefile.value.trim(),
    mysql: {
      server: mysql_server.value.trim(),
      user: mysql_user.value.trim(),
      password: mysql_pass.value.trim(),
      database: mysql_db.value.trim(),
    }
  };
  const r = await fetch('/api/save_prompts', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const j = await r.json();
  if (j.ok) toast(`Prompts guardados: ${j.guardados}`, 'success');
  else toast(j.error || 'No se guardaron prompts', 'danger');
});

// Directory picker modal
const dirModal = new bootstrap.Modal(document.getElementById('modalDirPicker'));
const dirList = document.getElementById('dir-list');
const dirPath = document.getElementById('dir-current-path');

async function loadDir(path='') {
  const r = await fetch('/api/list_dir?path=' + encodeURIComponent(path));
  const j = await r.json();
  if (!j.ok) { toast(j.error || 'No se pudo leer la carpeta', 'danger'); return; }
  dirPath.value = j.path;
  dirList.innerHTML = '';
  const parent = j.path.includes('/') ? j.path.split('/').slice(0,-1).join('/') : '';
  const up = document.createElement('li');
  up.className = 'list-group-item dir d-flex align-items-center gap-2';
  up.innerHTML = '<i class="bi bi-arrow-90deg-up"></i> ..';
  up.onclick = () => loadDir(parent);
  dirList.appendChild(up);
  j.dirs.forEach(d => {
    const li = document.createElement('li');
    li.className = 'list-group-item dir d-flex align-items-center gap-2';
    li.innerHTML = `<i class="bi bi-folder-fill text-warning"></i> ${d.name}`;
    li.onclick = () => loadDir(d.path);
    dirList.appendChild(li);
  });
}

document.getElementById('btn-browse-proyecto').addEventListener('click', () => {
  loadDir(proyecto.value.trim() || '');
  dirModal.show();
});

document.getElementById('btn-open-dir').addEventListener('click', () => {
  loadDir(proyecto.value.trim() || '');
  dirModal.show();
});
document.getElementById('dir-go').addEventListener('click', () => loadDir(dirPath.value));
document.getElementById('dir-select').addEventListener('click', () => {
  proyecto.value = dirPath.value;
  dirModal.hide();
});

// SQLite modal (manual path, for local app convenience)
const sqliteModal = new bootstrap.Modal(document.getElementById('modalSqlite'));
document.getElementById('btn-browse-sqlite').addEventListener('click', () => sqliteModal.show());
document.getElementById('btn-open-sqlite').addEventListener('click', () => sqliteModal.show());
document.getElementById('sqlite-select').addEventListener('click', () => {
  sqlitefile.value = document.getElementById('sqlite-path').value;
  sqliteModal.hide();
});
