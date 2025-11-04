import os
import re
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3

# Optional MySQL
try:
    import pymysql
except Exception:
    pymysql = None

app = Flask(__name__, template_folder="templates", static_folder="static")

# =========================
# Configuración / Constantes
# =========================
CONFIG_FILE = "config.json"

EXTENSIONES_PERMITIDAS_DEF = [
    ".html", ".css", ".js", ".php", ".py", ".java", ".sql",
    ".c", ".cpp", ".cu", ".h", ".json", ".xml", ".md"
]
CARPETAS_EXCLUIDAS_DEF = [
    ".git", "node_modules", "vendor", "venv", "__pycache__",
    "modelo_entrenado", ".venv", "__pycache__"
]

EXTENSIONES_PERMITIDAS = tuple(EXTENSIONES_PERMITIDAS_DEF)
CARPETAS_EXCLUIDAS = set(CARPETAS_EXCLUIDAS_DEF)

# =========================
# Persistencia de config
# =========================
def cargar_config():
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    cfg.setdefault("ultima_carpeta_codigo", "")
    cfg.setdefault("ultima_carpeta_guardar", "")
    cfg.setdefault("ultima_carpeta_sqlite", "")
    cfg.setdefault("sqlite_file", "")
    cfg.setdefault("mysql", {"server": "", "user": "", "password": "", "database": ""})
    cfg.setdefault("extensiones_permitidas", EXTENSIONES_PERMITIDAS_DEF)
    cfg.setdefault("carpetas_excluidas", CARPETAS_EXCLUIDAS_DEF)
    cfg.setdefault("mostrar_bienvenida", True)
    return cfg

def guardar_config(new_values: dict):
    cfg = cargar_config()
    cfg.update(new_values)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    _aplicar_config_a_variables(cfg)
    return cfg

def _aplicar_config_a_variables(cfg):
    global EXTENSIONES_PERMITIDAS, CARPETAS_EXCLUIDAS
    exts = cfg.get("extensiones_permitidas", EXTENSIONES_PERMITIDAS_DEF)
    exts_norm = []
    for e in exts:
        e = e.strip()
        if not e:
            continue
        if not e.startswith("."):
            e = "." + e
        exts_norm.append(e.lower())
    EXTENSIONES_PERMITIDAS = tuple(sorted(set(exts_norm)))
    excl = cfg.get("carpetas_excluidas", CARPETAS_EXCLUIDAS_DEF)
    CARPETAS_EXCLUIDAS = set([c.strip() for c in excl if c.strip()])

cfg = cargar_config()
_aplicar_config_a_variables(cfg)

# =========================
# Núcleo de análisis
# =========================
def construir_mapa_directorios(ruta_raiz):
    lineas = []
    raiz_abs = os.path.abspath(ruta_raiz)
    lineas.append(raiz_abs)

    def interno(dir_path, prefijo=""):
        try:
            entradas = sorted(os.listdir(dir_path))
        except Exception:
            return
        entradas = [
            e for e in entradas
            if not (os.path.isdir(os.path.join(dir_path, e)) and e in CARPETAS_EXCLUIDAS)
        ]
        for i, entrada in enumerate(entradas):
            ruta_completa = os.path.join(dir_path, entrada)
            conector = "└── " if i == len(entradas) - 1 else "├── "
            lineas.append(prefijo + conector + entrada)
            if os.path.isdir(ruta_completa):
                extension = "    " if i == len(entradas) - 1 else "│   "
                interno(ruta_completa, prefijo + extension)
    interno(ruta_raiz)
    return "\n".join(lineas)

def generar_reporte_intercalado(ruta_raiz, nivel=1):
    lang_map = {
        ".html": "html", ".css": "css", ".js": "js", ".php": "php",
        ".py": "python", ".java": "java", ".sql": "sql", ".c": "c",
        ".cpp": "cpp", ".cu": "cuda", ".h": "c", ".json": "json",
        ".xml": "xml", ".md": "markdown",
    }
    lineas = []
    nombre_carpeta = os.path.basename(ruta_raiz) if os.path.basename(ruta_raiz) else ruta_raiz
    encabezado = "#" * nivel
    lineas.append(f"{encabezado} {nombre_carpeta}")

    try:
        entradas = sorted(os.listdir(ruta_raiz))
    except Exception as e:
        lineas.append(f"Error listando la carpeta: {e}")
        return "\n".join(lineas)

    for entrada in entradas:
        ruta_completa = os.path.join(ruta_raiz, entrada)
        if os.path.isfile(ruta_completa) and entrada.lower().endswith(EXTENSIONES_PERMITIDAS):
            extension = os.path.splitext(entrada)[1].lower()
            lenguaje = lang_map.get(extension, "")
            lineas.append(f"**{entrada}**")
            try:
                with open(ruta_completa, "r", encoding="utf-8", errors="ignore") as f:
                    contenido = f.read()
            except Exception as e:
                contenido = f"Error al leer el archivo: {e}"
            lineas.append(f"```{lenguaje}")
            lineas.append(contenido)
            lineas.append("```")

    for entrada in entradas:
        ruta_completa = os.path.join(ruta_raiz, entrada)
        if os.path.isdir(ruta_completa) and entrada not in CARPETAS_EXCLUIDAS:
            lineas.append(generar_reporte_intercalado(ruta_completa, nivel + 1))

    return "\n".join(lineas)

def analizar_sqlite(db_path):
    detalles = [f"SQLite: {db_path}"]
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = [t[0] for t in cur.fetchall()]
        for t in tablas:
            detalles.append(f"    Tabla: {t}")
            cur.execute(f"PRAGMA table_info({t});")
            for col in cur.fetchall():
                detalles.append(f"        Columna: {col[1]} ({col[2]})")
        conn.close()
    except Exception:
        return None
    return "\n".join(detalles)

def analizar_mysql(servidor, usuario, contrasena, bd):
    if pymysql is None:
        return None
    detalles = [f"MySQL en {servidor} - {bd}"]
    try:
        conn = pymysql.connect(host=servidor, user=usuario, password=contrasena, database=bd)
        cur = conn.cursor()
        cur.execute("SHOW TABLES;")
        tablas = [t[0] for t in cur.fetchall()]
        for t in tablas:
            detalles.append(f"    Tabla: {t}")
            cur.execute(f"SHOW COLUMNS FROM `{t}`;")
            for col in cur.fetchall():
                detalles.append(f"        Columna: {col[0]} ({col[1]})")
        conn.close()
        return "\n".join(detalles)
    except Exception:
        return None

def generar_prompt_backend(contexto, objetivo, restricciones, formato, carpeta_proyecto, db_mode, sqlite_path, mysql_cfg):
    prompt = ""

    if contexto:
        prompt += f"Contexto: {contexto}\n\n"
    if objetivo:
        prompt += f"Objetivo: {objetivo}\n\n"
    if restricciones:
        prompt += f"Restricciones: {restricciones}\n\n"
    if formato:
        prompt += f"Formato de salida: {formato}\n\n"

    if carpeta_proyecto and os.path.isdir(carpeta_proyecto):
        arbol = construir_mapa_directorios(carpeta_proyecto)
        prompt += "\\n===== Estructura del proyecto =====\\n"
        prompt += "```\\n" + arbol + "\\n```\\n\\n"

        intercalado = generar_reporte_intercalado(carpeta_proyecto)
        prompt += "\\n===== Reporte de código (Intercalado) =====\\n" + intercalado + "\\n\\n"
    else:
        prompt += "\\n(No se ha seleccionado carpeta de proyecto para analizar código)\\n\\n"

    informe_bd = ""
    if db_mode == "sqlite":
        if sqlite_path and os.path.isfile(sqlite_path):
            rep = analizar_sqlite(sqlite_path)
            if rep:
                informe_bd = rep
    else:
        if mysql_cfg and all(mysql_cfg.get(k) for k in ("server", "user", "password", "database")):
            rep = analizar_mysql(mysql_cfg["server"], mysql_cfg["user"], mysql_cfg["password"], mysql_cfg["database"])
            if rep:
                informe_bd = rep

    if informe_bd:
        prompt += "\\n===== Informe de base de datos =====\\n" + informe_bd

    return prompt

# =========================
# Rutas
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "GET":
        return jsonify(cargar_config())
    data = request.json or {}
    cfg = guardar_config(data)
    return jsonify(cfg)

@app.route("/api/list_dir")
def api_list_dir():
    path = request.args.get("path", "") or os.getcwd()
    try:
        entries = sorted(os.listdir(path))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "path": path})
    dirs = []
    for e in entries:
        full = os.path.join(path, e)
        if os.path.isdir(full) and e not in CARPETAS_EXCLUIDAS:
            dirs.append({"name": e, "path": full})
    return jsonify({"ok": True, "path": path, "dirs": dirs})

@app.route("/api/test_db", methods=["POST"])
def api_test_db():
    data = request.json or {}
    mode = data.get("mode", "sqlite")
    if mode == "sqlite":
        sqlite_path = data.get("sqlite_path", "")
        if sqlite_path and os.path.isfile(sqlite_path):
            rep = analizar_sqlite(sqlite_path)
            if rep:
                return jsonify({"ok": True, "report": rep})
        return jsonify({"ok": False, "error": "No se pudo leer la base de datos SQLite."}), 400
    else:
        mysql_cfg = data.get("mysql", {})
        if not all(mysql_cfg.get(k) for k in ("server", "user", "password", "database")):
            return jsonify({"ok": False, "error": "Completa todos los campos de conexión."}), 400
        rep = analizar_mysql(mysql_cfg["server"], mysql_cfg["user"], mysql_cfg["password"], mysql_cfg["database"])
        if rep:
            return jsonify({"ok": True, "report": rep})
        return jsonify({"ok": False, "error": "No se pudo conectar o leer la base de datos MySQL."}), 400

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json or {}
    contexto = data.get("contexto", "").strip()
    objetivo = data.get("objetivo", "").strip()
    restricciones = data.get("restricciones", "").strip()
    formato = data.get("formato", "").strip()
    carpeta_proyecto = data.get("carpeta_proyecto", "").strip()
    db_mode = data.get("db_mode", "sqlite")
    sqlite_path = data.get("sqlite_path", "").strip()
    mysql_cfg = data.get("mysql", {})

    result = generar_prompt_backend(contexto, objetivo, restricciones, formato, carpeta_proyecto, db_mode, sqlite_path, mysql_cfg)
    return jsonify({"ok": True, "markdown": result})

@app.route("/api/save_report", methods=["POST"])
def api_save_report():
    data = request.json or {}
    markdown = data.get("markdown", "")
    carpeta_proyecto = data.get("carpeta_proyecto", "") or "reporte"
    base_name = os.path.basename(os.path.abspath(carpeta_proyecto)) if os.path.isdir(carpeta_proyecto) else "reporte"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    default_filename = f"{base_name}_{timestamp}.txt"

    out_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, default_filename)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        return jsonify({"ok": True, "path": out_path, "filename": default_filename})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/save_prompts", methods=["POST"])
def api_save_prompts():
    data = request.json or {}
    carpeta_proyecto = data.get("carpeta_proyecto", "").strip()
    contexto = data.get("contexto", "").strip()
    objetivo = data.get("objetivo", "").strip()
    restricciones = data.get("restricciones", "").strip()
    formato = data.get("formato", "").strip()
    db_mode = data.get("db_mode", "sqlite")
    sqlite_path = data.get("sqlite_path", "").strip()
    mysql_cfg = data.get("mysql", {})

    if not carpeta_proyecto or not os.path.isdir(carpeta_proyecto):
        return jsonify({"ok": False, "error": "Selecciona la carpeta contenedora de proyectos."}), 400

    out_dir = os.path.join(os.getcwd(), "prompts")
    os.makedirs(out_dir, exist_ok=True)
    guardados = 0
    errores = []
    for entrada in os.listdir(carpeta_proyecto):
        ruta = os.path.join(carpeta_proyecto, entrada)
        if os.path.isdir(ruta) and entrada.startswith("jocarsa-"):
            texto_prompt = generar_prompt_backend(contexto, objetivo, restricciones, formato, ruta, db_mode, sqlite_path, mysql_cfg)
            destino = os.path.join(out_dir, entrada + ".txt")
            try:
                with open(destino, "w", encoding="utf-8") as f:
                    f.write(texto_prompt)
                guardados += 1
            except Exception as e:
                errores.append(f"{entrada}: {e}")

    return jsonify({"ok": True, "guardados": guardados, "errores": errores})

# Descargar archivos guardados
@app.route("/download/<path:filename>")
def download_file(filename):
    # sirve archivos desde /reports o /prompts del cwd
    cwd = os.getcwd()
    if filename.startswith("reports/"):
        folder = os.path.join(cwd, "reports")
        return send_from_directory(folder, filename.split("/", 1)[1], as_attachment=True)
    if filename.startswith("prompts/"):
        folder = os.path.join(cwd, "prompts")
        return send_from_directory(folder, filename.split("/", 1)[1], as_attachment=True)
    return "Not Found", 404

if __name__ == "__main__":
    # Para desarrollo local
    app.run(host="127.0.0.1", port=5000, debug=True)
