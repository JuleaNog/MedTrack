import streamlit as st

from services.auth import (
    esta_autenticado,
    login,
    logout,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="MedTrack",
    page_icon="🏥",
    layout="wide",
)


# ============================================================
# PRESERVAR EQUIPAMENTO VINDO DO QR CODE
# ============================================================

codigo_url = st.query_params.get(
    "equipamento"
)

if codigo_url:

    st.session_state[
        "equipamento_pendente"
    ] = codigo_url


# ============================================================
# LOGIN
# ============================================================

if not esta_autenticado():

    st.title("MedTrack")

    st.subheader(
        "Gerenciamento de equipamentos "
        "médico-hospitalares"
    )

    st.write(
        "Entre com suas credenciais para "
        "acessar o sistema."
    )

    st.divider()

    coluna_login, coluna_vazia = (
        st.columns([1, 2])
    )

    with coluna_login:

        with st.form("form_login"):

            email = st.text_input(
                "E-mail"
            )

            senha = st.text_input(
                "Senha",
                type="password",
            )

            entrar = st.form_submit_button(
                "Entrar",
                type="primary",
                use_container_width=True,
            )

        if entrar:

            if not email or not senha:

                st.warning(
                    "Informe e-mail e senha."
                )

            else:

                try:

                    login(
                        email=email.strip(),
                        senha=senha,
                    )

                    # Restaura o equipamento
                    # originalmente acessado pelo QR.
                    equipamento_pendente = (
                        st.session_state.get(
                            "equipamento_pendente"
                        )
                    )

                    if equipamento_pendente:

                        st.query_params[
                            "equipamento"
                        ] = equipamento_pendente

                    st.rerun()

                except Exception:

                    st.error(
                        "E-mail ou senha inválidos."
                    )

    st.stop()


# ============================================================
# USUÁRIO AUTENTICADO
# ============================================================

with st.sidebar:

    st.caption(
        "Usuário conectado"
    )

    st.write(
        st.session_state.get(
            "usuario_email",
            "",
        )
    )

    if st.button(
        "Sair",
        use_container_width=True,
    ):

        logout()

        st.rerun()


# ============================================================
# NAVEGAÇÃO
# ============================================================

paginas = {
    "Gestão": [
        st.Page(
            "app_pages/equipamentos.py",
            title="Equipamentos",
            icon="🩺",
            default=True,
        ),
    ]
}


pagina = st.navigation(
    paginas
)

pagina.run()