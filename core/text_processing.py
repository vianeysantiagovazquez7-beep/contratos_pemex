# core/text_processing.py
import re
import json
from pathlib import Path

# Base inicial de anexos conocidos (almacenada en memoria)
BASE_ANEXOS = [
    "A", "B", "B-1", "C", "CN", "E", "F", "I", "SSPA", "PACMA",
    "AP", "MMRDD", "GNR", "PUE", "BDE", "GARANTÍAS", "FORMA", "DT-9",
    "II", "IV", "O"
]

# Área fija (según tu requerimiento)
AREA_FIJA = "SUBDIRECCIÓN DE PRODUCCIÓN REGIÓN NORTE GERENCIA DE MANTENIMIENTO CONFIABILIDAD Y CONSTRUCCIÓN"

# Cache en memoria para anexos conocidos (sin archivos locales)
_ANEXOS_CONOCIDOS_CACHE = set(BASE_ANEXOS)

# ----------------- Helpers -----------------
def _clean_whitespace(text):
    """Limpia espacios en blanco y normaliza el texto"""
    if not text:
        return ""
    
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def _agregar_anexo_conocido(anexo):
    """Agrega un anexo a la cache en memoria (sin guardar en archivos)"""
    if anexo and anexo not in _ANEXOS_CONOCIDOS_CACHE:
        _ANEXOS_CONOCIDOS_CACHE.add(anexo.upper())
        return True
    return False

def obtener_anexos_conocidos():
    """Retorna la lista de anexos conocidos (desde memoria)"""
    return sorted(list(_ANEXOS_CONOCIDOS_CACHE))

# ----------------- Extracción específica -----------------
def _extract_contrato_and_contratista(text):
    """Extrae número de contrato y contratista del texto"""
    contrato = ""
    contratista = ""

    # Patrón para número de contrato PEMEX (64XXXXXXX)
    m = re.search(r'\b(64\d{6,7})\b', text)
    if m:
        contrato = m.group(1)

    # Patrón mejorado para contrato y contratista
    m = re.search(
        r'Contrato\s*(?:N(?:ú|u)mero|N\.|NO\.|N)\s*[:\-]?\s*(64\d{6,7}|\d{6,10})\s+([A-ZÁÉÍÓÚÑ0-9\.,\s&\-]{5,200}?)\s+(?:Hoja|Página|\bHoja\b|\bPágina\b|\bDE\b)',
        text,
        re.IGNORECASE
    )
    if m:
        if not contrato:
            contrato = m.group(1).strip()
        contratista = m.group(2).strip()

    # Búsqueda contextual si no se encontró contratista
    if not contratista and contrato:
        pattern = rf'.{{0,80}}{re.escape(contrato)}[^\n]*\n([^\n]{{5,200}})'
        m2 = re.search(pattern, text, re.IGNORECASE)
        if m2:
            candidate = m2.group(1).strip()
            if len(candidate) > 4:
                contratista = candidate.split('Hoja')[0].strip()

    # Búsqueda por campos específicos
    if not contratista:
        m3 = re.search(r'(?:PROVEEDOR|RAZ[ÓO]N\s+SOCIAL|CONTRATISTA)\s*[:\-]\s*([^\n]{5,200})', text, re.IGNORECASE)
        if m3:
            contratista = m3.group(1).strip()

    return contrato or "", contratista or ""

def _extract_objeto(text):
    """Extrae el objeto del contrato"""
    # Patrón 1: Buscar por numeración (4. OBJETO)
    m = re.search(r'(?:\n|^)\s*4\.\s*.*?OBJETO[^\n]*\n(.*?)(?=\n\s*(?:5\.|\d+\.)|\n\s*MONTO|\n\s*CL[AÁ]USULA|\n{2,})', text, re.IGNORECASE | re.DOTALL)
    if not m:
        # Patrón 2: Buscar por palabra clave OBJETO
        m = re.search(r'OBJETO(?:\s+DEL\s+CONTRATO)?[^\n]*[:\-]?\s*(.*?)(?=\n\s*\d+\.|\n{2,}|MONTO|PLAZO)', text, re.IGNORECASE | re.DOTALL)
    
    if m:
        objeto = m.group(1).strip()
        # Extraer texto entre comillas si existe
        q = re.search(r'[“"«]([^”"»]+)[”"»]', objeto)
        if q:
            return q.group(1).strip()
        # Limpiar espacios extra
        objeto = re.sub(r'\s+', ' ', objeto)
        return objeto.strip()
    return ""

def _extract_monto(text):
    """Extrae el monto del contrato"""
    # Patrón para formato $ XXX,XXX.XX
    m = re.search(r'\$\s*([\d{1,3}\.,]{1,}\d{0,2})(?:\s*M\.?N\.?)?', text, re.IGNORECASE)
    if m:
        val = m.group(1).strip()
        val = val.replace(' ', '')
        return f"${val}"
    
    # Patrón alternativo para montos en texto
    m2 = re.search(r'(?:MONTO|IMPORTE|VALOR)[^\d]*(\$?\s*[\d,]+\.?\d*)', text, re.IGNORECASE)
    if m2:
        return m2.group(1).strip()
    
    return ""

def _extract_plazo(text):
    """Extrae el plazo en días del contrato"""
    # Patrón 1: Buscar en sección 11. PLAZO
    m = re.search(r'11\.\s*PLAZO[^\n]*?(?:es\s+de\s+)?\s*(\d{1,4})\s*(?:D[IÍ]AS|DIAS)', text, re.IGNORECASE)
    if m:
        return m.group(1)
    
    # Patrón 2: Buscar cualquier mención de días
    m2 = re.search(r'(\d{1,4})\s*(?:D[IÍ]AS|DIAS)', text, re.IGNORECASE)
    if m2:
        return m2.group(1)
    
    # Patrón 3: Buscar en contexto de plazo
    m3 = re.search(r'plazo\s*(?:de\s+)?(\d{1,4})\s*(?:d[ií]a)', text, re.IGNORECASE)
    if m3:
        return m3.group(1)
    
    return ""

def _extract_anexos_avanzado(text):
    """Extrae anexos usando múltiples patrones avanzados"""
    anexos_detectados = set()
    
    # Convertir texto a mayúsculas para búsqueda consistente
    texto_upper = text.upper()
    
    # Patrón 1: Anexo entre comillas
    patron1 = r'ANEXO\s+[“”"\'´`]+\s*([A-Z0-9\-]+)\s*[“”"\'´`]+'
    matches1 = re.findall(patron1, texto_upper)
    for match in matches1:
        if match.strip():
            anexos_detectados.add(match.strip())
    
    # Patrón 2: Anexo con formato claro
    patron2 = r'ANEXO\s+([A-Z]{1,3}(?:-[A-Z0-9]{1,3})?)(?:\s|\.|\,|\:|$)'
    matches2 = re.findall(patron2, texto_upper)
    for match in matches2:
        anexo = match.strip()
        if anexo and (anexo in _ANEXOS_CONOCIDOS_CACHE or re.match(r'^[A-Z]{1,3}(?:-[A-Z0-9]{1,3})?$', anexo)):
            anexos_detectados.add(anexo)
    
    # Patrón 3: Buscar en sección de integridad del contrato
    patron_integridad = r'2\.\s*INTEGRIDAD\s+DEL\s+CONTRATO(.*?)(?=\n\s*\d+\.)'
    m_integridad = re.search(patron_integridad, texto_upper, re.IGNORECASE | re.DOTALL)
    if not m_integridad:
        patron_integridad_alt = r'INTEGRIDAD\s+DEL\s+CONTRATO(.*?)(?=\n{2,}|\n\s*\d+\.)'
        m_integridad = re.search(patron_integridad_alt, texto_upper, re.IGNORECASE | re.DOTALL)
    
    if m_integridad:
        bloque_integridad = m_integridad.group(1)
        anexos_integridad = re.findall(r'ANEXO\s*[“"\'\s]*([A-Z0-9\-]+)[”"\'\s]*', bloque_integridad, re.IGNORECASE)
        for anexo in anexos_integridad:
            if anexo.strip():
                anexos_detectados.add(anexo.strip().upper())
    
    # Buscar anexos conocidos específicamente
    for anexo_conocido in _ANEXOS_CONOCIDOS_CACHE:
        patron_especifico = rf'ANEXO\s+(?:[“]\"\'´`]*\s*)?{re.escape(anexo_conocido)}(?:\s*[“]\"\'´`])?(?:\s|\.|\,|\:|$)'
        if re.search(patron_especifico, texto_upper):
            anexos_detectados.add(anexo_conocido)
    
    return sorted(list(anexos_detectados))

def extract_contract_data(raw_text):
    """
    Función principal para extraer datos del contrato del texto OCR
    No usa archivos locales, todo en memoria
    """
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

    # Limpiar y normalizar texto
    text = _clean_whitespace(raw_text)

    # Extraer todos los campos
    contrato, contratista = _extract_contrato_and_contratista(text)
    objeto = _extract_objeto(text)
    monto = _extract_monto(text)
    plazo = _extract_plazo(text)
    anexos = _extract_anexos_avanzado(text)

    # Agregar nuevos anexos a la cache en memoria
    for anexo in anexos:
        _agregar_anexo_conocido(anexo)

    return {
        "contrato": contrato,
        "contratista": contratista,
        "objeto": objeto,
        "monto": monto,
        "plazo": plazo,
        "anexos": anexos,
        "area": AREA_FIJA
    }

# Función auxiliar para debugging
def debug_extraccion(texto):
    """Función para debugging de la extracción de datos"""
    resultado = extract_contract_data(texto)
    print("=== DEBUG EXTRACCIÓN ===")
    print(f"Contrato: {resultado['contrato']}")
    print(f"Contratista: {resultado['contratista']}")
    print(f"Objeto: {resultado['objeto'][:100]}...")
    print(f"Monto: {resultado['monto']}")
    print(f"Plazo: {resultado['plazo']}")
    print(f"Anexos: {resultado['anexos']}")
    print(f"Área: {resultado['area']}")
    print("========================")
    return resultado

if __name__ == "__main__":
    # Ejemplo de uso sin archivos locales
    texto_ejemplo = """
    CONTRATO NÚMERO 641234567
    EMPRESA CONSTRUCTORA XYZ S.A. DE C.V.
    
    4. OBJETO
    "OBRAS DE MANTENIMIENTO Y CONSTRUCCIÓN EN PLANTA"
    
    MONTO: $1,500,000.00 M.N.
    
    11. PLAZO
    El plazo es de 180 DÍAS para la ejecución total de los trabajos.
    
    2. INTEGRIDAD DEL CONTRATO
    Este contrato se integra por los Anexos "A", "B-1", "C" y "SSPA".
    """
    
    debug_extraccion(texto_ejemplo)
    print(f"Anexos conocidos en memoria: {obtener_anexos_conocidos()}")
    