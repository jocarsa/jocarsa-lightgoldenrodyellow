
# 📄 Generador de Reportes Markdown de Proyectos

Este script en Python genera automáticamente un **reporte completo en formato Markdown** (`.md`) a partir del contenido de una carpeta de código.  
El reporte incluye:

- 🗂️ **Árbol de directorios** con indentación tipo `tree`
- 💻 **Código fuente intercalado**, mostrando el contenido de cada archivo permitido dentro de bloques de código Markdown con su respectiva sintaxis resaltada.

Ideal para:
- Documentar proyectos antes de publicarlos.
- Crear informes de entregas o prácticas de programación.
- Respaldar el código en un solo documento legible y portable.

---

## 🚀 Características

✅ Genera un único archivo `.md` con todo el código del proyecto.  
✅ Incluye un árbol visual de carpetas y archivos.  
✅ Detecta el lenguaje automáticamente según la extensión.  
✅ Omite carpetas comunes como `node_modules`, `.git`, `__pycache__`, etc.  
✅ Permite definir tus propias extensiones o carpetas excluidas.  

---

## 🧩 Extensiones soportadas

El script incluye por defecto las siguientes extensiones:

| Tipo de archivo | Extensión | Lenguaje usado en Markdown |
|-----------------|------------|-----------------------------|
| HTML            | `.html`    | html                        |
| CSS             | `.css`     | css                         |
| JavaScript      | `.js`      | js                          |
| PHP             | `.php`     | php                         |
| Python          | `.py`      | python                      |
| Java            | `.java`    | java                        |
| SQL             | `.sql`     | sql                         |
| C / C++         | `.c`, `.cpp`, `.h` | c / cpp             |
| CUDA            | `.cu`      | cuda                        |
| JSON            | `.json`    | json                        |
| XML             | `.xml`     | xml                         |
| Markdown        | `.md`      | markdown                    |

---

## 📁 Carpetas excluidas por defecto

Las siguientes carpetas no se incluyen en el análisis:

```

.git
node_modules
vendor
venv
.venv
**pycache**
modelo_entrenado

````

Puedes modificar la constante `CARPETAS_EXCLUIDAS` en el script para personalizar esta lista.

---

## ⚙️ Instalación

No requiere dependencias externas más allá de Python 3.

```bash
git clone https://github.com/tuusuario/generador-reporte-markdown.git
cd generador-reporte-markdown
chmod +x generador_reporte.py
````

---

## 🖥️ Uso

Ejecuta el script indicando:

1. La carpeta **origen** del proyecto.
2. La carpeta **destino** donde se guardará el reporte.

```bash
./generador_reporte.py /ruta/a/tu/proyecto /ruta/de/salida
```

### Ejemplo:

```bash
./generador_reporte.py ~/proyectos/miapp ./reportes
```

Salida esperada:

```
[OK] Reporte generado: /ruta/absoluta/reportes/miapp_20251105184522.md
```

---

## 🧠 Estructura del resultado

El archivo Markdown generado incluye:

```markdown
# Reporte de proyecto

## Estructura del proyecto
```

```
/ruta/al/proyecto
├── index.html
├── styles.css
└── src
    ├── app.py
    └── utils.py
```

````markdown
## Código (intercalado)

# src
**app.py**
```python
print("Hola mundo")
````

**utils.py**

```python
def suma(a, b):
    return a + b
```

```

---

## 🧩 Integración y personalización

Puedes integrar este script en pipelines de documentación o CI/CD para generar automáticamente un `.md` de cada commit o versión de tu código.

### Opciones posibles de personalización:
- Cambiar la lista de extensiones soportadas (`EXTENSIONES_PERMITIDAS`).
- Excluir o incluir carpetas adicionales.
- Modificar el formato del nombre del archivo generado.
- Integrar metadatos como autor, fecha o hash de commit.

---

## 🧑‍💻 Autor

**José Vicente Carratalá Sanchis**  
📧 [info@josevicentecarratala.com](mailto:info@josevicentecarratala.com)  
🌐 [https://www.josevicentecarratala.com](https://www.josevicentecarratala.com)  
💼 [JOCARSA](https://jocarsa.com)

---

## 🪪 Licencia

Este proyecto se distribuye bajo la licencia **MIT**.  
Eres libre de usarlo, modificarlo y compartirlo, siempre que mantengas la atribución al autor original.

```

MIT License © 2025 José Vicente Carratalá Sanchis

```

---

## ⭐ Ejemplo visual

![Ejemplo del reporte](https://raw.githubusercontent.com/tuusuario/generador-reporte-markdown/main/preview.png)

---

## 📘 Historial de versiones

| Versión | Fecha | Cambios principales |
|----------|--------|---------------------|
| 1.0.0 | 2025-11-05 | Versión inicial pública |

---



