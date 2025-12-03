# pages/2_CONSULTA.py
import streamlit as st
from pathlib import Path
import re
import base64
import json 
from core.database import get_db_manager  # Importar el nuevo manager

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

# --- Verificar sesión ---
if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.error("Acceso denegado. Inicie sesión.")
    st.stop()

usuario = st.session_state.get("nombre", "").upper()

# --- Mensaje informativo ---
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Información:</strong><br>
        Usa la barra de búsqueda para encontrar contratos específicos. Puedes buscar por número de contrato, nombre del contratista o cualquier palabra clave.<br>
        <strong>PostgreSQL:</strong> Consulta todos los archivos (CONTRATO, ANEXOS, CÉDULAS, SOPORTES) almacenados en la base de datos.
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================
#  ESTILOS IGUALES AL LOGIN (MANTENIENDO DISEÑO ORIGINAL)
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
    border-radius: 6px;
    padding: 12px;
    margin: 8px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.boton-descarga {{
    background-color: #17a2b8 !important;
    color: white !important;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 0.9em;
}}

.boton-descarga:hover {{
    background-color: #138496 !important;
}}

.carpeta-header {{
    background: linear-gradient(135deg, #6b0012, #40000a);
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 15px 0 10px 0;
    font-weight: bold;
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

# ==================================================
#  FUNCIONES AUXILIARES CORREGIDAS
# ==================================================
def obtener_archivos_por_contrato(manager, contrato_id):
    """✅ FUNCIÓN CORREGIDA: Obtener todos los archivos de un contrato"""
    try:
        # Usar el método existente en el manager
        archivos = []
        
        # Obtener archivos por categoría usando métodos existentes
        for categoria in ['CONTRATO', 'ANEXOS', 'CEDULAS', 'SOPORTES FISICOS']:
            archivos_categoria = manager.obtener_archivos(contrato_id, categoria)
            for archivo in archivos_categoria:
                archivos.append({
                    'id': archivo.id,
                    'nombre_archivo': archivo.nombre_archivo,
                    'categoria': categoria,
                    'tamaño_bytes': archivo.tamaño_bytes,
                    'contenido': archivo.contenido
                })
        
        return archivos
        
    except Exception as e:
        st.error(f"❌ Error obteniendo archivos: {str(e)}")
        return []

def mostrar_contrato_postgresql(manager, contrato_id):
    """✅ FUNCIÓN MEJORADA: Mostrar TODOS los archivos del contrato desde PostgreSQL"""
    try:
        # Obtener información del contrato
        contratos = manager.buscar_contratos_pemex({'id': contrato_id})
        if not contratos:
            st.error("❌ Contrato no encontrado")
            return
        
        contrato_info = contratos[0]
        
        # Obtener TODOS los archivos del contrato usando la función corregida
        archivos = obtener_archivos_por_contrato(manager, contrato_id)
        
        if not archivos:
            st.error("❌ No se encontraron archivos para este contrato")
            return
        
        # Mostrar información del contrato
        st.markdown("**📋 Información del contrato:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"- **Número:** {contrato_info.get('numero_contrato', 'No especificado')}")
            st.write(f"- **Contratista:** {contrato_info.get('contratista', 'No especificado')}")
            st.write(f"- **Área:** {contrato_info.get('area', 'No especificado')}")
        with col2:
            st.write(f"- **Monto:** {contrato_info.get('monto_contrato', 'No especificado')}")
            st.write(f"- **Plazo:** {contrato_info.get('plazo_dias', 'No especificado')} días")
            st.write(f"- **Total archivos:** {len(archivos)}")
        
        # Agrupar archivos por categoría
        archivos_por_categoria = {}
        for archivo in archivos:
            categoria = archivo['categoria']
            if categoria not in archivos_por_categoria:
                archivos_por_categoria[categoria] = []
            archivos_por_categoria[categoria].append(archivo)
        
        # Mostrar archivos por categoría (MISMA ESTRUCTURA QUE TU DISEÑO ORIGINAL)
        st.markdown("---")
        st.markdown("### 📎 Archivos del Contrato")
        
        secciones = [
            ("📄 CONTRATO", "CONTRATO"),
            ("📋 CÉDULA", "CEDULAS"),
            ("📎 ANEXOS", "ANEXOS"), 
            ("📂 SOPORTES", "SOPORTES FISICOS")
        ]
        
        archivos_encontrados = False
        
        for icono, categoria in secciones:
            if categoria in archivos_por_categoria:
                archivos_encontrados = True
                st.markdown(f"#### {icono} {categoria}")
                
                for archivo in archivos_por_categoria[categoria]:
                    size_mb = archivo['tamaño_bytes'] / 1024 / 1024
                    
                    st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**{archivo['nombre_archivo']}**")
                        st.markdown(f"*Tamaño: {size_mb:.2f} MB*")
                    
                    with col2:
                        # Botón de descarga individual - MISMOS ESTILOS
                        st.download_button(
                            label="📥 Descargar",
                            data=archivo['contenido'],
                            file_name=archivo['nombre_archivo'],
                            mime="application/octet-stream",
                            key=f"download_{archivo['id']}_{categoria}",
                            use_container_width=True
                        )
                    
                    st.markdown("</div>", unsafe_allow_html=True)

        if not archivos_encontrados:
            st.info("ℹ️ No se encontraron archivos en este contrato.")
        
    except Exception as e:
        st.error(f"❌ Error mostrando contrato: {str(e)}")

# ==================================================
#  INTERFAZ PRINCIPAL - MANTENIENDO DISEÑO ORIGINAL
# ==================================================
with st.form("form_consulta", clear_on_submit=False):
    
    if logo_base64:
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='200'></div>",
            unsafe_allow_html=True
        )

    st.markdown("<h2 style='text-align:center;'>SISTEMA DE CONSULTA DE CONTRATOS PEMEX</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>📚 CONSULTA DE CONTRATOS</h4>", unsafe_allow_html=True)
    
    # Información del usuario
    st.markdown(f"<div class='usuario-info'>👤 Usuario: {usuario}</div>", unsafe_allow_html=True)

    # --- Buscador ---
    st.markdown("---")
    st.markdown("### 🔍 Búsqueda de Contratos")
    
    busqueda = st.text_input(
        "Buscar por número de contrato, contratista o palabra clave:",
        placeholder="Ej: 12345, PEMEX, servicios...",
        key="busqueda_contratos"
    ).strip().upper()

    # ==================================================
    #  MODO BASE DE DATOS POSTGRESQL (ÚNICO MODO AHORA)
    # ==================================================
    manager = get_db_manager()
    if not manager:
        st.error("❌ No se pudo conectar a la base de datos PostgreSQL")
        st.info("💡 Verifica que DATABASE_URL esté configurada en los secrets")
    else:
        try:
            # Buscar contratos en PostgreSQL
            filtros = {}
            if busqueda:
                if re.fullmatch(r"\d+", busqueda):
                    filtros['numero_contrato'] = busqueda
                else:
                    filtros['contratista'] = busqueda

            contratos_db = manager.buscar_contratos_pemex(filtros)
            
            if not contratos_db:
                st.warning("❌ No se encontraron contratos en la base de datos que coincidan con la búsqueda.")
            else:
                # --- Selección de contrato ---
                st.markdown("---")
                st.markdown("### 📂 Contratos Encontrados (PostgreSQL)")
                
                if len(contratos_db) > 1:
                    seleccion_db = st.selectbox(
                        "Selecciona un contrato para ver sus archivos:",
                        contratos_db,
                        format_func=lambda c: f"{c['numero_contrato']} - {c['contratista']}",
                        key="select_contrato_db"
                    )
                    contrato_id = seleccion_db['id']
                else:
                    seleccion_db = contratos_db[0]
                    contrato_id = seleccion_db['id']
                    st.info(f"📄 Contrato encontrado: {seleccion_db['numero_contrato']} - {seleccion_db['contratista']}")

                # Mostrar información del contrato seleccionado
                st.markdown(f"<div class='carpeta-header'>📁 CONTRATO: {seleccion_db['numero_contrato']}</div>", unsafe_allow_html=True)
                
                # Mostrar contrato completo desde PostgreSQL
                mostrar_contrato_postgresql(manager, contrato_id)

        except Exception as e:
            st.error(f"❌ Error consultando base de datos: {str(e)}")

    # --- Botones de acción ---
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        actualizar = st.form_submit_button("🔄 ACTUALIZAR VISTA", use_container_width=True)
    
    with col2:
        nueva_busqueda = st.form_submit_button("🔍 NUEVA BÚSQUEDA", use_container_width=True)
    
    if actualizar or nueva_busqueda:
        st.rerun()

