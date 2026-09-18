import streamlit as st
from supabase import Client, create_client


def criar_cliente_supabase() -> Client:
    """
    Cria um novo cliente Supabase utilizando
    apenas a Publishable/Anon Key.
    """

    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]

    return create_client(url, key)


def get_supabase() -> Client:
    """
    Retorna um cliente Supabase autenticado
    com a sessão armazenada no Streamlit.
    """

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if not access_token or not refresh_token:
        raise RuntimeError(
            "Usuário não autenticado."
        )

    supabase = criar_cliente_supabase()

    response = supabase.auth.set_session(
        access_token,
        refresh_token,
    )

    # set_session pode renovar os tokens se necessário.
    if response.session:
        st.session_state["access_token"] = (
            response.session.access_token
        )

        st.session_state["refresh_token"] = (
            response.session.refresh_token
        )

    return supabase