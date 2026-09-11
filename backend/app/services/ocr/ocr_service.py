import os
import hashlib
import logging
from typing import Tuple
import pypdf
import fitz
from PIL import Image

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

class OCRService:
    @staticmethod
    def calculate_sha256(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def process_file(file_path: str) -> Tuple[str, float]:
        """
        Extracts text from PDF or Image file.
        Returns: (extracted_text, ocr_confidence)
        """
        ext = os.path.splitext(file_path)[1].lower()
        extracted_text = ""
        confidence = 95.0

        if ext == ".pdf":
            # 1. Try PyMuPDF
            try:
                doc = fitz.open(file_path)
                full_text = []
                for page in doc:
                    text = page.get_text("text")
                    if text.strip():
                        full_text.append(text)
                doc.close()
                extracted_text = "\n".join(full_text).strip()
            except Exception:
                extracted_text = ""

            # 2. Fallback to pypdf
            if not extracted_text:
                try:
                    reader = pypdf.PdfReader(file_path)
                    pypdf_text = []
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            pypdf_text.append(t)
                    extracted_text = "\n".join(pypdf_text).strip()
                except Exception as exc:
                    logger.warning("PDF text extraction fallback failed for %s: %s", file_path, exc)

            # 3. Render image-only PDFs and run the existing OCR engine.
            if not extracted_text:
                try:
                    with open(file_path, "rb") as raw_file:
                        raw = raw_file.read().decode("utf-8", errors="ignore").strip()
                    if any(marker in raw.upper() for marker in (
                        "GSTIN", "GOODS AND SERVICES TAX", "GST", "UDYAM", "PERMANENT ACCOUNT NUMBER",
                        "INCOME TAX", "PAN", "EPFO", "EMPLOYEES' PROVIDENT FUND",
                    )):
                        extracted_text = raw
                        confidence = 75.0
                except Exception as exc:
                    logger.warning("Raw PDF content fallback failed for %s: %s", file_path, exc)

            if not extracted_text:
                try:
                    if PYTESSERACT_AVAILABLE:
                        doc = fitz.open(file_path)
                        ocr_pages = []
                        for page in doc:
                            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                            page_text = pytesseract.image_to_string(image).strip()
                            if page_text:
                                ocr_pages.append(page_text)
                        doc.close()
                        extracted_text = "\n".join(ocr_pages).strip()
                        confidence = 90.0 if extracted_text else 50.0
                    else:
                        logger.warning("PDF OCR required but pytesseract is unavailable for %s", file_path)
                except Exception as exc:
                    logger.exception("PDF OCR failed for %s", file_path)
                    confidence = 50.0

        elif ext in [".png", ".jpg", ".jpeg"]:
            if PYTESSERACT_AVAILABLE:
                try:
                    img = Image.open(file_path)
                    extracted_text = pytesseract.image_to_string(img).strip()
                    confidence = 90.0
                except Exception:
                    extracted_text = ""
                    confidence = 50.0
            
            if not extracted_text:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        raw = f.read()
                        if "GSTIN" in raw or "UDYAM" in raw or "PAN" in raw:
                            extracted_text = raw.strip()
                            confidence = 90.0
                except Exception as exc:
                    logger.warning("Image OCR fallback failed for %s: %s", file_path, exc)

        return extracted_text, confidence
