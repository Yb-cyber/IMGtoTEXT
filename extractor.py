"""
extractor.py - Extractor de texto inteligente para PDFs e Imágenes usando PyMuPDF y Tesseract OCR.
Soporta detección automática de binario portable de Tesseract, modo híbrido digital/OCR, y múltiples idiomas.
"""

import os
import sys
import argparse
import io
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

import pymupdf  # PyMuPDF
import pytesseract
from PIL import Image

# Extensiones de imagen soportadas
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}


def get_base_dir() -> Path:
    """Retorna el directorio base del script o ejecutable."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def find_tesseract_binary(custom_path: Optional[str] = None) -> Optional[str]:
    """
    Localiza el ejecutable de Tesseract en orden de prioridad:
    1. Ruta personalizada vía parámetro o variable de entorno TESSERACT_CMD.
    2. Binario portable local dentro del proyecto (ej: bin/tesseract/tesseract.exe).
    3. Rutas de instalación típicas en Windows.
    4. Sistema PATH.
    """
    base_dir = get_base_dir()

    candidates: List[Path] = []

    # 1. Argumento personalizado o variable de entorno
    if custom_path:
        candidates.append(Path(custom_path))
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd:
        candidates.append(Path(env_cmd))

    # 2. Rutas locales portables dentro del proyecto
    candidates.extend([
        base_dir / "bin" / "tesseract" / "tesseract.exe",
        base_dir / "bin" / "tesseract.exe",
        base_dir / "tesseract" / "tesseract.exe",
        base_dir / "tesseract_bin" / "tesseract.exe",
    ])

    # 3. Rutas del sistema en Windows
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")

    candidates.extend([
        Path(program_files) / "Tesseract-OCR" / "tesseract.exe",
        Path(program_files_x86) / "Tesseract-OCR" / "tesseract.exe",
        Path(local_appdata) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
    ])

    # Verificar existencia en orden
    for candidate in candidates:
        if candidate and candidate.is_file():
            cmd_str = str(candidate.resolve())
            configure_tessdata(candidate.parent)
            return cmd_str

    # 4. PATH del sistema
    path_in_env = shutil.which("tesseract") or shutil.which("tesseract.exe")
    if path_in_env:
        resolved = Path(path_in_env).resolve()
        configure_tessdata(resolved.parent)
        return str(resolved)

    return None


def configure_tessdata(tesseract_dir: Path) -> None:
    """Configura la variable TESSDATA_PREFIX si existe la carpeta tessdata junto al binario."""
    possible_tessdata = [
        tesseract_dir / "tessdata",
        tesseract_dir.parent / "tessdata",
    ]
    for td in possible_tessdata:
        if td.is_dir() and not os.environ.get("TESSDATA_PREFIX"):
            os.environ["TESSDATA_PREFIX"] = str(td.resolve())
            break


def setup_tesseract(custom_path: Optional[str] = None) -> bool:
    """Configura pytesseract con el ejecutable encontrado."""
    bin_path = find_tesseract_binary(custom_path)
    if bin_path:
        pytesseract.pytesseract.tesseract_cmd = bin_path
        return True
    return False


# Auto-configurar al cargar el módulo si el binario está disponible
setup_tesseract()


def get_available_languages() -> List[str]:
    """Retorna lista de idiomas disponibles en Tesseract si está configurado."""
    try:
        return pytesseract.get_languages(config="")
    except Exception:
        return []


def extract_from_image(image_path: Path, lang: str = "spa+eng") -> str:
    """Extrae texto de un archivo de imagen usando Tesseract OCR."""
    setup_tesseract()
    with Image.open(image_path) as img:
        # Convertir a RGB si es necesario (ej: imágenes con paleta o RGBA)
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        text = pytesseract.image_to_string(img, lang=lang)
    return text.strip()


def extract_from_pdf(
    pdf_path: Path,
    lang: str = "spa+eng",
    mode: str = "auto",
    dpi: int = 300,
    min_chars: int = 40,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Extrae texto de un archivo PDF página por página.
    Modos:
      - 'auto': Usa texto digital nativo si existe; si la página está vacía/escaneada, aplica OCR.
      - 'ocr': Forzar OCR en todas las páginas rasterizadas.
      - 'text': Solo extrae texto digital nativo (rápido, sin OCR).
    """
    setup_tesseract()
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    pages_result = []

    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)

    for page_num in range(total_pages):
        page = doc[page_num]
        method_used = "digital"
        extracted_text = ""

        if mode in ("auto", "text"):
            extracted_text = page.get_text().strip()

        # Determinar si requiere OCR
        needs_ocr = False
        if mode == "ocr":
            needs_ocr = True
        elif mode == "auto" and len(extracted_text) < min_chars:
            needs_ocr = True

        if needs_ocr:
            method_used = "ocr"
            # Rasterizar la página a imagen en memoria
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            img_bytes = pixmap.tobytes("png")
            with Image.open(io.BytesIO(img_bytes)) as pil_img:
                extracted_text = pytesseract.image_to_string(pil_img, lang=lang).strip()

        pages_result.append({
            "page_number": page_num + 1,
            "method": method_used,
            "text": extracted_text,
        })

        if progress_callback:
            progress_callback(page_num + 1, total_pages, method_used)

    doc.close()

    full_text = "\n\n".join(
        f"--- Página {p['page_number']} [{p['method'].upper()}] ---\n{p['text']}"
        for p in pages_result
    )

    return {
        "file": str(pdf_path),
        "total_pages": total_pages,
        "pages": pages_result,
        "full_text": full_text,
    }


def process_input(
    input_path: Path,
    output_path: Optional[Path] = None,
    lang: str = "spa+eng",
    mode: str = "auto",
    dpi: int = 300,
    min_chars: int = 40,
    tesseract_cmd: Optional[str] = None,
) -> str:
    """Procesa un archivo (PDF o Imagen) o un directorio completo."""
    if not input_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo o ruta: {input_path}")

    # Configurar Tesseract si el modo requiere OCR o es una imagen
    tesseract_ok = setup_tesseract(tesseract_cmd)
    
    suffix = input_path.suffix.lower()
    is_image = suffix in SUPPORTED_IMAGE_EXTENSIONS
    is_pdf = suffix in SUPPORTED_PDF_EXTENSIONS

    if (is_image or mode in ("auto", "ocr")) and not tesseract_ok:
        if is_image or mode == "ocr":
            raise RuntimeError(
                "No se encontró el binario de Tesseract OCR. "
                "Coloca Tesseract portable en la carpeta 'bin/tesseract/' o especifica la ruta con --tesseract-cmd."
            )
        else:
            print("AVISO: Tesseract OCR no detectado. Se extraerá únicamente texto digital disponible.", file=sys.stderr)

    result_text = ""

    if is_pdf:
        def on_progress(current, total, method):
            print(f"Procesando página {current}/{total} (Método: {method})...", file=sys.stderr)

        pdf_data = extract_from_pdf(
            input_path,
            lang=lang,
            mode=mode,
            dpi=dpi,
            min_chars=min_chars,
            progress_callback=on_progress,
        )
        result_text = pdf_data["full_text"]

    elif is_image:
        print(f"Procesando imagen: {input_path.name} con OCR ({lang})...", file=sys.stderr)
        text = extract_from_image(input_path, lang=lang)
        result_text = f"--- Imagen: {input_path.name} [OCR] ---\n{text}"

    else:
        raise ValueError(
            f"Formato no soportado: '{suffix}'. "
            f"Formatos soportados: {sorted(list(SUPPORTED_PDF_EXTENSIONS | SUPPORTED_IMAGE_EXTENSIONS))}"
        )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result_text, encoding="utf-8")
        print(f"\n[OK] Resultado guardado exitosamente en: {output_path}")

    return result_text


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extractor inteligente de texto de PDFs e Imágenes (PyMuPDF + Tesseract OCR)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Extraer texto de un PDF en modo automático (digital con fallback a OCR):
  python extractor.py documento.pdf -o resultado.txt

  # Forzar OCR en español a 300 DPI:
  python extractor.py escaneo.pdf -o resultado.txt --mode ocr --lang spa --dpi 300

  # Extraer texto de una imagen:
  python extractor.py captura.png -o texto_captura.txt --lang spa+eng

  # Usar un binario portable de Tesseract en ruta específica:
  python extractor.py documento.pdf --tesseract-cmd bin/tesseract/tesseract.exe
        """,
    )

    parser.add_argument("input", nargs="?", default=None, help="Ruta al archivo PDF o Imagen")
    parser.add_argument("-o", "--output", help="Ruta del archivo de salida (.txt). Si se omite, se muestra en consola.")
    parser.add_argument(
        "-l", "--lang",
        default="spa+eng",
        help="Idioma(s) para OCR separados por '+'. Ej: 'spa', 'eng', 'spa+eng'. Por defecto: 'spa+eng'.",
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["auto", "ocr", "text"],
        default="auto",
        help="Modo para PDFs: 'auto' (híbrido inteligente), 'ocr' (forzar OCR), 'text' (solo texto nativo). Por defecto: 'auto'.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolución de rasterizado DPI para OCR en PDFs. Recomendado 300 para alta calidad. Por defecto: 300.",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=40,
        help="Mínimo de caracteres digitales por página en modo 'auto' antes de activar OCR. Por defecto: 40.",
    )
    parser.add_argument(
        "--tesseract-cmd",
        help="Ruta explícita al ejecutable tesseract.exe si no está en bin/tesseract ni en el sistema.",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Verifica el entorno: detección de Tesseract, idiomas instalados y versiones de librerías.",
    )

    return parser


def check_environment(custom_cmd: Optional[str] = None):
    """Muestra información de diagnóstico del sistema y Tesseract."""
    print("=== Diagnóstico de Entorno ===")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"PyMuPDF version: {pymupdf.__version__}")
    print(f"Pillow version: {Image.__version__}")
    print(f"pytesseract version: {pytesseract.__version__}")

    tess_path = find_tesseract_binary(custom_cmd)
    if tess_path:
        print(f"\n[OK] Tesseract detectado: {tess_path}")
        pytesseract.pytesseract.tesseract_cmd = tess_path
        try:
            version = pytesseract.get_tesseract_version()
            print(f"Versión de Tesseract: {version}")
            langs = get_available_languages()
            print(f"Idiomas disponibles en tessdata: {', '.join(langs) if langs else 'Ninguno detectado'}")
        except Exception as e:
            print(f"Aviso al consultar versión o idiomas: {e}")
    else:
        print("\n[!] Tesseract NO fue detectado en rutas locales ni del sistema.")
        print("    Para habilitar OCR portable, coloca los binarios en:")
        print(f"    {get_base_dir() / 'bin' / 'tesseract' / 'tesseract.exe'}")
        print("    O instala Tesseract en el sistema con: winget install UB-Mannheim.TesseractOCR")


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.check_env:
        check_environment(args.tesseract_cmd)
        return

    if not args.input:
        parser.error("El argumento 'input' es obligatorio a menos que se use --check-env")

    input_file = Path(args.input)
    output_file = Path(args.output) if args.output else None

    try:
        result = process_input(
            input_path=input_file,
            output_path=output_file,
            lang=args.lang,
            mode=args.mode,
            dpi=args.dpi,
            min_chars=args.min_chars,
            tesseract_cmd=args.tesseract_cmd,
        )
        if not output_file:
            print("\n" + result)
    except Exception as e:
        print(f"\n[ERROR]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
