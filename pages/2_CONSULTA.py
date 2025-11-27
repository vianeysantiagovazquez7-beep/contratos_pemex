# pages/2_CONSULTA.py
import streamlit as st
from pathlib import Path
import base64
from core.database import get_db_manager

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

.contrato-item {{
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    transition: all 0.3s ease;
}}

.contrato-item:hover {{
    background: #e9ecef;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}

.archivo-item {{
    background: white;
    border: 1px solid #e9ecef;
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

.carpeta-header {{
    background: linear-gradient(135deg, #6b0012, #40000a);
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    margin: 20px 0 10px 0;
    text-align: center;
    font-weight: bold;
    font-size: 1.2em;
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

.estadisticas-container {{
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin: 20px 0;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}

.estadistica-item {{
    background: rgba(255,255,255,0.2);
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}}

.contrato-encontrado {{
    background: rgba(255,255,255,0.98);
    border: 2px solid #28a745;
    border-radius: 12px;
    padding: 25px;
    margin: 20px 0;
    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
}}

.busqueda-section {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
}}

.resultados-section {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
}}

.info-message {{
    background: rgba(255,255,255,0.9);
    border: 2px solid #17a2b8;
    border-radius: 10px;
    padding: 15px;
    margin: 15px 0;
    text-align: center;
}}
</style>
""", unsafe_allow_html=True)

# ==================================================
#  FUNCIONES AUXILIARES - MANTENIDAS
# ==================================================
def mostrar_contrato_completo(manager, contrato_id):
    """✅ FUNCIÓN MEJORADA: Mostrar contrato completo con descarga directa"""
    try:
        # Obtener información del contrato
        contratos = manager.buscar_contratos_pemex({})
        contrato_info = None
        for c in contratos:
            if c['id'] == contrato_id:
                contrato_info = c
                break
        
        if not contrato_info:
            st.error("❌ Contrato no encontrado")
            return
        
        # Obtener archivo principal del contrato
        archivo_data = manager.obtener_contrato_por_id(contrato_id)
        
        if not archivo_data:
            st.error("❌ No se encontraron archivos para este contrato")
            return
        
        # Mostrar información del contrato
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
            st.write(f"**• Tamaño archivo:** {archivo_data['metadata']['tamaño_bytes'] / 1024 / 1024:.2f} MB")
            st.write(f"**• Fecha de subida:** {contrato_info.get('fecha_subida', 'No especificada')}")
        
        # Mostrar archivo principal
        st.markdown("---")
        st.markdown("### 📎 Archivo del Contrato")
        
        metadata = archivo_data['metadata']
        size_mb = metadata['tamaño_bytes'] / 1024 / 1024
        
        st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**📄 {metadata['nombre_archivo']}**")
            st.markdown(f"**Tamaño:** {size_mb:.2f} MB")
        
        with col2:
            # Botón de descarga
            st.download_button(
                label="📥 Descargar PDF",
                data=archivo_data['contenido'],
                file_name=metadata['nombre_archivo'],
                mime="application/pdf",
                key=f"download_{contrato_id}",
                use_container_width=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Mostrar anexos si existen
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
            st.markdown(f"# {stats['total_contratos']}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<div class='estadistica-item'>", unsafe_allow_html=True)
            st.markdown(f"**👥 Cantidad de Contratistas**")
            st.markdown(f"# {stats['contratistas_unicos']}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"<div class='estadistica-item'>", unsafe_allow_html=True)
            st.markdown(f"**💾 Almacenamiento Total**")
            st.markdown(f"# {stats['total_bytes'] / (1024*1024):.2f} MB")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Información adicional
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**📅 Contrato más antiguo:** {stats.get('fecha_mas_antigua', 'N/A')}")
        with col2:
            st.info(f"**📅 Contrato más reciente:** {stats.get('fecha_mas_reciente', 'N/A')}")
            
    except Exception as e:
        st.error(f"❌ Error obteniendo estadísticas: {str(e)}")

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
# Buscar contratos
try:
    if buscar and busqueda:
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
                # --- Mostrar resultados de búsqueda ---
                if len(contratos_db) == 1:
                    # Si hay solo un resultado, mostrarlo directamente
                    contrato_seleccionado = contratos_db[0]
                    contrato_id = contrato_seleccionado['id']
                    
                    st.success(f"✅ **1 contrato encontrado**")
                    st.markdown("---")
                    
                    # Mostrar contrato completo automáticamente
                    mostrar_contrato_completo(manager, contrato_id)
                    
                else:
                    # Si hay múltiples resultados, mostrar selector
                    st.success(f"✅ **{len(contratos_db)} contratos encontrados**")
                    st.markdown("---")
                    
                    seleccion_db = st.selectbox(
                        "Selecciona un contrato para ver sus detalles:",
                        contratos_db,
                        format_func=lambda c: f"{c['numero_contrato']} - {c['contratista']}",
                        key="select_contrato_db"
                    )
                    
                    if seleccion_db:
                        contrato_id = seleccion_db['id']
                        
                        # Mostrar contrato completo
                        mostrar_contrato_completo(manager, contrato_id)
                st.markdown("</div>", unsafe_allow_html=True)
    
    elif not buscar and not busqueda:
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