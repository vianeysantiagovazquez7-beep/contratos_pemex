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
# --- Mensaje informativo al final ---
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Información Rápida:</strong><br>
        • <strong>Para ver archivos:</strong> Selecciona un contrato y haz clic en "EXPANDIR"<br>
        • <strong>Para descargar:</strong> Usa el botón azul "📥 Descargar" en cada archivo<br>
        • <strong>Para eliminar archivo:</strong> Haz clic en "🗑️ ELIMINAR" y confirma<br>
        • <strong>Para eliminar contrato:</strong> Expande el contrato y usa el botón rojo al final<br>
        • <strong>PostgreSQL:</strong> Almacena archivos hasta 4TB cada uno
    </div>
    """,
    unsafe_allow_html=True
)

def crear_enlace_descarga(archivo_path):
    """Crea un enlace temporal para descargar el archivo"""
    try:
        with open(archivo_path, "rb") as f:
            datos = f.read()
        b64 = base64.b64encode(datos).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{archivo_path.name}" class="boton-descarga">📥 Descargar {archivo_path.name}</a>'
        return href
    except Exception as e:
        return f'<button class="boton-descarga" disabled>❌ Error al cargar</button>'

def crear_enlace_descarga_postgresql(archivo_data):
    """Crea enlace de descarga para archivos de PostgreSQL"""
    try:
        b64 = base64.b64encode(archivo_data['contenido']).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{archivo_data["nombre_archivo"]}" class="boton-descarga">📥 Descargar {archivo_data["nombre_archivo"]}</a>'
        return href
    except Exception as e:
        return f'<button class="boton-descarga" disabled>❌ Error al cargar</button>'

def eliminar_archivo(ruta_archivo):
    """Elimina un archivo específico"""
    try:
        Path(ruta_archivo).unlink()
        return True, "✅ Archivo eliminado correctamente"
    except Exception as e:
        return False, f"❌ Error al eliminar: {e}"

def eliminar_contrato_completo(ruta_contrato):
    """Elimina un contrato completo con todo su contenido"""
    try:
        for root, dirs, files in os.walk(ruta_contrato, topdown=False):
            for name in files:
                (Path(root) / name).unlink()
            for name in dirs:
                (Path(root) / name).rmdir()
        ruta_contrato.rmdir()
        return True, "✅ Contrato eliminado completamente"
    except Exception as e:
        return False, f"❌ No se pudo eliminar el contrato: {e}"

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
if 'modo_almacenamiento' not in st.session_state:
    st.session_state.modo_almacenamiento = "Sistema de Archivos Local"

with st.form("form_gestion_archivos", clear_on_submit=True):
    
    if logo_base64:
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='200'></div>",
            unsafe_allow_html=True
        )

    st.markdown("<h2 style='text-align:center;'>SISTEMA DE GESTIÓN DE DOCUMENTOS PEMEX</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>📁 ARCHIVOS Y CONTRATOS</h4>", unsafe_allow_html=True)

    # ==================================================
    #  SELECTOR DE MODO DE ALMACENAMIENTO
    # ==================================================
    st.markdown("---")
    st.markdown("### 🗄️ Modo de Almacenamiento")
    
    modo_almacenamiento = st.radio(
        "Selecciona dónde almacenar los archivos:",
        ["📂 Sistema de Archivos Local", "🗄️ PostgreSQL (Hasta 4TB por archivo)"],
        key="modo_almacenamiento_radio",
        horizontal=True
    )
    
    # Actualizar session_state
    st.session_state.modo_almacenamiento = modo_almacenamiento
    
    # Obtener manager de PostgreSQL si es necesario
    manager = None
    if "PostgreSQL" in modo_almacenamiento:
        manager = get_db_manager()
        if not manager:
            st.error("❌ No se pudo conectar a PostgreSQL. Revisa la configuración.")
            st.session_state.modo_almacenamiento = "📂 Sistema de Archivos Local"

    # ==================================================
    #  SECCIÓN PARA SUBIR NUEVOS ARCHIVOS
    # ==================================================
    st.markdown("---")
    st.markdown("### 📤 Subir Archivos a Contrato Existente")
    
    if "PostgreSQL" in st.session_state.modo_almacenamiento and manager:
        # MODO POSTGRESQL
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
    else:
        # MODO SISTEMA DE ARCHIVOS LOCAL
        user_dir = BASE_DIR / nombre / "CONTRATOS"
        
        if not user_dir.exists():
            st.warning("📂 No se encontraron contratos en tu directorio personal.")
        else:
            contratos = sorted([c for c in user_dir.iterdir() if c.is_dir()])
            nombres_contratos = [c.name for c in contratos] if contratos else []
            
            if nombres_contratos:
                contrato_seleccionado = st.selectbox(
                    "Seleccionar contrato:",
                    nombres_contratos,
                    key="select_contrato_local"
                )
            else:
                st.warning("📭 No hay contratos disponibles localmente")
                contrato_seleccionado = None

    # Selección de sección (común para ambos modos)
    seccion_seleccionada = st.selectbox(
        "Seleccionar sección:",
        ["CEDULAS", "ANEXOS", "SOPORTES FISICOS"],
        key="select_seccion_subir"
    )
    
    # Subir archivos
    archivos_subir = st.file_uploader(
        f"Seleccionar archivo(s) para subir {'(Hasta 4TB en PostgreSQL)' if 'PostgreSQL' in st.session_state.modo_almacenamiento else ''}:",
        accept_multiple_files=True,
        key="file_uploader_subir"
    )
    
    # Botón para subir
    subir_archivos = st.form_submit_button("🚀 SUBIR ARCHIVOS SELECCIONADOS", use_container_width=True)
    
    if subir_archivos and archivos_subir:
        if "PostgreSQL" in st.session_state.modo_almacenamiento and manager:
            # Subir a PostgreSQL
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
        else:
            # Subir a sistema de archivos local
            if contrato_seleccionado:
                contrato_path = user_dir / contrato_seleccionado / seccion_seleccionada
                contrato_path.mkdir(parents=True, exist_ok=True)
                
                for archivo in archivos_subir:
                    save_path = contrato_path / archivo.name
                    with open(save_path, "wb") as f:
                        f.write(archivo.getbuffer())
                
                st.success(f"✅ {len(archivos_subir)} archivo(s) subido(s) a {contrato_seleccionado}/{seccion_seleccionada}")
            else:
                st.error("❌ No se seleccionó un contrato válido")

    # ==================================================
    #  CONTROL DE EXPANSIÓN DE CARPETAS
    # ==================================================
    st.markdown("---")
    st.markdown("### 📂 Control de Visualización")
    
    if "PostgreSQL" in st.session_state.modo_almacenamiento and manager:
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
    else:
        # Selección de contrato local para expandir
        user_dir = BASE_DIR / nombre / "CONTRATOS"
        if user_dir.exists():
            contratos = sorted([c for c in user_dir.iterdir() if c.is_dir()])
            nombres_contratos = [c.name for c in contratos]
        else:
            nombres_contratos = []
        
        contrato_a_expandir = st.selectbox(
            "Seleccionar contrato para ver detalles:",
            ["NINGUNO"] + nombres_contratos,
            key="select_contrato_expandir_local"
        )
    
    expandir_contrato = st.form_submit_button("📂 EXPANDIR CONTRATO SELECCIONADO", use_container_width=True)
    
    if expandir_contrato and contrato_a_expandir != "NINGUNO":
        st.session_state.contrato_expandido = contrato_a_expandir

    # ==================================================
    #  VISUALIZACIÓN DEL CONTRATO EXPANDIDO
    # ==================================================
    if st.session_state.contrato_expandido:
        st.markdown("---")
        
        if "POSTGRESQL_" in str(st.session_state.contrato_expandido):
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
            
        else:
            # MODO SISTEMA DE ARCHIVOS LOCAL (CÓDIGO ORIGINAL)
            contrato = user_dir / st.session_state.contrato_expandido
            
            st.markdown(f"<div class='carpeta-abierta'>", unsafe_allow_html=True)
            st.markdown(f"#### 📂 {st.session_state.contrato_expandido} (Expandido)")
            
            # ... (TODO EL CÓDIGO ORIGINAL PARA SISTEMA DE ARCHIVOS LOCAL SE MANTIENE IGUAL)
            # Botón para contraer
            contraer = st.form_submit_button("📂 CERRAR CONTRATO", use_container_width=True)
            if contraer:
                st.session_state.contrato_expandido = None
                st.session_state.archivo_eliminando = None
                st.session_state.contrato_eliminando = None
                st.rerun()
            
            # Leer y mostrar metadatos
            meta_path = contrato / "metadatos.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    
                    st.markdown("**📋 Información del contrato:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"- **Número:** {meta.get('contrato', 'No especificado')}")
                        st.write(f"- **Contratista:** {meta.get('contratista', 'No especificado')}")
                        st.write(f"- **Área:** {meta.get('area', 'No especificado')}")
                    with col2:
                        st.write(f"- **Monto:** {meta.get('monto', 'No especificado')}")
                        st.write(f"- **Plazo:** {meta.get('plazo', 'No especificado')} días")
                        st.write(f"- **Anexos detectados:** {len(meta.get('anexos', []))}")
                    
                    if meta.get('objeto'):
                        st.markdown(f"**📝 Objeto:** {meta.get('objeto', '')}")
                        
                except Exception as e:
                    st.warning("⚠️ No se pudieron leer los metadatos del contrato.")
            else:
                st.caption("ℹ️ Sin metadatos de contrato registrados.")
            
            # Secciones de archivos (código original)
            secciones = [
                ("📋 CÉDULA", "CEDULAS"),
                ("📎 ANEXOS", "ANEXOS"), 
                ("📂 SOPORTES", "SOPORTES FISICOS")
            ]
            
            for icono, subfolder in secciones:
                st.markdown(f"##### {icono} {subfolder}")
                
                sub_path = contrato / subfolder
                sub_path.mkdir(exist_ok=True)
                
                existing_files = list(sub_path.glob("*"))
                if existing_files:
                    for archivo in existing_files:
                        if archivo.is_file():
                            size_kb = round(archivo.stat().st_size / 1024, 2)
                            archivo_key = f"{st.session_state.contrato_expandido}_{subfolder}_{archivo.name}"
                            
                            st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([3, 2])
                            with col1:
                                st.markdown(f"**📄 {archivo.name}**")
                                st.markdown(f"*Tamaño: {size_kb} KB*")
                            
                            with col2:
                                enlace_descarga = crear_enlace_descarga(archivo)
                                st.markdown(enlace_descarga, unsafe_allow_html=True)
                                
                                if st.session_state.archivo_eliminando == archivo_key:
                                    st.markdown("<div class='confirmacion-eliminar'>", unsafe_allow_html=True)
                                    st.warning(f"¿Eliminar **{archivo.name}**?")
                                    col_confirm, col_cancel = st.columns(2)
                                    with col_confirm:
                                        confirmar = st.form_submit_button("✅ SÍ, ELIMINAR", use_container_width=True)
                                        if confirmar:
                                            success, message = eliminar_archivo(archivo)
                                            if success:
                                                st.success(message)
                                                st.session_state.archivo_eliminando = None
                                                st.rerun()
                                            else:
                                                st.error(message)
                                    with col_cancel:
                                        cancelar = st.form_submit_button("❌ CANCELAR", use_container_width=True)
                                        if cancelar:
                                            st.session_state.archivo_eliminando = None
                                            st.rerun()
                                    st.markdown("</div>", unsafe_allow_html=True)
                                else:
                                    iniciar_eliminar = st.form_submit_button(
                                        f"🗑️ ELIMINAR {archivo.name}", 
                                        key=f"iniciar_del_{archivo_key}",
                                        use_container_width=True
                                    )
                                    if iniciar_eliminar:
                                        st.session_state.archivo_eliminando = archivo_key
                                        st.rerun()
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.caption("No hay archivos en esta sección.")
            
            # Eliminar contrato completo (código original)
            st.markdown("---")
            st.markdown("### 🗑️ Eliminar Contrato Completo")
            
            if st.session_state.contrato_eliminando == st.session_state.contrato_expandido:
                st.markdown("<div class='confirmacion-eliminar'>", unsafe_allow_html=True)
                st.error("⚠️ **ADVERTENCIA CRÍTICA**")
                st.warning(f"Estás a punto de eliminar el contrato **{st.session_state.contrato_expandido}** COMPLETAMENTE")
                st.info("❌ **Esta acción NO se puede deshacer**")
                st.info("📁 **Se eliminarán TODOS los archivos y carpetas del contrato**")
                
                col1, col2 = st.columns(2)
                with col1:
                    confirmar_eliminar = st.form_submit_button("✅ SÍ, ELIMINAR CONTRATO COMPLETO", use_container_width=True)
                    if confirmar_eliminar:
                        success, message = eliminar_contrato_completo(contrato)
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
                    "🚨 ELIMINAR CONTRATO COMPLETO", 
                    use_container_width=True
                )
                if iniciar_eliminar_contrato:
                    st.session_state.contrato_eliminando = st.session_state.contrato_expandido
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

    # ==================================================
    #  LISTA DE CONTRATOS DISPONIBLES
    # ==================================================
    st.markdown("---")
    st.markdown("### 📂 Contratos Disponibles")
    
    if "PostgreSQL" in st.session_state.modo_almacenamiento and manager:
        # Mostrar contratos de PostgreSQL
        success, contratos_db = obtener_contratos_postgresql(manager)
        if success and contratos_db:
            for contrato in contratos_db:
                if st.session_state.contrato_expandido != f"POSTGRESQL_{contrato['id']}":
                    st.markdown(f"<div class='carpeta-cerrada'>🗄️ {contrato['numero_contrato']} - {contrato['contratista']} <span class='postgres-badge'>PostgreSQL</span></div>", unsafe_allow_html=True)
        else:
            st.info("ℹ️ No hay contratos en PostgreSQL")
    else:
        # Mostrar contratos locales
        user_dir = BASE_DIR / nombre / "CONTRATOS"
        if user_dir.exists():
            contratos = sorted([c for c in user_dir.iterdir() if c.is_dir()])
            for contrato in contratos:
                if st.session_state.contrato_expandido != contrato.name:
                    st.markdown(f"<div class='carpeta-cerrada'>📁 {contrato.name} <span class='local-badge'>Local</span></div>", unsafe_allow_html=True)

    # ==================================================
    #  BOTÓN DE ACTUALIZACIÓN GENERAL
    # ==================================================
    st.markdown("---")
    actualizar = st.form_submit_button("🔄 ACTUALIZAR VISTA COMPLETA", use_container_width=True)
    if actualizar:
        st.session_state.archivo_eliminando = None
        st.session_state.contrato_eliminando = None
        st.rerun()
