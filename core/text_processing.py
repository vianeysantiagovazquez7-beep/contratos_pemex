# core/text_processing.py
import re
import json
from pathlib import Path

# Persistencia de anexos detectados
ANEXOS_DB_PATH = Path("data") / "anexos_base.json"

# Base inicial (puedes ajustar)
BASE_ANEXOS = [
    "A", "B", "B-1", "C", "CN", "E", "F", "I", "SSPA", "PACMA",
    "AP", "MMRDD", "GNR", "PUE", "BDE", "Garantías"
]

# Área fija (según tu requerimiento)
AREA_FIJA = "SUBDIRECCIÓN DE PRODUCCIÓN REGIÓN NORTE GERENCIA DE MANTENIMIENTO CONFIABILIDAD Y CONSTRUCCIÓN"

# ----------------- Helpers -----------------
def _ensure_db():
    ANEXOS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # corregido
    if not ANEXOS_DB_PATH.exists():
        with open(ANEXOS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted(set(BASE_ANEXOS)), f, ensure_ascii=False, indent=2)

def load_known_anexos():
    _ensure_db()
    with open(ANEXOS_DB_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return list(data)
        except Exception:
            return BASE_ANEXOS.copy()

def save_known_anexos(anexos):
    _ensure_db()
    with open(ANEXOS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(set(anexos)), f, ensure_ascii=False, indent=2)

def _clean_whitespace(text):
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ----------------- Extracción específica -----------------
def _extract_contrato_and_contratista(text):
    contrato = ""
    contratista = ""

    m = re.search(r'\b(64\d{6,7})\b', text)
    if m:
        contrato = m.group(1)

    m = re.search(
        r'Contrato\s*(?:N(?:ú|u)mero|N\.|NO\.|N)\s*[:\-]?\s*(64\d{6,7}|\d{6,10})\s+([A-ZÁÉÍÓÚÑ0-9\.,\s&\-]{5,200}?)\s+(?:Hoja|Página|\bHoja\b|\bPágina\b|\bDE\b)',
        text,
        re.IGNORECASE
    )
    if m:
        if not contrato:
            contrato = m.group(1).strip()
        contratista = m.group(2).strip()

    if not contratista and contrato:
        pattern = rf'.{{0,80}}{re.escape(contrato)}[^\n]*\n([^\n]{{5,200}})'
        m2 = re.search(pattern, text, re.IGNORECASE)
        if m2:
            candidate = m2.group(1).strip()
            if len(candidate) > 4:
                contratista = candidate.split('Hoja')[0].strip()

    if not contratista:
        m3 = re.search(r'(?:PROVEEDOR|RAZ[ÓO]N\s+SOCIAL|CONTRATISTA)\s*[:\-]\s*([^\n]{5,200})', text, re.IGNORECASE)
        if m3:
            contratista = m3.group(1).strip()

    return contrato or "", contratista or ""

def _extract_objeto(text):
    m = re.search(r'(?:\n|^)\s*4\.\s*.*?OBJETO[^\n]*\n(.*?)(?=\n\s*(?:5\.|\d+\.)|\n\s*MONTO|\n\s*CL[AÁ]USULA|\n{2,})', text, re.IGNORECASE | re.DOTALL)
    if not m:
        m = re.search(r'OBJETO(?:\s+DEL\s+CONTRATO)?[^\n]*[:\-]?\s*(.*?)(?=\n\s*\d+\.|\n{2,}|MONTO|PLAZO)', text, re.IGNORECASE | re.DOTALL)
    if m:
        objeto = m.group(1).strip()
        q = re.search(r'[“"«]([^”"»]+)[”"»]', objeto)
        if q:
            return q.group(1).strip()
        objeto = re.sub(r'\s+', ' ', objeto)
        return objeto.strip()
    return ""

def _extract_monto(text):
    m = re.search(r'\$\s*([\d{1,3}\.,]{1,}\d{0,2})(?:\s*M\.?N\.?)?', text, re.IGNORECASE)
    if m:
        val = m.group(1).strip()
        val = val.replace(' ', '')
        return f"${val}"
    return ""

def _extract_plazo(text):
    m = re.search(r'11\.\s*PLAZO[^\n]*?(?:es\s+de\s+)?\s*(\d{1,4})\s*(?:D[IÍ]AS|DIAS)', text, re.IGNORECASE)
    if m:
        return m.group(1)
    m2 = re.search(r'(\d{1,4})\s*(?:D[IÍ]AS|DIAS)', text, re.IGNORECASE)
    if m2:
        return m2.group(1)
    return ""

def _extract_anexos_from_integridad(text):
    m = re.search(r'2\.\s*INTEGRIDAD\s+DEL\s+CONTRATO(.*?)(?=\n\s*\d+\.)', text, re.IGNORECASE | re.DOTALL)
    if not m:
        m = re.search(r'INTEGRIDAD\s+DEL\s+CONTRATO(.*?)(?=\n{2,}|\n\s*\d+\.)', text, re.IGNORECASE | re.DOTALL)
    if not m:
        return []

    bloque = m.group(1)
    raw = re.findall(r'Anexo\s*[“"\'\s]*([A-Z0-9\-]+)[”"\'\s]*', bloque, re.IGNORECASE)
    anexos = []
    for a in raw:
        a_clean = a.strip().upper()
        if a_clean:
            anexos.append(f"Anexo {a_clean}")

    seen = set()
    result = []
    for x in anexos:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result

def extract_contract_data(raw_text):
    if not raw_text:
        return {
            "contrato": "",
            "contratista": "",
            "objeto": "",
            "monto": "",
            "plazo": "",
            "anexos": [],
            "area": AREA_FIJA
        }

    text = _clean_whitespace(raw_text)

    contrato, contratista = _extract_contrato_and_contratista(text)
    objeto = _extract_objeto(text)
    monto = _extract_monto(text)
    plazo = _extract_plazo(text)
    anexos = _extract_anexos_from_integridad(text)

    if anexos:
        known = load_known_anexos()
        changed = False
        for an in anexos:
            label = an.replace("Anexo ", "").strip()
            if label and label not in known:
                known.append(label)
                changed = True
        if changed:
            save_known_anexos(known)

    return {
        "contrato": contrato,
        "contratista": contratista,
        "objeto": objeto,
        "monto": monto,
        "plazo": plazo,
        "anexos": anexos,
        "area": AREA_FIJA
    }

if __name__ == "__main__":
    sample = Path("ejemplo_ocr.txt")
    if sample.exists():
        txt = sample.read_text(encoding="utf-8")
        import pprint
        pprint.pprint(extract_contract_data(txt))
    else:
        print("Coloca 'ejemplo_ocr.txt' con texto de prueba en la raíz para probar.")
