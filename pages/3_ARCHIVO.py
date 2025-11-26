# pages/3_ARCHIVO.py
import streamlit as st
from pathlib import Path
import json
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
usuario = st.session_state.get("usuario", "").upper()
nombre = st.session_state.get("nombre", "").upper()

if not usuario or not nombre:
    st.error("⚠️ Debes iniciar sesión primero desde INICIO.py")
    st.stop()

# ==============================
#  FUNCIONES PARA POSTGRESQL
# ==============================
def obtener_contratos_postgresql(manager):
    """Obtener lista de contratos desde PostgreSQL"""
    try:
        contratos = manager.buscar_contratos_pemex({})
        return True, contratos
    except Exception as e:
        return False, f"❌ Error obteniendo contratos: {str(e)}"

def obtener_contrato_completo_postgresql(manager, contrato_id):
    """Obtener contrato completo con archivo desde PostgreSQL"""
    try:
        contrato_data = manager.obtener_contrato_por_id(contrato_id)
        return True, contrato_data
    except Exception as e:
        return False, f"❌ Error obteniendo contrato: {str(e)}"

def eliminar_contrato_postgresql(manager, contrato_id):
    """Eliminar contrato completo de PostgreSQL"""
    try:
        success = manager.eliminar_contrato(contrato_id)
        if success:
            return True, "✅ Contrato eliminado completamente de PostgreSQL"
        else:
            return False, "❌ No se pudo eliminar el contrato"
    except Exception as e:
        return False, f"❌ Error eliminando contrato: {str(e)}"

# ==============================
#  ESTILOS (MANTENIENDO DISEÑO ORIGINAL)
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

.confirmacion-eliminar {{
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}}

.postgres-badge {{
    background: linear-gradient(135deg, #28a745, #218838);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: bold;
    margin-left: 10px;
}}

.estadisticas-container {{
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 15px;
    border-radius: 10px;
    margin: 15px 0;
    text-align: center;
}}

.estadistica-item {{
    background: rgba(255,255,255,0.2);
    border-radius: 8px;
    padding: 10px;
    margin: 5px 0;
}}
</style>
""", unsafe_allow_html=True)

# ==================================================
#  INICIALIZACIÓN Y CONEXIÓN POSTGRESQL
# ==================================================

# Inicializar estados en session_state
if 'contrato_expandido' not in st.session_state:
    st.session_state.contrato_expandido = None
if 'contrato_eliminando' not in st.session_state:
    st.session_state.contrato_eliminando = None

# Obtener manager de PostgreSQL
manager = get_db_manager()
if not manager:
    st.error("❌ No se pudo conectar a PostgreSQL. Revisa la configuración.")
    st.stop()

# ==================================================
#  INTERFAZ PRINCIPAL
# ==================================================
with st.form("form_gestion_archivos", clear_on_submit=True):
    
    if logo_base64:
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='200'></div>",
            unsafe_allow_html=True
        )

    st.markdown("<h2 style='text-align:center;'>SISTEMA DE GESTIÓN DE DOCUMENTOS PEMEX</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>🗄️ ARCHIVOS EN POSTGRESQL</h4>", unsafe_allow_html=True)

    # Información del usuario
    st.markdown(f"<div class='contrato-header'>👤 Usuario: {nombre} | 🗄️ Almacenamiento: PostgreSQL</div>", unsafe_allow_html=True)

    # ==================================================
    #  ESTADÍSTICAS POSTGRESQL
    # ==================================================
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
            st.markdown(f"**👥 Contratistas Únicos**")
            st.markdown(f"# {stats['contratistas_unicos']}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"<div class='estadistica-item'>", unsafe_allow_html=True)
            st.markdown(f"**💾 Almacenamiento Total**")
            st.markdown(f"# {stats['total_bytes'] / (1024*1024):.2f} MB")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo estadísticas: {str(e)}")

    # ==================================================
    #  CONTROL DE EXPANSIÓN DE CONTRATOS
    # ==================================================
    st.markdown("---")
    st.markdown("### 📂 Seleccionar Contrato")
    
    # Obtener contratos de PostgreSQL
    success, contratos_db = obtener_contratos_postgresql(manager)
    
    if not success:
        st.error(contratos_db)
        contratos_lista = []
    else:
        contratos_lista = [(c['id'], f"{c['numero_contrato']} - {c['contratista']} - {c.get('fecha_subida', '')}") for c in contratos_db]
    
    if contratos_lista:
        contrato_a_expandir = st.selectbox(
            "Seleccionar contrato para ver detalles:",
            ["NINGUNO"] + [f"POSTGRESQL_{c[0]}" for c in contratos_lista],
            format_func=lambda x: next((c[1] for c in contratos_lista if f"POSTGRESQL_{c[0]}" == x), x),
            key="select_contrato_expandir"
        )
    else:
        contrato_a_expandir = "NINGUNO"
        st.info("ℹ️ No hay contratos en la base de datos")
    
    expandir_contrato = st.form_submit_button("📂 EXPANDIR CONTRATO SELECCIONADO", use_container_width=True)
    
    if expandir_contrato and contrato_a_expandir != "NINGUNO":
        st.session_state.contrato_expandido = contrato_a_expandir

    # ==================================================
    #  VISUALIZACIÓN DEL CONTRATO EXPANDIDO
    # ==================================================
    if st.session_state.contrato_expandido and "POSTGRESQL_" in str(st.session_state.contrato_expandido):
        st.markdown("---")
        
        contrato_id = int(st.session_state.contrato_expandido.replace("POSTGRESQL_", ""))
        
        st.markdown(f"<div class='carpeta-abierta'>", unsafe_allow_html=True)
        st.markdown(f"#### 🗄️ CONTRATO PostgreSQL")
        
        # Obtener información del contrato
        success, contratos_db = obtener_contratos_postgresql(manager)
        contrato_info = None
        if success:
            for c in contratos_db:
                if c['id'] == contrato_id:
                    contrato_info = c
                    break
        
        if contrato_info:
            st.markdown("**📋 Información del contrato:**")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"- **Número:** {contrato_info.get('numero_contrato', 'No especificado')}")
                st.write(f"- **Contratista:** {contrato_info.get('contratista', 'No especificado')}")
                st.write(f"- **Área:** {contrato_info.get('area', 'No especificado')}")
                st.write(f"- **Fecha de subida:** {contrato_info.get('fecha_subida', 'No especificada')}")
            with col2:
                st.write(f"- **Monto:** {contrato_info.get('monto_contrato', 'No especificado')}")
                st.write(f"- **Plazo:** {contrato_info.get('plazo_dias', 'No especificado')} días")
                st.write(f"- **Usuario que subió:** {contrato_info.get('usuario_subio', 'No especificado')}")
        
        # Obtener archivo del contrato
        success, archivo_data = obtener_contrato_completo_postgresql(manager, contrato_id)
        
        if success and archivo_data:
            metadata = archivo_data['metadata']
            size_mb = metadata['tamaño_bytes'] / 1024 / 1024
            
            st.markdown("---")
            st.markdown("### 📎 Archivo Principal del Contrato")
            
            st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**📄 {metadata['nombre_archivo']}**")
                st.markdown(f"*Tamaño: {size_mb:.2f} MB*")
                st.markdown(f"*Tipo: {metadata.get('tipo_archivo', 'No especificado')}*")
                st.markdown(f"*Hash SHA256: {metadata.get('hash_sha256', '')[:16]}...*")
            
            with col2:
                # Botón de descarga
                st.download_button(
                    label="📥 Descargar PDF",
                    data=archivo_data['contenido'],
                    file_name=metadata['nombre_archivo'],
                    mime="application/octet-stream",
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
            
            # Información técnica
            st.markdown("---")
            st.markdown("#### 🔧 Información Técnica")
            st.info(f"""
            **Almacenamiento PostgreSQL:**
            - ✅ Archivo almacenado en Large Object (hasta 4TB)
            - ✅ Hash SHA256 para verificación de integridad
            - ✅ Metadatos completos del contrato
            - ✅ Información de auditoría (fecha, usuario)
            - ✅ Búsqueda y recuperación rápida
            """)
            
        else:
            st.error("❌ No se pudo cargar el archivo del contrato")
        
        # ==================================================
        #  ELIMINACIÓN DE CONTRATO
        # ==================================================
        st.markdown("---")
        st.markdown("### 🗑️ Eliminar Contrato")
        
        if st.session_state.contrato_eliminando == st.session_state.contrato_expandido:
            st.markdown("<div class='confirmacion-eliminar'>", unsafe_allow_html=True)
            st.error("⚠️ **ADVERTENCIA CRÍTICA**")
            st.warning(f"Estás a punto de eliminar el contrato **{contrato_info.get('numero_contrato', '')}** COMPLETAMENTE de PostgreSQL")
            st.info("❌ **Esta acción NO se puede deshacer**")
            st.info("🗄️ **Se eliminarán TODOS los datos del contrato de la base de datos**")
            
            col1, col2 = st.columns(2)
            with col1:
                confirmar_eliminar = st.form_submit_button("✅ SÍ, ELIMINAR CONTRATO", use_container_width=True)
                if confirmar_eliminar:
                    success, message = eliminar_contrato_postgresql(manager, contrato_id)
                    if success:
                        st.success(message)
                        st.session_state.contrato_eliminando = None
                        st.session_state.contrato_expandido = None
                        st.rerun()
                    else:
                        st.error(message)
            
            with col2:
                cancelar_eliminar = st.form_submit_button("❌ CANCELAR ELIMINACIÓN", use_container_width=True)
                if cancelar_eliminar:
                    st.session_state.contrato_eliminando = None
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            iniciar_eliminar_contrato = st.form_submit_button(
                "🚨 ELIMINAR CONTRATO DE POSTGRESQL", 
                use_container_width=True
            )
            if iniciar_eliminar_contrato:
                st.session_state.contrato_eliminando = st.session_state.contrato_expandido
                st.rerun()
        
        # Botón para contraer
        st.markdown("---")
        contraer = st.form_submit_button("📂 CERRAR CONTRATO", use_container_width=True)
        if contraer:
            st.session_state.contrato_expandido = None
            st.session_state.contrato_eliminando = None
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ==================================================
    #  LISTA DE CONTRATOS DISPONIBLES
    # ==================================================
    st.markdown("---")
    st.markdown("### 📂 Contratos en PostgreSQL")
    
    if contratos_lista:
        for contrato_id, contrato_nombre in contratos_lista:
            if st.session_state.contrato_expandido != f"POSTGRESQL_{contrato_id}":
                st.markdown(f"<div class='carpeta-cerrada'>🗄️ {contrato_nombre} <span class='postgres-badge'>PostgreSQL</span></div>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ No hay contratos en la base de datos PostgreSQL")

    # ==================================================
    #  BOTÓN DE ACTUALIZACIÓN
    # ==================================================
    st.markdown("---")
    actualizar = st.form_submit_button("🔄 ACTUALIZAR VISTA COMPLETA", use_container_width=True)
    if actualizar:
        st.session_state.contrato_eliminando = None
        st.rerun()

# --- Mensaje informativo al final ---
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Información del Sistema PostgreSQL:</strong><br>
        • <strong>Almacenamiento:</strong> Todos los archivos se guardan directamente en PostgreSQL<br>
        • <strong>Capacidad:</strong> Hasta 4TB por archivo individual<br>
        • <strong>Seguridad:</strong> Hash SHA256 para verificación de integridad<br>
        • <strong>Auditoría:</strong> Fecha, usuario y metadatos completos<br>
        • <strong>Eliminación:</strong> Eliminación completa con confirmación<br>
        • <strong>🗄️ Sistema 100% centralizado en base de datos</strong>
    </div>
    """,
    unsafe_allow_html=True
)
