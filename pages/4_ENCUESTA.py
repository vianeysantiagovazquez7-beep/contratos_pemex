import streamlit as st
import streamlit as st
from pathlib import Path
import re
import base64
import json 
from core.database import get_db_manager_por_usuario
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

def survey():
    st.markdown("---")
    st.subheader("📝 Encuesta de satisfacción (7 preguntas)")
    st.caption("Esto ayuda a validar el sistema con usuarios reales (tu 50% de muestra).")

    opciones_emojis = {
        1: "😠 Totalmente insatisfecho",
        2: "😞 Insatisfecho",
        3: "😐 Neutral",
        4: "🙂 Satisfecho",
        5: "😄 Totalmente satisfecho"
    }
    
    opciones_lista = list(opciones_emojis.values())

    with st.form("tutorial_survey_form"):
        # Pregunta 1
        p1_text = st.radio(
            "1) ¿Qué tan fácil fue usar el sistema?",
            options=opciones_lista,
            index=3,  # Por defecto en "Satisfecho"
            key="p1"
        )
        p1 = list(opciones_emojis.keys())[list(opciones_emojis.values()).index(p1_text)]
        
        # Pregunta 2
        p2_text = st.radio(
            "2) ¿Qué tan claro fue el tutorial?",
            options=opciones_lista,
            index=3,
            key="p2"
        )
        p2 = list(opciones_emojis.keys())[list(opciones_emojis.values()).index(p2_text)]
        
        # Pregunta 3
        p3_text = st.radio(
            "3) ¿La navegación entre páginas fue intuitiva?",
            options=opciones_lista,
            index=3,
            key="p3"
        )
        p3 = list(opciones_emojis.keys())[list(opciones_emojis.values()).index(p3_text)]
        
        # Pregunta 4
        p4_text = st.radio(
            "4) ¿Qué tan fácil fue encontrar contratos en Consulta?",
            options=opciones_lista,
            index=3,
            key="p4"
        )
        p4 = list(opciones_emojis.keys())[list(opciones_emojis.values()).index(p4_text)]
        
        # Pregunta 5
        p5_text = st.radio(
            "5) ¿Qué tan fácil fue subir archivos en Archivo?",
            options=opciones_lista,
            index=3,
            key="p5"
        )
        p5 = list(opciones_emojis.keys())[list(opciones_emojis.values()).index(p5_text)]
        
        # Pregunta 6
        p6_text = st.radio(
            "6) ¿El sistema respondió rápido?",
            options=opciones_lista,
            index=3,
            key="p6"
        )
        p6 = list(opciones_emojis.keys())[list(opciones_emojis.values()).index(p6_text)]
        
        # Pregunta 7
        p7 = st.text_area(
            "7) Comentarios / mejoras (opcional):", 
            placeholder="Ej. mejorar botones, texto, orden...",
            key="p7"
        )

        if st.form_submit_button("📨 Enviar encuesta"):
            st.session_state.tutorial["survey_open"] = False
            st.success("✅ Encuesta enviada. ¡Gracias por tu retroalimentación!")
            
            # Aquí puedes guardar los resultados en PostgreSQL si lo deseas
            # Por ejemplo:
            # guardar_encuesta_en_postgresql(p1, p2, p3, p4, p5, p6, p7)
            
            st.rerun()
    enviar = st.form_submit_button("Enviar encuesta")


    # Regresar a principal
    st.switch_page("pages/1_PAGINA PRINCIPAL.py")