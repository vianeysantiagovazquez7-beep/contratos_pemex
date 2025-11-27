# pages/1_PROCESAMIENTO.py
import streamlit as st
from pathlib import Path
import base64
import re
import io
import os
from core.database import get_db_manager
from core.config import UPLOAD_DIR, TEMPLATE_PATH, timestamp
from core.ocr_utils import pdf_to_text
from core.text_processing import extract_contract_data
from core.excel_utils import load_excel

# === VERIFICAR SESIÓN ===
if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.error("Acceso denegado. Inicie sesión primero.")
    st.switch_page("INICIO.py")

# === CONFIGURACIÓN DE RUTAS ===
assets_dir = Path(__file__).parent.parent / "assets"
fondo_path = assets_dir / "fondo.jpg"
logo_path = assets_dir / "logo.jpg"

def get_base64_image(path: Path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

fondo_base64 = get_base64_image(fondo_path)
logo_base64 = get_base64_image(logo_path)

# === INICIALIZAR ESTADO ===
if 'datos_contrato' not in st.session_state:
    st.session_state.update({
        'datos_contrato': {},
        'texto_extraido': "",
        'anexos_detectados': [],
        'excel_generado': None,
        'excel_filename': ""
    })

# === FUNCIONES ===
def detectar_anexos_robusta(texto):
    texto_upper = texto.upper()
    anexos_detectados = []
    
    patron_principal = r'ANEXO\s+[“”"\'´`]+\s*([A-Z0-9\-]+)\s*[“”"\'´`]+'
    
    matches_principal = re.findall(patron_principal, texto_upper)
    for match in matches_principal:
        anexo = match.strip()
        if anexo and anexo not in anexos_detectados:
            anexos_detectados.append(anexo)
    
    return sorted(list(set(anexos_detectados)))

def preparar_archivos_para_bd(uploaded_file):
    return {'principal': uploaded_file}

def guardar_contrato_bd(archivos_data, datos_contrato):
    try:
        manager = get_db_manager()
        if not manager:
            st.error("❌ Error de conexión")
            return False
        
        contrato_id = manager.guardar_contrato_completo(archivos_data, datos_contrato)
        
        if contrato_id:
            st.success("✅ Contrato guardado exitosamente")
            return True
        else:
            st.error("❌ No se pudo guardar el contrato")
            return False
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False

def generar_excel_contrato():
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

        sh["B6"] = d.get("area", "")
        sh["B7"] = d.get("contratista", "")
        sh["K7"] = d.get("contrato", "")
        sh["B8"] = f"DESCRIPCIÓN DEL CONTRATO: {d.get('objeto', '')}"
        sh["C13"] = d.get("monto", "")
        sh["F13"] = d.get("plazo", "")

        anexos = d.get("anexos", [])
        for idx, anexo in enumerate(anexos):
            if idx < 31:
                sh[f"B{29+idx}"] = f"ANEXO \"{anexo}\""

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        st.session_state["excel_generado"] = buffer.getvalue()
        st.session_state["excel_filename"] = f"CEDULA_CONTRATO_{timestamp()}.xlsx"
        
        return True
    except Exception as e:
        st.error(f"❌ Error al generar Excel: {e}")
        return False

# ==============================
#  ESTILOS MEJORADOS
# ==============================
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

.main-container {{
    background: rgba(255,255,255,0.95);
    border: 3px solid #d4af37;
    border-radius: 20px;
    box-shadow: 0 18px 45px rgba(0,0,0,0.22);
    padding: 30px 40px;
    width: 100%;
    max-width: 1200px;
    margin: 30px auto;
}}

/* Estilos para elementos internos del formulario */
div[data-testid="stForm"] {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 15px;
    padding: 20px 25px;
    margin: 20px 0;
}}

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

.contrato-header {{
    background: linear-gradient(135deg, #6b0012, #40000a);
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    margin: 20px 0 10px 0;
    text-align: center;
    font-weight: bold;
    font-size: 1.2em;
}}

.archivo-item {{
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    transition: all 0.3s ease;
}}

.archivo-item:hover {{
    background: #e9ecef;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}

.eliminar-btn {{
    background-color: #dc3545 !important;
    color: white !important;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 0.9em;
    width: 100%;
    margin-top: 10px;
}}

.eliminar-btn:hover {{
    background-color: #c82333 !important;
}}

.subir-btn {{
    background-color: #28a745 !important;
    color: white !important;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    width: 100%;
}}

.carpeta-cerrada {{
    background: linear-gradient(135deg, #d4af37, #b38e2f);
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    margin: 10px 0;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid #b38e2f;
}}

.carpeta-cerrada:hover {{
    background: linear-gradient(135deg, #b38e2f, #d4af37);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}

.carpeta-abierta {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}

.seccion-archivos {{
    background: rgba(248,249,250,0.8);
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}}

.boton-descarga {{
    background-color: #17a2b8 !important;
    color: white !important;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 0.9em;
    width: 100%;
    margin: 5px 0;
}}

.boton-descarga:hover {{
    background-color: #138496 !important;
}}

.archivo-info {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}}

.archivo-acciones {{
    display: flex;
    gap: 10px;
    margin-top: 10px;
}}

.confirmacion-eliminar {{
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}}

.accion-rapida {{
    display: flex;
    gap: 10px;
    margin-top: 10px;
}}

.usuario-info {{
    background: linear-gradient(135deg, #d4af37, #b38e2f);
    color: white;
    padding: 12px 20px;
    border-radius: 10px;
    margin: 15px 0;
    text-align: center;
    font-weight: bold;
    font-size: 1.1em;
}}

.procesamiento-section {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
}}

.anexos-section {{
    background: rgba(248,249,250,0.9);
    border: 2px solid #17a2b8;
    border-radius: 10px;
    padding: 15px;
    margin: 15px 0;
}}

.ocr-container {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #6f42c1;
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
}}

.acciones-section {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
}}

.excel-section {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #28a745;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
}}
</style>
""", unsafe_allow_html=True)

# === BARRA LATERAL ===
with st.sidebar:
    st.header("📊 Sistema")
    try:
        manager = get_db_manager()
        if manager:
            stats = manager.obtener_estadisticas_pemex()
            st.success("✅ Sistema conectado")
            st.info(f"📋 Contratos: {stats['total_contratos']}")
        else:
            st.error("❌ Error de conexión")
    except Exception:
        st.error("❌ Error de conexión")
    
    st.markdown("---")
    st.header("👤 Usuario")
    st.info(f"**Nombre:** {st.session_state.nombre}")

# ==================================================
#  INTERFAZ PRINCIPAL - MEJORADA
# ==================================================
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# Logo y título
if logo_base64:
    st.markdown(
        f"<div style='text-align:center; margin-bottom: 20px;'><img src='data:image/jpeg;base64,{logo_base64}' width='180'></div>",
        unsafe_allow_html=True
    )

st.markdown("<h1 style='text-align:center; color: #6b0012; margin-bottom: 10px;'>PROCESAMIENTO DE CONTRATOS PEMEX</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color: #666; margin-bottom: 30px;'>Sistema de carga, procesamiento y gestión de contratos</p>", unsafe_allow_html=True)

# Información del usuario
st.markdown(f"<div class='usuario-info'>👤 Usuario: {st.session_state.nombre}</div>", unsafe_allow_html=True)

# ==================================================
#  FORMULARIO DE PROCESAMIENTO
# ==================================================
st.markdown("<div class='procesamiento-section'>", unsafe_allow_html=True)
st.markdown("### 📤 Carga y Procesamiento de Contratos")

with st.form("form_contratos"):
    st.markdown("#### 📄 Subir Contrato PDF")
    uploaded_file = st.file_uploader("Selecciona el archivo PDF del contrato:", type=["pdf"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("#### 📋 Información del Contrato")
    
    datos = st.session_state.get("datos_contrato", {})
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        area = st.text_input("Área:", datos.get("area",""), placeholder="Ej: Administración, Operaciones...")
        contrato = st.text_input("Número de contrato:", datos.get("contrato",""), placeholder="Ej: 12345, PEMEX-2024...")
        contratista = st.text_input("Contratista:", datos.get("contratista",""), placeholder="Nombre del contratista...")

    with col2:
        monto = st.text_input("Monto del contrato:", datos.get("monto",""), placeholder="Ej: $1,000,000.00")
        plazo = st.text_input("Plazo (días):", datos.get("plazo",""), placeholder="Ej: 30, 60, 90...")
        objeto = st.text_area("Descripción del contrato:", datos.get("objeto",""), height=100, placeholder="Descripción detallada del objeto del contrato...")

    # Guardar datos editados
    datos_editados = {
        "area": area, "contrato": contrato, "contratista": contratista,
        "monto": monto, "plazo": plazo, "objeto": objeto, "anexos": st.session_state.get("anexos_detectados", [])
    }
    st.session_state["datos_contrato"] = datos_editados

    # ==================================================
    #  ACCIONES DEL FORMULARIO
    # ==================================================
    st.markdown("<div class='acciones-section'>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Acciones de Procesamiento")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        procesar = st.form_submit_button("🚀 Procesar PDF", use_container_width=True)
    with col2:
        guardar = st.form_submit_button("💾 Guardar Contrato", use_container_width=True)
    with col3:
        generar_excel_btn = st.form_submit_button("📊 Generar Excel", use_container_width=True)
    with col4:
        revisar_ocr = st.form_submit_button("🔍 Ver Texto OCR", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # PROCESAMIENTO
    if procesar:
        if not uploaded_file:
            st.warning("⚠️ Sube un archivo PDF antes de procesar.")
        else:
            with st.spinner("Procesando PDF con OCR..."):
                temp_path = UPLOAD_DIR / uploaded_file.name
                temp_path.parent.mkdir(exist_ok=True)
                temp_path.write_bytes(uploaded_file.getbuffer())

                texto = pdf_to_text(temp_path)
                st.session_state["texto_extraido"] = texto

                if texto.startswith("[ERROR]"):
                    st.error(f"❌ Error en OCR: {texto}")
                else:
                    datos_extraidos = extract_contract_data(texto) or {}
                    
                    # Extracción de plazo
                    plazo_match = re.search(r"(\d{1,4})\s*d[ií]as", texto, re.IGNORECASE)
                    datos_extraidos["plazo"] = plazo_match.group(1) if plazo_match else ""
                    
                    # Detección de anexos
                    anexos_detectados = detectar_anexos_robusta(texto)
                    st.session_state["anexos_detectados"] = anexos_detectados
                    datos_extraidos["anexos"] = anexos_detectados

                    st.session_state["datos_contrato"] = datos_extraidos
                    st.success("✅ Procesamiento completado exitosamente")
                    st.rerun()

    # GUARDAR EN BASE DE DATOS
    if guardar:
        if not st.session_state.get("datos_contrato"):
            st.warning("⚠️ No hay datos para guardar.")
        else:
            d = st.session_state["datos_contrato"]
            
            with st.spinner("Guardando contrato en la base de datos..."):
                archivos_data = preparar_archivos_para_bd(uploaded_file)
                exito_bd = guardar_contrato_bd(archivos_data, d)
                
                if exito_bd:
                    st.balloons()
                    st.success("🎉 ¡Contrato guardado exitosamente en el sistema!")

    # GENERAR EXCEL
    if generar_excel_btn:
        if generar_excel_contrato():
            st.success("✅ Archivo Excel generado exitosamente!")

    # REVISAR OCR
    if revisar_ocr:
        texto = st.session_state.get("texto_extraido","")
        if not texto:
            st.info("ℹ️ No hay texto OCR disponible. Procesa un contrato primero.")
        else:
            st.markdown("<div class='ocr-container'>", unsafe_allow_html=True)
            st.markdown("#### 🔍 Texto Extraído por OCR")
            texto_preview = texto[:5000] + ("..." if len(texto) > 5000 else "")
            st.text_area("Texto OCR (primeras 5000 caracteres)", texto_preview, height=200, key="ocr_text_area")
            st.info(f"📄 **Total de caracteres extraídos:** {len(texto)}")
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # Cierre de procesamiento-section

# ==================================================
#  ANEXOS DETECTADOS
# ==================================================
anexos_detectados = st.session_state.get("anexos_detectados", [])
if anexos_detectados:
    st.markdown("<div class='anexos-section'>", unsafe_allow_html=True)
    st.markdown("#### 📋 Anexos Detectados Automáticamente")
    st.success(f"✅ **{len(anexos_detectados)} anexos identificados en el documento:**")
    
    for anexo in anexos_detectados:
        st.markdown(f"<div class='anexo-item'>📄 ANEXO \"{anexo}\"</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ==================================================
#  DESCARGA DE EXCEL
# ==================================================
if st.session_state.get("excel_generado"):
    st.markdown("<div class='excel-section'>", unsafe_allow_html=True)
    st.markdown("#### 📊 Cédula Libro Blanco Generada")
    st.success("✅ **Archivo Excel generado exitosamente**")
    
    st.download_button(
        label="📥 DESCARGAR ARCHIVO EXCEL",
        data=st.session_state["excel_generado"],
        file_name=st.session_state["excel_filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ==================================================
#  PIE DE PÁGINA
# ==================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Sistema de Procesamiento de Contratos PEMEX</strong><br>
        • Carga y procesamiento de contratos • Detección automática de anexos • Generación de cédulas Excel • Almacenamiento seguro
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)  # Cierre del main-container
