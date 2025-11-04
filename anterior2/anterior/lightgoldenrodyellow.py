import os
import re
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import sqlite3
from datetime import datetime  # NUEVO

# Soporte opcional para MySQL (pip install pymysql)
try:
    import pymysql
except ImportError:
    pymysql = None

# Drag & Drop opcional (pip install tkinterdnd2)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _TKDND_OK = True
except Exception:
    _TKDND_OK = False
    DND_FILES = None
    TkinterDnD = None

# =========================
# Configuración / Constantes (valores por defecto)
# =========================
CONFIG_FILE = "config.json"

EXTENSIONES_PERMITIDAS_DEF = [
    '.html', '.css', '.js', '.php', '.py', '.java', '.sql',
    '.c', '.cpp', '.cu', '.h', '.json', '.xml', '.md'
]
CARPETAS_EXCLUIDAS_DEF = [
    '.git', 'node_modules', 'vendor', 'venv', '__pycache__',
    'modelo_entrenado', '.venv', '__pycache__'
]

# Estas variables se sobreescriben al cargar config.json
EXTENSIONES_PERMITIDAS = tuple(EXTENSIONES_PERMITIDAS_DEF)
CARPETAS_EXCLUIDAS = set(CARPETAS_EXCLUIDAS_DEF)

# =========================
# Utilidades de persistencia
# =========================
def cargar_config():
    """Carga el JSON de configuración; crea estructura por defecto si falta."""
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}

    # Asegurar claves mínimas
    cfg.setdefault("ultima_carpeta_codigo", "")
    cfg.setdefault("ultima_carpeta_guardar", "")
    cfg.setdefault("ultima_carpeta_sqlite", "")
    cfg.setdefault("sqlite_file", "")
    cfg.setdefault("mysql", {"server": "", "user": "", "password": "", "database": ""})
    cfg.setdefault("extensiones_permitidas", EXTENSIONES_PERMITIDAS_DEF)
    cfg.setdefault("carpetas_excluidas", CARPETAS_EXCLUIDAS_DEF)
    cfg.setdefault("mostrar_bienvenida", True)
    return cfg

def guardar_config(**kwargs):
    """Actualiza config.json con las claves dadas."""
    cfg = cargar_config()
    for k, v in kwargs.items():
        cfg[k] = v
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    _aplicar_config_a_variables(cfg)

def _aplicar_config_a_variables(cfg):
    """Sincroniza variables globales desde cfg."""
    global EXTENSIONES_PERMITIDAS, CARPETAS_EXCLUIDAS
    exts = cfg.get("extensiones_permitidas", EXTENSIONES_PERMITIDAS_DEF)
    # Normalizar: asegurar que empiecen por punto
    exts_norm = []
    for e in exts:
        e = e.strip()
        if not e:
            continue
        if not e.startswith('.'):
            e = '.' + e
        exts_norm.append(e.lower())
    EXTENSIONES_PERMITIDAS = tuple(sorted(set(exts_norm)))

    excl = cfg.get("carpetas_excluidas", CARPETAS_EXCLUIDAS_DEF)
    CARPETAS_EXCLUIDAS = set([c.strip() for c in excl if c.strip()])

# Cargar configuración al inicio y aplicarla
cfg = cargar_config()
_aplicar_config_a_variables(cfg)

# =========================
# Generadores de reportes
# =========================
def construir_mapa_directorios(ruta_raiz):
    """Construye un árbol de directorios en texto."""
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
    """
    Reporte Markdown intercalado por carpetas, con encabezados por nivel y
    bloques de código por archivo permitido.
    """
    lang_map = {
        '.html': 'html',
        '.css': 'css',
        '.js': 'js',
        '.php': 'php',
        '.py': 'python',
        '.java': 'java',
        '.sql': 'sql',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cu': 'cuda',
        '.h': 'c',
        '.json': 'json',
        '.xml': 'xml',
        '.md': 'markdown',
    }
    lineas = []
    nombre_carpeta = os.path.basename(ruta_raiz) if os.path.basename(ruta_raiz) else ruta_raiz
    encabezado = "#" * nivel
    lineas.append(f"{encabezado} {nombre_carpeta}")

    # Listado de entradas
    try:
        entradas = sorted(os.listdir(ruta_raiz))
    except Exception as e:
        lineas.append(f"Error listando la carpeta: {e}")
        return "\n".join(lineas)

    # Archivos permitidos en carpeta actual
    for entrada in entradas:
        ruta_completa = os.path.join(ruta_raiz, entrada)
        if os.path.isfile(ruta_completa) and entrada.lower().endswith(EXTENSIONES_PERMITIDAS):
            extension = os.path.splitext(entrada)[1].lower()
            lenguaje = lang_map.get(extension, '')
            lineas.append(f"**{entrada}**")
            try:
                with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                    contenido = f.read()
            except Exception as e:
                contenido = f"Error al leer el archivo: {e}"
            lineas.append(f"```{lenguaje}")
            lineas.append(contenido)
            lineas.append("```")

    # Subdirectorios (excluyendo los filtrados)
    for entrada in entradas:
        ruta_completa = os.path.join(ruta_raiz, entrada)
        if os.path.isdir(ruta_completa) and entrada not in CARPETAS_EXCLUIDAS:
            lineas.append(generar_reporte_intercalado(ruta_completa, nivel + 1))

    return "\n".join(lineas)

# =========================
# Análisis de bases de datos
# =========================
def analizar_sqlite(db_path):
    """Devuelve estructura de tablas/columnas de una base SQLite."""
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
    """Devuelve estructura de tablas/columnas de MySQL."""
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

# =========================
# Estado global (UI)
# =========================
carpeta_proyecto = cfg.get("ultima_carpeta_codigo", "") or None
sqlite_path = cfg.get("sqlite_file", "")

# =========================
# Helpers UI
# =========================
def toast(titulo, mensaje):
    try:
        ttk.ToastNotification(title=titulo, message=mensaje, duration=3000, position=ttk.POSITION_BOTTOM_RIGHT).show_toast()
    except Exception:
        messagebox.showinfo(titulo, mensaje)

def set_status(texto):
    var_status.set(texto)

# =========================
# Drag & Drop de carpetas
# =========================
def _normalizar_rutas_drop(data: str):
    """
    Convierte event.data (que puede traer {C:\\ruta con espacios} "A" "B" etc.) en una lista de rutas limpias.
    """
    rutas = []
    if not data:
        return rutas
    token = ""
    en_llaves = False
    for ch in data:
        if ch == "{":
            en_llaves = True
            token = ""
        elif ch == "}":
            en_llaves = False
            if token:
                rutas.append(token)
                token = ""
        elif ch in (" ", "\n", "\t") and not en_llaves:
            if token:
                rutas.append(token)
                token = ""
        else:
            token += ch
    if token:
        rutas.append(token)
    rutas = [r.strip().strip('"').strip("'") for r in rutas if r.strip()]
    return rutas

def _on_drop_files(event):
    """
    Recibe archivos/carpetas soltados. Toma la PRIMERA carpeta válida,
    la usa como proyecto, actualiza UI+config y dispara 'Generar'.
    """
    global carpeta_proyecto
    rutas = _normalizar_rutas_drop(event.data)
    carpeta = None
    for r in rutas:
        if os.path.isdir(r):
            carpeta = r
            break

    if not carpeta:
        toast("Arrastra una carpeta", "Por favor, suelta una carpeta válida.")
        return

    carpeta_proyecto = carpeta
    guardar_config(ultima_carpeta_codigo=carpeta_proyecto)
    lbl_carpeta["text"] = carpeta_proyecto
    toast("Carpeta seleccionada", f"Has seleccionado:\n{carpeta_proyecto}")

    # Disparar generación de reporte automáticamente
    try:
        generar_prompt()
    except Exception as e:
        messagebox.showerror("Error al generar", f"Ocurrió un error al generar el reporte:\n{e}")

# =========================
# Splash / Bienvenida
# =========================
def mostrar_bienvenida():
    if not cfg.get("mostrar_bienvenida", True):
        return

    top = ttk.Toplevel(root)
    top.title("Bienvenido")
    top.resizable(False, False)
    top.transient(root)
    top.grab_set()
    # Centrar
    w, h = 520, 360
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (sw - w) // 2, (sh - h) // 3
    top.geometry(f"{w}x{h}+{x}+{y}")

    cont = ttk.Frame(top, padding=20)
    cont.pack(fill=tk.BOTH, expand=True)

    # Logo
    try:
        img = tk.PhotoImage(file="lightgoldenrodyellow.png")
        lbl_logo = ttk.Label(cont, image=img)
        lbl_logo.image = img
        lbl_logo.pack(pady=(0, 10))
    except Exception:
        ttk.Label(cont, text="Generador de Prompt", font=("Helvetica", 18, "bold")).pack(pady=(0, 10))

    ttk.Label(
        cont,
        text="Bienvenido/a al Generador de Prompt.\nConfigura tu proyecto, ajusta las extensiones y genera prompts con análisis automático.",
        justify="center"
    ).pack(pady=6)

    var_no_mostrar = tk.BooleanVar(value=False)
    ttk.Checkbutton(cont, text="No volver a mostrar", variable=var_no_mostrar).pack(pady=4)

    botones = ttk.Frame(cont)
    botones.pack(pady=10)
    def _abrir():
        seleccionar_carpeta_proyecto()
        if var_no_mostrar.get():
            guardar_config(mostrar_bienvenida=False)
        top.destroy()

    def _empezar():
        if var_no_mostrar.get():
            guardar_config(mostrar_bienvenida=False)
        top.destroy()

    ttk.Button(botones, text="Abrir proyecto…", bootstyle=PRIMARY, command=_abrir).pack(side=tk.LEFT, padx=6)
    ttk.Button(botones, text="Empezar", command=_empezar).pack(side=tk.LEFT, padx=6)

# =========================
# Lógica de UI principal
# =========================
def seleccionar_carpeta_proyecto():
    global carpeta_proyecto
    cfg_local = cargar_config()
    inicial = cfg_local.get("ultima_carpeta_codigo") or os.getcwd()
    carpeta = filedialog.askdirectory(
        title="Selecciona la carpeta del proyecto",
        initialdir=inicial
    )
    if carpeta:
        carpeta_proyecto = carpeta
        guardar_config(ultima_carpeta_codigo=carpeta_proyecto)
        lbl_carpeta["text"] = carpeta_proyecto
        toast("Carpeta seleccionada", f"Has seleccionado:\n{carpeta_proyecto}")

def seleccionar_sqlite():
    global sqlite_path
    cfg_local = cargar_config()
    inicial = cfg_local.get("ultima_carpeta_sqlite") or os.getcwd()
    ruta = filedialog.askopenfilename(
        title="Selecciona un archivo SQLite",
        initialdir=inicial,
        filetypes=[("SQLite", "*.sqlite *.db *.sqlite3"), ("Todos los archivos", "*.*")]
    )
    if ruta:
        sqlite_path = ruta
        guardar_config(sqlite_file=sqlite_path, ultima_carpeta_sqlite=os.path.dirname(sqlite_path))
        lbl_sqlite["text"] = os.path.basename(sqlite_path)
        toast("Base de datos SQLite", f"Archivo seleccionado:\n{sqlite_path}")

def alternar_opciones_bd():
    if var_bd.get() == "sqlite":
        marco_sqlite.pack(fill=tk.X, pady=5)
        marco_mysql.pack_forget()
    else:
        marco_sqlite.pack_forget()
        marco_mysql.pack(fill=tk.X, pady=5)

def probar_conexion_bd():
    if var_bd.get() == "sqlite":
        if sqlite_path and os.path.isfile(sqlite_path):
            reporte = analizar_sqlite(sqlite_path)
            if reporte:
                messagebox.showinfo("Estructura SQLite", reporte)
            else:
                messagebox.showwarning("SQLite", "No se pudo leer la base de datos seleccionada.")
        else:
            messagebox.showwarning("SQLite", "Selecciona primero un archivo SQLite válido.")
    else:
        servidor = ent_mysql_servidor.get().strip()
        usuario = ent_mysql_usuario.get().strip()
        contrasena = ent_mysql_contrasena.get().strip()
        bd = ent_mysql_bd.get().strip()
        if not (servidor and usuario and contrasena and bd):
            messagebox.showwarning("MySQL", "Completa todos los campos de conexión.")
            return
        guardar_config(mysql={"server": servidor, "user": usuario,
                              "password": contrasena, "database": bd})
        reporte = analizar_mysql(servidor, usuario, contrasena, bd)
        if reporte:
            messagebox.showinfo("Estructura MySQL", reporte)
        else:
            messagebox.showwarning("MySQL", "No se pudo conectar o leer la base de datos.")

def guardar_datos_mysql_si_cambian(*_):
    servidor = ent_mysql_servidor.get().strip()
    usuario = ent_mysql_usuario.get().strip()
    contrasena = ent_mysql_contrasena.get().strip()
    bd = ent_mysql_bd.get().strip()
    guardar_config(mysql={"server": servidor, "user": usuario,
                          "password": contrasena, "database": bd})

def generar_prompt():
    """
    Genera el prompt final en base a:
      - Contexto, Objetivo, Restricciones, Formato de salida
      - Estructura del proyecto
      - Reporte intercalado de código
      - Informe de base de datos SOLO si hay una BD válida seleccionada
    """
    prompt = ""

    # Datos del formulario
    contexto = txt_contexto.get("1.0", tk.END).strip()
    objetivo = txt_objetivo.get("1.0", tk.END).strip()
    restricciones = txt_restricciones.get("1.0", tk.END).strip()
    formato = txt_formato.get("1.0", tk.END).strip()

    if contexto:
        prompt += f"Contexto: {contexto}\n\n"
    if objetivo:
        prompt += f"Objetivo: {objetivo}\n\n"
    if restricciones:
        prompt += f"Restricciones: {restricciones}\n\n"
    if formato:
        prompt += f"Formato de salida: {formato}\n\n"

    # Estructura + código intercalado
    if carpeta_proyecto:
        arbol = construir_mapa_directorios(carpeta_proyecto)
        prompt += "\n===== Estructura del proyecto =====\n"
        prompt += "```\n" + arbol + "\n```\n\n"

        intercalado = generar_reporte_intercalado(carpeta_proyecto)
        prompt += "\n===== Reporte de código (Intercalado) =====\n" + intercalado + "\n\n"
    else:
        prompt += "\n(No se ha seleccionado carpeta de proyecto para analizar código)\n\n"

    # Informe de base de datos SOLO si procede
    informe_bd = ""
    if var_bd.get() == "sqlite":
        if sqlite_path and os.path.isfile(sqlite_path):
            rep = analizar_sqlite(sqlite_path)
            if rep:
                informe_bd = rep
    else:
        servidor = ent_mysql_servidor.get().strip()
        usuario = ent_mysql_usuario.get().strip()
        contrasena = ent_mysql_contrasena.get().strip()
        bd = ent_mysql_bd.get().strip()
        if servidor and usuario and contrasena and bd:
            rep = analizar_mysql(servidor, usuario, contrasena, bd)
            if rep:
                informe_bd = rep

    if informe_bd:
        prompt += "\n===== Informe de base de datos =====\n" + informe_bd

    # Volcado a la UI (siempre almacenamos el Markdown crudo en txt_salida_raw)
    txt_salida_raw.config(state=tk.NORMAL)
    txt_salida_raw.delete("1.0", tk.END)
    txt_salida_raw.insert(tk.END, prompt)
    txt_salida_raw.config(state=tk.DISABLED)

    # Actualizar la vista según el modo
    actualizar_vista_salida()
    set_status("Prompt generado correctamente.")

def generar_prompt_para_carpeta(carpeta):
    """Igual que generar_prompt() pero para una subcarpeta concreta (jocarsa-...)."""
    prompt = ""

    contexto = txt_contexto.get("1.0", tk.END).strip()
    objetivo = txt_objetivo.get("1.0", tk.END).strip()
    restricciones = txt_restricciones.get("1.0", tk.END).strip()
    formato = txt_formato.get("1.0", tk.END).strip()

    if contexto:
        prompt += f"Contexto: {contexto}\n\n"
    if objetivo:
        prompt += f"Objetivo: {objetivo}\n\n"
    if restricciones:
        prompt += f"Restricciones: {restricciones}\n\n"
    if formato:
        prompt += f"Formato de salida: {formato}\n\n"

    arbol = construir_mapa_directorios(carpeta)
    prompt += "\n===== Estructura del proyecto =====\n"
    prompt += "```\n" + arbol + "\n```\n\n"

    intercalado = generar_reporte_intercalado(carpeta)
    prompt += "\n===== Reporte de código (Intercalado) =====\n" + intercalado + "\n\n"

    # Informe de BD (solo si válido)
    informe_bd = ""
    if var_bd.get() == "sqlite":
        if sqlite_path and os.path.isfile(sqlite_path):
            rep = analizar_sqlite(sqlite_path)
            if rep:
                informe_bd = rep
    else:
        servidor = ent_mysql_servidor.get().strip()
        usuario = ent_mysql_usuario.get().strip()
        contrasena = ent_mysql_contrasena.get().strip()
        bd = ent_mysql_bd.get().strip()
        if servidor and usuario and contrasena and bd:
            rep = analizar_mysql(servidor, usuario, contrasena, bd)
            if rep:
                informe_bd = rep
    if informe_bd:
        prompt += "\n===== Informe de base de datos =====\n" + informe_bd

    return prompt

def copiar_reporte():
    # Copia del Markdown crudo (modo fuente)
    texto = txt_salida_raw.get("1.0", tk.END)
    root.clipboard_clear()
    root.clipboard_append(texto)
    toast("Copiado", "El reporte (Markdown) se ha copiado al portapapeles.")
    set_status("Reporte copiado al portapapeles.")

def guardar_reporte():
    cfg_local = cargar_config()
    inicial = cfg_local.get("ultima_carpeta_guardar") or (carpeta_proyecto or os.getcwd())
    texto = txt_salida_raw.get("1.0", tk.END)

    # Nombre por defecto = nombre_carpeta + _YYYYMMDDHHMMSS.txt
    base_name = "reporte"
    if carpeta_proyecto:
        base_name = os.path.basename(os.path.abspath(carpeta_proyecto)) or "reporte"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    default_filename = f"{base_name}_{timestamp}.txt"

    ruta = filedialog.asksaveasfilename(
        title="Guardar reporte",
        initialdir=inicial,
        initialfile=default_filename,   # NUEVO
        defaultextension=".txt",
        filetypes=[("Texto", "*.txt"), ("Todos los archivos", "*.*")]
    )
    if ruta:
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(texto)
            guardar_config(ultima_carpeta_guardar=os.path.dirname(ruta))
            toast("Guardado", f"Reporte guardado en:\n{ruta}")
            set_status("Reporte guardado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el reporte: {e}")

def guardar_prompts_para_jocarsa():
    if not carpeta_proyecto:
        messagebox.showwarning("Carpeta no seleccionada",
                               "Selecciona primero la carpeta contenedora de proyectos.")
        return
    script_dir = os.path.dirname(os.path.abspath(__file__))
    carpeta_prompts = os.path.join(script_dir, "prompts")
    os.makedirs(carpeta_prompts, exist_ok=True)

    guardados = 0
    for entrada in os.listdir(carpeta_proyecto):
        ruta = os.path.join(carpeta_proyecto, entrada)
        if os.path.isdir(ruta) and entrada.startswith("jocarsa-"):
            texto_prompt = generar_prompt_para_carpeta(ruta)
            destino = os.path.join(carpeta_prompts, entrada + ".txt")
            try:
                with open(destino, "w", encoding="utf-8") as f:
                    f.write(texto_prompt)
                guardados += 1
            except Exception as e:
                print(f"Error al guardar prompt en {entrada}: {e}")

    if guardados > 0:
        toast("Prompts guardados", f"Se han guardado {guardados} prompt(s) en 'prompts'.")
        set_status(f"{guardados} prompts guardados en /prompts.")
    else:
        messagebox.showinfo("Sin proyectos", "No se encontraron carpetas que comiencen por 'jocarsa-'.")

# =========================
# Ventana de configuración (extensiones y carpetas excluidas)
# =========================
def abrir_config_ext_y_excluidas():
    cfg_local = cargar_config()

    top = ttk.Toplevel(root)
    top.title("Configuración: Extensiones y carpetas excluidas")
    top.geometry("700x500")
    top.transient(root)
    top.grab_set()

    frame = ttk.Frame(top, padding=12)
    frame.pack(fill=tk.BOTH, expand=True)

    cols = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
    cols.pack(fill=tk.BOTH, expand=True)

    # Panel extensiones
    panel_ext = ttk.Labelframe(cols, text="Extensiones permitidas (una por línea)", padding=10)
    cols.add(panel_ext, weight=1)
    txt_ext = tk.Text(panel_ext, height=10, wrap="word")
    txt_ext.pack(fill=tk.BOTH, expand=True)

    # Cargar extensiones actuales
    exts = cfg_local.get("extensiones_permitidas", EXTENSIONES_PERMITIDAS_DEF)
    txt_ext.delete("1.0", tk.END)
    txt_ext.insert(tk.END, "\n".join(exts))

    # Panel carpetas excluidas
    panel_exc = ttk.Labelframe(cols, text="Carpetas excluidas (una por línea)", padding=10)
    cols.add(panel_exc, weight=1)
    txt_exc = tk.Text(panel_exc, height=10, wrap="word")
    txt_exc.pack(fill=tk.BOTH, expand=True)

    excs = cfg_local.get("carpetas_excluidas", CARPETAS_EXCLUIDAS_DEF)
    txt_exc.delete("1.0", tk.END)
    txt_exc.insert(tk.END, "\n".join(excs))

    # Barra de acciones
    barra = ttk.Frame(frame)
    barra.pack(fill=tk.X, pady=10)

    def restaurar_por_defecto():
        txt_ext.delete("1.0", tk.END)
        txt_ext.insert(tk.END, "\n".join(EXTENSIONES_PERMITIDAS_DEF))
        txt_exc.delete("1.0", tk.END)
        txt_exc.insert(tk.END, "\n".join(CARPETAS_EXCLUIDAS_DEF))

    def guardar_cambios():
        nuevas_exts = [l.strip() for l in txt_ext.get("1.0", tk.END).splitlines() if l.strip()]
        nuevas_excs = [l.strip() for l in txt_exc.get("1.0", tk.END).splitlines() if l.strip()]
        guardar_config(extensiones_permitidas=nuevas_exts, carpetas_excluidas=nuevas_excs)
        toast("Configuración guardada", "Se han actualizado extensiones y carpetas excluidas.")
        top.destroy()

    ttk.Button(barra, text="Restaurar valores por defecto", command=restaurar_por_defecto).pack(side=tk.LEFT, padx=4)
    ttk.Button(barra, text="Guardar", bootstyle=SUCCESS, command=guardar_cambios).pack(side=tk.RIGHT, padx=4)
    ttk.Button(barra, text="Cancelar", command=top.destroy).pack(side=tk.RIGHT, padx=4)

# =========================
# UI Mejorada (ttkbootstrap) + raíz compatible con DnD
# =========================
# RAÍZ compatible con DnD si está disponible
if _TKDND_OK:
    root = TkinterDnD.Tk()  # raíz con soporte de arrastrar y soltar
else:
    root = tk.Tk()

# Aplica ttkbootstrap sobre esa raíz
style = ttk.Style('flatly')  # p.ej. 'darkly', 'superhero', etc.
root.title("Generador de Prompt para IA")

# Icono opcional
try:
    icono = tk.PhotoImage(file="lightgoldenrodyellow.png")
    root.iconphoto(True, icono)
except Exception:
    pass

# Maximizar/ajustar
try:
    root.state("zoomed")
except Exception:
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")

# ======= Menú de aplicación =======
menubar = tk.Menu(root)
menu_archivo = tk.Menu(menubar, tearoff=0)
menu_archivo.add_command(label="Seleccionar carpeta de proyecto…", command=seleccionar_carpeta_proyecto)
menu_archivo.add_command(label="Seleccionar archivo SQLite…", command=seleccionar_sqlite)
menu_archivo.add_separator()
menu_archivo.add_command(label="Guardar reporte…", command=guardar_reporte)
menu_archivo.add_separator()
menu_archivo.add_command(label="Salir", command=root.destroy)
menubar.add_cascade(label="Archivo", menu=menu_archivo)

menu_config = tk.Menu(menubar, tearoff=0)
menu_config.add_command(label="Extensiones y carpetas excluidas…", command=abrir_config_ext_y_excluidas)
menubar.add_cascade(label="Configuración", menu=menu_config)

root.config(menu=menubar)

# ======= Barra superior =======
header = ttk.Frame(root, padding=(16, 10))
header.pack(fill=tk.X)
lbl_titulo = ttk.Label(header, text="Generador de Prompt", font=("Helvetica", 18, "bold"))
lbl_titulo.pack(side=tk.LEFT)

# Barra de herramientas
toolbar = ttk.Frame(root, padding=(12, 6))
toolbar.pack(fill=tk.X)
ttk.Button(toolbar, text="Seleccionar carpeta del proyecto", bootstyle=SECONDARY, command=seleccionar_carpeta_proyecto).pack(side=tk.LEFT, padx=4)
ttk.Button(toolbar, text="Generar", bootstyle=SUCCESS, command=generar_prompt).pack(side=tk.LEFT, padx=4)
ttk.Button(toolbar, text="Copiar", command=copiar_reporte).pack(side=tk.LEFT, padx=4)
ttk.Button(toolbar, text="Guardar", command=guardar_reporte).pack(side=tk.LEFT, padx=4)
ttk.Button(toolbar, text="Guardar prompts 'jocarsa-*'", bootstyle=INFO, command=guardar_prompts_para_jocarsa).pack(side=tk.LEFT, padx=4)

# Pista/área de drop en el header
drop_hint = ttk.Label(header, text="Arrastra aquí tu CARPETA de proyecto ↓", bootstyle=INFO)
drop_hint.pack(side=tk.RIGHT, padx=8)

if _TKDND_OK:
    # Registrar destinos de drop para mejor UX
    root.drop_target_register(DND_FILES)
    root.dnd_bind("<<Drop>>", _on_drop_files)

    header.drop_target_register(DND_FILES)
    header.dnd_bind("<<Drop>>", _on_drop_files)
else:
    # Aviso ligero al pasar el ratón si no hay DnD
    def _avisar_sin_dnd():
        toast("Drag & Drop no disponible", "Instala 'tkinterdnd2' para activar arrastrar y soltar:\n\npip install tkinterdnd2")
    drop_hint.bind("<Enter>", lambda e: _avisar_sin_dnd())

# Separador
ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)

# Paned principal
paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
paned.pack(fill=tk.BOTH, expand=True)

# -------- ScrollableFrame reutilizable (para recuperar scroll en la izquierda) --------
class ScrollableFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.vscroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vscroll.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.inner = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Scroll con rueda del ratón (Windows/Linux/Mac)
        self._bind_mousewheel(self.canvas)
        self._bind_mousewheel(self.inner)

    def _on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _bind_mousewheel(self, widget):
        widget.bind("<Enter>", lambda e: widget.bind_all("<MouseWheel>", self._on_mousewheel))
        widget.bind("<Leave>", lambda e: widget.unbind_all("<MouseWheel>"))
        widget.bind("<Enter>", lambda e: (widget.bind_all("<Button-4>", self._on_mousewheel_linux),
                                          widget.bind_all("<Button-5>", self._on_mousewheel_linux)), add="+")
        widget.bind("<Leave>", lambda e: (widget.unbind_all("<Button-4>"),
                                          widget.unbind_all("<Button-5>")), add="+")

    def _on_mousewheel(self, event):
        delta = int(-1*(event.delta/120))
        self.canvas.yview_scroll(delta, "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(3, "units")

# -------- Panel Izquierdo (Formulario con scroll recuperado) --------
left_scroll = ScrollableFrame(paned)
paned.add(left_scroll, weight=1)
frame_izq = left_scroll.inner  # Usamos el frame interior

# Grupo: Parámetros del prompt
grp_param = ttk.Labelframe(frame_izq, text="Parámetros del prompt", padding=12)
grp_param.pack(fill=tk.X, pady=6)

def crear_campo(master, titulo, ayuda, alto=3):
    frm = ttk.Frame(master)
    frm.pack(fill=tk.X, pady=6)
    ttk.Label(frm, text=titulo, font=("Helvetica", 10, "bold")).pack(anchor="w")
    ttk.Label(frm, text=ayuda, font=("Helvetica", 8)).pack(anchor="w")
    txt = tk.Text(frm, height=alto, wrap="word")
    txt.pack(fill=tk.X, pady=4)
    return txt

txt_contexto = crear_campo(grp_param, "Contexto", "Describe la situación o el problema.", alto=3)
txt_objetivo = crear_campo(grp_param, "Objetivo", "Expón claramente lo que quieres lograr.", alto=3)
txt_restricciones = crear_campo(grp_param, "Restricciones", "Tecnologías, versiones y limitaciones.", alto=3)
txt_formato = crear_campo(grp_param, "Formato de salida", "Código, explicación, JSON, etc.", alto=3)

# Grupo: Proyecto
grp_proy = ttk.Labelframe(frame_izq, text="Proyecto", padding=12)
grp_proy.pack(fill=tk.X, pady=6)

fila_proy = ttk.Frame(grp_proy)
fila_proy.pack(fill=tk.X)
ttk.Button(fila_proy, text="Seleccionar carpeta…", command=seleccionar_carpeta_proyecto).pack(side=tk.LEFT)
lbl_carpeta = ttk.Label(fila_proy, text=cfg.get("ultima_carpeta_codigo") or "(sin carpeta seleccionada)")
lbl_carpeta.pack(side=tk.LEFT, padx=8)

# Grupo: Base de datos
grp_bd = ttk.Labelframe(frame_izq, text="Base de datos", padding=12)
grp_bd.pack(fill=tk.X, pady=6)

var_bd = tk.StringVar(value="sqlite")
fila_bd_opts = ttk.Frame(grp_bd)
fila_bd_opts.pack(fill=tk.X, pady=4)
ttk.Radiobutton(fila_bd_opts, text="SQLite", variable=var_bd, value="sqlite",
                command=alternar_opciones_bd).pack(side=tk.LEFT, padx=6)
ttk.Radiobutton(fila_bd_opts, text="MySQL", variable=var_bd, value="mysql",
                command=alternar_opciones_bd).pack(side=tk.LEFT, padx=6)

# SQLite
marco_sqlite = ttk.Frame(grp_bd)
fila_sqlite = ttk.Frame(marco_sqlite)
fila_sqlite.pack(fill=tk.X, pady=4)
ttk.Button(fila_sqlite, text="Seleccionar archivo SQLite…", command=seleccionar_sqlite).pack(side=tk.LEFT)
lbl_sqlite = ttk.Label(fila_sqlite, text=os.path.basename(cfg.get("sqlite_file")) if cfg.get("sqlite_file") else "(ningún archivo seleccionado)")
lbl_sqlite.pack(side=tk.LEFT, padx=8)

# MySQL
marco_mysql = ttk.Frame(grp_bd)
ttk.Label(marco_mysql, text="Servidor:").pack(anchor="w", padx=4, pady=2)
ent_mysql_servidor = ttk.Entry(marco_mysql)
ent_mysql_servidor.pack(fill=tk.X, padx=4, pady=2)
ent_mysql_servidor.bind("<FocusOut>", guardar_datos_mysql_si_cambian)

ttk.Label(marco_mysql, text="Usuario:").pack(anchor="w", padx=4, pady=2)
ent_mysql_usuario = ttk.Entry(marco_mysql)
ent_mysql_usuario.pack(fill=tk.X, padx=4, pady=2)
ent_mysql_usuario.bind("<FocusOut>", guardar_datos_mysql_si_cambian)

ttk.Label(marco_mysql, text="Contraseña:").pack(anchor="w", padx=4, pady=2)
ent_mysql_contrasena = ttk.Entry(marco_mysql, show="*")
ent_mysql_contrasena.pack(fill=tk.X, padx=4, pady=2)
ent_mysql_contrasena.bind("<FocusOut>", guardar_datos_mysql_si_cambian)

ttk.Label(marco_mysql, text="Base de datos:").pack(anchor="w", padx=4, pady=2)
ent_mysql_bd = ttk.Entry(marco_mysql)
ent_mysql_bd.pack(fill=tk.X, padx=4, pady=2)
ent_mysql_bd.bind("<FocusOut>", guardar_datos_mysql_si_cambian)

# Botones de BD y generación
fila_acciones = ttk.Frame(frame_izq)
fila_acciones.pack(fill=tk.X, pady=8)
ttk.Button(fila_acciones, text="Probar conexión BD", command=probar_conexion_bd).pack(side=tk.LEFT, padx=4)
ttk.Button(fila_acciones, text="Generar Prompt", bootstyle=SUCCESS, command=generar_prompt).pack(side=tk.LEFT, padx=4)
ttk.Button(fila_acciones, text="Guardar prompts para 'jocarsa-*'", bootstyle=INFO, command=guardar_prompts_para_jocarsa).pack(side=tk.LEFT, padx=4)

# -------- Panel Derecho (Salida con conmutador Markdown/WYSIWYG y barra de scroll) --------
frame_der = ttk.Frame(paned, padding=10)
paned.add(frame_der, weight=1)

header_der = ttk.Frame(frame_der)
header_der.pack(fill=tk.X)
ttk.Label(header_der, text="Salida", font=("Helvetica", 14, "bold")).pack(side=tk.LEFT)

vista_modo = tk.StringVar(value="markdown")  # 'markdown' o 'vista'
def on_toggle_vista():
    actualizar_vista_salida()

ttk.Label(header_der, text="Vista:").pack(side=tk.RIGHT, padx=(0, 6))
ttk.Radiobutton(header_der, text="WYSIWYG", variable=vista_modo, value="vista", command=on_toggle_vista).pack(side=tk.RIGHT)
ttk.Radiobutton(header_der, text="Markdown", variable=vista_modo, value="markdown", command=on_toggle_vista).pack(side=tk.RIGHT)

# 1) CONTENEDOR de Markdown crudo con SCROLLBAR VERTICAL visible
frame_markdown = ttk.Frame(frame_der)
frame_markdown.pack(fill=tk.BOTH, expand=True)
scroll_md = ttk.Scrollbar(frame_markdown, orient="vertical")
txt_salida_raw = tk.Text(frame_markdown, wrap="word", state=tk.DISABLED, yscrollcommand=scroll_md.set)
scroll_md.config(command=txt_salida_raw.yview)
txt_salida_raw.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll_md.pack(side=tk.RIGHT, fill=tk.Y)

# 2) Vista “WYSIWYG” (Text con estilos + su propia barra de scroll)
frame_vista = ttk.Frame(frame_der)
txt_vista = tk.Text(frame_vista, wrap="word", state=tk.DISABLED)
scroll_vista = ttk.Scrollbar(frame_vista, orient="vertical", command=txt_vista.yview)
txt_vista.configure(yscrollcommand=scroll_vista.set)
txt_vista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll_vista.pack(side=tk.RIGHT, fill=tk.Y)

# Fuentes para vista
font_base = tkfont.Font(family="Helvetica", size=11)
font_h1 = tkfont.Font(family="Helvetica", size=18, weight="bold")
font_h2 = tkfont.Font(family="Helvetica", size=16, weight="bold")
font_h3 = tkfont.Font(family="Helvetica", size=14, weight="bold")
font_bold = tkfont.Font(family="Helvetica", size=11, weight="bold")
font_code = tkfont.Font(family="Courier", size=10)

# Tags
txt_vista.tag_configure("h1", font=font_h1, spacing3=6)
txt_vista.tag_configure("h2", font=font_h2, spacing3=4)
txt_vista.tag_configure("h3", font=font_h3, spacing3=2)
txt_vista.tag_configure("bold", font=font_bold)
txt_vista.tag_configure("codeblock", font=font_code, background="#f5f5f5", spacing1=2, spacing3=6, lmargin1=8, lmargin2=8)
txt_vista.tag_configure("mono", font=font_code)
txt_vista.tag_configure("p", font=font_base, spacing3=6)

def renderizar_vista(markdown_text: str):
    """
    Render sencillo de Markdown a Text con estilos:
    - #, ##, ### como headers
    - **negrita**
    - ``` bloques de código ```
    - `inline code`
    - resto como párrafos
    """
    txt_vista.config(state=tk.NORMAL)
    txt_vista.delete("1.0", tk.END)

    in_code = False
    code_buffer = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip("\n")

        # Bloques de código ```lang
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_buffer = []
            else:
                # Fin de bloque
                if code_buffer:
                    start = txt_vista.index(tk.INSERT)
                    txt_vista.insert(tk.END, "\n".join(code_buffer) + "\n")
                    end = txt_vista.index(tk.INSERT)
                    txt_vista.tag_add("codeblock", start, end)
                in_code = False
            continue

        if in_code:
            code_buffer.append(line)
            continue

        # Encabezados
        if line.startswith("### "):
            start = txt_vista.index(tk.INSERT)
            txt_vista.insert(tk.END, line[4:] + "\n")
            end = txt_vista.index(tk.INSERT)
            txt_vista.tag_add("h3", start, end)
            continue
        if line.startswith("## "):
            start = txt_vista.index(tk.INSERT)
            txt_vista.insert(tk.END, line[3:] + "\n")
            end = txt_vista.index(tk.INSERT)
            txt_vista.tag_add("h2", start, end)
            continue
        if line.startswith("# "):
            start = txt_vista.index(tk.INSERT)
            txt_vista.insert(tk.END, line[2:] + "\n")
            end = txt_vista.index(tk.INSERT)
            txt_vista.tag_add("h1", start, end)
            continue

        # Negrita **texto**
        start_para = txt_vista.index(tk.INSERT)
        txt_vista.insert(tk.END, line + "\n")
        end_para = txt_vista.index(tk.INSERT)

        for m in re.finditer(r"\*\*(.+?)\*\*", line):
            s = f"{start_para}+{m.start(1)}c"
            e = f"{start_para}+{m.end(1)}c"
            txt_vista.tag_add("bold", s, e)

        # `inline code`
        for m in re.finditer(r"\`(.+?)\`", line):
            s = f"{start_para}+{m.start(1)}c"
            e = f"{start_para}+{m.end(1)}c"
            txt_vista.tag_add("mono", s, e)

        txt_vista.tag_add("p", start_para, end_para)

    txt_vista.config(state=tk.DISABLED)

def actualizar_vista_salida():
    modo = vista_modo.get()
    if modo == "markdown":
        frame_vista.pack_forget()
        frame_markdown.pack(fill=tk.BOTH, expand=True)
    else:
        contenido = txt_salida_raw.get("1.0", tk.END)
        renderizar_vista(contenido)
        frame_markdown.pack_forget()
        frame_vista.pack(fill=tk.BOTH, expand=True)

# ======= Barra de estado =======
statusbar = ttk.Frame(root, padding=(10, 6))
statusbar.pack(fill=tk.X)
var_status = tk.StringVar(value="Listo.")
ttk.Label(statusbar, textvariable=var_status).pack(side=tk.LEFT)
prog = ttk.Progressbar(statusbar, mode="indeterminate", bootstyle=INFO)

# Mostrar el panel correcto según la BD seleccionada
alternar_opciones_bd()

# Splash de bienvenida
root.after(250, mostrar_bienvenida)

set_status("Listo. Configura los parámetros y genera el prompt.")
root.mainloop()

