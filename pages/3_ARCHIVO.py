# pages/3_ARCHIVO.py
import streamlit as st
from pathlib import Path
import base64
from core.database import get_db_manager

# --- CONFIGURACIÓN DE RUTAS ---
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

# --- VALIDAR SESIÓN ---
nombre = st.session_state.get("nombre", "")

if not nombre:
    st.error("⚠️ Debes iniciar sesión primero desde INICIO.py")
    st.stop()

# ==============================
#  FUNCIONES PARA BASE DE DATOS
# ==============================
def obtener_contratos_bd(manager):
    """Obtener lista de contratos desde la base de datos"""
    try:
        contratos = manager.buscar_contratos_pemex({})
        return True, contratos
    except Exception as e:
        return False, f"❌ Error obteniendo contratos: {str(e)}"

def obtener_contrato_completo_bd(manager, contrato_id):
    """Obtener contrato completo con archivo desde la base de datos"""
    try:
        contrato_data = manager.obtener_contrato_por_id(contrato_id)
        return True, contrato_data
    except Exception as e:
        return False, f"❌ Error obteniendo contrato: {str(e)}"

def eliminar_contrato_bd(manager, contrato_id):
    """Eliminar contrato completo de la base de datos"""
    try:
        success = manager.eliminar_contrato(contrato_id)
        if success:
            return True, "✅ Contrato eliminado completamente del sistema"
        else:
            return False, "❌ No se pudo eliminar el contrato"
    except Exception as e:
        return False, f"❌ Error eliminando contrato: {str(e)}"

# ==============================
#  ESTILOS MEJORADOS - ANCHO COMPLETO
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
    width: 95%;
    max-width: 95vw;
    margin: 20px auto;
}}

/* Estilos para elementos internos del formulario */
div[data-testid="stForm"] {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 15px;
    padding: 20px 25px;
    margin: 20px 0;
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
    border-radius: 8px;
    border: none;
    height: 44px;
    width: 100%;
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
    width: 100%;
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
    width: 100%;
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
    width: 100%;
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
    text-align: left;
    width: 100%;
}}

.carpeta-cerrada:hover {{
    background: linear-gradient(135deg, #b38e2f, #d4af37);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}

.carpeta-abierta {{
    background: rgba(255,255,255,0.98);
    border: 2px solid #d4af37;
    border-radius: 12px;
    padding: 25px;
    margin: 15px 0;
    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    width: 100%;
}}

.seccion-archivos {{
    background: rgba(248,249,250,0.9);
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    width: 100%;
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
    width: 100%;
}}

.archivo-acciones {{
    display: flex;
    gap: 10px;
    margin-top: 10px;
    width: 100%;
}}

.confirmacion-eliminar {{
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 20px;
    margin: 15px 0;
    width: 100%;
}}

.accion-rapida {{
    display: flex;
    gap: 10px;
    margin-top: 10px;
    width: 100%;
}}

.estadisticas-simple {{
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin: 20px 0;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    width: 100%;
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
    width: 100%;
}}

.busqueda-section {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
    width: 100%;
}}

.contratos-section {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #d4af37;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
    width: 100%;
}}
</style>
""", unsafe_allow_html=True)

# ==================================================
#  INICIALIZACIÓN Y CONEXIÓN
# ==================================================

# Inicializar estados en session_state
if 'contrato_expandido' not in st.session_state:
    st.session_state.contrato_expandido = None
if 'contrato_eliminando' not in st.session_state:
    st.session_state.contrato_eliminando = None

# Obtener manager de base de datos
manager = get_db_manager()
if not manager:
    st.error("❌ No se pudo conectar al sistema.")
    st.stop()

# ==================================================
#  INTERFAZ PRINCIPAL - TODO DENTRO DEL CONTENEDOR
# ==================================================
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# Logo y título
if logo_base64:
    st.markdown(
        f"<div style='text-align:center; margin-bottom: 20px;'><img src='data:image/jpeg;base64,{logo_base64}' width='150'></div>",
        unsafe_allow_html=True
    )

st.markdown("<h1 style='text-align:center; color: #6b0012; margin-bottom: 10px;'>ARCHIVO DE CONTRATOS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color: #666; margin-bottom: 30px;'>Sistema de gestión y consulta de contratos PEMEX</p>", unsafe_allow_html=True)

# Información del usuario
st.markdown(f"<div class='usuario-info'>👤 Usuario: {nombre}</div>", unsafe_allow_html=True)

# ==================================================
#  ESTADÍSTICA SIMPLE
# ==================================================
st.markdown("<div class='estadisticas-simple'>", unsafe_allow_html=True)
try:
    stats = manager.obtener_estadisticas_pemex()
    st.markdown(f"### 📊 CONTRATOS EN SISTEMA: {stats['total_contratos']}")
    st.markdown(f"**👥 Contratistas únicos:** {stats.get('contratistas_unicos', 0)} | **💾 Almacenamiento:** {stats['total_bytes'] / (1024*1024):.2f} MB")
except Exception as e:
    st.error(f"❌ Error obteniendo estadísticas: {str(e)}")
st.markdown("</div>", unsafe_allow_html=True)

# ==================================================
#  BÚSQUEDA Y FILTROS
# ==================================================
st.markdown("<div class='busqueda-section'>", unsafe_allow_html=True)
st.markdown("### 🔍 Buscar Contratos")

with st.form("busqueda_form"):
    col1, col2 = st.columns(2)
    with col1:
        numero_contrato = st.text_input("Número de contrato", placeholder="Ej: 12345, PEMEX-2024...")
    with col2:
        contratista = st.text_input("Contratista", placeholder="Nombre del contratista...")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        buscar = st.form_submit_button("🔍 Buscar Contratos", use_container_width=True)
    with col_btn2:
        actualizar = st.form_submit_button("🔄 Actualizar Lista", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Aplicar filtros
filtros = {}
if numero_contrato:
    filtros['numero_contrato'] = numero_contrato
if contratista:
    filtros['contratista'] = contratista

# Obtener contratos
success, contratos_db = obtener_contratos_bd(manager)

if not success:
    st.error(contratos_db)
    contratos_lista = []
else:
    # Aplicar filtros manualmente
    if filtros:
        contratos_filtrados = []
        for contrato in contratos_db:
            coincide = True
            if 'numero_contrato' in filtros and filtros['numero_contrato']:
                if filtros['numero_contrato'].lower() not in contrato.get('numero_contrato', '').lower():
                    coincide = False
            if 'contratista' in filtros and filtros['contratista']:
                if filtros['contratista'].lower() not in contrato.get('contratista', '').lower():
                    coincide = False
            if coincide:
                contratos_filtrados.append(contrato)
        contratos_db = contratos_filtrados
    
    contratos_lista = [(c['id'], f"{c['numero_contrato']} - {c['contratista']}") for c in contratos_db]

# ==================================================
#  LISTA DE CONTRATOS CON CARPETAS EXPANDIBLES
# ==================================================
st.markdown("<div class='contratos-section'>", unsafe_allow_html=True)
st.markdown("### 📂 Contratos Guardados")

if not contratos_lista:
    st.info("ℹ️ No hay contratos en el sistema. Utilice la página de procesamiento para agregar contratos.")
else:
    # Mostrar resultados de búsqueda
    if filtros:
        st.success(f"🔍 **{len(contratos_lista)} contratos encontrados** que coinciden con la búsqueda")
    else:
        st.info(f"📊 **Total de contratos en el sistema:** {len(contratos_lista)}")

    # Mostrar cada contrato como carpeta
    for contrato_id, contrato_nombre in contratos_lista:
        # Encontrar la información completa del contrato
        contrato_info = None
        for c in contratos_db:
            if c['id'] == contrato_id:
                contrato_info = c
                break
        
        if not contrato_info:
            continue
        
        # Si el contrato está expandido, mostrar detalles
        if st.session_state.contrato_expandido == contrato_id:
            st.markdown(f"<div class='carpeta-abierta'>", unsafe_allow_html=True)
            
            # Encabezado del contrato expandido
            col_head1, col_head2 = st.columns([3, 1])
            with col_head1:
                st.markdown(f"#### 📄 {contrato_info.get('numero_contrato', 'N/A')}")
                st.markdown(f"**Contratista:** {contrato_info.get('contratista', 'N/A')}")
            with col_head2:
                if st.button("📂 Cerrar", key=f"close_{contrato_id}", use_container_width=True):
                    st.session_state.contrato_expandido = None
                    st.rerun()
            
            # Información del contrato
            st.markdown("---")
            st.markdown("**📋 Información del contrato:**")
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.write(f"**• Área:** {contrato_info.get('area', 'No especificado')}")
                st.write(f"**• Fecha de subida:** {contrato_info.get('fecha_subida', 'No especificada')}")
            with col_info2:
                st.write(f"**• Monto:** {contrato_info.get('monto_contrato', 'No especificado')}")
                st.write(f"**• Plazo:** {contrato_info.get('plazo_dias', 'No especificado')} días")
            
            # Descripción
            descripcion = contrato_info.get('descripcion', '')
            if descripcion:
                st.markdown(f"**• Descripción:** {descripcion}")
            
            # Obtener archivo del contrato
            success, archivo_data = obtener_contrato_completo_bd(manager, contrato_id)
            
            if success and archivo_data:
                metadata = archivo_data['metadata']
                size_mb = metadata['tamaño_bytes'] / 1024 / 1024
                
                st.markdown("---")
                st.markdown("### 📎 Archivo Principal")
                
                st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
                
                col_file1, col_file2 = st.columns([3, 1])
                with col_file1:
                    st.markdown(f"**📄 {metadata['nombre_archivo']}**")
                    st.markdown(f"**Tamaño:** {size_mb:.2f} MB")
                
                with col_file2:
                    # Botón de descarga del archivo principal
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=archivo_data['contenido'],
                        file_name=metadata['nombre_archivo'],
                        mime="application/pdf",
                        key=f"download_file_{contrato_id}",
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
            
            # ==================================================
            #  ELIMINACIÓN DE CONTRATO COMPLETO
            # ==================================================
            st.markdown("---")
            st.markdown("### 🗑️ Eliminar Contrato Completo")
            
            if st.session_state.contrato_eliminando == contrato_id:
                st.markdown("<div class='confirmacion-eliminar'>", unsafe_allow_html=True)
                st.error("⚠️ **ADVERTENCIA**")
                st.warning(f"Estás a punto de eliminar el contrato **{contrato_info.get('numero_contrato', '')}** COMPLETAMENTE del sistema")
                st.info("❌ **Esta acción NO se puede deshacer**")
                
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("✅ SÍ, ELIMINAR CONTRATO", key=f"confirm_del_{contrato_id}", use_container_width=True):
                        success, message = eliminar_contrato_bd(manager, contrato_id)
                        if success:
                            st.success(message)
                            st.session_state.contrato_eliminando = None
                            st.session_state.contrato_expandido = None
                            st.rerun()
                        else:
                            st.error(message)
                
                with col_cancel:
                    if st.button("❌ CANCELAR", key=f"cancel_del_{contrato_id}", use_container_width=True):
                        st.session_state.contrato_eliminando = None
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                if st.button("🚨 ELIMINAR CONTRATO COMPLETO", key=f"init_del_{contrato_id}", use_container_width=True):
                    st.session_state.contrato_eliminando = contrato_id
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        else:
            # Mostrar carpeta cerrada
            if st.button(f"📂 {contrato_nombre}", key=f"folder_{contrato_id}", use_container_width=True):
                st.session_state.contrato_expandido = contrato_id
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)  # Cierre de contratos-section

# ==================================================
#  PIE DE PÁGINA
# ==================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Sistema de Archivo de Contratos PEMEX</strong><br>
        • Gestión centralizada de contratos • Descarga segura de documentos • Eliminación controlada
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)  # Cierre del main-container