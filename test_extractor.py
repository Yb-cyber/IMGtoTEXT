"""
test_extractor.py - Suite de pruebas automáticas para extractor.py
Valida:
1. Extracción de imagen directa (PNG/JPG con OCR).
2. Extracción de PDF con texto digital (vía PyMuPDF).
3. Extracción de PDF escaneado/imagen (vía PyMuPDF + Tesseract OCR).
"""

import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pymupdf

import extractor

TEST_DIR = Path("test_data")


class TestExtractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        cls.image_path = TEST_DIR / "sample_image.png"
        cls.digital_pdf_path = TEST_DIR / "sample_digital.pdf"
        cls.scanned_pdf_path = TEST_DIR / "sample_scanned.pdf"

        cls.expected_image_text = "Prueba de OCR con Imagen en Espanol"
        cls.expected_digital_text = "Texto digital extraido directamente por PyMuPDF sin necesidad de OCR."
        cls.expected_scanned_text = "Documento escaneado simulado para probar el motor Tesseract OCR."

        font = ImageFont.load_default(size=36)

        # 1. Crear imagen de prueba con Pillow
        img = Image.new("RGB", (900, 200), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((40, 70), cls.expected_image_text, fill="black", font=font)
        img.save(cls.image_path)

        # 2. Crear PDF con texto digital nativo
        doc_digital = pymupdf.open()
        p1 = doc_digital.new_page()
        p1.insert_text((50, 72), cls.expected_digital_text, fontsize=14)
        doc_digital.save(cls.digital_pdf_path)
        doc_digital.close()

        # 3. Crear PDF escaneado (insertando imagen con texto)
        scanned_img = Image.new("RGB", (1200, 250), color="white")
        d_scanned = ImageDraw.Draw(scanned_img)
        d_scanned.text((40, 80), cls.expected_scanned_text, fill="black", font=font)
        scanned_img_path = TEST_DIR / "scanned_page.png"
        scanned_img.save(scanned_img_path)

        doc_scanned = pymupdf.open()
        p2 = doc_scanned.new_page(width=1000, height=300)
        p2.insert_image(pymupdf.Rect(0, 0, 1000, 300), filename=str(scanned_img_path))
        doc_scanned.save(cls.scanned_pdf_path)
        doc_scanned.close()

    def test_01_environment(self):
        tess_bin = extractor.find_tesseract_binary()
        self.assertIsNotNone(tess_bin, "Tesseract binary should be detected")
        self.assertTrue(Path(tess_bin).exists(), f"Binary file does not exist: {tess_bin}")

    def test_02_extract_from_image(self):
        text = extractor.extract_from_image(self.image_path, lang="spa+eng")
        print("\n[Resultado Test Imagen]:", text)
        self.assertIn("Prueba", text)
        self.assertIn("OCR", text)

    def test_03_extract_from_digital_pdf(self):
        res = extractor.extract_from_pdf(self.digital_pdf_path, mode="auto")
        self.assertEqual(res["total_pages"], 1)
        self.assertEqual(res["pages"][0]["method"], "digital")
        self.assertIn("Texto digital extraido", res["full_text"])

    def test_04_extract_from_scanned_pdf_auto_mode(self):
        # En modo auto, debe detectar que no hay texto digital y usar OCR
        res = extractor.extract_from_pdf(self.scanned_pdf_path, mode="auto", min_chars=30)
        self.assertEqual(res["total_pages"], 1)
        self.assertEqual(res["pages"][0]["method"], "ocr")
        print("\n[Resultado Test PDF Escaneado]:", res["pages"][0]["text"])
        self.assertIn("Documento", res["pages"][0]["text"])
        self.assertIn("Tesseract", res["pages"][0]["text"])

    def test_05_process_input_with_output_file(self):
        output_txt = TEST_DIR / "output_result.txt"
        extractor.process_input(self.scanned_pdf_path, output_path=output_txt, mode="auto")
        self.assertTrue(output_txt.exists())
        content = output_txt.read_text(encoding="utf-8")
        self.assertIn("--- Página 1 [OCR] ---", content)


if __name__ == "__main__":
    unittest.main()
