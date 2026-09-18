import streamlit as st

from services.database import criar_cliente_supabase


def login(email: str, senha: str):
    """
    Realiza login com email e senha
    utilizando Supabase Auth.
    """

    supabase = criar_cliente_supabase()

    response = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": senha,
        }
    )

    if not response.session:
        raise RuntimeError(
            "Não foi possível criar a sessão."
        )

    st.session_state["access_token"] = (
        response.session.access_token
    )

    st.session_state["refresh_token"] = (
        response.session.refresh_token
    )

    st.session_state["usuario_id"] = (
        response.user.id
    )

    st.session_state["usuario_email"] = (
        response.user.email
    )

    return response.user


def esta_autenticado() -> bool:
    """
    Verifica se existem tokens de sessão.
    """

    return bool(
        st.session_state.get("access_token")
        and st.session_state.get("refresh_token")
    )


def logout():
    """
    Encerra a sessão do Supabase e limpa
    os dados locais do Streamlit.
    """

    access_token = st.session_state.get(
        "access_token"
    )

    refresh_token = st.session_state.get(
        "refresh_token"
    )

    if access_token and refresh_token:

        try:
            supabase = criar_cliente_supabase()

            supabase.auth.set_session(
                access_token,
                refresh_token,
            )

            supabase.auth.sign_out()

        except Exception:
            # Mesmo se o logout remoto falhar,
            # a sessão local será removida.
            pass

    chaves = [
        "access_token",
        "refresh_token",
        "usuario_id",
        "usuario_email",
    ]

    for chave in chaves:
        st.session_state.pop(chave, None)