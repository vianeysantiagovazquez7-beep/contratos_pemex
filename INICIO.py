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

# === INTERFAZ DE LOGIN ===
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

        # === AUTENTICACIÓN REAL ===
        if submit:
            login_usuario_upper = login_usuario.strip().upper()
            password_hash_input = sha256(login_password.encode()).hexdigest()

            if login_usuario_upper in USERS:
                if USERS[login_usuario_upper]["password_hash"] == password_hash_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario = login_usuario_upper
                    st.session_state.nombre = USERS[login_usuario_upper]["nombre"]

                    st.success(f"Bienvenido {st.session_state.nombre}")

                    # === NO SE ELIMINÓ TU SISTEMA DE CARPETAS ===
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
                    st.error("Contraseña incorrecta.")
            else:
                st.error("Usuario no encontrado.")

    st.stop()

# Redirección si está autenticado
if st.session_state.get("autenticado", False):
    st.switch_page("pages/1_PAGINA PRINCIPAL.py")
