import streamlit as st

from services.database import get_supabase


st.set_page_config(
    page_title="MedTrack",
    page_icon="🏥",
    layout="wide"
)

st.title("MedTrack")
st.write("Sistema de gerenciamento de equipamentos médico-hospitalares")


supabase = get_supabase()

response = (
    supabase
    .table("equipamentos")
    .select("*")
    .execute()
)

st.write(response.data)