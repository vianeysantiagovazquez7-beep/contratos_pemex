import streamlit as st
from core.tutorial_state import mark_completed, is_first_time

# CORRECCIÓN: Rutas exactas de los archivos (deben coincidir con los nombres reales)
PAGES = {
    "principal": "pages/1_PAGINA PRINCIPAL.py",  # Nombre EXACTO del archivo
    "consulta": "pages/2_CONSULTA.py",
    "archivo": "pages/3_ARCHIVO.py",
}

def init():
    if "tutorial" not in st.session_state:
        st.session_state.tutorial = {
            "active": False,
            "step": 0,
            "done": {},
            "force_first_time": True,
            "survey_open": False,
        }

def start():
    st.session_state.tutorial["active"] = True
    st.session_state.tutorial["step"] = 1
    st.session_state.tutorial["survey_open"] = False
    st.rerun()

def stop():
    st.session_state.tutorial["active"] = False
    st.session_state.tutorial["step"] = 0
    st.rerun()

def header_button():
    # Botón superior derecha
    col1, col2, col3 = st.columns([6, 1.5, 1.5])
    with col3:
        if st.button("🧭 Ver tutorial", use_container_width=True):
            start()

def mark_step_done(key: str):
    st.session_state.tutorial["done"][key] = True

def finish_tutorial_if_ready():
    # condición final: ya guardó archivo en ARCHIVO
    if st.session_state.tutorial["done"].get("archivo_guardado_ok"):
        st.session_state.tutorial["active"] = False
        st.session_state.tutorial["step"] = 0
        st.session_state.tutorial["survey_open"] = True
        st.rerun()

def _go_to(page_key: str):
    if page_key in PAGES:
        st.switch_page(PAGES[page_key])

def overlay(page_key: str):
    if "tutorial" not in st.session_state:
        return

    t = st.session_state.tutorial
    if not t["active"]:
        # Si terminó, muestra encuesta si aplica
        if t.get("survey_open"):
            survey()
        return

    step = t["step"]

    # Control de navegación automática por pasos
    # 1 = principal, 2 = consulta, 3 = archivo
    if step == 1 and page_key != "principal":
        _go_to("principal")
        return
    if step == 2 and page_key != "consulta":
        _go_to("consulta")
        return
    if step == 3 and page_key != "archivo":
        _go_to("archivo")
        return

    # Overlay UI
    with st.container():
        st.markdown(
            """
            <div style="
                position: fixed;
                top: 90px;
                right: 30px;
                width: 360px;
                background: rgba(255,255,255,0.96);
                border: 2px solid #d4af37;
                border-radius: 14px;
                padding: 14px 16px;
                z-index: 9999;
                box-shadow: 0 12px 35px rgba(0,0,0,0.20);
            ">
            """,
            unsafe_allow_html=True
        )

    # Contenido por paso
    if step == 1 and page_key == "principal":
        st.info("📌 Tutorial (1/3): Aquí subes y registras contratos.")
        st.write("➡️ Cuando termines de capturar un contrato, pasa al siguiente paso.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Siguiente ➜ Consulta"):
                t["step"] = 2
                st.rerun()
        with c2:
            if st.button("Salir"):
                stop()

    elif step == 2 and page_key == "consulta":
        st.info("📌 Tutorial (2/3): Aquí buscas contratos y descargas archivos.")
        st.write("🔍 Usa el buscador para ubicar contratos por número, contratista o palabra clave.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Siguiente ➜ Archivo"):
                t["step"] = 3
                st.rerun()
        with c2:
            if st.button("Salir"):
                stop()

    elif step == 3 and page_key == "archivo":
        st.info("📌 Tutorial (3/3): Aquí guardas anexos, cédulas y soportes.")
        st.write("📤 Selecciona un contrato, elige sección y sube archivo(s).")
        st.warning("El tutorial termina automáticamente cuando subas al menos 1 archivo exitosamente.")
        if st.button("Salir"):
            stop()

# CORRECCIÓN: Encuesta con emojis de caritas del 1 al 5
def survey():
    st.markdown("---")
    st.subheader("📝 Encuesta de satisfacción (7 preguntas)")
    st.caption("Esto ayuda a validar el sistema con usuarios reales (tu 50% de muestra).")

    # Definir las opciones con emojis
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