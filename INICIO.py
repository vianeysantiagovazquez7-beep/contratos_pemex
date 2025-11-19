import streamlit as st
import json
from pathlib import Path
from hashlib import sha256
import warnings
import base64
import re

from core.config import SYSTEM_READY, UPLOAD_DIR, OUTPUT_DIR, TEMPLATE_PATH, timestamp
from core.ocr_utils import pdf_to_text
from core.text_processing import extract_contract_data
from core.excel_utils import load_excel, save_excel
from core.ui_config import aplicar_estilo_global

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.reader.drawings")

# === CONFIGURACIÓN DE RUTAS ===
assets_dir = Path(__file__).parent / "assets"
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

# === Página en modo wide ===
st.set_page_config(layout="wide")

# === SESSION STATE ===
for key, default in {
    "autenticado": False,
    "usuario": "",
    "nombre": "",
    "datos_contrato": {},
    "ultimo_pdf_temp": "",
    "ultimo_guardado": "",
    "texto_extraido": "",
    "anexos_detectados": [],
    "procesamiento_completado": False,
    "excel_generado": None,
    "excel_filename": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# === CARGAR USUARIOS ===
def cargar_usuarios():
    ruta = Path("usuarios.json")
    if not ruta.exists():
        st.error("No se encontró el archivo usuarios.json")
        st.stop()
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    usuarios = {}
    for u in data:
        usuario = u.get("usuario", "").strip().upper()
        password_raw = u.get("password", "") or ""
        password_hash = sha256(password_raw.encode()).hexdigest()
        usuarios[usuario] = {
            "password_hash": password_hash,
            "nombre": u.get("nombre", "").strip().upper()
        }
    return usuarios

USERS = cargar_usuarios()

# === AUTENTICACIÓN ===
def autenticar(usuario: str, password: str):
    if not usuario:
        return False, None
    user_data = USERS.get(usuario.strip().upper())
    if not user_data:
        return False, None
    hashed = sha256(password.encode()).hexdigest()
    if user_data["password_hash"] == hashed:
        return True, user_data["nombre"]
    return False, None

# === DETECCIÓN MEJORADA DE ANEXOS ===
def detectar_anexos_robusta(texto):
    """
    Detección robusta de anexos que captura específicamente los códigos entre comillas
    y evita falsos positivos como 'ANEXO' o palabras incompletas
    """
    # Convertir a mayúsculas para consistencia
    texto_upper = texto.upper()
    
    anexos_detectados = []
    
    # Patrón principal: busca "Anexo" seguido de comillas y contenido entre ellas
    patron_principal = r'ANEXO\s+[“”"\'´`]+\s*([A-Z0-9\-]+)\s*[“”"\'´`]+'
    
    # Patrón secundario: para casos sin comillas pero con formato claro
    patron_secundario = r'ANEXO\s+([A-Z]{1,3}(?:-[A-Z0-9]{1,3})?)(?:\s|\.|\,|\:|$)'
    
    # Patrón para anexos conocidos específicos
    anexos_conocidos = ["A", "AP", "B", "B-1", "BDE", "C", "CN", "DT-9", "E", "F", 
                       "FORMA", "GARANTÍAS", "GNR", "I", "II", "IV", "MMRDD", "O", 
                       "PACMA", "PUE", "SSPA"]
    
    # Buscar con patrón principal (comillas)
    matches_principal = re.findall(patron_principal, texto_upper)
    for match in matches_principal:
        anexo = match.strip()
        if anexo and anexo not in anexos_detectados:
            anexos_detectados.append(anexo)
    
    # Buscar con patrón secundario (sin comillas pero formato claro)
    matches_secundario = re.findall(patron_secundario, texto_upper)
    for match in matches_secundario:
        anexo = match.strip()
        # Validar que sea un anexo válido (esté en la lista de conocidos o tenga formato válido)
        if (anexo in anexos_conocidos or 
            re.match(r'^[A-Z]{1,3}(?:-[A-Z0-9]{1,3})?$', anexo)) and \
           anexo not in anexos_detectados:
            anexos_detectados.append(anexo)
    
    # Buscar específicamente anexos conocidos que puedan aparecer sin formato estándar
    for anexo_conocido in anexos_conocidos:
        # Patrón que busca el anexo conocido con contexto de "ANEXO"
        patron_especifico = rf'ANEXO\s+(?:[“]\"\'´`]*\s*)?{re.escape(anexo_conocido)}(?:\s*[“”"\'´`])?(?:\s|\.|\,|\:|$)'
        if re.search(patron_especifico, texto_upper) and anexo_conocido not in anexos_detectados:
            anexos_detectados.append(anexo_conocido)
    
    # Eliminar posibles duplicados y ordenar
    anexos_detectados = sorted(list(set(anexos_detectados)))
    
    return anexos_detectados

# === FUNCIÓN PARA GENERAR EXCEL ===
def generar_excel_contrato():
    """Genera el archivo Excel y lo prepara para descarga"""
    d = st.session_state.get("datos_contrato")
    if not d:
        st.warning("⚠️ No hay datos para generar Excel.")
        return False
    
    if not TEMPLATE_PATH.exists():
        st.error("❌ No se encontró la plantilla Excel.")
        return False
    
    try:
        wb = load_excel(TEMPLATE_PATH)
        sh = wb.active

        # Mapeo de datos al Excel
        sh["B6"] = d.get("area", "")
        sh["B7"] = d.get("contratista", "")
        sh["K7"] = d.get("contrato", "")
        sh["B8"] = f"DESCRIPCIÓN DEL CONTRATO: {d.get('objeto', '')}"
        sh["C13"] = d.get("monto", "")
        sh["F13"] = d.get("plazo", "")

        # Inserción de anexos en celdas B29 a B59
        anexos = d.get("anexos", [])
        for idx, anexo in enumerate(anexos):
            if idx < 31:  # B29 a B59 = 31 celdas
                sh[f"B{29+idx}"] = f"ANEXO \"{anexo}\""

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUTPUT_DIR / f"CEDULA_LIBRO_BLANCO_{timestamp()}.xlsx"
        save_excel(wb, out)

        # Guardar el archivo en session state para descarga
        with open(out, "rb") as f:
            st.session_state["excel_generado"] = f.read()
        st.session_state["excel_filename"] = out.name
        
        return True
    except Exception as e:
        st.error(f"❌ Error al generar Excel: {e}")
        return False

# === LOGIN === (NO TOCAR)
if not st.session_state.autenticado:
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/jpeg;base64,{fondo_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        div[data-testid="stForm"] {{
            background: rgba(255, 255, 255, 0.85);
            border: 3px solid #d4af37;
            border-radius: 20px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.25);
            backdrop-filter: blur(15px);
            padding: 60px 50px;
            width: 70%;
            max-width: 900px;
            margin: auto;
        }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #6b0012 0%, #40000a 100%);
            color: white;
        }}
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}
        div.stButton > button:first-child {{
            background-color: #d4af37;
            color: black;
            font-weight: 600;
            border-radius: 10px;
            border: none;
            height: 45px;
        }}
        div.stButton > button:first-child:hover {{
            background-color: #b38e2f;
            color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        if logo_base64:
            st.markdown(
                f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='230'></div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            "<h2 style='font-family:Montserrat;color:#1c1c1c;text-align:center;'>🔐 SISTEMA DE CONTRATOS PEMEX</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h4 style='font-family:Poppins;color:#000;text-align:center;background:white;padding:6px 10px;border-radius:8px;display:inline-block;'>INICIO DE SESIÓN</h4>",
            unsafe_allow_html=True,
        )

        login_usuario = st.text_input("👤 NÚMERO DE FICHA", key="login_usuario", placeholder="Ingresa tu número de ficha")
        login_password = st.text_input("🔒 CONTRASEÑA", type="password", key="login_password", placeholder="Ingresa tu contraseña")
        submit = st.form_submit_button("INICIAR SESIÓN", use_container_width=True)

        if submit:
            ok, nombre = autenticar(login_usuario, login_password)
            if ok:
                st.session_state.autenticado = True
                st.session_state.usuario = login_usuario.strip().upper()
                st.session_state.nombre = nombre or ""
                st.success(f"Bienvenido {st.session_state.nombre}")
                base_dir = Path("data") / st.session_state.nombre.upper()
                if not base_dir.exists():
                    for carpeta in [
                        base_dir / "CONTRATOS",
                        base_dir / "CONTRATOS" / "SOPORTES FISICOS",
                        base_dir / "CONTRATOS" / "CEDULAS",
                        base_dir / "CONTRATOS" / "ANEXOS",
                        base_dir / "TEMP",
                    ]:
                        carpeta.mkdir(parents=True, exist_ok=True)
                else:
                    st.info("🔹 Carpeta personal existente. Acceso concedido.")
            else:
                st.error("Credenciales incorrectas.")
    st.stop()

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
</style>
""", unsafe_allow_html=True)

# ==================================================
#  FORMULARIO PRINCIPAL (UN SOLO FORM)
# ==================================================
with st.form("form_contratos", clear_on_submit=False):

    if logo_base64:
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/jpeg;base64,{logo_base64}' width='200'></div>",
            unsafe_allow_html=True
        )

    st.markdown("<h2 style='text-align:center;'>SISTEMA DE PROCESAMIENTO DE CONTRATOS PEMEX</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>📘 CÉDULA LIBRO BLANCO</h4>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📤 Subir contrato PDF", type=["pdf"])

    datos = st.session_state.get("datos_contrato", {})

    col1, col2 = st.columns(2, gap="large")
    with col1:
        area = st.text_input("Área:", datos.get("area",""))
        contrato = st.text_input("Número de contrato:", datos.get("contrato",""))
        contratista = st.text_input("Contratista:", datos.get("contratista",""))

    with col2:
        monto = st.text_input("Monto del contrato:", datos.get("monto",""))
        plazo = st.text_input("Plazo (días):", datos.get("plazo",""))
        objeto = st.text_area("Descripción del contrato:", datos.get("objeto",""), height=130)

    # Sección de anexos detectados
    st.markdown("---")
    st.markdown("<div class='anexo-header'>📎 ANEXOS DETECTADOS</div>", unsafe_allow_html=True)
    
    anexos_detectados = st.session_state.get("anexos_detectados", [])
    if anexos_detectados:
        st.markdown("<div class='resultado-container'>", unsafe_allow_html=True)
        st.success(f"✅ **{len(anexos_detectados)} ANEXOS IDENTIFICADOS:**")
        
        # Mostrar anexos en formato de lista ordenada
        for i, anexo in enumerate(anexos_detectados, 1):
            st.markdown(f"<div class='anexo-item'>📄 ANEXO \"{anexo}\"</div>", unsafe_allow_html=True)
        
        st.info(f"**Nota:** Los anexos se insertarán automáticamente en las celdas B29-B59 del Excel")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ **No se han detectado anexos.** Procesa un contrato para identificar anexos automáticamente.")

    datos_editados = {
        "area": area,
        "contrato": contrato,
        "contratista": contratista,
        "monto": monto,
        "plazo": plazo,
        "objeto": objeto,
        "anexos": anexos_detectados
    }

    st.session_state["datos_contrato"] = datos_editados

    st.markdown("---")

    # Botones de acción
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        procesar = st.form_submit_button("🚀 Procesar contrato", use_container_width=True)
    with b2:
        guardar = st.form_submit_button("💾 Guardar contrato", use_container_width=True)
    with b3:
        generar_excel_btn = st.form_submit_button("📊 Generar Excel", use_container_width=True)
    with b4:
        revisar_ocr = st.form_submit_button("🔍 Revisar OCR", use_container_width=True)

    # ========= PROCESAMIENTO DENTRO DEL FORM =========
    if procesar:
        if not uploaded_file:
            st.warning("⚠️ Sube un PDF antes de procesar.")
        else:
            with st.spinner("🔄 Procesando OCR y extrayendo datos..."):
                temp_path = Path(UPLOAD_DIR) / uploaded_file.name
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                texto = pdf_to_text(temp_path)
                st.session_state["texto_extraido"] = texto

                if texto.startswith("[ERROR]"):
                    st.error(f"❌ Error en OCR: {texto}")
                else:
                    datos_extraidos = extract_contract_data(texto) or {}

                    # Limpieza de campos no requeridos
                    datos_extraidos.pop("partida", None)
                    datos_extraidos.pop("observaciones", None)

                    # Extracción mejorada de plazo
                    plazo_regex = re.search(
                        r"(?:plazo del contrato|plazo(?:\s+total)?|tendrá un plazo|plazo es de)\s*(?:de\s*)?(\d{1,4})\s*(?:d[ií]as?)",
                        texto,
                        flags=re.IGNORECASE
                    )
                    if plazo_regex:
                        datos_extraidos["plazo"] = plazo_regex.group(1)
                    else:
                        plazo_alt = re.search(r"(\d{1,4})\s*d[ií]as", texto, flags=re.IGNORECASE)
                        datos_extraidos["plazo"] = plazo_alt.group(1) if plazo_alt else ""

                    # Detección ROBUSTA de anexos
                    anexos_detectados = detectar_anexos_robusta(texto)
                    st.session_state["anexos_detectados"] = anexos_detectados
                    datos_extraidos["anexos"] = anexos_detectados

                    st.session_state["datos_contrato"] = datos_extraidos
                    st.session_state["procesamiento_completado"] = True
                    
                    st.success("✅ Procesamiento completado exitosamente!")
                    st.rerun()

    # ========= GUARDAR DENTRO DEL FORM =========
    if guardar:
        if not st.session_state.get("datos_contrato"):
            st.warning("⚠️ No hay datos para guardar.")
        else:
            d = st.session_state["datos_contrato"]
            owner = st.session_state.get("nombre","ANONIMO")
            
            # === EXTRACCIÓN Y FORMATEO DEL NÚMERO DE CONTRATO ===
            numero_contrato = d.get("contrato", "").strip()
            
            # Extraer solo dígitos del número de contrato
            solo_digitos = re.sub(r'\D', '', numero_contrato)
            
            # Verificar si comienza con 64 y tiene al menos 9 dígitos (64 + 7)
            if solo_digitos.startswith('64') and len(solo_digitos) >= 9:
                # Tomar solo los primeros 9 dígitos (64 + 7)
                numero_formateado = solo_digitos[:9]
            else:
                # Si no cumple el formato, usar el número original sin espacios
                numero_formateado = numero_contrato.replace(" ", "_").upper() or "SIN_NUM"
            
            # === EXTRACCIÓN DE PALABRAS CLAVE ===
            objeto_contrato = d.get("objeto", "").upper()
            palabras_clave = []
            
            # Lista de palabras comunes a excluir
            palabras_excluir = {"DE", "PARA", "Y", "LOS", "LAS", "DEL", "EL", "LA", "EN", "CON", 
                               "POR", "SIN", "AL", "SE", "SU", "SUS", "UN", "UNA", "UNOS", "UNAS",
                               "ES", "SON", "QUE", "A", "O", "E", "I", "U", "ME", "TE", "LE", "NOS",
                               "CONTRATO", "SERVICIO", "SUMINISTRO", "OBRA", "MANTENIMIENTO"}
            
            if objeto_contrato:
                # Extraer palabras de 4 o más letras que no estén en la lista de exclusión
                palabras = re.findall(r'\b[A-Z]{4,}\b', objeto_contrato)
                for palabra in palabras:
                    if (palabra not in palabras_excluir and 
                        len(palabra) >= 4 and 
                        palabra not in palabras_clave):
                        palabras_clave.append(palabra)
                
                # Limitar a 3 palabras clave máximo para evitar nombres demasiado largos
                palabras_clave = palabras_clave[:3]
            
            # Crear sufijo con palabras clave
            sufijo_clave = "_" + "_".join(palabras_clave) if palabras_clave else ""
            
            # Crear UID con número de contrato formateado y palabras clave
            uid = f"CONTRATO_{numero_formateado}{sufijo_clave}"
            
            base = Path("data") / owner.upper() / "CONTRATOS" / uid
            for sub in ["CEDULAS","ANEXOS","SOPORTES FISICOS"]:
                (base/sub).mkdir(parents=True, exist_ok=True)

            if uploaded_file:
                with open(base / "SOPORTES FISICOS" / uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            # Guardar también las palabras clave en los metadatos
            d["palabras_clave"] = palabras_clave
            d["numero_contrato_formateado"] = numero_formateado
            with open(base/"metadatos.json","w",encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)

            mensaje_guardado = f"✅ Contrato guardado en: {base}"
            if palabras_clave:
                mensaje_guardado += f"\n🔑 Palabras clave extraídas: {', '.join(palabras_clave)}"
            
            st.success(mensaje_guardado)

    # ========= GENERAR EXCEL DENTRO DEL FORM =========
    if generar_excel_btn:
        if generar_excel_contrato():
            st.success("✅ Excel generado exitosamente! Revisa la sección de descarga abajo.")
            st.rerun()

    # ========= REVISAR OCR DENTRO DEL FORM =========
    if revisar_ocr:
        texto = st.session_state.get("texto_extraido","")
        if not texto:
            st.info("ℹ️ No hay OCR disponible. Procesa un contrato primero.")
        else:
            st.markdown("<div class='resultado-container'>", unsafe_allow_html=True)
            st.subheader("🔍 Texto Extraído por OCR")
            st.text_area(
                "Texto OCR completo", 
                texto[:50000] + ("...[texto truncado para visualización]" if len(texto)>50000 else ""), 
                height=30000,
                key="ocr_text_area"
            )
            st.markdown("</div>", unsafe_allow_html=True)


#  SECCIÓN DE DESCARGA FUERA DEL FORM (por restricciones de Streamlit)

if st.session_state.get("excel_generado"):
    st.markdown("---")
    st.markdown("<div class='descarga-container'>", unsafe_allow_html=True)
    st.success("📊 **EXCEL GENERADO EXITOSAMENTE**")
    
    st.download_button(
        label="📥 DESCARGAR ARCHIVO EXCEL",
        data=st.session_state["excel_generado"],
        file_name=st.session_state["excel_filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.markdown("</div>", unsafe_allow_html=True)