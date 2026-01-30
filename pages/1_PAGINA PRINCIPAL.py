import streamlit as st
from pathlib import Path
import base64
import re
import io
import os
import json
import warnings

from core.database import get_db_manager_por_usuario
from core.config import UPLOAD_DIR, TEMPLATE_PATH, timestamp
from core.ocr_utils import pdf_to_text
from core.text_processing import extract_contract_data
from core.excel_utils import load_excel
from hashlib import sha256
from core.config import OUTPUT_DIR
from pathlib import Path
OUTPUT_DIR = Path("output")
from core.excel_utils import save_excel, load_excel
# CORRECCIÓN: Solo importar las funciones que existen
from core.tutorial import init, header_button, overlay

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.reader.drawings")

# --- Configuración de rutas ---
BASE_DIR = Path("data")
ASSETS_DIR = Path(__file__).parent.parent / "assets"
FONDO = ASSETS_DIR / "fondo.jpg"
LOGO = ASSETS_DIR / "logo.jpg"

def get_base64_image(path: Path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

fondo_base64 = get_base64_image(FONDO)
logo_base64 = get_base64_image(LOGO)


# === Página en modo wide ===
st.set_page_config(layout="wide")
init()
header_button()
overlay("principal")
# === SESSION STATE ===
for key, default in {
    "autenticado": False,
    "usuario": "",
    "nombre": "",
    "datos_contrato": {},
    "ultimo_pdf_temp": "",
    "ultimo_guardado": "",
    "texto_extraido": "",
    "anexos_detectados": [],
    "procesamiento_completado": False,
    "excel_generado": None,
    "excel_filename": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# === CARGAR USUARIOS ===
def cargar_usuarios():
    ruta = Path("usuarios.json")
    if not ruta.exists():
        st.error("No se encontró el archivo usuarios.json")
        st.stop()
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    usuarios = {}
    for u in data:
        usuario = u.get("usuario", "").strip().upper()
        password_raw = u.get("password", "") or ""
        password_hash = sha256(password_raw.encode()).hexdigest()
        usuarios[usuario] = {
            "password_hash": password_hash,
            "nombre": u.get("nombre", "").strip().upper()
        }
    return usuarios

USERS = cargar_usuarios()

# === AUTENTICACIÓN ===
def autenticar(usuario: str, password: str):
    if not usuario:
        return False, None
    user_data = USERS.get(usuario.strip().upper())
    if not user_data:
        return False, None
    hashed = sha256(password.encode()).hexdigest()
    if user_data["password_hash"] == hashed:
        return True, user_data["nombre"]
    return False, None

# === DETECCIÓN MEJORADA DE ANEXOS ===
def detectar_anexos_robusta(texto):
    """
    Detección robusta de anexos que captura específicamente los códigos entre comillas
    y evita falsos positivos como 'ANEXO' o palabras incompletas
    """
    # Convertir a mayúsculas para consistencia
    texto_upper = texto.upper()
    
    anexos_detectados = []
    
    # Patrón principal: busca "Anexo" seguido de comillas y contenido entre ellas
    patron_principal = r'ANEXO\s+[""\'´]+\s*([A-Z0-9\-]+)\s*[""\'´]+'
    
    # Patrón secundario: para casos sin comillas pero con formato claro
    patron_secundario = r'ANEXO\s+([A-Z]{1,3}(?:-[A-Z0-9]{1,3})?)(?:\s|\.|\,|\:|$)'
    
    # Patrón para anexos conocidos específicos
    anexos_conocidos = ["A", "AP", "B", "B-1", "BDE", "C", "CN", "DT-9", "E", "F", 
                       "FORMA", "GARANTÍAS", "GNR", "I", "II", "IV", "MMRDD", "O", 
                       "PACMA", "PUE", "SSPA"]
    
    # Buscar con patrón principal (comillas)
    matches_principal = re.findall(patron_principal, texto_upper)
    for match in matches_principal:
        anexo = match.strip()
        if anexo and anexo not in anexos_detectados:
            anexos_detectados.append(anexo)
    
    # Buscar con patrón secundario (sin comillas pero formato claro)
    matches_secundario = re.findall(patron_secundario, texto_upper)
    for match in matches_secundario:
        anexo = match.strip()
        # Validar que sea un anexo válido (esté en la lista de conocidos o tenga formato válido)
        if (anexo in anexos_conocidos or 
            re.match(r'^[A-Z]{1,3}(?:-[A-Z0-9]{1,3})?$', anexo)) and \
           anexo not in anexos_detectados:
            anexos_detectados.append(anexo)
    
    # Buscar específicamente anexos conocidos que puedan aparecer sin formato estándar
    for anexo_conocido in anexos_conocidos:
        # Patrón que busca el anexo conocido con contexto de "ANEXO"
        patron_especifico = rf'ANEXO\s+(?:[""\'´]*\s*)?{re.escape(anexo_conocido)}(?:\s*[""\'´])?(?:\s|\.|\,|\:|$)'
        if re.search(patron_especifico, texto_upper) and anexo_conocido not in anexos_detectados:
            anexos_detectados.append(anexo_conocido)
    
    # Eliminar posibles duplicados y ordenar
    anexos_detectados = sorted(list(set(anexos_detectados)))
    
    return anexos_detectados

# === FUNCIONES PARA POSTGRESQL ===
def preparar_archivos_para_postgresql(uploaded_file, datos_contrato, excel_generado=None, excel_filename=None):
    """
    Prepara todos los archivos del contrato para PostgreSQL
    """
    archivos_data = {
        'principal': None,
        'anexos': [],
        'cedulas': [],
        'soportes': []
    }
    
    try:
        # 1. Archivo principal (PDF del contrato)
        if uploaded_file:
            archivos_data['principal'] = uploaded_file
        
        # 2. Cédulas (Excel generado)
        if excel_generado and excel_filename:
            # Crear objeto similar a UploadedFile desde los bytes del Excel
            archivo_cedula = io.BytesIO(excel_generado)
            archivo_cedula.name = excel_filename
            archivos_data['cedulas'].append(archivo_cedula)
        
        # 3. Anexos detectados (crear archivos virtuales para los anexos detectados)
        anexos_detectados = datos_contrato.get('anexos', [])
        for anexo in anexos_detectados:
            # Crear un archivo virtual con la información del anexo
            anexo_info = f"ANEXO {anexo} - Detectado automáticamente del contrato"
            archivo_anexo = io.BytesIO(anexo_info.encode('utf-8'))
            archivo_anexo.name = f"ANEXO_{anexo}.txt"
            archivos_data['anexos'].append(archivo_anexo)
        
        # 4. Soporte físico (el PDF original)
        if uploaded_file:
            archivos_data['soportes'].append(uploaded_file)
        
        return archivos_data
        
    except Exception as e:
        st.error(f"❌ Error preparando archivos para PostgreSQL: {str(e)}")
        return None

def guardar_contrato_postgresql(archivos_data, datos_contrato, usuario):
    """
    Guarda el contrato automáticamente en PostgreSQL
    """
    try:
        # Obtener manager específico para el usuario ← CAMBIADO
        usuario = st.session_state.get("usuario", "").upper()
        manager = get_db_manager_por_usuario(usuario)  # ← CAMBIADO
        
        if not manager:
            st.warning("⚠️ No se pudo conectar a la base de datos")
            return False
        
        # Preparar datos para PostgreSQL
        datos_postgresql = {
            'contrato': datos_contrato.get('contrato', ''),
            'contratista': datos_contrato.get('contratista', ''),
            'monto': datos_contrato.get('monto', ''),
            'plazo': datos_contrato.get('plazo', ''),
            'objeto': datos_contrato.get('objeto', ''),
            'anexos': datos_contrato.get('anexos', []),
            'area': datos_contrato.get('area', 'SUBDIRECCIÓN DE PRODUCCIÓN REGIÓN NORTE GERENCIA DE MANTENIMIENTO CONFIABILIDAD Y CONSTRUCCIÓN')
        }
        
        # Guardar en PostgreSQL
        contrato_id = manager.guardar_contrato_completo(archivos_data, datos_postgresql, usuario)
        
        if contrato_id:
            st.success(f"✅ *Contrato guardado exitosamente en PostgreSQL* (ID: {contrato_id})")
            return True
        else:
            st.warning("⚠️ No se pudo guardar en la base de datos")
            return False
            
    except Exception as e:
        st.error(f"❌ Error guardando en PostgreSQL: {str(e)}")
        return False

# === FUNCIÓN PARA GENERAR EXCEL ===
def generar_excel_contrato():
    """Genera el archivo Excel y lo prepara para descarga"""
    d = st.session_state.get("datos_contrato")
    if not d:
        st.warning("⚠️ No hay datos para generar Excel.")
        return False
    
    if not TEMPLATE_PATH.exists():
        st.error("❌ No se encontró la plantilla Excel.")
        return False
    
    try:
        wb = load_excel(TEMPLATE_PATH)
        sh = wb.active

        # Mapeo de datos al Excel
        sh["B6"] = d.get("area", "")
        sh["B7"] = d.get("contratista", "")
        sh["K7"] = d.get("contrato", "")
        sh["B8"] = f"DESCRIPCIÓN DEL CONTRATO: {d.get('objeto', '')}"
        sh["C13"] = d.get("monto", "")
        sh["F13"] = d.get("plazo", "")

        # Inserción de anexos en celdas B29 a B59
        anexos = d.get("anexos", [])
        for idx, anexo in enumerate(anexos):
            if idx < 31:  # B29 a B59 = 31 celdas
                sh[f"B{29+idx}"] = f'ANEXO "{anexo}"'

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUTPUT_DIR / f"CEDULA_LIBRO_BLANCO_{timestamp()}.xlsx"
        save_excel(wb, out)

        # Guardar el archivo en session state para descarga
        with open(out, "rb") as f:
            st.session_state["excel_generado"] = f.read()
        st.session_state["excel_filename"] = out.name
        
        return True
    except Exception as e:
        st.error(f"❌ Error al generar Excel: {e}")
        return False

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/jpeg;base64,{fondo_base64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #6b0012 0%, #40000a 100%);
    color: white;
}}
[data-testid="stSidebar"] * {{ color:white !important; }}

div[data-testid="stForm"] {{
    background: rgba(255,255,255,0.90);
    border: 3px solid #d4af37;
    border-radius: 20px;
    box-shadow: 0 18px 45px rgba(0,0,0,0.22);
    padding: 26px 36px;
    width: 100%;
    max-width: 1066px;
    margin: 40px auto;
}}

/* Estilos para elementos internos del formulario */
div[data-testid="stForm"] label {{
    color: #2c2c2c !important;
    font-weight: 500;
}}

div[data-testid="stForm"] .stTextInput input,
div[data-testid="stForm"] .stNumberInput input,
div[data-testid="stForm"] .stTextArea textarea {{
    background: rgba(255,255,255,0.85);
    border: 2px solid #d4af37;
    border-radius: 8px;
    color: #2c2c2c;
}}

div[data-testid="stForm"] .stSelectbox div {{
    color: #2c2c2c !important;
}}

div.stButton > button:first-child {{
    background-color: #d4af37;
    color: black;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    height: 44px;
}}
div.stButton > button:first-child:hover {{
    background-color: #b38e2f;
    color: white;
}}

/* Estilos para las secciones de resultados */
.resultado-container {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
}}

.anexo-item {{
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 4px 0;
    font-family: monospace;
    font-weight: bold;
}}

.anexo-header {{
    background: linear-gradient(135deg, #d4af37, #b38e2f);
    color: white;
    padding: 10px 15px;
    border-radius: 8px;
    margin-bottom: 10px;
    text-align: center;
    font-weight: bold;
}}

.descarga-container {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #28a745;
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
    text-align: center;
}}
</style>
""", unsafe_allow_html=True)

# ==================================================
#  FORMULARIO PRINCIPAL (UN SOLO FORM)
# ==================================================
with st.form("form_contratos", clear_on_submit=False):

    if logo_base64:
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='200'></div>",
            unsafe_allow_html=True
        )

    st.markdown("<h2 style='text-align:center;'>SISTEMA DE PROCESAMIENTO DE CONTRATOS PEMEX</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>📘 CÉDULA LIBRO BLANCO</h4>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📤 Subir contrato PDF", type=["pdf"])

    datos = st.session_state.get("datos_contrato", {})

    col1, col2 = st.columns(2, gap="large")
    with col1:
        area = st.text_input("Área:", datos.get("area",""))
        contrato = st.text_input("Número de contrato:", datos.get("contrato",""))
        contratista = st.text_input("Contratista:", datos.get("contratista",""))

    with col2:
        monto = st.text_input("Monto del contrato:", datos.get("monto",""))
        plazo = st.text_input("Plazo (días):", datos.get("plazo",""))
        objeto = st.text_area("Descripción del contrato:", datos.get("objeto",""), height=130)

    # Sección de anexos detectados
    st.markdown("---")
    st.markdown("<div class='anexo-header'>📎 ANEXOS DETECTADOS</div>", unsafe_allow_html=True)
    
    anexos_detectados = st.session_state.get("anexos_detectados", [])
    if anexos_detectados:
        st.markdown("<div class='resultado-container'>", unsafe_allow_html=True)
        st.success(f"✅ *{len(anexos_detectados)} ANEXOS IDENTIFICADOS:*")
        
        # Mostrar anexos en formato de lista ordenada
        for i, anexo in enumerate(anexos_detectados, 1):
            st.markdown(f"<div class='anexo-item'>📄 ANEXO \"{anexo}\"</div>", unsafe_allow_html=True)
        
        st.info(f"*Nota:* Los anexos se insertarán automáticamente en las celdas B29-B59 del Excel")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ *No se han detectado anexos.* Procesa un contrato para identificar anexos automáticamente.")

    datos_editados = {
        "area": area,
        "contrato": contrato,
        "contratista": contratista,
        "monto": monto,
        "plazo": plazo,
        "objeto": objeto,
        "anexos": anexos_detectados
    }

    st.session_state["datos_contrato"] = datos_editados

    st.markdown("---")

    # Botones de acción
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        procesar = st.form_submit_button("🚀 Procesar contrato", use_container_width=True)
    with b2:
        guardar = st.form_submit_button("💾 Guardar contrato", use_container_width=True)
    with b3:
        generar_excel_btn = st.form_submit_button("📊 Generar Excel", use_container_width=True)
    with b4:
        revisar_ocr = st.form_submit_button("🔍 Revisar OCR", use_container_width=True)

    # ========= PROCESAMIENTO DENTRO DEL FORM =========
    if procesar:
        if not uploaded_file:
            st.warning("⚠️ Sube un PDF antes de procesar.")
        else:
            with st.spinner("🔄 Procesando OCR y extrayendo datos..."):
                temp_path = Path(UPLOAD_DIR) / uploaded_file.name
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                texto = pdf_to_text(temp_path)
                st.session_state["texto_extraido"] = texto

                if texto.startswith("[ERROR]"):
                    st.error(f"❌ Error en OCR: {texto}")
                else:
                    datos_extraidos = extract_contract_data(texto) or {}

                    # Limpieza de campos no requeridos
                    datos_extraidos.pop("partida", None)
                    datos_extraidos.pop("observaciones", None)

                    # Extracción mejorada de plazo
                    plazo_regex = re.search(
                        r"(?:plazo del contrato|plazo(?:\s+total)?|tendrá un plazo|plazo es de)\s*(?:de\s*)?(\d{1,4})\s*(?:d[ií]as?)",
                        texto,
                        flags=re.IGNORECASE
                    )
                    if plazo_regex:
                        datos_extraidos["plazo"] = plazo_regex.group(1)
                    else:
                        plazo_alt = re.search(r"(\d{1,4})\s*d[ií]as", texto, flags=re.IGNORECASE)
                        datos_extraidos["plazo"] = plazo_alt.group(1) if plazo_alt else ""

                    # Detección ROBUSTA de anexos
                    anexos_detectados = detectar_anexos_robusta(texto)
                    st.session_state["anexos_detectados"] = anexos_detectados
                    datos_extraidos["anexos"] = anexos_detectados

                    st.session_state["datos_contrato"] = datos_extraidos
                    st.session_state["procesamiento_completado"] = True
                    
                    st.success("✅ Procesamiento completado exitosamente!")
                    st.rerun()

    # ========= GUARDAR DENTRO DEL FORM =========
    if guardar:
        if not st.session_state.get("datos_contrato"):
            st.warning("⚠️ No hay datos para guardar.")
        else:
            d = st.session_state["datos_contrato"]
            owner = st.session_state.get("nombre","ANONIMO")
            
            with st.spinner("🔄 Guardando en PostgreSQL..."):
                # Preparar archivos para PostgreSQL
                archivos_data = preparar_archivos_para_postgresql(
                    uploaded_file, 
                    d, 
                    st.session_state.get("excel_generado"),
                    st.session_state.get("excel_filename")
                )
                
                if archivos_data:
                    exito_postgresql = guardar_contrato_postgresql(archivos_data, d, owner)
                    
                    if exito_postgresql:
                        st.success("🎉 *¡CONTRATO GUARDADO EXITOSAMENTE EN POSTGRESQL!*")
                        st.info("🗄️ *PostgreSQL:* Disponible en la base de datos centralizada")
                        # CORRECCIÓN: Eliminado el código que usaba funciones no existentes
                        # if is_active() and step() == 5:
                        #     finish_and_open_survey()
                    else:
                        st.warning("⚠️ No se pudo guardar el contrato en la base de datos")
                else:
                    st.warning("⚠️ No se pudieron preparar los archivos para guardar")

    # ========= GENERAR EXCEL DENTRO DEL FORM =========
    if generar_excel_btn:
        if generar_excel_contrato():
            st.success("✅ Excel generado exitosamente! Revisa la sección de descarga abajo.")
            st.rerun()

    # ========= REVISAR OCR DENTRO DEL FORM =========
    if revisar_ocr:
        texto = st.session_state.get("texto_extraido","")
        if not texto:
            st.info("ℹ️ No hay OCR disponible. Procesa un contrato primero.")
        else:
            st.markdown("<div class='resultado-container'>", unsafe_allow_html=True)
            st.subheader("🔍 Texto Extraído por OCR")
            st.text_area(
                "Texto OCR completo", 
                texto[:50000] + ("...[texto truncado para visualización]" if len(texto)>50000 else ""), 
                height=300,
                key="ocr_text_area"
            )
            st.markdown("</div>", unsafe_allow_html=True)


#  SECCIÓN DE DESCARGA FUERA DEL FORM (por restricciones de Streamlit)

if st.session_state.get("excel_generado"):
    st.markdown("---")
    st.markdown("<div class='descarga-container'>", unsafe_allow_html=True)
    st.success("📊 *EXCEL GENERADO EXITOSAMENTE*")
    
    st.download
