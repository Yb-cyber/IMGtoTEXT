"""
setup_portable_tesseract.py
Descarga los modelos de idioma necesarios (español, inglés, osd) dentro de bin/tesseract/tessdata/
y limpia los archivos temporales de instalación.
"""

import os
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TESSDATA_DIR = BASE_DIR / "bin" / "tesseract" / "tessdata"
TEMP_DIR = BASE_DIR / "temp_setup"

MODELS = {
    "spa.traineddata": "https://github.com/tesseract-ocr/tessdata_fast/raw/main/spa.traineddata",
    "eng.traineddata": "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata",
    "osd.traineddata": "https://github.com/tesseract-ocr/tessdata_fast/raw/main/osd.traineddata",
}


def download_file(url: str, dest_path: Path, description: str):
    print(f"Descargando {description}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as out_file:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        block_size = 65536
        while True:
            chunk = resp.read(block_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                percent = downloaded / total * 100
                sys.stdout.write(f"\r  Progreso: {percent:.1f}% ({downloaded / 1024 / 1024:.2f} MB / {total / 1024 / 1024:.2f} MB)")
                sys.stdout.flush()
    print("\n  [OK] Guardado en:", dest_path.name)


def main():
    print("=== Configuración de Modelos de Idioma para Tesseract Portable ===")
    TESSDATA_DIR.mkdir(parents=True, exist_ok=True)

    for filename, url in MODELS.items():
        dest = TESSDATA_DIR / filename
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"[OK] {filename} ya está presente.")
        else:
            download_file(url, dest, filename)

    # Limpiar carpeta temporal si existe
    if TEMP_DIR.exists():
        print("\nLimpiando archivos temporales...")
        for p in TEMP_DIR.iterdir():
            try:
                p.unlink()
            except Exception:
                pass
        try:
            TEMP_DIR.rmdir()
        except Exception:
            pass

    print("\n[OK] Modelos instalados correctamente en:", TESSDATA_DIR)


if __name__ == "__main__":
    main()
