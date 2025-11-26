# pages/2_CONSULTA.py
import streamlit as st
from pathlib import Path
import re
import base64
import json 
import os
from core.database import get_db_manager  # Importar el nuevo manager

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

# --- Mensaje informativo al final ---
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Información del Sistema PostgreSQL:</strong><br>
        • Todos los contratos se almacenan directamente en la base de datos PostgreSQL<br>
        • Búsqueda rápida por número de contrato, contratista o descripción<br>
        • Descarga directa de archivos PDF desde la base de datos<br>
        • Estadísticas en tiempo real del sistema<br>
        • <strong>🗄️ Almacenamiento centralizado y seguro</strong>
    </div>
    """,
    unsafe_allow_html=True
)

# ==================================================
#  FUNCIONES AUXILIARES - SOLO POSTGRESQL
# ==================================================
def crear_enlace_descarga_postgresql(archivo_data):
    """Crea enlace de descarga para archivos de PostgreSQL"""
    try:
        b64 = base64.b64encode(archivo_data['contenido']).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{archivo_data["nombre_archivo"]}" class="boton-descarga">📥 Descargar {archivo_data["nombre_archivo"]}</a>'
        return href
    except Exception as e:
        return f'<button class="boton-descarga" disabled>❌ Error al cargar</button>'

def mostrar_contrato_postgresql(manager, contrato_id):
    """✅ FUNCIÓN MEJORADA: Mostrar TODOS los archivos del contrato desde PostgreSQL"""
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
        st.markdown("**📋 Información del contrato:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"- **Número:** {contrato_info.get('numero_contrato', 'No especificado')}")
            st.write(f"- **Contratista:** {contrato_info.get('contratista', 'No especificado')}")
            st.write(f"- **Área:** {contrato_info.get('area', 'No especificado')}")
        with col2:
            st.write(f"- **Monto:** {contrato_info.get('monto_contrato', 'No especificado')}")
            st.write(f"- **Plazo:** {contrato_info.get('plazo_dias', 'No especificado')} días")
            st.write(f"- **Tamaño archivo:** {archivo_data['metadata']['tamaño_bytes'] / 1024 / 1024:.2f} MB")
            st.write(f"- **Fecha de subida:** {contrato_info.get('fecha_subida', 'No especificada')}")
        
        # Mostrar archivo principal
        st.markdown("---")
        st.markdown("### 📎 Archivo del Contrato")
        
        metadata = archivo_data['metadata']
        size_mb = metadata['tamaño_bytes'] / 1024 / 1024
        
        st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{metadata['nombre_archivo']}**")
            st.markdown(f"*Tamaño: {size_mb:.2f} MB*")
            st.markdown(f"*Tipo: {metadata.get('tipo_archivo', 'No especificado')}*")
            st.markdown(f"*Subido por: {metadata.get('usuario_subio', 'No especificado')}*")
        
        with col2:
            # Botón de descarga
            st.download_button(
                label="📥 Descargar PDF",
                data=archivo_data['contenido'],
                file_name=metadata['nombre_archivo'],
                mime="application/octet-stream",
                key=f"download_{contrato_id}"
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Mostrar anexos si existen
        anexos = contrato_info.get('anexos', [])
        if anexos:
            st.markdown("#### 📋 Anexos Detectados")
            for anexo in anexos:
                st.markdown(f"<div class='anexo-item'>📄 ANEXO \"{anexo}\"</div>", unsafe_allow_html=True)
        
        # Información adicional
        st.markdown("---")
        st.markdown("#### ℹ️ Información Adicional")
        st.info("""
        **Almacenamiento en PostgreSQL:**
        - ✅ Archivo PDF del contrato almacenado en la base de datos
        - ✅ Metadatos completos del contrato
        - ✅ Anexos detectados automáticamente
        - ✅ Información de auditoría (fecha, usuario)
        """)
        
    except Exception as e:
        st.error(f"❌ Error mostrando contrato: {str(e)}")

def mostrar_estadisticas_postgresql(manager):
    """Muestra estadísticas de la base de datos PostgreSQL"""
    try:
        stats = manager.obtener_estadisticas_pemex()
        
        st.markdown("<div class='estadisticas-container'>", unsafe_allow_html=True)
        st.markdown("### 📊 ESTADÍSTICAS POSTGRESQL")
        
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
        
        # Información adicional
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**📅 Contrato más antiguo:** {stats.get('fecha_mas_antigua', 'N/A')}")
        with col2:
            st.info(f"**📅 Contrato más reciente:** {stats.get('fecha_mas_reciente', 'N/A')}")
            
    except Exception as e:
        st.error(f"❌ Error obteniendo estadísticas: {str(e)}")

# ==================================================
#  INTERFAZ PRINCIPAL - SOLO POSTGRESQL
# ==================================================
with st.form("form_consulta", clear_on_submit=False):
    
    if logo_base64:
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='200'></div>",
            unsafe_allow_html=True
        )

    st.markdown("<h2 style='text-align:center;'>SISTEMA DE CONSULTA DE CONTRATOS PEMEX</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>🗄️ CONSULTA EN BASE DE DATOS POSTGRESQL</h4>", unsafe_allow_html=True)
    
    # Información del usuario
    st.markdown(f"<div class='usuario-info'>👤 Usuario: {usuario}</div>", unsafe_allow_html=True)

    # --- Verificar conexión a PostgreSQL ---
    manager = get_db_manager()
    if not manager:
        st.error("❌ No se pudo conectar a la base de datos PostgreSQL")
        st.info("💡 Verifica que la conexión a PostgreSQL esté configurada correctamente")
        
        # BOTÓN DE SUBMIT REQUERIDO
        submit_btn = st.form_submit_button("🔄 REINTENTAR CONEXIÓN", use_container_width=True)
        if submit_btn:
            st.rerun()
        st.stop()

    # --- Mostrar estadísticas ---
    mostrar_estadisticas_postgresql(manager)

    # --- Buscador ---
    st.markdown("---")
    st.markdown("### 🔍 Búsqueda de Contratos")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        busqueda = st.text_input(
            "Buscar por número de contrato, contratista o palabra clave:",
            placeholder="Ej: 12345, PEMEX, servicios...",
            key="busqueda_contratos"
        ).strip().upper()

    with col2:
        tipo_busqueda = st.selectbox(
            "Tipo de búsqueda:",
            ["Todos los campos", "Número de contrato", "Contratista", "Descripción"],
            key="tipo_busqueda"
        )

    # Buscar contratos en PostgreSQL
    try:
        filtros = {}
        if busqueda:
            if tipo_busqueda == "Número de contrato":
                filtros['numero_contrato'] = busqueda
            elif tipo_busqueda == "Contratista":
                filtros['contratista'] = busqueda
            elif tipo_busqueda == "Descripción":
                filtros['descripcion'] = busqueda
            else:  # Todos los campos
                filtros['numero_contrato'] = busqueda
                # Nota: La búsqueda en todos los campos se maneja en la lógica de búsqueda

        contratos_db = manager.buscar_contratos_pemex(filtros)
        
        if not contratos_db:
            st.warning("❌ No se encontraron contratos en la base de datos que coincidan con la búsqueda.")
            
            # Mostrar todos los contratos si no hay búsqueda
            if not busqueda:
                st.info("💡 No hay contratos en la base de datos. Ve a la página de procesamiento para crear el primer contrato.")
            
            # BOTÓN DE SUBMIT REQUERIDO
            submit_btn = st.form_submit_button("🔄 ACTUALIZAR BÚSQUEDA", use_container_width=True)
            if submit_btn:
                st.rerun()
        else:
            # --- Selección de contrato ---
            st.markdown("---")
            st.markdown(f"### 📂 Contratos Encontrados ({len(contratos_db)} resultados)")
            
            if len(contratos_db) > 1:
                seleccion_db = st.selectbox(
                    "Selecciona un contrato para ver sus detalles:",
                    contratos_db,
                    format_func=lambda c: f"{c['numero_contrato']} - {c['contratista']} - {c.get('fecha_subida', '')}",
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
        # BOTÓN DE SUBMIT REQUERIDO
        submit_btn = st.form_submit_button("🔄 REINTENTAR", use_container_width=True)
        if submit_btn:
            st.rerun()

    # --- BOTÓN DE SUBMIT PRINCIPAL ---
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        actualizar = st.form_submit_button("🔄 ACTUALIZAR VISTA", use_container_width=True)
    
    with col2:
        nueva_busqueda = st.form_submit_button("🔍 NUEVA BÚSQUEDA", use_container_width=True)
    
    with col3:
        exportar_datos = st.form_submit_button("📊 EXPORTAR ESTADÍSTICAS", use_container_width=True)
    
    # Asegurarnos de que siempre hay un botón de submit activo
    if not any([actualizar, nueva_busqueda, exportar_datos]):
        st.form_submit_button("🔄 ACTUALIZAR", use_container_width=True, key="default_submit")
    elif actualizar or nueva_busqueda:
        st.rerun()
    elif exportar_datos:
        try:
            # Exportar estadísticas
            stats = manager.obtener_estadisticas_pemex()
            stats_json = json.dumps(stats, indent=2, ensure_ascii=False, default=str)
            
            st.download_button(
                label="📥 DESCARGAR ESTADÍSTICAS JSON",
                data=stats_json,
                file_name=f"estadisticas_contratos_{usuario}.json",
                mime="application/json",
                key="download_stats"
            )
        except Exception as e:
            st.error(f"❌ Error exportando estadísticas: {str(e)}")
