# PDF & Image Text Extractor (PyMuPDF + Tesseract OCR)

Herramienta en Python para la extracción inteligente de texto desde documentos PDF (tanto digitales como escaneados) e imágenes (PNG, JPG, TIFF, WebP, etc.).

El proyecto está diseñado con **portabilidad total**: incluye una versión portable de **Tesseract OCR (v5.5)** y sus modelos de idioma (`spa`, `eng`, `osd`) dentro de la carpeta local `bin/tesseract/`. **No requiere instalar Tesseract en Windows ni configurar variables de entorno del sistema**.

---

## Características Principales

1. **Modo Híbrido Inteligente (`--mode auto`)**:
   - Para PDFs: primero intenta extraer texto digital nativo usando **PyMuPDF** (ultra rápido).
   - Si una página no contiene texto digital o es un documento escaneado/imagen, rasteriza automáticamente la página a alta resolución (300 DPI por defecto) y aplica **Tesseract OCR**.
2. **Extracción Directa de Imágenes**:
   - Procesa directamente archivos de imagen (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp`) aplicando OCR.
3. **100% Portable**:
   - El ejecutable de Tesseract, todas sus DLLs y los modelos de idioma (`spa.traineddata`, `eng.traineddata`) residen en `bin/tesseract/`.
   - Puedes copiar o mover esta carpeta a otra computadora con Windows y funcionará directamente.
4. **Entorno Aislado**:
   - Todas las librerías de Python están instaladas en el entorno virtual local `.venv/`.

---

## Estructura del Proyecto

```text
PDFext/
├── .venv/                      # Entorno virtual de Python
├── bin/
│   └── tesseract/              # Motor Tesseract OCR portable (tesseract.exe + DLLs)
│       └── tessdata/           # Modelos de lenguaje (spa, eng, osd)
├── extractor.py                # Script principal de extracción (CLI y módulo)
├── test_extractor.py           # Suite de pruebas unitarias y de integración
├── requirements.txt            # Dependencias del proyecto
└── README.md                   # Documentación de uso
```

---

## Instrucciones de Uso

### 1. Activar el Entorno Virtual (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
```
*(O puedes ejecutar directamente invocando `.\.venv\Scripts\python.exe` sin necesidad de activar)*

---

### 2. Comprobar el Entorno y Tesseract
Para verificar que el motor OCR y los idiomas están listos:
```powershell
.\.venv\Scripts\python.exe extractor.py --check-env
```

---

### 3. Extraer Texto de un PDF

#### Modo Automático (Digital con fallback a OCR si está escaneado):
```powershell
.\.venv\Scripts\python.exe extractor.py "documento.pdf" -o "resultado.txt"
```

#### Forzar OCR en todas las páginas (en Español):
```powershell
.\.venv\Scripts\python.exe extractor.py "escaneo.pdf" -o "resultado.txt" --mode ocr -l spa
```

#### Solo texto digital nativo (rápido, sin OCR):
```powershell
.\.venv\Scripts\python.exe extractor.py "documento.pdf" -o "resultado.txt" --mode text
```

---

### 4. Extraer Texto de una Imagen

```powershell
.\.venv\Scripts\python.exe extractor.py "foto_pagina.png" -o "texto_imagen.txt" -l spa
```
*(Si omites el parámetro `-o`, el texto se imprimirá directamente en la consola)*

---

## Opciones y Parámetros Disponibles (`extractor.py`)

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `input` | Ruta al archivo PDF o imagen a procesar. | *Obligatorio* |
| `-o, --output` | Ruta del archivo `.txt` donde guardar el resultado. Si se omite, se muestra en pantalla. | Consola (`stdout`) |
| `-l, --lang` | Idioma(s) para OCR (`spa`, `eng`, `spa+eng`). | `spa+eng` |
| `-m, --mode` | Modo para PDFs: `auto` (híbrido inteligente), `ocr` (forzar OCR), `text` (solo texto digital). | `auto` |
| `--dpi` | Resolución DPI de rasterizado para OCR en PDFs (300 DPI recomendado para máxima precisión). | `300` |
| `--min-chars` | Umbral de caracteres en modo `auto` para considerar que la página necesita OCR. | `40` |
| `--tesseract-cmd`| Ruta personalizada al ejecutable `tesseract.exe` (opcional). | Auto-detectado en `bin/tesseract/` |
| `--check-env` | Muestra diagnóstico de librerías, versión de Tesseract e idiomas detectados. | - |

---

## Ejecutar Pruebas Automatizadas

Para validar que todos los componentes (PyMuPDF, Pillow, Tesseract OCR portable) funcionan al 100%:
```powershell
.\.venv\Scripts\python.exe test_extractor.py
```

---

## ¿Cómo llevarlo a otra computadora?

1. Copia la carpeta `PDFext` a la otra computadora.
2. Si la otra computadora tiene Python instalado:
   - Puedes crear un entorno virtual e instalar `pip install -r requirements.txt`.
   - **No necesitas instalar Tesseract ni drivers**, ya que la carpeta `bin/tesseract/` ya contiene todo lo necesario para procesar OCR de forma independiente.
