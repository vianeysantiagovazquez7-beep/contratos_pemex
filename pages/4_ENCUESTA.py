import streamlit as st

st.set_page_config(page_title="Encuesta", page_icon="📝", layout="wide")

st.title("📝 Encuesta de satisfacción")
st.caption("7 preguntas rápidas. Esto ayuda a mejorar el sistema y el tutorial.")

with st.form("encuesta_7"):
    q1 = st.slider("1) ¿Qué tan fácil fue usar el sistema?", 1, 5, 4)
    q2 = st.slider("2) ¿El tutorial fue claro y entendible?", 1, 5, 4)
    q3 = st.slider("3) ¿Te ayudó a completar el flujo completo?", 1, 5, 4)
    q4 = st.slider("4) ¿Qué tan rápida sentiste la aplicación?", 1, 5, 4)
    q5 = st.slider("5) ¿Qué tan confiable es el guardado en la base de datos?", 1, 5, 4)
    q6 = st.slider("6) ¿Qué tan útil fue la sección de Consulta?", 1, 5, 4)
    q7 = st.text_area("7) Comentarios o mejoras (opcional)")

    enviar = st.form_submit_button("Enviar encuesta")

if enviar:
    # Aquí puedes guardarlo en PostgreSQL cuando quieras.
    st.success("Encuesta enviada correctamente. Gracias.")

    # Regresar a principal
    st.switch_page("pages/1_PAGINA PRINCIPAL.py")