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

# === ESTILOS ===
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
}}
[data-testid="stSidebar"] * {{ color:white !important; }}
.main-container {{
    background: rgba(255,255,255,0.95);
    border-radius: 15px;
    padding: 25px;
    margin: 20px auto;
}}
.stButton button {{
    background-color: #d4af37;
    color: black;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    height: 44px;
}}
.stButton button:hover {{
    background-color: #b38e2f;
    color: white;
}}
.ocr-container {{
    background: rgba(248,249,250,0.95);
    border: 2px solid #dee2e6;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
}}
.usuario-info {{
    background: linear-gradient(135deg, #d4af37, #b38e2f);
    color: white;
    padding: 10px 15px;
    border-radius: 8px;
    margin: 10px 0;
    text-align: center;
    font-weight: bold;
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

# === INTERFAZ PRINCIPAL ===
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

if logo_base64:
    st.markdown(f'<div style="text-align:center"><img src="data:image/jpeg;base64,{logo_base64}" width="150"></div>', unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center'>PROCESAMIENTO DE CONTRATOS</h2>", unsafe_allow_html=True)
st.markdown(f"<div class='usuario-info'>👤 Usuario: {st.session_state.nombre}</div>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center'>📘 CÉDULA LIBRO BLANCO</h4>", unsafe_allow_html=True)

with st.form("form_contratos"):
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
        objeto = st.text_area("Descripción del contrato:", datos.get("objeto",""), height=100)

    # ANEXOS
    anexos_detectados = st.session_state.get("anexos_detectados", [])
    if anexos_detectados:
        st.markdown("---")
        st.success(f"✅ **{len(anexos_detectados)} ANEXOS IDENTIFICADOS:**")
        for anexo in anexos_detectados:
            st.write(f"📄 ANEXO \"{anexo}\"")

    datos_editados = {
        "area": area, "contrato": contrato, "contratista": contratista,
        "monto": monto, "plazo": plazo, "objeto": objeto, "anexos": anexos_detectados
    }
    st.session_state["datos_contrato"] = datos_editados

    st.markdown("---")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        procesar = st.form_submit_button("🚀 Procesar", use_container_width=True)
    with b2:
        guardar = st.form_submit_button("💾 Guardar", use_container_width=True)
    with b3:
        generar_excel_btn = st.form_submit_button("📊 Excel", use_container_width=True)
    with b4:
        revisar_ocr = st.form_submit_button("🔍 Ver OCR", use_container_width=True)

    # PROCESAMIENTO
    if procesar:
        if not uploaded_file:
            st.warning("⚠️ Sube un PDF antes de procesar.")
        else:
            with st.spinner("Procesando PDF..."):
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
                    st.success("✅ Procesamiento completado")
                    st.rerun()

    # GUARDAR EN BASE DE DATOS
    if guardar:
        if not st.session_state.get("datos_contrato"):
            st.warning("⚠️ No hay datos para guardar.")
        else:
            d = st.session_state["datos_contrato"]
            
            with st.spinner("Guardando contrato..."):
                archivos_data = preparar_archivos_para_bd(uploaded_file)
                exito_bd = guardar_contrato_bd(archivos_data, d)
                
                if exito_bd:
                    st.balloons()
                    st.success("🎉 ¡Contrato guardado exitosamente!")

    # GENERAR EXCEL
    if generar_excel_btn:
        if generar_excel_contrato():
            st.success("✅ Excel generado exitosamente!")

    # REVISAR OCR
    if revisar_ocr:
        texto = st.session_state.get("texto_extraido","")
        if not texto:
            st.info("ℹ️ No hay OCR disponible. Procesa un contrato primero.")
        else:
            st.markdown("---")
            st.markdown("<div class='ocr-container'>", unsafe_allow_html=True)
            st.subheader("🔍 Texto Extraído por OCR")
            texto_preview = texto[:5000] + ("..." if len(texto) > 5000 else "")
            st.text_area("Texto OCR (primeras 5000 caracteres)", texto_preview, height=200, key="ocr_text_area")
            st.info(f"📄 Total de caracteres: {len(texto)}")
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# SECCIÓN DE DESCARGA FUERA DEL FORM
if st.session_state.get("excel_generado"):
    st.markdown("---")
    st.success("📊 **EXCEL GENERADO EXITOSAMENTE**")
    
    st.download_button(
        label="📥 DESCARGAR ARCHIVO EXCEL",
        data=st.session_state["excel_generado"],
        file_name=st.session_state["excel_filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    