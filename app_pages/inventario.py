from collections import Counter
from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

from services.inventarios import (
    criar_inventario,
    listar_inventarios,
    listar_itens_inventario,
    registrar_equipamento_inventario,
    registrar_divergencia,
    finalizar_inventario,
)

from services.locais import (
    listar_locais_ativos,
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def formatar_data(valor):
    if not valor:
        return "-"

    try:
        return date.fromisoformat(
            valor
        ).strftime(
            "%d/%m/%Y"
        )

    except (ValueError, TypeError):
        return str(valor)


def formatar_data_hora(valor):
    if not valor:
        return "-"

    try:

        data = datetime.fromisoformat(
            valor.replace(
                "Z",
                "+00:00",
            )
        )

        data = data.astimezone(
            ZoneInfo(
                "America/Sao_Paulo"
            )
        )

        return data.strftime(
            "%d/%m/%Y %H:%M"
        )

    except (ValueError, TypeError):
        return str(valor)


def formatar_local(local):
    local = local or {}

    setor = (
        local.get("setor")
        or "-"
    )

    sala = (
        local.get("sala")
        or "-"
    )

    return f"{setor} — {sala}"


def formatar_resultado(resultado):
    nomes = {
        "PENDENTE":
            "Pendente",

        "CORRETO":
            "Correto",

        "DIVERGENTE":
            "Divergente",

        "NAO_ENCONTRADO":
            "Não encontrado",

        "NAO_PREVISTO":
            "Não previsto",
    }

    return nomes.get(
        resultado,
        resultado,
    )


# ============================================================
# DIALOG - DIVERGÊNCIA
# ============================================================

@st.dialog("Registrar divergência")
def dialog_divergencia(
    inventario,
    itens,
):

    pendentes = [
        item
        for item in itens
        if item.get("resultado")
        == "PENDENTE"
    ]


    if not pendentes:

        st.info(
            "Não existem equipamentos "
            "pendentes para registrar divergência."
        )

        return


    opcoes_equipamento = {}


    for item in pendentes:

        equipamento = (
            item.get("equipamento")
            or {}
        )

        modelo = (
            equipamento.get("modelo")
            or {}
        )

        texto = (
            f"{equipamento.get('codigo')} — "
            f"{modelo.get('tipo') or 'Equipamento'}"
        )

        opcoes_equipamento[
            texto
        ] = item


    equipamento_nome = st.selectbox(
        "Equipamento",
        list(
            opcoes_equipamento.keys()
        ),
    )


    item = opcoes_equipamento[
        equipamento_nome
    ]


    esperado = (
        item.get("esperado")
        or {}
    )


    st.write(
        "Local esperado: "
        f"**{formatar_local(esperado)}**"
    )


    try:

        locais = listar_locais_ativos()

    except Exception as erro:

        st.error(
            "Não foi possível carregar os locais."
        )

        st.exception(erro)

        return


    locais_disponiveis = [
        local
        for local in locais
        if local["id"]
        != esperado.get("id")
    ]


    opcoes_local = {}


    for local in locais_disponiveis:

        texto = (
            f"{local.get('setor')} — "
            f"{local.get('sala')} "
            f"({local.get('codigo')})"
        )

        opcoes_local[
            texto
        ] = local["id"]


    local_nome = st.selectbox(
        "Local onde foi encontrado",
        list(
            opcoes_local.keys()
        ),
    )


    if st.button(
        "Registrar divergência",
        type="primary",
        use_container_width=True,
    ):

        try:

            registrar_divergencia(
                inventario_id=
                    inventario["id"],

                equipamento_id=
                    item[
                        "equipamento_id"
                    ],

                local_encontrado_id=
                    opcoes_local[
                        local_nome
                    ],
            )


            st.session_state[
                "toast_inventario"
            ] = (
                "Divergência registrada "
                "com sucesso."
            )


            st.rerun()


        except Exception as erro:

            st.error(
                "Não foi possível registrar "
                "a divergência."
            )

            st.exception(erro)


# ============================================================
# DIALOG - FINALIZAÇÃO
# ============================================================

@st.dialog("Finalizar inventário")
def dialog_finalizar(
    inventario,
    itens,
):

    pendentes = sum(
        1
        for item in itens
        if item.get("resultado")
        == "PENDENTE"
    )


    st.warning(
        f"Existem **{pendentes} item(ns) "
        f"pendente(s)**."
    )


    st.write(
        "Ao finalizar, todos os itens "
        "ainda pendentes serão classificados "
        "como **NÃO ENCONTRADOS**."
    )


    confirmar = st.checkbox(
        "Confirmo a finalização do inventário."
    )


    if st.button(
        "Finalizar inventário",
        type="primary",
        use_container_width=True,
        disabled=not confirmar,
    ):

        try:

            resultado = finalizar_inventario(
                inventario["id"]
            )


            mensagem = (
                "Inventário finalizado "
                "com sucesso."
            )


            if resultado:

                resumo = resultado[0]

                mensagem = (
                    "Inventário finalizado. "
                    f"Corretos: "
                    f"{resumo.get('corretos', 0)}, "
                    f"divergentes: "
                    f"{resumo.get('divergentes', 0)}, "
                    f"não encontrados: "
                    f"{resumo.get('nao_encontrados', 0)}, "
                    f"não previstos: "
                    f"{resumo.get('nao_previstos', 0)}."
                )


            st.session_state[
                "toast_inventario"
            ] = mensagem


            st.rerun()


        except Exception as erro:

            st.error(
                "Não foi possível finalizar "
                "o inventário."
            )

            st.exception(erro)


# ============================================================
# CABEÇALHO
# ============================================================

st.title("Inventário")

st.caption(
    "Conferência física e rastreabilidade "
    "dos equipamentos médico-hospitalares."
)


# ============================================================
# TOAST
# ============================================================

if "toast_inventario" in st.session_state:

    st.toast(
        st.session_state.pop(
            "toast_inventario"
        ),
        icon="✅",
    )


# ============================================================
# CRIAR NOVO INVENTÁRIO
# ============================================================

with st.expander(
    "➕ Criar novo inventário"
):

    try:

        locais = listar_locais_ativos()

    except Exception as erro:

        st.error(
            "Não foi possível carregar "
            "os locais."
        )

        st.exception(erro)

        locais = []


    if locais:

        opcoes_local = {}


        for local in locais:

            texto = (
                f"{local.get('hospital')} — "
                f"{local.get('setor')} — "
                f"{local.get('sala')} "
                f"({local.get('codigo')})"
            )

            opcoes_local[
                texto
            ] = local["id"]


        with st.form(
            "form_novo_inventario"
        ):

            nome = st.text_input(
                "Nome do inventário *",
                placeholder=(
                    "Ex.: Inventário mensal "
                    "UTI Adulto"
                ),
            )


            local_nome = st.selectbox(
                "Local *",
                list(
                    opcoes_local.keys()
                ),
            )


            observacoes = st.text_area(
                "Observações",
                placeholder=(
                    "Informações adicionais "
                    "(opcional)"
                ),
            )


            criar = st.form_submit_button(
                "Criar inventário",
                type="primary",
                use_container_width=True,
            )


        if criar:

            if not nome.strip():

                st.warning(
                    "Informe um nome "
                    "para o inventário."
                )

            else:

                try:

                    resultado = criar_inventario(
                        nome=nome,
                        local_id=opcoes_local[
                            local_nome
                        ],
                        observacoes=observacoes,
                    )


                    quantidade = 0

                    if resultado:

                        quantidade = (
                            resultado[0].get(
                                "itens_previstos",
                                0,
                            )
                        )


                    st.session_state[
                        "toast_inventario"
                    ] = (
                        "Inventário criado "
                        f"com {quantidade} "
                        "equipamento(s) previsto(s)."
                    )


                    st.rerun()


                except Exception as erro:

                    st.error(
                        "Não foi possível criar "
                        "o inventário."
                    )

                    st.exception(erro)


# ============================================================
# LISTAR INVENTÁRIOS
# ============================================================

st.divider()

st.subheader(
    "Inventários"
)


try:

    inventarios = listar_inventarios()

except Exception as erro:

    st.error(
        "Não foi possível carregar "
        "os inventários."
    )

    st.exception(erro)

    st.stop()


if not inventarios:

    st.info(
        "Nenhum inventário cadastrado."
    )

    st.stop()


opcoes_inventario = {}


for inventario in inventarios:

    local = (
        inventario.get("local")
        or {}
    )

    texto = (
        f"{inventario['nome']} — "
        f"{formatar_local(local)} — "
        f"{inventario['status']}"
    )

    opcoes_inventario[
        texto
    ] = inventario


inventario_nome = st.selectbox(
    "Selecione o inventário",
    list(
        opcoes_inventario.keys()
    ),
)


inventario = opcoes_inventario[
    inventario_nome
]


# ============================================================
# INFORMAÇÕES DO INVENTÁRIO
# ============================================================

local = (
    inventario.get("local")
    or {}
)


col1, col2, col3 = st.columns(3)


with col1:

    st.write(
        "**Local:** "
        f"{formatar_local(local)}"
    )


with col2:

    st.write(
        "**Início:** "
        f"{formatar_data(inventario.get('data_inicio'))}"
    )


with col3:

    st.write(
        "**Status:** "
        f"{inventario.get('status')}"
    )


# ============================================================
# CARREGAR ITENS
# ============================================================

try:

    itens = listar_itens_inventario(
        inventario["id"]
    )

except Exception as erro:

    st.error(
        "Não foi possível carregar "
        "os itens do inventário."
    )

    st.exception(erro)

    st.stop()


contagem = Counter(
    item.get("resultado")
    for item in itens
)


total_previstos = sum(
    1
    for item in itens
    if item.get("resultado")
    != "NAO_PREVISTO"
)


# ============================================================
# INDICADORES
# ============================================================

st.markdown(
    "#### Progresso"
)


m1, m2, m3, m4, m5 = (
    st.columns(5)
)


with m1:

    st.metric(
        "Previstos",
        total_previstos,
        border=True,
    )


with m2:

    st.metric(
        "Pendentes",
        contagem.get(
            "PENDENTE",
            0,
        ),
        border=True,
    )


with m3:

    st.metric(
        "Corretos",
        contagem.get(
            "CORRETO",
            0,
        ),
        border=True,
    )


with m4:

    st.metric(
        "Divergentes",
        contagem.get(
            "DIVERGENTE",
            0,
        ),
        border=True,
    )


with m5:

    st.metric(
        "Não previstos",
        contagem.get(
            "NAO_PREVISTO",
            0,
        ),
        border=True,
    )


# ============================================================
# COLETA
# ============================================================

if inventario.get(
    "status"
) == "ABERTO":

    st.divider()

    st.subheader(
        "Registrar equipamento encontrado"
    )


    with st.form(
        "form_registrar_equipamento"
    ):

        codigo = st.text_input(
            "Código do equipamento",
            placeholder="Ex.: EQ-000001",
        )


        registrar = (
            st.form_submit_button(
                "Registrar encontrado",
                type="primary",
                use_container_width=True,
            )
        )


    if registrar:

        if not codigo.strip():

            st.warning(
                "Informe o código "
                "do equipamento."
            )

        else:

            try:

                resultado = (
                    registrar_equipamento_inventario(
                        inventario_id=
                            inventario["id"],

                        codigo_equipamento=
                            codigo,
                    )
                )


                classificacao = "-"

                if resultado:

                    classificacao = (
                        resultado[0].get(
                            "resultado",
                            "-",
                        )
                    )


                st.session_state[
                    "toast_inventario"
                ] = (
                    f"{codigo.upper()} "
                    f"registrado como "
                    f"{formatar_resultado(classificacao)}."
                )


                st.rerun()


            except Exception as erro:

                st.error(
                    "Não foi possível registrar "
                    "o equipamento."
                )

                st.exception(erro)


    col_divergencia, col_finalizar = (
        st.columns(2)
    )


    with col_divergencia:

        if st.button(
            "⚠️ Registrar divergência",
            use_container_width=True,
        ):

            dialog_divergencia(
                inventario,
                itens,
            )


    with col_finalizar:

        if st.button(
            "✅ Finalizar inventário",
            use_container_width=True,
        ):

            dialog_finalizar(
                inventario,
                itens,
            )


# ============================================================
# RESULTADOS
# ============================================================

st.divider()

st.subheader(
    "Itens do inventário"
)


linhas = []


for item in itens:

    equipamento = (
        item.get("equipamento")
        or {}
    )

    modelo = (
        equipamento.get("modelo")
        or {}
    )


    linhas.append(
        {
            "Código":
                equipamento.get(
                    "codigo"
                ),

            "Equipamento":
                modelo.get(
                    "tipo"
                )
                or "-",

            "Esperado":
                formatar_local(
                    item.get(
                        "esperado"
                    )
                ),

            "Encontrado":
                formatar_local(
                    item.get(
                        "encontrado"
                    )
                )
                if item.get(
                    "encontrado"
                )
                else "-",

            "Resultado":
                formatar_resultado(
                    item.get(
                        "resultado"
                    )
                ),

            "Conferido em":
                formatar_data_hora(
                    item.get(
                        "data_hora"
                    )
                ),
        }
    )


st.dataframe(
    linhas,
    hide_index=True,
    width="stretch",
)