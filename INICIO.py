# INICIO.py
import streamlit as st
import json
from pathlib import Path
from hashlib import sha256
import base64

# === CONFIGURACIÓN INICIAL ===
st.set_page_config(
    page_title="Sistema de Contratos PEMEX",
    page_icon="🏢",
    layout="centered"
)

# Inicializar estado de sesión
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""
    st.session_state.nombre = ""

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

# === CARGAR USUARIOS ===
def cargar_usuarios():
    ruta = Path("usuarios.json")
    if not ruta.exists():
        st.error("No se encontró el archivo de usuarios")
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
            "nombre": u.get("nombre", "").strip().title()
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

# === ESTILOS ===
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/jpeg;base64,{fondo_base64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

.main-container {{
    background: rgba(255,255,255,0.95);
    border-radius: 20px;
    padding: 40px;
    margin: 50px auto;
    max-width: 500px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    border: 3px solid #d4af37;
}}

.logo-container {{
    text-align: center;
    margin-bottom: 30px;
}}

.welcome-title {{
    text-align: center;
    color: #6b0012;
    font-weight: bold;
    margin-bottom: 10px;
}}

.welcome-subtitle {{
    text-align: center;
    color: #666;
    margin-bottom: 30px;
}}

.stTextInput input {{
    background: rgba(255,255,255,0.9);
    border: 2px solid #d4af37;
    border-radius: 10px;
    padding: 12px;
}}

.stButton button {{
    background-color: #d4af37;
    color: black;
    font-weight: bold;
    border-radius: 10px;
    border: none;
    padding: 12px 24px;
    width: 100%;
    font-size: 16px;
}}
.stButton button:hover {{
    background-color: #b38e2f;
    color: white;
}}

.footer {{
    text-align: center;
    margin-top: 30px;
    color: #666;
    font-size: 0.9em;
}}
</style>
""", unsafe_allow_html=True)

# === INTERFAZ DE LOGIN ===
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# Logo
if logo_base64:
    st.markdown(
        f"<div class='logo-container'><img src='data:image/jpeg;base64,{logo_base64}' width='120'></div>",
        unsafe_allow_html=True
    )

# Título
st.markdown("<h1 class='welcome-title'>SISTEMA DE CONTRATOS PEMEX</h1>", unsafe_allow_html=True)
st.markdown("<p class='welcome-subtitle'>Ingrese sus credenciales para acceder al sistema</p>", unsafe_allow_html=True)

# Formulario de login
with st.form("login_form"):
    usuario = st.text_input("👤 Usuario", placeholder="Ingrese su usuario...")
    password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña...")
    
    submit = st.form_submit_button("🚀 INICIAR SESIÓN", use_container_width=True)

# Procesar login
if submit:
    if not usuario or not password:
        st.error("⚠️ Por favor ingrese usuario y contraseña")
    else:
        with st.spinner("Verificando credenciales..."):
            autenticado, nombre = autenticar(usuario, password)
            
            if autenticado:
                st.session_state.autenticado = True
                st.session_state.usuario = usuario.strip().upper()
                st.session_state.nombre = nombre
                st.success(f"✅ Bienvenido {nombre}")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")

# Footer
st.markdown("<div class='footer'>Sistema de Gestión de Contratos PEMEX</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Redirección si está autenticado
if st.session_state.get("autenticado", False):
    st.switch_page("pages/1_PROCESAMIENTO.py")