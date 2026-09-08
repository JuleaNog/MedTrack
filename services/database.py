import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def get_supabase() -> Client:
    """
    Cliente padrão do Supabase.

    Utiliza a publishable/anon key e respeita
    as políticas de Row Level Security (RLS).
    """

    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]

    return create_client(url, key)


@st.cache_resource
def get_supabase_admin() -> Client:
    """
    Cliente administrativo usado temporariamente
    durante o desenvolvimento local.

    Utiliza a Secret Key e ignora as políticas RLS.

    IMPORTANTE:
    A Secret Key nunca deve ser enviada ao GitHub
    ou exposta ao navegador.
    """

    url = st.secrets["supabase"]["url"]
    secret_key = st.secrets["supabase"]["secret_key"]

    return create_client(url, secret_key)