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
#  ESTILOS SIMPLIFICADOS
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

.carpeta-cerrada {{
    background: linear-gradient(135deg, #336791, #2b5278);
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    margin: 10px 0;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid #2b5278;
}}

.carpeta-cerrada:hover {{
    background: linear-gradient(135deg, #2b5278, #336791);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}

.carpeta-abierta {{
    background: rgba(255,255,255,0.95);
    border: 2px solid #336791;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}

.archivo-item {{
    background: #f8f9fa;
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

.eliminar-btn {{
    background-color: #dc3545 !important;
    color: white !important;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 0.9em;
    width: 100%;
    margin: 5px 0;
}}

.eliminar-btn:hover {{
    background-color: #c82333 !important;
}}

.estadisticas-simple {{
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 15px;
    border-radius: 10px;
    margin: 15px 0;
    text-align: center;
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

.confirmacion-eliminar {{
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
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
#  INTERFAZ PRINCIPAL
# ==================================================
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

if logo_base64:
    st.markdown(
        f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='150'></div>",
        unsafe_allow_html=True
    )

st.markdown("<h2 style='text-align:center;'>ARCHIVO DE CONTRATOS</h2>", unsafe_allow_html=True)

# Información del usuario
st.info(f"👤 **Usuario:** {nombre}")

# ==================================================
#  ESTADÍSTICA SIMPLE
# ==================================================
try:
    stats = manager.obtener_estadisticas_pemex()
    
    st.markdown("<div class='estadisticas-simple'>", unsafe_allow_html=True)
    st.markdown(f"### 📊 CONTRATOS EN SISTEMA: {stats['total_contratos']}")
    st.markdown("</div>", unsafe_allow_html=True)
    
except Exception as e:
    st.error(f"❌ Error obteniendo estadísticas: {str(e)}")

# ==================================================
#  BÚSQUEDA Y FILTROS
# ==================================================
st.markdown("---")
st.markdown("### 🔍 Buscar Contratos")

with st.form("busqueda_form"):
    col1, col2 = st.columns(2)
    with col1:
        numero_contrato = st.text_input("Número de contrato")
    with col2:
        contratista = st.text_input("Contratista")
    
    buscar = st.form_submit_button("🔍 Buscar", use_container_width=True)
    actualizar = st.form_submit_button("🔄 Actualizar lista", use_container_width=True)

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
st.markdown("---")
st.markdown("### 📂 Contratos Guardados")

if not contratos_lista:
    st.info("ℹ️ No hay contratos en el sistema")
else:
    # Mostrar resultados de búsqueda
    if filtros:
        st.info(f"🔍 Mostrando {len(contratos_lista)} contratos que coinciden con la búsqueda")
    else:
        st.info(f"📊 Total de contratos: {len(contratos_lista)}")

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
            st.markdown("**📋 Información del contrato:**")
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.write(f"- **Área:** {contrato_info.get('area', 'No especificado')}")
                st.write(f"- **Fecha de subida:** {contrato_info.get('fecha_subida', 'No especificada')}")
            with col_info2:
                st.write(f"- **Monto:** {contrato_info.get('monto_contrato', 'No especificado')}")
                st.write(f"- **Plazo:** {contrato_info.get('plazo_dias', 'No especificado')} días")
            
            # Descripción
            descripcion = contrato_info.get('descripcion', '')
            if descripcion:
                st.markdown(f"**Descripción:** {descripcion}")
            
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
                    st.markdown(f"*Tamaño: {size_mb:.2f} MB*")
                    # ❌ ELIMINADO: Información técnica del tipo de archivo
                
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

st.markdown("</div>", unsafe_allow_html=True)
