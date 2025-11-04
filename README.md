# Generador de Prompt (Flask)

Versión web del app de Tkinter con una interfaz moderna (Bootstrap 5), render de Markdown (marked.js) y resaltado de código (highlight.js).

## Requisitos
- Python 3.10+
- pip

## Instalación
```bash
cd prompt_generator_webapp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso
```bash
python app.py
# abre http://127.0.0.1:5000
```

> **Nota:** Al ejecutarlo en local, el selector de carpetas funciona como un mini-explorador de rutas del sistema desde el navegador. 
Las operaciones de análisis (`os.walk`, SQLite y MySQL) se ejecutan en el servidor local (Flask), por lo que deben apuntar a rutas válidas de tu máquina.

## Características
- **Parámetros del prompt**: Contexto, Objetivo, Restricciones, Formato.
- **Explorador de carpetas** integrado para elegir el proyecto.
- **Generación de estructura y reporte intercalado** del código (mismas reglas que el Tkinter).
- **Análisis de base de datos** SQLite o MySQL (opcional PyMySQL).
- **Vista Markdown y WYSIWYG** con resaltado.
- **Guardar reportes** con nombre `<carpeta>_YYYYmmddHHMMSS.txt`.
- **Guardar prompts de subcarpetas `jocarsa-*`** en carpeta `prompts/`.
- **Persistencia** en `config.json`.

## Configuración
Pulsa "Guardar configuración" para actualizar `config.json`.
