# pages/3_ARCHIVO.py
import streamlit as st
from pathlib import Path
import json
import os
import base64

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
#  ESTILOS IGUALES AL LOGIN
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
</style>
""", unsafe_allow_html=True)

# ==================================================
#  FUNCIONES AUXILIARES
# ==================================================
def crear_enlace_descarga(archivo_path):
    """Crea un enlace temporal para descargar el archivo"""
    try:
        with open(archivo_path, "rb") as f:
            datos = f.read()
        # Codificar en base64 para el enlace de datos
        b64 = base64.b64encode(datos).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{archivo_path.name}" class="boton-descarga">📥 Descargar {archivo_path.name}</a>'
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

with st.form("form_gestion_archivos", clear_on_submit=True):
    
    if logo_base64:
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='200'></div>",
            unsafe_allow_html=True
        )

    st.markdown("<h2 style='text-align:center;'>SISTEMA DE GESTIÓN DE DOCUMENTOS PEMEX</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>📁 ARCHIVOS Y CONTRATOS</h4>", unsafe_allow_html=True)

    user_dir = BASE_DIR / nombre / "CONTRATOS"
    
    if not user_dir.exists():
        st.warning("📂 No se encontraron contratos en tu directorio personal.")
        st.info("💡 Ve a la página de procesamiento para crear tu primer contrato.")
        st.form_submit_button("🔄 ACTUALIZAR", use_container_width=True)
        st.stop()

    # --- LISTAR CONTRATOS EXISTENTES ---
    contratos = sorted([c for c in user_dir.iterdir() if c.is_dir()])
    
    if not contratos:
        st.info("ℹ️ No hay contratos disponibles todavía.")
        st.info("💡 Ve a la página de procesamiento para crear tu primer contrato.")
        st.form_submit_button("🔄 ACTUALIZAR", use_container_width=True)
        st.stop()

    # ==================================================
    #  SECCIÓN PARA SUBIR NUEVOS ARCHIVOS
    # ==================================================
    st.markdown("---")
    st.markdown("### 📤 Subir Archivos a Contrato Existente")
    
    col1, col2 = st.columns(2)
    with col1:
        # Seleccionar contrato
        nombres_contratos = [c.name for c in contratos]
        contrato_seleccionado = st.selectbox(
            "Seleccionar contrato:",
            nombres_contratos,
            key="select_contrato_subir"
        )
    
    with col2:
        # Seleccionar sección
        seccion_seleccionada = st.selectbox(
            "Seleccionar sección:",
            ["CEDULAS", "ANEXOS", "SOPORTES FISICOS"],
            key="select_seccion_subir"
        )
    
    # Subir archivos
    archivos_subir = st.file_uploader(
        "Seleccionar archivo(s) para subir:",
        accept_multiple_files=True,
        key="file_uploader_subir"
    )
    
    # Botón para subir
    subir_archivos = st.form_submit_button("🚀 SUBIR ARCHIVOS SELECCIONADOS", use_container_width=True)
    
    if subir_archivos and archivos_subir:
        contrato_path = user_dir / contrato_seleccionado / seccion_seleccionada
        contrato_path.mkdir(parents=True, exist_ok=True)
        
        for archivo in archivos_subir:
            save_path = contrato_path / archivo.name
            with open(save_path, "wb") as f:
                f.write(archivo.getbuffer())
        
        st.success(f"✅ {len(archivos_subir)} archivo(s) subido(s) a {contrato_seleccionado}/{seccion_seleccionada}")

    # ==================================================
    #  CONTROL DE EXPANSIÓN DE CARPETAS
    # ==================================================
    st.markdown("---")
    st.markdown("### 📂 Control de Visualización")
    
    # Seleccionar contrato para expandir
    contrato_a_expandir = st.selectbox(
        "Seleccionar contrato para ver detalles:",
        ["NINGUNO"] + [c.name for c in contratos],
        key="select_contrato_expandir"
    )
    
    expandir_contrato = st.form_submit_button("📂 EXPANDIR CONTRATO SELECCIONADO", use_container_width=True)
    
    if expandir_contrato and contrato_a_expandir != "NINGUNO":
        st.session_state.contrato_expandido = contrato_a_expandir

    # ==================================================
    #  VISUALIZACIÓN DEL CONTRATO EXPANDIDO
    # ==================================================
    if st.session_state.contrato_expandido:
        contrato = user_dir / st.session_state.contrato_expandido
        
        st.markdown("---")
        st.markdown(f"<div class='carpeta-abierta'>", unsafe_allow_html=True)
        st.markdown(f"#### 📂 {st.session_state.contrato_expandido} (Expandido)")
        
        # Botón para contraer
        contraer = st.form_submit_button("📂 CERRAR CONTRATO", use_container_width=True)
        if contraer:
            st.session_state.contrato_expandido = None
            st.session_state.archivo_eliminando = None
            st.session_state.contrato_eliminando = None
            st.rerun()
        
        # --- Leer y mostrar metadatos ---
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
        
        # --- SECCIONES DE ARCHIVOS ---
        secciones = [
            ("📋 CÉDULA", "CEDULAS"),
            ("📎 ANEXOS", "ANEXOS"), 
            ("📂 SOPORTES", "SOPORTES FISICOS")
        ]
        
        for icono, subfolder in secciones:
            st.markdown(f"##### {icono} {subfolder}")
            
            sub_path = contrato / subfolder
            sub_path.mkdir(exist_ok=True)
            
            # Mostrar archivos existentes con enlaces de descarga
            existing_files = list(sub_path.glob("*"))
            if existing_files:
                for archivo in existing_files:
                    if archivo.is_file():
                        size_kb = round(archivo.stat().st_size / 1024, 2)
                        archivo_key = f"{st.session_state.contrato_expandido}_{subfolder}_{archivo.name}"
                        
                        st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
                        
                        # Información del archivo
                        col1, col2 = st.columns([3, 2])
                        with col1:
                            st.markdown(f"**📄 {archivo.name}**")
                            st.markdown(f"*Tamaño: {size_kb} KB*")
                        
                        with col2:
                            # Crear enlace de descarga
                            enlace_descarga = crear_enlace_descarga(archivo)
                            st.markdown(enlace_descarga, unsafe_allow_html=True)
                            
                            # Eliminación directa e intuitiva
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
                                # Botón para iniciar eliminación
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
        
        # --- ELIMINAR CONTRATO COMPLETO (MÁS INTUITIVO) ---
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
            # Botón para iniciar eliminación de contrato
            iniciar_eliminar_contrato = st.form_submit_button(
                "🚨 ELIMINAR CONTRATO COMPLETO", 
                use_container_width=True
            )
            if iniciar_eliminar_contrato:
                st.session_state.contrato_eliminando = st.session_state.contrato_expandido
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ==================================================
    #  LISTA DE CONTRATOS DISPONIBLES (CARPETAS CERRADAS)
    # ==================================================
    st.markdown("---")
    st.markdown("### 📂 Contratos Disponibles")
    
    for contrato in contratos:
        if st.session_state.contrato_expandido != contrato.name:
            st.markdown(f"<div class='carpeta-cerrada'>📁 {contrato.name}</div>", unsafe_allow_html=True)

    # ==================================================
    #  BOTÓN DE ACTUALIZACIÓN GENERAL
    # ==================================================
    st.markdown("---")
    actualizar = st.form_submit_button("🔄 ACTUALIZAR VISTA COMPLETA", use_container_width=True)
    if actualizar:
        st.session_state.archivo_eliminando = None
        st.session_state.contrato_eliminando = None
        st.rerun()

# --- Mensaje informativo al final ---
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Información Rápida:</strong><br>
        • <strong>Para ver archivos:</strong> Selecciona un contrato y haz clic en "EXPANDIR"<br>
        • <strong>Para descargar:</strong> Usa el botón azul "📥 Descargar" en cada archivo<br>
        • <strong>Para eliminar archivo:</strong> Haz clic en "🗑️ ELIMINAR" y confirma<br>
        • <strong>Para eliminar contrato:</strong> Expande el contrato y usa el botón rojo al final
    </div>
    """,
    unsafe_allow_html=True
)