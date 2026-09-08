import streamlit as st

from services.equipamentos import listar_equipamentos


st.title("Equipamentos")

st.caption(
    "Consulte os equipamentos médico-hospitalares cadastrados no sistema."
)


# ============================================================
# BUSCAR EQUIPAMENTOS
# ============================================================

try:
    equipamentos = listar_equipamentos()

except Exception as erro:
    st.error("Não foi possível carregar os equipamentos.")
    st.exception(erro)
    st.stop()


if not equipamentos:
    st.info("Nenhum equipamento cadastrado.")
    st.stop()


# ============================================================
# FILTROS
# ============================================================

st.subheader("Filtros")

col_busca, col_status, col_setor = st.columns([2, 1, 1])


with col_busca:

    busca = st.text_input(
        "Buscar",
        placeholder="Código, patrimônio, modelo, fabricante..."
    )


status_disponiveis = sorted(
    {
        equipamento["status"]
        for equipamento in equipamentos
        if equipamento.get("status")
    }
)


with col_status:

    status_selecionado = st.selectbox(
        "Status",
        ["Todos"] + status_disponiveis
    )


setores_disponiveis = sorted(
    {
        equipamento["local"]["setor"]
        for equipamento in equipamentos
        if equipamento.get("local")
        and equipamento["local"].get("setor")
    }
)


with col_setor:

    setor_selecionado = st.selectbox(
        "Setor",
        ["Todos"] + setores_disponiveis
    )


# ============================================================
# APLICAR FILTROS
# ============================================================

equipamentos_filtrados = []


for equipamento in equipamentos:

    modelo = equipamento.get("modelo") or {}
    local = equipamento.get("local") or {}

    texto_busca = " ".join(
        [
            str(equipamento.get("codigo") or ""),
            str(equipamento.get("patrimonio") or ""),
            str(equipamento.get("numero_serie") or ""),
            str(modelo.get("tipo") or ""),
            str(modelo.get("fabricante") or ""),
            str(modelo.get("modelo") or ""),
        ]
    ).lower()


    corresponde_busca = (
        not busca
        or busca.lower() in texto_busca
    )


    corresponde_status = (
        status_selecionado == "Todos"
        or equipamento.get("status") == status_selecionado
    )


    corresponde_setor = (
        setor_selecionado == "Todos"
        or local.get("setor") == setor_selecionado
    )


    if (
        corresponde_busca
        and corresponde_status
        and corresponde_setor
    ):
        equipamentos_filtrados.append(equipamento)


# ============================================================
# TABELA
# ============================================================

st.divider()

st.subheader("Equipamentos cadastrados")

st.caption(
    f"{len(equipamentos_filtrados)} equipamento(s) encontrado(s)"
)


linhas_tabela = []


for equipamento in equipamentos_filtrados:

    modelo = equipamento.get("modelo") or {}
    local = equipamento.get("local") or {}

    linhas_tabela.append(
        {
            "Código": equipamento.get("codigo"),
            "Patrimônio": equipamento.get("patrimonio"),
            "Equipamento": modelo.get("tipo"),
            "Fabricante": modelo.get("fabricante"),
            "Modelo": modelo.get("modelo"),
            "Setor": local.get("setor"),
            "Sala": local.get("sala"),
            "Status": equipamento.get("status"),
            "Criticidade": equipamento.get("criticidade"),
        }
    )

st.dataframe(
    linhas_tabela,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# FICHA DO EQUIPAMENTO
# ============================================================

if equipamentos_filtrados:

    st.divider()

    st.subheader("Ficha do equipamento")


    opcoes_equipamentos = {}


    for equipamento in equipamentos_filtrados:

        modelo = equipamento.get("modelo") or {}

        texto = (
            f"{equipamento['codigo']} — "
            f"{modelo.get('tipo', 'Equipamento')} — "
            f"{modelo.get('modelo', '')}"
        )

        opcoes_equipamentos[texto] = equipamento


    equipamento_selecionado_nome = st.selectbox(
        "Selecione um equipamento",
        list(opcoes_equipamentos.keys())
    )


    equipamento = opcoes_equipamentos[
        equipamento_selecionado_nome
    ]


    modelo = equipamento.get("modelo") or {}
    local = equipamento.get("local") or {}


    st.markdown(
        f"### {modelo.get('tipo', 'Equipamento')}"
    )

    st.caption(equipamento.get("codigo"))


    col1, col2, col3 = st.columns(3)


    with col1:

        st.markdown("**Identificação**")

        st.write(
            f"**Código:** {equipamento.get('codigo') or '-'}"
        )

        st.write(
            f"**Patrimônio:** "
            f"{equipamento.get('patrimonio') or '-'}"
        )

        st.write(
            f"**Número de série:** "
            f"{equipamento.get('numero_serie') or '-'}"
        )


    with col2:

        st.markdown("**Modelo**")

        st.write(
            f"**Fabricante:** "
            f"{modelo.get('fabricante') or '-'}"
        )

        st.write(
            f"**Modelo:** "
            f"{modelo.get('modelo') or '-'}"
        )

        st.write(
            f"**Criticidade:** "
            f"{equipamento.get('criticidade') or '-'}"
        )


    with col3:

        st.markdown("**Localização**")

        st.write(
            f"**Setor:** "
            f"{local.get('setor') or '-'}"
        )

        st.write(
            f"**Sala:** "
            f"{local.get('sala') or '-'}"
        )

        st.write(
            f"**Status:** "
            f"{equipamento.get('status') or '-'}"
        )