import pytesseract 
from PIL import Image
import io
import re
from pathlib import Path
import os

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

def pdf_to_text(file_path):
    """
    Extraer texto de PDF o imagen con OCR mejorado
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return "[ERROR] Archivo no encontrado"
    
    try:
        if file_path.suffix.lower() == ".pdf":
            return _process_pdf(file_path)
        else:
            return _process_image(file_path)
            
    except Exception as e:
        return f"[ERROR] {str(e)}"

def _process_pdf(file_path):
    """Procesar archivo PDF"""
    if not PYMUPDF_AVAILABLE:
        return "[ERROR] PyMuPDF no disponible: pip install pymupdf"
    
    try:
        doc = fitz.open(file_path)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Intentar extracción directa primero
            text = page.get_text().strip()
            if text:
                text_parts.append(f"--- Página {page_num + 1} ---\n{text}")
            else:
                # Fallback a OCR
                ocr_text = _extract_with_ocr(page)
                if ocr_text:
                    text_parts.append(f"--- Página {page_num + 1} (OCR) ---\n{ocr_text}")
        
        doc.close()
        return "\n\n".join(text_parts) if text_parts else "[INFO] PDF sin texto extraíble"
        
    except Exception as e:
        return f"[ERROR] Procesando PDF: {str(e)}"

def _process_image(file_path):
    """Procesar archivo de imagen"""
    try:
        img = Image.open(file_path)
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÁÉÍÓÚáéíóúÑñ.,;:()$-/ '
        text = pytesseract.image_to_string(img, lang="spa", config=custom_config)
        return text.strip() if text.strip() else "[INFO] Imagen sin texto detectable"
    except Exception as e:
        return f"[ERROR] Procesando imagen: {str(e)}"

def _extract_with_ocr(page):
    """Extraer texto usando OCR desde página PDF"""
    try:
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, lang="spa", config=custom_config)
        return text.strip()
    except Exception:
        return ""

# Alias para compatibilidad
extract_text_from_pdf = pdf_to_text