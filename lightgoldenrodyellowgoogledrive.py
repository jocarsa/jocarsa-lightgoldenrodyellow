import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import sqlite3
import re

placeholder = 0

# For MySQL support, ensure you have pymysql installed (pip install pymysql)
try:
    import pymysql
except ImportError:
    pymysql = None

# --- Configuraciones ---
ALLOWED_EXTENSIONS = ('.html', '.css', '.js', '.php', '.py', '.java', '.sql','.c','.cpp','.cu','.h','.json')
EXCLUDED_DIRS = {'.git', 'node_modules', 'vendor'}

# --- NUEVA FUNCIÓN: Reporte intercalado (Interleaved) ---
def generate_interleaved_report(root_path, depth=1):
    global placeholder
    """
    Genera un reporte en Markdown intercalando:
      - Un encabezado para cada carpeta basado en su profundidad.
      - Dentro de cada carpeta, se listan los archivos permitidos con su nombre en negrita y su contenido en bloques de código.
    Cuando estamos dentro de un folder con "Proyecto" en el nombre, se muestra primero la estructura del proyecto y luego todos los archivos recursivamente,
    sin generar títulos de subcarpetas, anteponiendo la ruta relativa al nombre de archivo.
    """
    # Mapeo de extensiones a etiquetas para bloques de código Markdown.
    lang_mapping = {
        '.html': 'html', '.css': 'css', '.js': 'js', '.php': 'php',
        '.py': 'python', '.java': 'java', '.sql': 'sql', '.c': 'c',
        '.cpp': 'cpp', '.cu': 'cuda', '.h': 'c', '.json': 'json'
    }
    report_lines = []
    base_name = os.path.basename(root_path)
    is_proyecto = 'Proyecto' in base_name

    print(f"Root Path: {root_path}")
    print(f"Base Name: {base_name}")

    if is_proyecto:
        # Encabezado de la carpeta Proyecto
        header = '#' * depth
        report_lines.append(f"{header} {base_name}")
        placeholder += 1
        report_lines.append(f"/n[placeholder {placeholder}] /n")
        # Estructura del proyecto
        structure_tree = build_directory_map(root_path)
        report_lines.append(" \n Estructura del proyecto: \n ")
        report_lines.append(" \n" + structure_tree + "\n \n")
        # Listado recursivo de archivos permitidos sin títulos de carpetas
        for dirpath, dirnames, filenames in os.walk(root_path):
            midir = dirpath.replace(root_path,"")
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
            rel_dir = os.path.relpath(dirpath, root_path)
            print(f"Directory Path: {dirpath}")
            print(f"Relative Directory: {rel_dir}")
            prefix = '' if rel_dir == '.' else rel_dir.replace('\\', '/') + '/'
            for filename in sorted(filenames):
                if filename.lower().endswith(ALLOWED_EXTENSIONS):
                    full_path = os.path.join(dirpath, filename)
                    report_lines.append(f"\n . \n ###### {prefix}{filename}")
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        content = f"Error al leer el archivo: {e}"
                    for line in content.splitlines():
                        if '-' in line:
                            #line = line.split('-', 1)[-1].strip()
                            line = line
                        if not line.strip():
                            line = ' '
                        report_lines.append(f"###### `{line}`")
                    report_lines.append(" ")
                elif filename.lower().endswith(('.jpg', '.png')):
                    rel_path = os.path.relpath(dirpath, root_path)
                    print(f"Base Name: {base_name}")
                    print(f"Relative Path: {rel_path}")
                    github_path = f"https://github.com/jocarsa{midir}/{filename}"
                    report_lines.append(f"\n . \n ###### ![{filename}]({github_path})")
        return "\n ".join(report_lines)

    # Flujo original para carpetas que no son Proyecto
    try:
        entries = sorted(os.listdir(root_path))
    except Exception as e:
        report_lines.append(f"Error listando la carpeta: {e}")
        return "\n".join(report_lines)

    # Archivos permitidos en el directorio actual
    for entry in entries:
        full_path = os.path.join(root_path, entry)
        midir = root_path.replace(root_path,"")
        if os.path.isfile(full_path) and entry.lower().endswith(ALLOWED_EXTENSIONS):
            placeholder += 1
            report_lines.append(f" [Placeholder {placeholder}] ")
            report_lines.append(f"###### {entry}")
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                content = f"Error al leer el archivo: {e}"
            for line in content.splitlines():
                if '-' in line:
                    #line = line.split('-', 1)[-1].strip()
                    line = line
                if not line.strip():
                    line = ' '
                report_lines.append(f"###### `{line}`")
        elif os.path.isfile(full_path) and entry.lower().endswith(('.jpg', '.png')):
            rel_path = os.path.relpath(root_path, start=os.path.dirname(root_path))
            github_path = f"https://github.com/jocarsa/tree/main{midir}/{entry}"
            report_lines.append(f"\n . \n ###### ![{entry}]({github_path})")

    # Recursión a subdirectorios
    for entry in entries:
        full_path = os.path.join(root_path, entry)
        if os.path.isdir(full_path) and entry not in EXCLUDED_DIRS:
            folder_name = entry
            if '-' in folder_name:
                folder_name = folder_name.split('-', 1)[-1].strip()
            header = '#' * depth
            report_lines.append(f"{header} {folder_name}")
            placeholder += 1
            report_lines.append(f" [Placeholder {placeholder}] ")
            report_lines.append(generate_interleaved_report(full_path, depth + 1))

    return "\n".join(report_lines)








# --- Funciones originales para análisis de código (para otros usos) ---
def build_directory_map(root_path):
    """Construye un mapa de directorios en forma de árbol."""
    lines = []
    root_abs = os.path.abspath(root_path)
    # Get the base name of the root path
    root_name = os.path.basename(root_abs)
    lines.append(f"###### `{root_name}`")

    def inner(dir_path, prefix=""):
        try:
            entries = sorted(os.listdir(dir_path))
        except Exception:
            return
        entries = [e for e in entries if not (os.path.isdir(os.path.join(dir_path, e)) and e in EXCLUDED_DIRS)]
        for i, entry in enumerate(entries):
            full_path = os.path.join(dir_path, entry)
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"###### `{prefix}{connector}{entry}`")
            if os.path.isdir(full_path):
                extension = "    " if i == len(entries) - 1 else "│   "
                inner(full_path, prefix + extension)
    inner(root_path)
    return "\n".join(lines)

def parse_files(root_path):
    """Recorre la carpeta y obtiene el contenido de archivos con extensiones permitidas."""
    parsed_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            if filename.lower().endswith(ALLOWED_EXTENSIONS):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception as e:
                    content = f"Error reading file: {e}"
                parsed_files.append((file_path, content))
    return parsed_files

def generate_code_report(root_path):
    """Genera un reporte con el mapa de directorios y el contenido de archivos en formato Markdown."""
    report_lines = []
    report_lines.append("### Project Directory Map")
    report_lines.append("")
    report_lines.append(build_directory_map(root_path))
    report_lines.append("")
    report_lines.append("\n### Parsed Files\n")
    parsed_files = parse_files(root_path)
    lang_mapping = {
        '.html': 'html',
        '.css': 'css',
        '.js': 'js',
        '.php': 'php',
        '.py': 'python',
        '.java': 'java'
    }
    for file_path, content in parsed_files:
        filename = os.path.basename(file_path)
        extension = os.path.splitext(filename)[1].lower()
        language = lang_mapping.get(extension, '')
        report_lines.append(f"**{filename}**")
        report_lines.append(f"```{language}")
        report_lines.append(content)
        report_lines.append("```")
    return "\n".join(report_lines)

def generate_folder_titles(root_path):
    """
    Genera una jerarquía de títulos en Markdown basada en la estructura de carpetas.
    """
    markdown_lines = []
    for current_root, dirs, _ in os.walk(root_path):
        rel_path = os.path.relpath(current_root, root_path)
        if rel_path == '.':
            continue
        depth = len(rel_path.split(os.sep))
        heading = "#" * depth
        folder_name = os.path.basename(current_root)
        markdown_lines.append(f"{heading} {folder_name}")
    return "\n".join(markdown_lines)

# --- Funciones para análisis de base de datos ---
def analyze_sqlite_database(db_path):
    """Analiza una base de datos SQLite y devuelve su estructura (tablas y columnas)."""
    db_details = f"SQLite Database: {db_path}\n"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_details = []
        for table in tables:
            table_name = table[0]
            table_details.append(f"    Table: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                table_details.append(f"        Column: {col[1]} ({col[2]})")
        conn.close()
        db_details += "\n".join(table_details)
    except Exception as e:
        db_details += f"\n    Error reading SQLite database: {e}"
    return db_details

def analyze_mysql_database(server, user, password, database):
    """Analiza una base de datos MySQL y devuelve su estructura (tablas y columnas)."""
    db_details = f"MySQL Database on {server} - {database}\n"
    if pymysql is None:
        return db_details + "    pymysql no está instalado."
    try:
        conn = pymysql.connect(host=server, user=user, password=password, database=database)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        table_details = []
        for table in tables:
            table_name = table[0]
            table_details.append(f"    Table: {table_name}")
            cursor.execute(f"SHOW COLUMNS FROM {table_name};")
            columns = cursor.fetchall()
            for col in columns:
                table_details.append(f"        Column: {col[0]} ({col[1]})")
        conn.close()
        db_details += "\n".join(table_details)
    except Exception as e:
        db_details += f"\n    Error connecting/reading MySQL database: {e}"
    return db_details

# --- Variables Globales ---
selected_project_folder = None  # Carpeta del proyecto
sqlite_file_path = ""           # Archivo SQLite seleccionado

# --- Funciones para la selección de carpeta y base de datos ---
def select_project_folder():
    """Permite seleccionar la carpeta del proyecto y guarda la ruta."""
    global selected_project_folder
    # Load the last used folder from the configuration file
    last_used_paths = load_last_used_paths()
    initial_dir = last_used_paths.get("last_code_folder", os.getcwd())

    folder = filedialog.askdirectory(title="Selecciona carpeta del proyecto", initialdir=initial_dir)
    if folder:
        selected_project_folder = folder
        save_last_used_paths(code_folder=folder)
        messagebox.showinfo("Carpeta seleccionada", f"Carpeta seleccionada:\n{folder}")
    return folder

def seleccionar_sqlite():
    """Permite seleccionar un archivo SQLite (.db, .sqlite, .sqlite3)."""
    global sqlite_file_path
    file_path = filedialog.askopenfilename(
        title="Selecciona archivo SQLite",
        filetypes=[("SQLite Database", "*.sqlite *.db *.sqlite3"), ("Todos los archivos", "*.*")]
    )
    if file_path:
        sqlite_file_path = file_path
        save_last_used_paths(db_folder=os.path.dirname(file_path))
        lbl_sqlite.config(text=os.path.basename(file_path))

def toggle_db_options():
    """Muestra u oculta campos según la opción de base de datos seleccionada."""
    if db_option.get() == "sqlite":
        frame_sqlite.pack(fill=tk.X, pady=5)
        frame_mysql.pack_forget()
    else:
        frame_sqlite.pack_forget()
        frame_mysql.pack(fill=tk.X, pady=5)

def test_db_connection():
    """Conecta a la base de datos seleccionada y muestra su estructura (tablas y columnas)."""
    if db_option.get() == "sqlite":
        if sqlite_file_path:
            db_report = analyze_sqlite_database(sqlite_file_path)
            messagebox.showinfo("SQLite DB Structure", db_report)
        else:
            messagebox.showwarning("No SQLite File", "Por favor, selecciona un archivo SQLite.")
    else:
        server = entry_mysql_server.get().strip()
        user = entry_mysql_user.get().strip()
        password = entry_mysql_pass.get().strip()
        database = entry_mysql_db.get().strip()
        if not (server and user and password and database):
            messagebox.showwarning("Campos incompletos", "Por favor, completa todos los campos de conexión MySQL.")
            return
        save_last_used_paths(mysql_data={"server": server, "user": user, "password": password, "database": database})
        db_report = analyze_mysql_database(server, user, password, database)
        messagebox.showinfo("MySQL DB Structure", db_report)

def save_mysql_data():
    """Guarda los datos de conexión MySQL al perder el foco en cualquier campo."""
    server = entry_mysql_server.get().strip()
    user = entry_mysql_user.get().strip()
    password = entry_mysql_pass.get().strip()
    database = entry_mysql_db.get().strip()
    save_last_used_paths(mysql_data={"server": server, "user": user, "password": password, "database": database})

# --- Funciones para generar el prompt ---
def generar_prompt():
    """Genera el prompt usando los datos del formulario, la estructura del proyecto y el reporte intercalado."""
    prompt = "Crea / modifica un software informático en base a los parámetros que a continuación te voy a indicar:\n\n"

    # Recopilar datos del formulario
    contexto = txt_contexto.get("1.0", tk.END).strip()
    objetivo = txt_objetivo.get("1.0", tk.END).strip()
    restricciones = txt_restricciones.get("1.0", tk.END).strip()
    formato_salida = txt_formato.get("1.0", tk.END).strip()

    if contexto:
        prompt += f"Contexto: {contexto}\n\n"
    if objetivo:
        prompt += f"Objetivo: {objetivo}\n\n"
    if restricciones:
        prompt += f"Restricciones: {restricciones}\n\n"
    if formato_salida:
        prompt += f"Formato de salida: {formato_salida}\n\n"

    # Agregar la estructura del proyecto en forma de árbol si la carpeta contiene "Proyecto"
    if selected_project_folder:
        if "Proyecto" in selected_project_folder:
            structure_tree = build_directory_map(selected_project_folder)
            prompt += "\n Estructura del proyecto \n"
            prompt += "\n" + structure_tree + "\n\n\n"

        # Agregar reporte del código intercalado
        interleaved_report = generate_interleaved_report(selected_project_folder)
        prompt += "\n===== Code Report (Interleaved) =====\n" + interleaved_report + "\n\n"
    else:
        prompt += "\n(No se ha seleccionado carpeta del proyecto para análisis de código)\n\n"

    # Agregar reporte de base de datos (si se ha seleccionado)
    db_report = ""
    if db_option.get() == "sqlite":
        if sqlite_file_path:
            db_report = analyze_sqlite_database(sqlite_file_path)
    else:
        server = entry_mysql_server.get().strip()
        user = entry_mysql_user.get().strip()
        password = entry_mysql_pass.get().strip()
        database = entry_mysql_db.get().strip()
        if server and user and password and database:
            db_report = analyze_mysql_database(server, user, password, database)
    if db_report:
        prompt += "\n===== Database Report =====\n" + db_report

    txt_prompt_output.config(state=tk.NORMAL)
    txt_prompt_output.delete("1.0", tk.END)
    txt_prompt_output.insert(tk.END, prompt)
    txt_prompt_output.config(state=tk.DISABLED)

def generar_prompt_for_folder(project_folder):
    """Genera el prompt para un folder específico (usado para proyectos 'jocarsa-')."""
    prompt = "Crea / modifica un software informático en base a los parámetros que a continuación te voy a indicar:\n\n"

    contexto = txt_contexto.get("1.0", tk.END).strip()
    objetivo = txt_objetivo.get("1.0", tk.END).strip()
    restricciones = txt_restricciones.get("1.0", tk.END).strip()
    formato_salida = txt_formato.get("1.0", tk.END).strip()

    if contexto:
        prompt += f"Contexto: {contexto}\n\n"
    if objetivo:
        prompt += f"Objetivo: {objetivo}\n\n"
    if restricciones:
        prompt += f"Restricciones: {restricciones}\n\n"
    if formato_salida:
        prompt += f"Formato de salida: {formato_salida}\n\n"

    # Estructura del proyecto y reporte intercalado para el folder específico.
    structure_tree = build_directory_map(project_folder)
    prompt += "\n===== Project Structure =====\n"
    prompt += " \n" + structure_tree + "\n \n\n"

    code_report = generate_interleaved_report(project_folder)
    prompt += "\n===== Code Report (Interleaved) =====\n" + code_report + "\n\n"

    db_report = ""
    if db_option.get() == "sqlite":
        if sqlite_file_path:
            db_report = analyze_sqlite_database(sqlite_file_path)
    else:
        server = entry_mysql_server.get().strip()
        user = entry_mysql_user.get().strip()
        password = entry_mysql_pass.get().strip()
        database = entry_mysql_db.get().strip()
        if server and user and password and database:
            db_report = analyze_mysql_database(server, user, password, database)
    if db_report:
        prompt += "\n===== Database Report =====\n" + db_report
    return prompt

def copy_report():
    report_text = txt_prompt_output.get("1.0", tk.END)
    root.clipboard_clear()
    root.clipboard_append(report_text)
    messagebox.showinfo("Portapapeles", "Reporte copiado al portapapeles.")

def save_report():
    report_text = txt_prompt_output.get("1.0", tk.END)
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            messagebox.showinfo("Guardar Reporte", f"Reporte guardado en:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el reporte: {e}")

def load_last_used_paths():
    """Carga las rutas usadas anteriormente desde un archivo JSON."""
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}

def save_last_used_paths(code_folder=None, db_folder=None, mysql_data=None):
    """Guarda las rutas usadas en un archivo JSON."""
    config_path = "config.json"
    config = load_last_used_paths()
    if code_folder:
        config["last_code_folder"] = code_folder
    if db_folder:
        config["last_db_folder"] = db_folder
    if mysql_data:
        config["mysql"] = mysql_data
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

def save_prompts_for_jocarsa_projects():
    """
    Busca subcarpetas que comiencen con 'jocarsa-' en la carpeta seleccionada y guarda el prompt
    en la carpeta 'prompts' (creada junto al script) con el nombre de cada folder.
    """
    if not selected_project_folder:
        messagebox.showwarning("No folder selected", "Por favor, selecciona una carpeta del proyecto primero.")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_folder = os.path.join(script_dir, "prompts")
    if not os.path.exists(prompts_folder):
        os.makedirs(prompts_folder)

    saved_count = 0
    for entry in os.listdir(selected_project_folder):
        full_path = os.path.join(selected_project_folder, entry)
        if os.path.isdir(full_path) and entry.startswith("jocarsa-"):
            prompt_text = generar_prompt_for_folder(full_path)
            file_path = os.path.join(prompts_folder, entry + ".txt")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(prompt_text)
                saved_count += 1
            except Exception as e:
                print(f"Error al guardar prompt en {entry}: {e}")
    if saved_count > 0:
        messagebox.showinfo("Prompts guardados", f"Prompts guardados para {saved_count} proyecto(s) en la carpeta 'prompts'.")
    else:
        messagebox.showinfo("Sin proyectos", "No se encontraron carpetas que comiencen con 'jocarsa-'.")

# --- Configuración de la ventana principal ---
style = ttk.Style('flatly')
root = style.master
root.title("Generador de Prompt para IA")

try:
    logo = tk.PhotoImage(file="lightgoldenrodyellow.png")
    root.iconphoto(True, logo)
except Exception as e:
    print("Logo no encontrado o error al cargarlo:", e)

try:
    root.state("zoomed")
except Exception:
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")

paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
paned.pack(fill=tk.BOTH, expand=True)

frame_left_container = ttk.Frame(paned)
paned.add(frame_left_container, weight=1)

canvas_left = tk.Canvas(frame_left_container, borderwidth=0)
scrollbar_left = ttk.Scrollbar(frame_left_container, orient="vertical", command=canvas_left.yview)
canvas_left.configure(yscrollcommand=scrollbar_left.set)
scrollbar_left.pack(side=tk.RIGHT, fill=tk.Y)
canvas_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

frame_left = ttk.Frame(canvas_left, padding=(60, 20, 20, 20))
canvas_left.create_window((0, 0), window=frame_left, anchor="nw")

def on_frame_configure(event):
    canvas_left.configure(scrollregion=canvas_left.bbox("all"))
frame_left.bind("<Configure>", on_frame_configure)

frame_right = ttk.Frame(paned, padding=10)
paned.add(frame_right, weight=1)

# --- PANEL IZQUIERDO: FORMULARIO ---
lbl_form_title = ttk.Label(frame_left, text="Configuración del Prompt", font=("Arial", 14, "bold"))
lbl_form_title.pack(anchor="w", pady=(0,10))

def crear_campo(master, label_text, desc_text, height=3):
    frame = ttk.Frame(master)
    frame.pack(fill=tk.X, pady=5)
    lbl = ttk.Label(frame, text=label_text, font=("Arial", 10, "bold"))
    lbl.pack(anchor="w")
    lbl_desc = ttk.Label(frame, text=desc_text, font=("Arial", 8))
    lbl_desc.pack(anchor="w")
    txt = tk.Text(frame, height=height)
    txt.pack(fill=tk.X, pady=2)
    return txt

txt_contexto = crear_campo(frame_left, "Contexto", "Explica la situación o problema.", height=3)
txt_objetivo = crear_campo(frame_left, "Objetivo", "Define claramente lo que quieres lograr.", height=3)
txt_restricciones = crear_campo(frame_left, "Restricciones", "Especifica tecnologías, versiones y limitaciones.", height=3)
txt_formato = crear_campo(frame_left, "Formato de salida", "Define si necesitas código, explicación, JSON, etc.", height=3)

btn_select_folder = ttk.Button(frame_left, text="Seleccionar carpeta del proyecto", command=select_project_folder)
btn_select_folder.pack(pady=5, fill=tk.X)

separator = ttk.Separator(frame_left, orient=tk.HORIZONTAL)
separator.pack(fill=tk.X, pady=10)

lbl_db = ttk.Label(frame_left, text="Base de Datos", font=("Arial", 12, "bold"))
lbl_db.pack(anchor="w")

db_option = tk.StringVar(value="sqlite")
frame_db_options = ttk.Frame(frame_left)
frame_db_options.pack(fill=tk.X, pady=5)

rbtn_sqlite = ttk.Radiobutton(frame_db_options, text="SQLite", variable=db_option, value="sqlite", command=toggle_db_options)
rbtn_sqlite.pack(side=tk.LEFT, padx=5)
rbtn_mysql = ttk.Radiobutton(frame_db_options, text="MySQL Dump", variable=db_option, value="mysql", command=toggle_db_options)
rbtn_mysql.pack(side=tk.LEFT, padx=5)

frame_sqlite = ttk.Frame(frame_left)
btn_select_sqlite = ttk.Button(frame_sqlite, text="Seleccionar archivo SQLite", command=seleccionar_sqlite)
btn_select_sqlite.pack(side=tk.LEFT, padx=5)
lbl_sqlite = ttk.Label(frame_sqlite, text="Ningún archivo seleccionado")
lbl_sqlite.pack(side=tk.LEFT, padx=5)

frame_mysql = ttk.Frame(frame_left)
lbl_mysql_server = ttk.Label(frame_mysql, text="Servidor:")
lbl_mysql_server.pack(anchor="w", padx=5, pady=2)
entry_mysql_server = ttk.Entry(frame_mysql)
entry_mysql_server.pack(fill=tk.X, padx=5, pady=2)
entry_mysql_server.bind("<FocusOut>", lambda e: save_mysql_data())

lbl_mysql_user = ttk.Label(frame_mysql, text="Usuario:")
lbl_mysql_user.pack(anchor="w", padx=5, pady=2)
entry_mysql_user = ttk.Entry(frame_mysql)
entry_mysql_user.pack(fill=tk.X, padx=5, pady=2)
entry_mysql_user.bind("<FocusOut>", lambda e: save_mysql_data())

lbl_mysql_pass = ttk.Label(frame_mysql, text="Contraseña:")
lbl_mysql_pass.pack(anchor="w", padx=5, pady=2)
entry_mysql_pass = ttk.Entry(frame_mysql, show="*")
entry_mysql_pass.pack(fill=tk.X, padx=5, pady=2)
entry_mysql_pass.bind("<FocusOut>", lambda e: save_mysql_data())

lbl_mysql_db = ttk.Label(frame_mysql, text="Base de datos:")
lbl_mysql_db.pack(anchor="w", padx=5, pady=2)
entry_mysql_db = ttk.Entry(frame_mysql)
entry_mysql_db.pack(fill=tk.X, padx=5, pady=2)
entry_mysql_db.bind("<FocusOut>", lambda e: save_mysql_data())

btn_test_connection = ttk.Button(frame_left, text="Test DB Connection", command=test_db_connection)
btn_test_connection.pack(pady=5, fill=tk.X)

btn_generar = ttk.Button(frame_left, text="Generar Prompt", bootstyle=SUCCESS, command=generar_prompt)
btn_generar.pack(pady=10, fill=tk.X)

btn_save_prompts = ttk.Button(frame_left, text="Guardar Prompts para proyectos jocarsa-", bootstyle=SUCCESS, command=save_prompts_for_jocarsa_projects)
btn_save_prompts.pack(pady=10, fill=tk.X)

# --- PANEL DERECHO: SALIDA DEL PROMPT ---
lbl_prompt_title = ttk.Label(frame_right, text="Prompt Generado", font=("Arial", 14, "bold"))
lbl_prompt_title.pack(anchor="w", pady=(0,10))

txt_prompt_output = tk.Text(frame_right, wrap="word", state=tk.DISABLED)
txt_prompt_output.pack(fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(txt_prompt_output, orient="vertical", command=txt_prompt_output.yview)
txt_prompt_output.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

frame_report_buttons = ttk.Frame(frame_right)
frame_report_buttons.pack(fill=tk.X, pady=5)

btn_copy = ttk.Button(frame_report_buttons, text="Copiar Reporte", command=copy_report)
btn_copy.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

btn_save = ttk.Button(frame_report_buttons, text="Guardar Reporte", command=save_report)
btn_save.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

# Cargar rutas usadas anteriormente
last_used_paths = load_last_used_paths()
if "last_code_folder" in last_used_paths:
    selected_project_folder = last_used_paths["last_code_folder"]
if "last_db_folder" in last_used_paths:
    sqlite_file_path = last_used_paths["last_db_folder"]
    lbl_sqlite.config(text=os.path.basename(sqlite_file_path))
if "mysql" in last_used_paths:
    mysql_data = last_used_paths["mysql"]
    entry_mysql_server.insert(0, mysql_data.get("server", ""))
    entry_mysql_user.insert(0, mysql_data.get("user", ""))
    entry_mysql_pass.insert(0, mysql_data.get("password", ""))
    entry_mysql_db.insert(0, mysql_data.get("database", ""))

root.mainloop()
