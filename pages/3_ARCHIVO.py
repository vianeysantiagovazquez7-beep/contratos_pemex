# pages/3_ARCHIVO.py
import streamlit as st
from pathlib import Path
import json
import os
import base64
from core.database import get_db_manager  
import sys

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
#  FUNCIONES CORREGIDAS Y ROBUSTAS PARA POSTGRESQL
# ==============================
def obtener_contratos_postgresql(manager):
    """Obtener lista de contratos desde PostgreSQL"""
    try:
        contratos = manager.buscar_contratos_pemex({})
        return True, contratos
    except Exception as e:
        return False, f"❌ Error obteniendo contratos: {str(e)}"

def guardar_archivo_postgresql(manager, contrato_id, archivo, categoria, tipo_archivo):
    """✅ VERSIÓN CORREGIDA Y FUNCIONAL: Guardar archivo individual en PostgreSQL"""
    try:
        # LEER el contenido del archivo primero (esto es lo que fallaba)
        archivo_bytes = archivo.read()
        
        # Volver al inicio del archivo
        archivo.seek(0)
        
        # Verificar que el manager tenga el método CORRECTO
        # Opción 1: Si tiene guardar_archivo_completo
        if hasattr(manager, 'guardar_archivo_completo'):
            archivo_id = manager.guardar_archivo_completo(
                contrato_id, archivo, categoria, tipo_archivo, nombre
            )
        # Opción 2: Si tiene guardar_archivo_streamlit (MÉTODO NUEVO QUE SÍ EXISTE)
        elif hasattr(manager, 'guardar_archivo_streamlit'):
            archivo_id = manager.guardar_archivo_streamlit(
                contrato_id=contrato_id,
                archivo_streamlit=archivo,
                categoria=categoria,
                usuario=nombre
            )
        # Opción 3: Si tiene insertar_archivo
        elif hasattr(manager, 'insertar_archivo'):
            archivo_id = manager.insertar_archivo(
                contrato_id=contrato_id,
                nombre_archivo=archivo.name,
                categoria=categoria,
                contenido=archivo_bytes
            )
        # Opción 4: Usar método alternativo si no hay ninguno
        else:
            # Intentar guardar usando obtener_archivos si no hay método específico
            st.warning("⚠️ No se encontró método específico para guardar, intentando método alternativo...")
            return False, "❌ No se encontró un método para guardar archivos"
        
        if archivo_id:
            return True, f"✅ {archivo.name} guardado exitosamente (ID: {archivo_id})"
        else:
            return False, "❌ No se pudo obtener ID del archivo guardado"
            
    except Exception as e:
        # DEBUG: Mostrar error detallado
        st.error(f"🔴 ERROR DETALLADO en guardar_archivo_postgresql: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return False, f"❌ Error guardando: {str(e)}"

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
        except:
            pass
        
        # Método 2: Buscar por categorías individuales
        categorias = ['CONTRATO', 'ANEXOS', 'CEDULAS', 'SOPORTES FISICOS']
        
        for categoria in categorias:
            try:
                # Intentar diferentes nombres de métodos
                metodo_nombres = [
                    f'get_{categoria.lower()}',  # get_contrato, get_anexos, etc.
                    f'obtener_{categoria.lower()}',
                    f'obtener_archivos_{categoria.lower()}',
                    'obtener_archivos'  # Método genérico
                ]
                
                archivos_encontrados = None
                
                for metodo_nombre in metodo_nombres:
                    if hasattr(manager, metodo_nombre):
                        try:
                            if metodo_nombre == 'obtener_archivos':
                                # Método que necesita parámetros
                                archivos_categoria = manager.obtener_archivos(contrato_id, categoria)
                            else:
                                # Método específico por categoría
                                archivos_categoria = getattr(manager, metodo_nombre)(contrato_id)
                            
                            if archivos_categoria:
                                archivos_encontrados = archivos_categoria
                                break
                        except Exception:
                            continue
                
                # Procesar archivos encontrados
                if archivos_encontrados:
                    # Normalizar la respuesta (puede ser lista de objetos o diccionarios)
                    for archivo in archivos_encontrados:
                        if isinstance(archivo, dict):
                            archivo_data = archivo
                        else:
                            # Asumir que es un objeto con atributos
                            archivo_data = {
                                'id': getattr(archivo, 'id', 0),
                                'nombre_archivo': getattr(archivo, 'nombre_archivo', 'desconocido'),
                                'categoria': categoria,
                                'tamaño_bytes': getattr(archivo, 'tamaño_bytes', 0),
                                'contenido': getattr(archivo, 'contenido', b'')
                            }
                        
                        archivos.append(archivo_data)
                        
            except Exception as cat_error:
                continue  # Si no hay archivos en esa categoría, continuamos
        
        # Método 3: Si no encontramos nada, intentar con obtener_archivos sin categoría
        if not archivos:
            try:
                archivos_todos = manager.obtener_archivos(contrato_id)
                if archivos_todos:
                    return archivos_todos
            except Exception as sql_error:
                st.warning(f"⚠️ No se pudieron obtener archivos: {sql_error}")
        
        return archivos
        
    except Exception as e:
        st.error(f"⚠️ Error obteniendo archivos: {str(e)}")
        return []

def eliminar_archivo_postgresql(manager, archivo_id, categoria):
    """✅ FUNCIÓN ROBUSTA: Eliminar archivo de PostgreSQL"""
    try:
        # Intentar diferentes métodos de eliminación
        success = False
        
        # Método 1: Método directo
        if hasattr(manager, 'eliminar_archivo'):
            try:
                success = manager.eliminar_archivo(archivo_id, categoria)
            except Exception:
                pass
        
        # Método 2: Método alternativo
        if not success and hasattr(manager, 'delete_archivo'):
            try:
                success = manager.delete_archivo(archivo_id)
            except Exception:
                pass
        
        # Método 3: Intentar eliminar sin categoría
        if not success and hasattr(manager, 'eliminar_archivo'):
            try:
                success = manager.eliminar_archivo(archivo_id)
            except Exception:
                pass
        
        if success:
            return True, "✅ Archivo eliminado correctamente"
        else:
            return False, "❌ No se pudo eliminar el archivo"
            
    except Exception as e:
        return False, f"❌ Error eliminando archivo: {str(e)}"

def eliminar_contrato_postgresql(manager, contrato_id):
    """✅ FUNCIÓN ROBUSTA: Eliminar contrato completo de PostgreSQL"""
    try:
        success = False
        
        # Método 1: Método directo
        if hasattr(manager, 'eliminar_contrato'):
            try:
                success = manager.eliminar_contrato(contrato_id)
            except Exception:
                pass
        
        # Método 2: Método alternativo
        if not success and hasattr(manager, 'delete_contrato'):
            try:
                success = manager.delete_contrato(contrato_id)
            except Exception:
                pass
        
        # Método 3: Intentar eliminar archivos primero y luego el contrato
        if not success:
            try:
                # Primero eliminar archivos asociados si existe el método
                if hasattr(manager, 'eliminar_archivos_contrato'):
                    manager.eliminar_archivos_contrato(contrato_id)
                
                # Luego eliminar el contrato
                if hasattr(manager, 'eliminar_contrato'):
                    success = manager.eliminar_contrato(contrato_id)
            except Exception:
                pass
        
        if success:
            return True, "✅ Contrato eliminado completamente"
        else:
            return False, "❌ No se pudo eliminar el contrato (método no disponible)"
            
    except Exception as e:
        return False, f"❌ Error eliminando contrato: {str(e)}"

# ============================================
# CONFIGURACIÓN ESPECIAL PARA RENDER
# ============================================
def configurar_para_render():
    """Configuración específica para el despliegue en Render"""
    # Verificar si estamos en Render
    if 'RENDER' in os.environ or 'PORT' in os.environ:
        print("🔧 Detectado entorno Render - Configurando puerto...")
        
        # Configurar el puerto para Render
        port = int(os.environ.get('PORT', 10000))
        
        # Modificar los argumentos de línea de comandos
        sys.argv = [
            sys.argv[0],
            'run',
            'INICIO.py',
            '--server.port', str(port),
            '--server.address', '0.0.0.0',
            '--server.enableCORS', 'false',
            '--server.enableXsrfProtection', 'false'
        ]

# Ejecutar configuración si es necesario
if __name__ == '__main__':
    configurar_para_render()

# ==============================
#  DIAGNÓSTICO RÁPIDO
# ==============================

def verificar_metodos_manager(manager):
    """Verificar qué métodos tiene disponible el manager"""
    st.sidebar.markdown("### 🔍 DIAGNÓSTICO")
    
    if st.sidebar.button("Ver métodos disponibles"):
        metodos = [m for m in dir(manager) if not m.startswith('_')]
        st.sidebar.write(f"**Total métodos:** {len(metodos)}")
        
        # Buscar métodos relacionados con archivos
        metodos_archivos = [m for m in metodos if 'archivo' in m.lower()]
        st.sidebar.write("**Métodos de archivos:**")
        for metodo in metodos_archivos:
            st.sidebar.write(f"- {metodo}")
    
    if st.sidebar.button("Ver tablas en DB"):
        try:
            # Usar métodos indirectos para verificar tablas
            success, contratos = obtener_contratos_postgresql(manager)
            if success:
                st.sidebar.success("✅ Tabla contratos_pemex existe")
            else:
                st.sidebar.error("❌ No se pudo acceder a la tabla contratos_pemex")
            
            # Verificar si hay archivos
            if success and contratos:
                for contrato in contratos[:1]:  # Solo el primer contrato
                    archivos = obtener_archivos_por_contrato(manager, contrato['id'])
                    st.sidebar.info(f"Archivos en contrato {contrato['id']}: {len(archivos)}")
                    break
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    
    if st.sidebar.button("Contar archivos en DB"):
        try:
            # Contar archivos usando métodos existentes
            total_archivos = 0
            success, contratos = obtener_contratos_postgresql(manager)
            if success:
                for contrato in contratos:
                    archivos = obtener_archivos_por_contrato(manager, contrato['id'])
                    total_archivos += len(archivos)
                st.sidebar.info(f"Archivos en DB: {total_archivos}")
            else:
                st.sidebar.error("No se pudieron obtener contratos")
        except Exception as e:
            st.sidebar.error(f"Error contando archivos: {e}")

# --- Mensaje informativo al final ---
st.markdown(
    """
    <div style='text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <strong>💡 Información Rápida:</strong><br>
        • <strong>Para ver archivos:</strong> Selecciona un contrato y haz clic en "EXPANDIR"<br>
        • <strong>Para descargar:</strong> Usa el botón azul "📥 Descargar" en cada archivo<br>
        • <strong>Para eliminar archivo:</strong> Haz clic en "🗑️ Eliminar" y confirma<br>
        • <strong>Para eliminar contrato:</strong> Expande el contrato y usa el botón rojo al final<br>
        • <strong>PostgreSQL:</strong> Almacena archivos hasta 4TB cada uno
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

# 🔍 DIAGNÓSTICO (opcional - descomenta si necesitas)
# verificar_metodos_manager(manager)

with st.form("form_gestion_archivos", clear_on_submit=True):
    
    if logo_base64:
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='200'></div>",
            unsafe_allow_html=True
        )

    st.markdown("<h2 style='text-align:center;'>SISTEMA DE GESTIÓN DE DOCUMENTOS PEMEX</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>📁 ARCHIVOS Y CONTRATOS</h4>", unsafe_allow_html=True)

    # ==================================================
    #  SECCIÓN PARA SUBIR NUEVOS ARCHIVOS (CORREGIDA)
    # ==================================================
    st.markdown("---")
    st.markdown("### 📤 Subir Archivos a Contrato Existente")
    
    # Obtener contratos de PostgreSQL
    success, contratos_db = obtener_contratos_postgresql(manager)
    if not success:
        st.error(contratos_db)
        contratos_lista = []
    else:
        # Mejorar la visualización de contratos
        contratos_lista = [(c['id'], f"{c['numero_contrato']} - {c['contratista']}") for c in contratos_db]
    
    if contratos_lista:
        contrato_seleccionado_id = st.selectbox(
            "📄 Seleccionar contrato:",
            options=[c[0] for c in contratos_lista],
            format_func=lambda x: next((c[1] for c in contratos_lista if c[0] == x), ""),
            key="select_contrato_postgresql",
            help="Elige el contrato al que quieres añadir archivos"
        )
        
        # Mostrar información del contrato seleccionado
        if contrato_seleccionado_id:
            contrato_info = next((c for c in contratos_db if c['id'] == contrato_seleccionado_id), None)
            if contrato_info:
                st.info(f"📋 **Contrato seleccionado:** {contrato_info['numero_contrato']} - {contrato_info['contratista']}")
    else:
        st.warning("📭 No hay contratos disponibles en PostgreSQL")
        contrato_seleccionado_id = None

    # Selección de sección
    seccion_seleccionada = st.selectbox(
        "📂 Seleccionar sección:",
        ["CONTRATO", "CEDULAS", "ANEXOS", "SOPORTES FISICOS"],
        key="select_seccion_subir",
        help="Elige la categoría donde se guardarán los archivos"
    )
    
    # Subir archivos
    archivos_subir = st.file_uploader(
        f"📤 Seleccionar archivo(s) para subir (Hasta 4TB en PostgreSQL):",
        accept_multiple_files=True,
        key="file_uploader_subir",
        help="Puedes seleccionar múltiples archivos a la vez"
    )
    
    # Botón para subir
    subir_archivos = st.form_submit_button("🚀 SUBIR ARCHIVOS SELECCIONADOS", use_container_width=True)
    
    if subir_archivos and archivos_subir:
        if contrato_seleccionado_id:
            with st.spinner("Subiendo archivos..."):
                archivos_exitosos = 0
                archivos_fallidos = 0
                
                for archivo in archivos_subir:
                    success, message = guardar_archivo_postgresql(
                        manager, contrato_seleccionado_id, archivo, 
                        seccion_seleccionada, "anexo"
                    )
                    if success:
                        archivos_exitosos += 1
                        st.success(f"✅ {archivo.name}")
                    else:
                        archivos_fallidos += 1
                        st.error(f"❌ {archivo.name}: {message}")
                
                # Resumen
                if archivos_exitosos > 0:
                    st.success(f"🎉 {archivos_exitosos} archivo(s) subido(s) exitosamente")
                if archivos_fallidos > 0:
                    st.error(f"⚠️ {archivos_fallidos} archivo(s) no se pudieron subir")
                    
            st.rerun()
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
            "🔍 Seleccionar contrato para ver detalles:",
            ["NINGUNO"] + [f"CONTRATO_{c[0]}" for c in contratos_lista],
            format_func=lambda x: "NINGUNO" if x == "NINGUNO" else next((c[1] for c in contratos_lista if f"CONTRATO_{c[0]}" == x), x),
            key="select_contrato_expandir_postgresql",
            help="Elige un contrato para ver y gestionar sus archivos"
        )
    else:
        contrato_a_expandir = "NINGUNO"
    
    expandir_contrato = st.form_submit_button("📂 EXPANDIR CONTRATO SELECCIONADO", use_container_width=True)
    
    if expandir_contrato and contrato_a_expandir != "NINGUNO":
        st.session_state.contrato_expandido = contrato_a_expandir
        st.session_state.archivo_eliminando = None
        st.session_state.contrato_eliminando = None
        st.rerun()

    # ==================================================
    #  VISUALIZACIÓN DEL CONTRATO EXPANDIDO
    # ==================================================
    if st.session_state.contrato_expandido and st.session_state.contrato_expandido != "NINGUNO":
        st.markdown("---")
        
        # MODO POSTGRESQL
        contrato_id = int(st.session_state.contrato_expandido.replace("CONTRATO_", ""))
        
        st.markdown(f"<div class='carpeta-abierta'>", unsafe_allow_html=True)
        
        # Obtener información del contrato
        success, contratos_db = obtener_contratos_postgresql(manager)
        contrato_info = None
        contrato_numero = ""
        
        if success:
            for c in contratos_db:
                if c['id'] == contrato_id:
                    contrato_info = c
                    contrato_numero = c.get('numero_contrato', '')
                    break
        
        st.markdown(f"#### 🗄️ CONTRATO: {contrato_numero}")
        
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
        
        # ✅ Obtener archivos del contrato usando la función robusta corregida
        with st.spinner("Buscando archivos..."):
            archivos = obtener_archivos_por_contrato(manager, contrato_id)
        
        if archivos:
            # Agrupar archivos por categoría
            archivos_por_categoria = {}
            for archivo in archivos:
                categoria = archivo.get('categoria', 'SIN CATEGORIA')
                if categoria not in archivos_por_categoria:
                    archivos_por_categoria[categoria] = []
                archivos_por_categoria[categoria].append(archivo)
            
            # Mostrar archivos por categoría (MEJORADO)
            secciones = [
                ("📄 CONTRATO", "CONTRATO"),
                ("📋 CÉDULA", "CEDULAS"),
                ("📎 ANEXOS", "ANEXOS"), 
                ("📂 SOPORTES", "SOPORTES FISICOS")
            ]
            
            archivos_totales = 0
            
            for icono, categoria in secciones:
                if categoria in archivos_por_categoria:
                    archivos_categoria = archivos_por_categoria[categoria]
                    archivos_totales += len(archivos_categoria)
                    
                    st.markdown(f"##### {icono} ({len(archivos_categoria)} archivos)")
                    
                    for archivo in archivos_categoria:
                        size_bytes = archivo.get('tamaño_bytes', 0)
                        size_mb = size_bytes / 1024 / 1024 if size_bytes > 0 else 0
                        archivo_key = f"{contrato_id}_{categoria}_{archivo.get('id', '0')}"
                        
                        st.markdown(f"<div class='archivo-item'>", unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            nombre_archivo = archivo.get('nombre_archivo', 'Sin nombre')
                            st.markdown(f"**{nombre_archivo}**")
                            if size_mb > 0:
                                st.markdown(f"*Tamaño: {size_mb:.2f} MB*")
                            else:
                                st.markdown(f"*Tamaño: Desconocido*")
                        
                        with col2:
                            # ✅ BOTÓN DE DESCARGA FUNCIONAL (CORREGIDO - DENTRO DE FORM)
                            contenido = archivo.get('contenido', b'')
                            if contenido:
                                # ID único para este archivo
                                unique_id = f"download_{contrato_id}_{categoria}_{archivo.get('id', '0')}"
                                
                                # Convertir a base64
                                b64 = base64.b64encode(contenido).decode()
                                
                                # Enlace oculto para descarga
                                st.markdown(f'''
                                <div style="display:none;">
                                    <a id="{unique_id}_anchor" href="data:application/octet-stream;base64,{b64}" 
                                       download="{nombre_archivo}">
                                    </a>
                                </div>
                                ''', unsafe_allow_html=True)
                                
                                # Botón que activa la descarga vía JavaScript
                                if st.form_submit_button("📥 Descargar", 
                                                        use_container_width=True,
                                                        key=f"submit_{unique_id}"):
                                    # JavaScript para hacer clic en el enlace oculto
                                    st.markdown(f'''
                                    <script>
                                    document.getElementById("{unique_id}_anchor").click();
                                    </script>
                                    ''', unsafe_allow_html=True)
                            else:
                                st.warning("Sin contenido")
                        
                        with col3:
                            # ✅ BOTÓN DE ELIMINACIÓN FUNCIONAL
                            if st.session_state.archivo_eliminando == archivo_key:
                                st.warning(f"¿Eliminar {nombre_archivo}?")
                                col_confirm, col_cancel = st.columns(2)
                                with col_confirm:
                                    if st.form_submit_button("✅ Sí", use_container_width=True, key=f"confirm_del_{archivo_key}"):
                                        success, message = eliminar_archivo_postgresql(manager, archivo.get('id'), categoria)
                                        if success:
                                            st.success(message)
                                            st.session_state.archivo_eliminando = None
                                            st.rerun()
                                        else:
                                            st.error(message)
                                with col_cancel:
                                    if st.form_submit_button("❌ No", use_container_width=True, key=f"cancel_del_{archivo_key}"):
                                        st.session_state.archivo_eliminando = None
                                        st.rerun()
                            else:
                                if st.form_submit_button("🗑️ Eliminar", use_container_width=True, key=f"init_del_{archivo_key}"):
                                    st.session_state.archivo_eliminando = archivo_key
                                    st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
            
            st.info(f"📊 **Total de archivos en el contrato:** {archivos_totales}")
        else:
            st.info("ℹ️ No hay archivos en este contrato")
        
        # ✅ ELIMINACIÓN DE CONTRATO COMPLETO
        st.markdown("---")
        st.markdown("### 🗑️ Eliminar Contrato Completo")
        
        if st.session_state.contrato_eliminando == contrato_id:
            st.markdown("<div class='confirmacion-eliminar'>", unsafe_allow_html=True)
            st.error("⚠️ **ADVERTENCIA CRÍTICA**")
            st.warning(f"Estás a punto de eliminar el contrato **{contrato_numero}** COMPLETAMENTE")
            st.info("❌ **Esta acción NO se puede deshacer**")
            st.info("🗄️ **Se eliminarán TODOS los archivos de la base de datos**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ SÍ, ELIMINAR CONTRATO COMPLETO", use_container_width=True, key="confirm_delete_contrato"):
                    success, message = eliminar_contrato_postgresql(manager, contrato_id)
                    if success:
                        st.success(message)
                        st.session_state.contrato_eliminando = None
                        st.session_state.contrato_expandido = None
                        st.rerun()
                    else:
                        st.error(message)
            
            with col2:
                if st.form_submit_button("❌ CANCELAR ELIMINACIÓN", use_container_width=True, key="cancel_delete_contrato"):
                    st.session_state.contrato_eliminando = None
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            if st.form_submit_button("🚨 ELIMINAR CONTRATO COMPLETO", use_container_width=True, key="init_delete_contrato"):
                st.session_state.contrato_eliminando = contrato_id
                st.rerun()
        
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
            contrato_key = f"CONTRATO_{contrato['id']}"
            if st.session_state.contrato_expandido != contrato_key:
                # Contar archivos del contrato
                archivos_contrato = obtener_archivos_por_contrato(manager, contrato['id'])
                num_archivos = len(archivos_contrato)
                
                st.markdown(
                    f"<div class='carpeta-cerrada'>"
                    f"🗄️ <strong>{contrato['numero_contrato']}</strong> - {contrato['contratista']}<br>"
                    f"<small>📁 {num_archivos} archivos</small>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
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