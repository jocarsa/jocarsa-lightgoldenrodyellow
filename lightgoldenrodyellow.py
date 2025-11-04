#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime

# =========================
# Configuración mínima
# =========================
EXTENSIONES_PERMITIDAS = (
    ".html", ".css", ".js", ".php", ".py", ".java", ".sql",
    ".c", ".cpp", ".cu", ".h", ".json", ".xml", ".md"
)
CARPETAS_EXCLUIDAS = {
    ".git", "node_modules", "vendor", "venv", "__pycache__",
    "modelo_entrenado", ".venv"
}

LANG_MAP = {
    ".html": "html", ".css": "css", ".js": "js", ".php": "php",
    ".py": "python", ".java": "java", ".sql": "sql", ".c": "c",
    ".cpp": "cpp", ".cu": "cuda", ".h": "c", ".json": "json",
    ".xml": "xml", ".md": "markdown",
}

# =========================
# Utilidades
# =========================
def construir_mapa_directorios(ruta_raiz: str) -> str:
    """Devuelve un árbol de directorios estilo 'tree', excluyendo carpetas no deseadas."""
    lineas = []
    raiz_abs = os.path.abspath(ruta_raiz)
    lineas.append(raiz_abs)

    def interno(dir_path: str, prefijo: str = ""):
        try:
            entradas = sorted(os.listdir(dir_path))
        except Exception:
            return
        # Filtra carpetas excluidas
        entradas_visibles = []
        for e in entradas:
            full = os.path.join(dir_path, e)
            if os.path.isdir(full) and e in CARPETAS_EXCLUIDAS:
                continue
            entradas_visibles.append(e)

        for i, entrada in enumerate(entradas_visibles):
            ruta_completa = os.path.join(dir_path, entrada)
            conector = "└── " if i == len(entradas_visibles) - 1 else "├── "
            lineas.append(prefijo + conector + entrada)
            if os.path.isdir(ruta_completa):
                extension = "    " if i == len(entradas_visibles) - 1 else "│   "
                interno(ruta_completa, prefijo + extension)

    interno(ruta_raiz)
    return "\n".join(lineas)


def generar_reporte_intercalado(ruta_raiz: str, nivel: int = 1) -> str:
    """
    Recorre la carpeta y, para cada archivo con extensión permitida,
    inserta su contenido en un bloque de código Markdown.
    """
    encabezado = "#" * nivel
    nombre_carpeta = os.path.basename(ruta_raiz) or ruta_raiz
    lineas = [f"{encabezado} {nombre_carpeta}"]

    try:
        entradas = sorted(os.listdir(ruta_raiz))
    except Exception as e:
        lineas.append(f"Error listando la carpeta: {e}")
        return "\n".join(lineas)

    # Archivos de este nivel
    for entrada in entradas:
        ruta_completa = os.path.join(ruta_raiz, entrada)
        if os.path.isfile(ruta_completa) and entrada.lower().endswith(EXTENSIONES_PERMITIDAS):
            ext = os.path.splitext(entrada)[1].lower()
            lang = LANG_MAP.get(ext, "")
            lineas.append(f"**{entrada}**")
            try:
                with open(ruta_completa, "r", encoding="utf-8", errors="ignore") as f:
                    contenido = f.read()
            except Exception as e:
                contenido = f"Error al leer el archivo: {e}"
            lineas.append(f"```{lang}")
            lineas.append(contenido)
            lineas.append("```")

    # Subcarpetas (excluyendo las no deseadas)
    for entrada in entradas:
        ruta_completa = os.path.join(ruta_raiz, entrada)
        if os.path.isdir(ruta_completa) and entrada not in CARPETAS_EXCLUIDAS:
            lineas.append(generar_reporte_intercalado(ruta_completa, nivel + 1))

    return "\n".join(lineas)


def generar_reporte(ruta_origen: str) -> str:
    """
    Genera el contenido completo del reporte en Markdown:
    - Árbol de directorios
    - Código intercalado
    """
    arbol = construir_mapa_directorios(ruta_origen)
    intercalado = generar_reporte_intercalado(ruta_origen)

    partes = []
    partes.append("# Reporte de proyecto\n")
    partes.append("## Estructura del proyecto\n")
    partes.append("```\n" + arbol + "\n```\n")
    partes.append("## Código (intercalado)\n")
    partes.append(intercalado)
    return "\n".join(partes)


# =========================
# CLI
# =========================
def main():
    parser = argparse.ArgumentParser(
        description="Genera un reporte Markdown de una carpeta de código (árbol + contenidos)."
    )
    parser.add_argument("source_root", help="Carpeta origen a inspeccionar")
    parser.add_argument("dest_folder", help="Carpeta destino donde guardar el reporte")
    args = parser.parse_args()

    source_root = os.path.abspath(args.source_root)
    dest_folder = os.path.abspath(args.dest_folder)

    if not os.path.isdir(source_root):
        print(f"[ERROR] La carpeta origen no existe o no es un directorio: {source_root}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(dest_folder, exist_ok=True)

    base_name = os.path.basename(source_root.rstrip(os.sep)) or "reporte"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    out_name = f"{base_name}_{timestamp}.md"
    out_path = os.path.join(dest_folder, out_name)

    try:
        contenido = generar_reporte(source_root)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(contenido)
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Proceso cancelado por el usuario.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] No se pudo generar o guardar el reporte: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"[OK] Reporte generado: {out_path}")


if __name__ == "__main__":
    main()

