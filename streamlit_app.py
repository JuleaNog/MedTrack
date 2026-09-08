import streamlit as st


st.set_page_config(
    page_title="MedTrack",
    page_icon="🏥",
    layout="wide"
)


paginas = {
    "Gestão": [
        st.Page(
            "app_pages/equipamentos.py",
            title="Equipamentos",
            icon="🩺"
        ),
    ]
}


pagina = st.navigation(paginas)

pagina.run()