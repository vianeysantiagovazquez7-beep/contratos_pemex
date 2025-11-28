# pages/2_CONSULTA.py
import streamlit as st
from pathlib import Path
import base64
from core.database import get_db_manager
import re
import io

# --- Configuración de rutas ---
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

# --- Verificar sesión ---
if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.error("Acceso denegado. Inicie sesión.")
    st.stop()

usuario = st.session_state.get("nombre", "").upper()

# ==============================
#  ESTILOS MEJORADOS - ALINEADOS CON LOGIN (CONTENEDOR 85% + SCROLL INTERNO)
# ==============================
st.markdown(f"""
<style>
/* === Fondo global como LOGIN === */
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

/* === CONTENEDOR PRINCIPAL ESTILO LOGIN (85%) === */
.contenedor-85 {{
    background: rgba(255, 255, 255, 0.85);
    border: 3px solid #d4af37;
    border-radius: 20px;
    box-shadow: 0 15px 40px rgba(0,0,0,0.25);
    backdrop-filter: blur(15px);
    padding: 60px 50px;

    width: 70%;
    max-width: 900px;
    margin: auto;

    height: 85vh;
    overflow-y: auto;
}}

/* === TODOS TUS ESTILOS INTERNOS QUEDAN IGUALES === */
div[data-testid="stForm"] {{
    background: rgba(255,255,255,0.85);
    border: 3px solid #d4af37;
    border-radius: 20px;
    padding: 20px 25px;
    width: 100%;
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
    width: 100%;
}}

div[data-testid="stForm"] .stSelectbox div {{
    color: #2c2c2c !important;
}}

div.stButton > button:first-child {{
    background-color: #d4af37;
    color: black;
    font-weight: 600;
    border-radius: 10px;
    border: none;
    height: 45px;
}}
div.stButton > button:first-child:hover {{
    background-color: #b38e2f;
    color: white;
}}
</style>
""", unsafe_allow_html=True)

# ==================================================
#  FUNCIONES AUXILIARES - MANTENIDAS
# ==================================================
def mostrar_contrato_completo(manager, contrato_id):
    """✅ FUNCIÓN MEJORADA: Mostrar contrato completo con descarga directa"""
    try:
        contratos = manager.buscar_contratos_pemex({})
        contrato_info = None
        for c in contratos:
            if c.get('id') == contrato_id:
                contrato_info = c
                break

        if not contrato_info:
            st.error("❌ Contrato no encontrado")
            return

        archivo_data = manager.obtener_contrato_por_id(contrato_id)

        if not archivo_data:
            st.error("❌ No se encontraron archivos para este contrato")
            return

        st.markdown("<div class='contrato-encontrado'>", unsafe_allow_html=True)
        st.markdown("### 📋 Información del Contrato")

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**• Número:** {contrato_info.get('numero_contrato', 'No especificado')}")
            st.write(f"**• Contratista:** {contrato_info.get('contratista', 'No especificado')}")
            st.write(f"**• Área:** {contrato_info.get('area', 'No especificado')}")
        with col2:
            st.write(f"**• Monto:** {contrato_info.get('monto_contrato', 'No especificado')}")
            st.write(f"**• Plazo:** {contrato_info.get('plazo_dias', 'No especificado')} días")
            tamaño_bytes = archivo_data.get('metadata', {}).get('tamaño_bytes', 0)
            st.write(f"**• Tamaño archivo:** {tamaño_bytes / 1024 / 1024:.2f} MB")
            st.write(f"**• Fecha de subida:** {contrato_info.get('fecha_subida', 'No especificada')}")

        st.markdown("---")
        st.markdown("### 📎 Archivo del Contrato")

        metadata = archivo_data.get('metadata', {})
        size_mb = metadata.get('tamaño_bytes', 0) / 1024 / 1024

        st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**📄 {metadata.get('nombre_archivo', 'Archivo') }**")
            st.markdown(f"**Tamaño:** {size_mb:.2f} MB")
        with col2:
            st.download_button(
                label="📥 Descargar PDF",
                data=archivo_data.get('contenido'),
                file_name=metadata.get('nombre_archivo', 'archivo.pdf'),
                mime="application/pdf",
                key=f"download_{contrato_id}",
                use_container_width=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

        anexos = contrato_info.get('anexos', [])
        if anexos:
            st.markdown("---")
            st.markdown("#### 📋 Anexos Detectados")
            for anexo in anexos:
                st.markdown(f"<div class='anexo-item'>📄 ANEXO \"{anexo}\"</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error mostrando contrato: {str(e)}")

def mostrar_estadisticas(manager):
    """Muestra estadísticas simplificadas del sistema"""
    try:
        stats = manager.obtener_estadisticas_pemex()

        st.markdown("<div class='estadisticas-container'>", unsafe_allow_html=True)
        st.markdown("### 📊 ESTADÍSTICAS DEL SISTEMA")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='estadistica-item'>", unsafe_allow_html=True)
            st.markdown(f"**📋 Total Contratos**")
            st.markdown(f"# {stats.get('total_contratos', 0)}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"<div class='estadistica-item'>", unsafe_allow_html=True)
            st.markdown(f"**👥 Cantidad de Contratistas**")
            st.markdown(f"# {stats.get('contratistas_unicos', 0)}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown(f"<div class='estadistica-item'>", unsafe_allow_html=True)
            st.markdown(f"**💾 Almacenamiento Total**")
            st.markdown(f"# {stats.get('total_bytes', 0) / (1024*1024):.2f} MB")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**📅 Contrato más antiguo:** {stats.get('fecha_mas_antigua', 'N/A')}")
        with col2:
            st.info(f"**📅 Contrato más reciente:** {stats.get('fecha_mas_reciente', 'N/A')}")

    except Exception as e:
        st.error(f"❌ Error obteniendo estadísticas: {str(e)}")

# ==================================================
#  INTERFAZ PRINCIPAL - MEJORADA (TODO DENTRO DEL RECUADRO 85% CON SCROLL INTERNO)
# ==================================================
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# Logo y título
if logo_base64:
    st.markdown(
        f"<div style='text-align:center; margin-bottom: 20px;'><img src='data:image/jpeg;base64,{logo_base64}' width='180'></div>",
        unsafe_allow_html=True
    )

st.markdown("<h1 style='text-align:center; color: #6b0012; margin-bottom: 10px;'>CONSULTA DE CONTRATOS PEMEX</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color: #666; margin-bottom: 30px;'>Sistema de búsqueda y consulta de contratos</p>", unsafe_allow_html=True)

# Información del usuario
st.markdown(f"<div class='usuario-info'>👤 Usuario: {usuario}</div>", unsafe_allow_html=True)

# --- Verificar conexión a la base de datos ---
manager = get_db_manager()
if not manager:
    st.error("❌ No se pudo conectar a la base de datos")
    st.stop()

# --- Mostrar estadísticas ---
mostrar_estadisticas(manager)

# ==================================================
#  BÚSQUEDA DE CONTRATOS
# ==================================================
st.markdown("<div class='busqueda-section'>", unsafe_allow_html=True)
st.markdown("### 🔍 Búsqueda de Contratos")

with st.form("form_consulta", clear_on_submit=False):
    st.markdown("Busca contratos por número de contrato:")

    busqueda = st.text_input(
        "Número de contrato:",
        placeholder="Ej: 12345, PEMEX-2024...",
        key="busqueda_contratos",
        label_visibility="collapsed"
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        buscar = st.form_submit_button("🔍 Buscar Contrato", use_container_width=True)
    with col_btn2:
        actualizar = st.form_submit_button("🔄 Actualizar Vista", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# ==================================================
#  RESULTADOS DE BÚSQUEDA
# ==================================================
try:
    if 'buscar' in locals() and buscar and busqueda:
        with st.spinner("Buscando contratos..."):
            filtros = {'numero_contrato': busqueda}
            contratos_db = manager.buscar_contratos_pemex(filtros)

            if not contratos_db:
                st.markdown("<div class='resultados-section'>", unsafe_allow_html=True)
                st.warning(f"❌ No se encontraron contratos con el número: **{busqueda}**")
                st.info("💡 Verifica el número de contrato e intenta nuevamente")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='resultados-section'>", unsafe_allow_html=True)
                if len(contratos_db) == 1:
                    contrato_seleccionado = contratos_db[0]
                    contrato_id = contrato_seleccionado.get('id')
                    st.success(f"✅ **1 contrato encontrado**")
                    st.markdown("---")
                    mostrar_contrato_completo(manager, contrato_id)
                else:
                    st.success(f"✅ **{len(contratos_db)} contratos encontrados**")
                    st.markdown("---")
                    seleccion_db = st.selectbox(
                        "Selecciona un contrato para ver sus detalles:",
                        contratos_db,
                        format_func=lambda c: f"{c.get('numero_contrato','-')} - {c.get('contratista','-')}",
                        key="select_contrato_db"
                    )
                    if seleccion_db:
                        contrato_id = seleccion_db.get('id')
                        mostrar_contrato_completo(manager, contrato_id)
                st.markdown("</div>", unsafe_allow_html=True)

    elif not (('buscar' in locals() and buscar) or busqueda):
        st.markdown("<div class='info-message'>", unsafe_allow_html=True)
        st.info("💡 **Instrucciones:** Ingresa un número de contrato en el campo de búsqueda y haz click en 'Buscar Contrato' para comenzar")
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error consultando base de datos: {str(e)}")

# ==================================================
#  PIE DE PÁGINA
# ==================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Sistema de Consulta de Contratos PEMEX</strong><br>
        • Búsqueda rápida por número de contrato • Descarga directa de archivos PDF • Estadísticas en tiempo real
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)  # Cierre del main-container
