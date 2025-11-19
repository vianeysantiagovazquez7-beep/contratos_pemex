import base64
from pathlib import Path
import streamlit as st

def _imagen_base64(path: str) -> str:
    """Convierte una imagen (jpg, jpeg o png) a base64 seguro para Streamlit."""
    p = Path(path)
    if not p.exists():
        st.warning(f"No se encontró la imagen: {path}")
        return ""
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    with open(p, "rb") as f:
        data = f.read()
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

def aplicar_estilo_global(fondo_path="assets/fondo.jpg", logo_path="assets/logo.jpg", login=False):
    """Aplica el diseño visual global a toda la app."""
    fondo_url = _imagen_base64(fondo_path)
    logo_url = _imagen_base64(logo_path)

    css = f"""
    <style>
        /* ===== Fondo general ===== */
        .stApp {{
            background-image: url("{fondo_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #222;
        }}

        /* ===== Barra lateral ===== */
        [data-testid="stSidebar"] {{
            background-color: #800000 !important;
        }}
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}

        /* ===== Contenedor principal ===== */
        .main-container {{
            background-color: rgba(255, 255, 255, 0.85);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            margin-top: 30px;
        }}

        /* ===== Botones dorados ===== */
        div.stButton > button {{
            background-color: #b8860b;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            transition: 0.3s;
        }}
        div.stButton > button:hover {{
            background-color: #d4af37;
            color: #000;
        }}

        /* ===== Botón login (único diferente) ===== */
        .login-btn > button {{
            background-color: #800000 !important;
            color: white !important;
            font-weight: bold;
        }}
        .login-btn > button:hover {{
            background-color: #a52a2a !important;
            color: #fff !important;
        }}

        /* ===== Logotipo principal ===== */
        .header-logo {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .header-logo img {{
            width: 110px;
        }}

        /* ===== Logo centrado solo para login ===== */
        .login-logo {{
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }}

        /* ===== Input estilizado ===== */
        .stTextInput>div>div>input {{
            background-color: rgba(255,255,255,0.9);
            border-radius: 5px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    # Logo fijo en la esquina superior izquierda (solo fuera del login)
    if not login:
        st.markdown(
            f"""
            <div class="header-logo">
                <img src="{logo_url}">
                <h2 style="color:#800000;">📄 SISTEMA DE PROCESAMIENTO DE CONTRATOS PEMEX</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div class="login-logo"><img src="{logo_url}" width="220"></div>""",
            unsafe_allow_html=True,
        )