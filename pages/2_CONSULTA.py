# pages/2_CONSULTA.py
import streamlit as st
from pathlib import Path
import re
import base64
import json 
from core.database import get_db_manager_por_usuario # Importar el nuevo manager
from core.tutorial import init, header_button, overlay

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

init()
header_button()
overlay("consulta")

# --- Mensaje informativo al final ---
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

.descarga-btn {{
    background-color: #17a2b8 !important;
    color: white !important;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 0.9em;
    width: 100%;
    margin: 5px 0;
}}

.descarga-btn:hover {{
    background-color: #138496 !important;
}}

.download-link {{
    display: none;
}}
</style>
""", unsafe_allow_html=True)

# ==================================================
#  FUNCIONES AUXILIARES MEJORADAS
# ==================================================
def obtener_archivos_por_contrato(manager, contrato_id):
    """✅ FUNCIÓN ROBUSTA CORREGIDA: Obtener todos los archivos de un contrato"""
    try:
        archivos = []
        
        # Método 1: Intentar usar método directo si existe
        try:
            if hasattr(manager, 'obtener_archivos_por_contrato'):
                archivos_directo = manager.obtener_archivos_por_contrato(contrato_id)
                if archivos_directo:
                    return archivos_directo
        except Exception:
            pass
        
        # Método 2: Buscar por categorías individuales usando métodos disponibles
        categorias = ['CONTRATO', 'ANEXOS', 'CEDULAS', 'SOPORTES FISICOS']
        
        for categoria in categorias:
            try:
                archivos_categoria = []
                
                if hasattr(manager, 'obtener_archivos'):
                    archivos_categoria = manager.obtener_archivos(contrato_id, categoria)
                elif hasattr(manager, 'get_archivos'):
                    archivos_categoria = manager.get_archivos(contrato_id, categoria)
                elif hasattr(manager, f'get_{categoria.lower()}'):
                    metodo = getattr(manager, f'get_{categoria.lower()}')
                    archivos_categoria = metodo(contrato_id)
                elif hasattr(manager, f'obtener_{categoria.lower()}'):
                    metodo = getattr(manager, f'obtener_{categoria.lower()}')
                    archivos_categoria = metodo(contrato_id)
                else:
                    continue
                
                if archivos_categoria:
                    for archivo in archivos_categoria:
                        if isinstance(archivo, dict):
                            archivo_data = archivo
                        else:
                            archivo_data = {
                                'id': getattr(archivo, 'id', 0),
                                'nombre_archivo': getattr(archivo, 'nombre_archivo', getattr(archivo, 'nombre', 'desconocido')),
                                'categoria': categoria,
                                'tamaño_bytes': getattr(archivo, 'tamaño_bytes', getattr(archivo, 'tamaño', 0)),
                                'contenido': getattr(archivo, 'contenido', getattr(archivo, 'data', b''))
                            }
                        archivos.append(archivo_data)
                        
            except Exception:
                continue
        
        return archivos
        
    except Exception as e:
        return []

def buscar_contratos_avanzada(manager, texto_busqueda):
    """✅ BÚSQUEDA MEJORADA: Búsqueda avanzada en múltiples campos"""
    try:
        texto_busqueda = texto_busqueda.strip().upper()
        if not texto_busqueda:
            return []
        
        # Intentar diferentes estrategias de búsqueda
        resultados_finales = []
        contratos_vistos = set()
        
        # Estrategia 1: Búsqueda por número exacto de contrato
        try:
            filtros = {'numero_contrato': texto_busqueda}
            resultados = manager.buscar_contratos_pemex(filtros)
            if resultados:
                for contrato in resultados:
                    if contrato['id'] not in contratos_vistos:
                        resultados_finales.append(contrato)
                        contratos_vistos.add(contrato['id'])
        except Exception:
            pass
        
        # Estrategia 2: Búsqueda por contratista (coincidencia parcial)
        try:
            if hasattr(manager, 'buscar_contratos_like'):
                resultados = manager.buscar_contratos_like(texto_busqueda)
                if resultados:
                    for contrato in resultados:
                        if contrato['id'] not in contratos_vistos:
                            resultados_finales.append(contrato)
                            contratos_vistos.add(contrato['id'])
        except Exception:
            pass
        
        # Estrategia 3: Búsqueda en otros campos
        campos_busqueda = ['contratista', 'area', 'descripcion', 'numero_contrato']
        
        for campo in campos_busqueda:
            try:
                # Buscar cualquier contrato que contenga el texto en este campo
                filtros = {campo: texto_busqueda}
                resultados = manager.buscar_contratos_pemex(filtros)
                
                if resultados:
                    for contrato in resultados:
                        if contrato['id'] not in contratos_vistos:
                            resultados_finales.append(contrato)
                            contratos_vistos.add(contrato['id'])
            except Exception:
                continue
        
        # Estrategia 4: Si es un número, buscar también como subcadena
        if re.fullmatch(r"\d+", texto_busqueda) and len(texto_busqueda) > 3:
            try:
                # Buscar contratos cuyo número contenga estos dígitos
                filtros = {'numero_contrato': texto_busqueda}
                resultados = manager.buscar_contratos_pemex(filtros)
                
                if resultados:
                    for contrato in resultados:
                        if contrato['id'] not in contratos_vistos:
                            resultados_finales.append(contrato)
                            contratos_vistos.add(contrato['id'])
            except Exception:
                pass
        
        return resultados_finales
        
    except Exception as e:
        return []

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
    usuario_nombre = st.session_state.get("nombre", "").upper()
    st.markdown(f"<div class='usuario-info'>👤 Usuario: {usuario_nombre}</div>", unsafe_allow_html=True)

    # --- Buscador ---
    st.markdown("---")
    st.markdown("### 🔍 Búsqueda de Contratos")
    
    busqueda = st.text_input(
        "Buscar por número de contrato, contratista o palabra clave:",
        placeholder="Ej: 12345, PEMEX, servicios, mantenimiento...",
        key="busqueda_contratos"
    ).strip()

    # ==================================================
    #  MODO BASE DE DATOS POSTGRESQL
    # ==================================================
    usuario_id = st.session_state.get("usuario", "").upper()
    manager = get_db_manager_por_usuario(usuario_id)
    
    if not manager:
        st.error("❌ No se pudo conectar a la base de datos PostgreSQL")
        st.info("💡 Verifica que DATABASE_URL esté configurada en los secrets")
    else:
        # Usar session state para mantener resultados entre búsquedas
        if 'contratos_encontrados' not in st.session_state:
            st.session_state.contratos_encontrados = []
        if 'contrato_seleccionado' not in st.session_state:
            st.session_state.contrato_seleccionado = None
        if 'archivos_cargados' not in st.session_state:
            st.session_state.archivos_cargados = []
        
        # Realizar búsqueda si hay texto
        if busqueda:
            with st.spinner("🔍 Buscando contratos..."):
                resultados = buscar_contratos_avanzada(manager, busqueda)
                st.session_state.contratos_encontrados = resultados
        
        # Mostrar resultados
        if st.session_state.contratos_encontrados:
            st.markdown("---")
            st.markdown(f"### 📂 Contratos Encontrados ({len(st.session_state.contratos_encontrados)})")
            
            # Selección de contrato
            if len(st.session_state.contratos_encontrados) > 1:
                seleccion = st.selectbox(
                    "Selecciona un contrato para ver sus archivos:",
                    st.session_state.contratos_encontrados,
                    format_func=lambda c: f"{c.get('numero_contrato', 'N/A')} - {c.get('contratista', 'Sin nombre')}",
                    key="select_contrato_db"
                )
                if seleccion:
                    st.session_state.contrato_seleccionado = seleccion
            else:
                seleccion = st.session_state.contratos_encontrados[0]
                st.session_state.contrato_seleccionado = seleccion
                st.info(f"📄 Contrato encontrado: {seleccion.get('numero_contrato', 'N/A')} - {seleccion.get('contratista', 'Sin nombre')}")
        
        # Mostrar detalles del contrato seleccionado
        if st.session_state.contrato_seleccionado:
            contrato_info = st.session_state.contrato_seleccionado
            contrato_id = contrato_info.get('id')
            
            st.markdown(f"<div class='carpeta-header'>📁 CONTRATO: {contrato_info.get('numero_contrato', 'N/A')}</div>", unsafe_allow_html=True)
            
            # Botón para cargar archivos
            if st.form_submit_button("📂 CARGAR ARCHIVOS DEL CONTRATO", use_container_width=True):
                with st.spinner("🔍 Cargando archivos..."):
                    archivos = obtener_archivos_por_contrato(manager, contrato_id)
                    st.session_state.archivos_cargados = archivos
            
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
                st.write(f"- **Fecha Inicio:** {contrato_info.get('fecha_inicio', 'No especificado')}")
            
            # Mostrar archivos si están cargados
            if st.session_state.archivos_cargados:
                st.markdown("---")
                st.markdown(f"### 📎 Archivos del Contrato ({len(st.session_state.archivos_cargados)} encontrados)")
                
                # Agrupar archivos por categoría
                archivos_por_categoria = {}
                for archivo in st.session_state.archivos_cargados:
                    categoria = archivo.get('categoria', 'OTROS')
                    if categoria not in archivos_por_categoria:
                        archivos_por_categoria[categoria] = []
                    archivos_por_categoria[categoria].append(archivo)
                
                # Definir orden de visualización
                orden_categorias = ['CONTRATO', 'CEDULAS', 'ANEXOS', 'SOPORTES FISICOS', 'OTROS']
                
                for categoria in orden_categorias:
                    if categoria in archivos_por_categoria:
                        # Icono según categoría
                        iconos = {
                            'CONTRATO': '📄',
                            'CEDULAS': '📋',
                            'ANEXOS': '📎',
                            'SOPORTES FISICOS': '📂',
                            'OTROS': '📁'
                        }
                        icono = iconos.get(categoria, '📁')
                        
                        st.markdown(f"#### {icono} {categoria} ({len(archivos_por_categoria[categoria])} archivos)")
                        
                        for archivo in archivos_por_categoria[categoria]:
                            size_bytes = archivo.get('tamaño_bytes', 0)
                            size_mb = size_bytes / 1024 / 1024 if size_bytes > 0 else 0
                            nombre_archivo = archivo.get('nombre_archivo', 'archivo_sin_nombre')
                            archivo_id = archivo.get('id', '0')
                            contenido = archivo.get('contenido', b'')
                            
                            # Crear un contenedor para el archivo
                            st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{nombre_archivo}**")
                                if size_mb > 0:
                                    st.markdown(f"*Tamaño: {size_mb:.2f} MB*")
                                else:
                                    st.markdown(f"*Tamaño: Desconocido*")
                            
                            with col2:
                                # ✅ BOTÓN DE DESCARGA DENTRO DEL FORM - SOLUCIÓN DEFINITIVA
                                if contenido:
                                    # ID único para este archivo
                                    unique_id = f"download_{contrato_id}_{categoria}_{archivo_id}"
                                    
                                    # Convertir a base64
                                    b64 = base64.b64encode(contenido).decode()
                                    
                                    # Crear enlace de descarga oculto
                                    st.markdown(f'''
                                    <div class="download-link">
                                        <a id="{unique_id}_link" href="data:application/octet-stream;base64,{b64}" 
                                           download="{nombre_archivo}" style="display:none;">
                                        </a>
                                    </div>
                                    ''', unsafe_allow_html=True)
                                    
                                    # Botón que activa JavaScript para descargar
                                    if st.form_submit_button("📥 Descargar", 
                                                            key=f"btn_{unique_id}",
                                                            use_container_width=True):
                                        # Inyectar JavaScript para simular clic en enlace
                                        js_code = f'''
                                        <script>
                                        (function() {{
                                            var link = document.getElementById('{unique_id}_link');
                                            if (link) {{
                                                link.click();
                                            }}
                                        }})();
                                        </script>
                                        '''
                                        st.components.v1.html(js_code, height=0)
                                else:
                                    st.warning("Sin contenido")
                            
                            st.markdown("</div>", unsafe_allow_html=True)
            elif st.session_state.archivos_cargados == []:
                st.info("ℹ️ Presiona 'CARGAR ARCHIVOS DEL CONTRATO' para ver los archivos disponibles.")

    # --- Botones de acción ---
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        actualizar = st.form_submit_button("🔄 ACTUALIZAR", use_container_width=True)
    
    with col2:
        limpiar = st.form_submit_button("🗑️ LIMPIAR BÚSQUEDA", use_container_width=True)
    
    with col3:
        nueva_busqueda = st.form_submit_button("🔍 NUEVA BÚSQUEDA", use_container_width=True)
    
    # Manejar acciones de los botones
    if actualizar:
        st.rerun()
    
    if limpiar:
        st.session_state.contratos_encontrados = []
        st.session_state.contrato_seleccionado = None
        st.session_state.archivos_cargados = []
        st.rerun()
    
    if nueva_busqueda:
        st.session_state.contratos_encontrados = []
        st.session_state.contrato_seleccionado = None
        st.session_state.archivos_cargados = []
        st.rerun()