# pages/3_ARCHIVO.py
import streamlit as st
from pathlib import Path
import json
import os
import base64
from core.database import get_db_manager  # Nuevo import

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

# --- CONFIGURACIÓN BASE ---
BASE_DIR = Path("data")

# ==============================
#  FUNCIONES NUEVAS PARA POSTGRESQL (MANTENIENDO FUNCIONALIDAD ORIGINAL)
# ==============================
def guardar_archivo_postgresql(manager, contrato_id, archivo, categoria, tipo_archivo):
    """Guardar archivo individual en PostgreSQL"""
    try:
        archivo_id = manager.guardar_archivo_completo(
            contrato_id, archivo, categoria, tipo_archivo, nombre
        )
        return True, f"✅ {archivo.name} guardado en PostgreSQL"
    except Exception as e:
        return False, f"❌ Error guardando en PostgreSQL: {str(e)}"

def obtener_contratos_postgresql(manager):
    """Obtener lista de contratos desde PostgreSQL"""
    try:
        contratos = manager.buscar_contratos_pemex({})
        return True, contratos
    except Exception as e:
        return False, f"❌ Error obteniendo contratos: {str(e)}"

def obtener_archivos_contrato_postgresql(manager, contrato_id):
    """Obtener todos los archivos de un contrato desde PostgreSQL"""
    try:
        archivos = manager.obtener_archivos_por_contrato(contrato_id)
        return True, archivos
    except Exception as e:
        return False, f"❌ Error obteniendo archivos: {str(e)}"

def eliminar_archivo_postgresql(manager, archivo_id):
    """Eliminar archivo de PostgreSQL"""
    try:
        # Esta función necesitaría ser implementada en database.py
        # Por ahora retornamos un mensaje informativo
        return False, "❌ Eliminación en PostgreSQL no implementada aún"
    except Exception as e:
        return False, f"❌ Error eliminando archivo: {str(e)}"

def eliminar_contrato_postgresql(manager, contrato_id):
    """Eliminar contrato completo de PostgreSQL"""
    try:
        # Esta función necesitaría ser implementada en database.py
        # Por ahora retornamos un mensaje informativo
        return False, "❌ Eliminación de contrato en PostgreSQL no implementada aún"
    except Exception as e:
        return False, f"❌ Error eliminando contrato: {str(e)}"
    
# --- Mensaje informativo al final ---
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Información Rápida:</strong><br>
        • <strong>Para ver archivos:</strong> Selecciona un contrato y haz clic en "EXPANDIR"<br>
        • <strong>Para descargar:</strong> Usa el botón azul "📥 Descargar" en cada archivo<br>
    </strong> Almacena archivos hasta 4TB cada uno
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================
#  ESTILOS IGUALES AL LOGIN (SIN CAMBIOS)
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

.postgres-badge {{
    background: linear-gradient(135deg, #336791, #2b5278);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: bold;
    margin-left: 10px;
}}

.local-badge {{
    background: linear-gradient(135deg, #28a745, #218838);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: bold;
    margin-left: 10px;
}}
</style>
""", unsafe_allow_html=True)

# ==================================================
#  FUNCIONES AUXILIARES ORIGINALES (SIN CAMBIOS)
# ==================================================
def crear_enlace_descarga_postgresql(archivo_data):
    """Crea enlace de descarga para archivos de PostgreSQL"""
    try:
        b64 = base64.b64encode(archivo_data['contenido']).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{archivo_data["nombre_archivo"]}" class="boton-descarga">📥 Descargar {archivo_data["nombre_archivo"]}</a>'
        return href
    except Exception as e:
        return f'<button class="boton-descarga" disabled>❌ Error al cargar</button>'

# ==================================================
#  INTERFAZ PRINCIPAL DENTRO DEL FORMULARIO
# ==================================================

# Inicializar estados en session_state
if 'contrato_expandido' not in st.session_state:
    st.session_state.contrato_expandido = None
if 'archivo_eliminando' not in st.session_state:
    st.session_state.archivo_eliminando = None
if 'contrato_eliminando' not in st.session_state:
    st.session_state.contrato_eliminando = None

# Obtener manager de PostgreSQL
manager = get_db_manager()
if not manager:
    st.error("❌ No se pudo conectar a PostgreSQL. Revisa la configuración.")
    st.stop()

with st.form("form_gestion_archivos", clear_on_submit=True):
    
    if logo_base64:
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='200'></div>",
            unsafe_allow_html=True
        )

    st.markdown("<h2 style='text-align:center;'>SISTEMA DE GESTIÓN DE DOCUMENTOS PEMEX</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>📁 ARCHIVOS Y CONTRATOS</h4>", unsafe_allow_html=True)

    # ==================================================
    #  SECCIÓN PARA SUBIR NUEVOS ARCHIVOS
    # ==================================================
    st.markdown("---")
    st.markdown("### 📤 Subir Archivos a Contrato Existente")
    
    # Obtener contratos de PostgreSQL
    success, contratos_db = obtener_contratos_postgresql(manager)
    if not success:
        st.error(contratos_db)
        contratos_lista = []
    else:
        contratos_lista = [(c['id'], f"{c['numero_contrato']} - {c['contratista']}") for c in contratos_db]
    
    if contratos_lista:
        contrato_seleccionado_id = st.selectbox(
            "Seleccionar contrato:",
            options=[c[0] for c in contratos_lista],
            format_func=lambda x: next((c[1] for c in contratos_lista if c[0] == x), ""),
            key="select_contrato_postgresql"
        )
    else:
        st.warning("📭 No hay contratos disponibles en PostgreSQL")
        contrato_seleccionado_id = None

    # Selección de sección
    seccion_seleccionada = st.selectbox(
        "Seleccionar sección:",
        ["CEDULAS", "ANEXOS", "SOPORTES FISICOS"],
        key="select_seccion_subir"
    )
    
    # Subir archivos
    archivos_subir = st.file_uploader(
        f"Seleccionar archivo(s) para subir (Hasta 4TB en PostgreSQL):",
        accept_multiple_files=True,
        key="file_uploader_subir"
    )
    
    # Botón para subir
    subir_archivos = st.form_submit_button("🚀 SUBIR ARCHIVOS SELECCIONADOS", use_container_width=True)
    
    if subir_archivos and archivos_subir:
        if contrato_seleccionado_id:
            for archivo in archivos_subir:
                success, message = guardar_archivo_postgresql(
                    manager, contrato_seleccionado_id, archivo, 
                    seccion_seleccionada, "anexo"
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)
        else:
            st.error("❌ No se seleccionó un contrato válido")

    # ==================================================
    #  CONTROL DE EXPANSIÓN DE CARPETAS
    # ==================================================
    st.markdown("---")
    st.markdown("### 📂 Control de Visualización")
    
    # Selección de contrato PostgreSQL para expandir
    if contratos_lista:
        contrato_a_expandir = st.selectbox(
            "Seleccionar contrato para ver detalles:",
            ["NINGUNO"] + [f"POSTGRESQL_{c[0]}" for c in contratos_lista],
            format_func=lambda x: next((c[1] for c in contratos_lista if f"POSTGRESQL_{c[0]}" == x), x),
            key="select_contrato_expandir_postgresql"
        )
    else:
        contrato_a_expandir = "NINGUNO"
    
    expandir_contrato = st.form_submit_button("📂 EXPANDIR CONTRATO SELECCIONADO", use_container_width=True)
    
    if expandir_contrato and contrato_a_expandir != "NINGUNO":
        st.session_state.contrato_expandido = contrato_a_expandir

    # ==================================================
    #  VISUALIZACIÓN DEL CONTRATO EXPANDIDO
    # ==================================================
    if st.session_state.contrato_expandido:
        st.markdown("---")
        
        # MODO POSTGRESQL
        contrato_id = int(st.session_state.contrato_expandido.replace("POSTGRESQL_", ""))
        
        st.markdown(f"<div class='carpeta-abierta'>", unsafe_allow_html=True)
        st.markdown(f"#### 🗄️ CONTRATO PostgreSQL (Hasta 4TB por archivo)")
        
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
            with col2:
                st.write(f"- **Monto:** {contrato_info.get('monto_contrato', 'No especificado')}")
                st.write(f"- **Plazo:** {contrato_info.get('plazo_dias', 'No especificado')} días")
        
        # Botón para contraer
        contraer = st.form_submit_button("📂 CERRAR CONTRATO", use_container_width=True)
        if contraer:
            st.session_state.contrato_expandido = None
            st.session_state.archivo_eliminando = None
            st.session_state.contrato_eliminando = None
            st.rerun()
        
        # Obtener archivos del contrato
        success, archivos = obtener_archivos_contrato_postgresql(manager, contrato_id)
        
        if success and archivos:
            # Agrupar archivos por categoría
            archivos_por_categoria = {}
            for archivo in archivos:
                categoria = archivo['categoria']
                if categoria not in archivos_por_categoria:
                    archivos_por_categoria[categoria] = []
                archivos_por_categoria[categoria].append(archivo)
            
            # Mostrar archivos por categoría
            secciones = [
                ("📋 CÉDULA", "CEDULAS"),
                ("📎 ANEXOS", "ANEXOS"), 
                ("📂 SOPORTES", "SOPORTES FISICOS"),
                ("📄 CONTRATO", "CONTRATO")
            ]
            
            for icono, categoria in secciones:
                if categoria in archivos_por_categoria:
                    st.markdown(f"##### {icono} {categoria}")
                    
                    for archivo in archivos_por_categoria[categoria]:
                        size_mb = archivo['tamaño_bytes'] / 1024 / 1024
                        
                        st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([3, 2])
                        with col1:
                            st.markdown(f"**📄 {archivo['nombre_archivo']}**")
                            st.markdown(f"*Tamaño: {size_mb:.2f} MB*")
                        
                        with col2:
                            # Enlace de descarga
                            enlace_descarga = crear_enlace_descarga_postgresql(archivo)
                            st.markdown(enlace_descarga, unsafe_allow_html=True)
                            
                            # Eliminación (placeholder por ahora)
                            st.info("ℹ️ Eliminación en PostgreSQL próximamente")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("ℹ️ No hay archivos en este contrato de PostgreSQL")
        
        # Eliminar contrato completo
        st.markdown("---")
        st.markdown("### 🗑️ Eliminar Contrato Completo")
        
        st.info("ℹ️ Eliminación de contratos en PostgreSQL próximamente")
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ==================================================
    #  LISTA DE CONTRATOS DISPONIBLES
    # ==================================================
    st.markdown("---")
    st.markdown("### 📂 Contratos Disponibles")
    
    # Mostrar contratos de PostgreSQL
    success, contratos_db = obtener_contratos_postgresql(manager)
    if success and contratos_db:
        for contrato in contratos_db:
            if st.session_state.contrato_expandido != f"POSTGRESQL_{contrato['id']}":
                st.markdown(f"<div class='carpeta-cerrada'>🗄️ {contrato['numero_contrato']} - {contrato['contratista']} <span class='postgres-badge'>PostgreSQL</span></div>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ No hay contratos en PostgreSQL")

    # ==================================================
    #  BOTÓN DE ACTUALIZACIÓN GENERAL
    # ==================================================
    st.markdown("---")
    actualizar = st.form_submit_button("🔄 ACTUALIZAR VISTA COMPLETA", use_container_width=True)
    if actualizar:
        st.session_state.archivo_eliminando = None
        st.session_state.contrato_eliminando = None
        st.rerun()

