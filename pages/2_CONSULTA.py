# pages/2_CONSULTA.py
import streamlit as st
from pathlib import Path
import re
import base64
import json 

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
#  FUNCIONES AUXILIARES
# ==================================================
def crear_enlace_descarga(archivo_path):
    """Crea un enlace temporal para descargar el archivo"""
    try:
        with open(archivo_path, "rb") as f:
            datos = f.read()
        # Codificar en base64 para el enlace de datos
        b64 = base64.b64encode(datos).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{archivo_path.name}" class="boton-descarga">📥 Descargar</a>'
        return href
    except Exception as e:
        return f'<button class="boton-descarga" disabled>❌ Error</button>'

# ==================================================
#  INTERFAZ PRINCIPAL DENTRO DEL FORMULARIO
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

    # --- Lista de contratos del usuario ---
    user_dir = BASE_DIR / usuario / "CONTRATOS"
    
    if not user_dir.exists():
        st.warning("📂 No se encontraron contratos en tu directorio personal.")
        st.info("💡 Ve a la página de procesamiento para crear tu primer contrato.")
        st.form_submit_button("🔄 ACTUALIZAR", use_container_width=True)
        st.stop()

    contratos = sorted([d for d in user_dir.iterdir() if d.is_dir() and d.name.startswith("CONTRATO_")])

    # --- Filtrado de contratos ---
    if busqueda:
        # Si el usuario ingresó solo dígitos, buscar por número dentro del nombre
        if re.fullmatch(r"\d+", busqueda):
            contratos_filtrados = [c for c in contratos if busqueda in c.name]
        else:
            contratos_filtrados = [c for c in contratos if busqueda in c.name.upper()]
    else:
        contratos_filtrados = contratos

    if not contratos_filtrados:
        st.warning("❌ No se encontraron contratos que coincidan con la búsqueda.")
        st.form_submit_button("🔄 ACTUALIZAR BÚSQUEDA", use_container_width=True)
        st.stop()

    # --- Selección de contrato ---
    st.markdown("---")
    st.markdown("### 📂 Contratos Encontrados")
    
    if len(contratos_filtrados) > 1:
        seleccion = st.selectbox(
            "Selecciona un contrato para ver sus archivos:",
            contratos_filtrados,
            format_func=lambda p: p.name.replace("CONTRATO_", ""),
            key="select_contrato"
        )
    else:
        seleccion = contratos_filtrados[0]
        st.info(f"📄 Contrato encontrado: {seleccion.name.replace('CONTRATO_', '')}")

    # --- Mostrar información del contrato seleccionado ---
    st.markdown(f"<div class='carpeta-header'>📁 CONTRATO: {seleccion.name.replace('CONTRATO_', '')}</div>", unsafe_allow_html=True)
    
    # Leer metadatos si existen
    meta_path = seleccion / "metadatos.json"
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
                st.write(f"- **Anexos:** {len(meta.get('anexos', []))}")
            
            if meta.get('objeto'):
                st.markdown(f"**📝 Objeto del contrato:** {meta.get('objeto', '')}")
                
        except Exception as e:
            st.warning("⚠️ No se pudieron leer los metadatos del contrato.")

    # --- Mostrar carpetas internas y archivos ---
    st.markdown("---")
    st.markdown("### 📎 Archivos del Contrato")
    
    secciones = [
        ("📋 CÉDULA", "CEDULAS"),
        ("📎 ANEXOS", "ANEXOS"), 
        ("📂 SOPORTES", "SOPORTES FISICOS")
    ]
    
    archivos_encontrados = False
    
    for icono, subfolder in secciones:
        carpeta_path = seleccion / subfolder
        if carpeta_path.exists():
            archivos = sorted(carpeta_path.glob("*"))
            if archivos:
                archivos_encontrados = True
                st.markdown(f"#### {icono} {subfolder}")
                
                for archivo in archivos:
                    if archivo.is_file():
                        size_kb = round(archivo.stat().st_size / 1024, 2)
                        
                        st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{archivo.name}**")
                            st.markdown(f"*Tamaño: {size_kb} KB*")
                        
                        with col2:
                            # Crear enlace de descarga
                            enlace_descarga = crear_enlace_descarga(archivo)
                            st.markdown(enlace_descarga, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)

    # Mostrar archivos en la raíz del contrato
    archivos_raiz = [f for f in seleccion.iterdir() if f.is_file()]
    if archivos_raiz:
        archivos_encontrados = True
        st.markdown("#### 📄 Archivos Principales")
        
        for archivo in archivos_raiz:
            size_kb = round(archivo.stat().st_size / 1024, 2)
            
            st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{archivo.name}**")
                st.markdown(f"*Tamaño: {size_kb} KB*")
            
            with col2:
                # Crear enlace de descarga
                enlace_descarga = crear_enlace_descarga(archivo)
                st.markdown(enlace_descarga, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

    if not archivos_encontrados:
        st.info("ℹ️ No se encontraron archivos en este contrato.")

    # --- Botones de acción ---
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        actualizar = st.form_submit_button("🔄 ACTUALIZAR VISTA", use_container_width=True)
    
    with col2:
        nueva_busqueda = st.form_submit_button("🔍 NUEVA BÚSQUEDA", use_container_width=True)
    
    if actualizar or nueva_busqueda:
        st.rerun()

# --- Mensaje informativo al final ---
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Información:</strong><br>
        Usa la barra de búsqueda para encontrar contratos específicos. Puedes buscar por número de contrato, nombre del contratista o cualquier palabra clave.
    </div>
    """,
    unsafe_allow_html=True
)