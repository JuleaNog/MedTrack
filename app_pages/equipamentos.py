import streamlit as st

from datetime import datetime
from zoneinfo import ZoneInfo

from services.equipamentos import listar_equipamentos
from services.locais import listar_locais_ativos

from services.movimentacoes import (
    registrar_movimentacao,
    listar_movimentacoes_equipamento,
)

from services.qr_codes import gerar_qr_equipamento

# funções de formatação

def formatar_data_hora(valor):
    """
    Converte uma data/hora retornada pelo Supabase
    para o formato brasileiro.
    """

    if not valor:
        return "-"

    try:
        data = datetime.fromisoformat(
            valor.replace("Z", "+00:00")
        )

        data = data.astimezone(
            ZoneInfo("America/Sao_Paulo")
        )

        return data.strftime("%d/%m/%Y às %H:%M")

    except (ValueError, TypeError):
        return str(valor)

# ============================================================
# DIÁLOGO DE MOVIMENTAÇÃO
# ============================================================

@st.dialog("Alterar localização")
def dialog_movimentacao(equipamento):
    """
    Exibe o formulário responsável por registrar a movimentação
    de um equipamento para outro local.
    """

    modelo = equipamento.get("modelo") or {}
    local_atual = equipamento.get("local") or {}

    st.write(
        f"**{equipamento.get('codigo')} — "
        f"{modelo.get('tipo', 'Equipamento')}**"
    )

    setor_atual = local_atual.get("setor") or "Não definido"
    sala_atual = local_atual.get("sala") or "Não definida"

    st.write(
        f"Local atual: **{setor_atual} / {sala_atual}**"
    )

    st.divider()

    # --------------------------------------------------------
    # Buscar locais disponíveis
    # --------------------------------------------------------

    try:
        locais = listar_locais_ativos()

    except Exception as erro:
        st.error("Não foi possível carregar os locais cadastrados.")
        st.exception(erro)
        return

    local_atual_id = local_atual.get("id")

    # Remove o local em que o equipamento já se encontra
    destinos = [
        local
        for local in locais
        if local["id"] != local_atual_id
    ]

    if not destinos:
        st.warning(
            "Não existem outros locais ativos disponíveis para movimentação."
        )
        return

    # Cria textos amigáveis para o selectbox
    opcoes_destino = {}

    for local in destinos:
        setor = local.get("setor") or "Setor não informado"
        sala = local.get("sala") or "Sala não informada"
        codigo = local.get("codigo") or "-"

        nome_exibicao = (
            f"{setor} — {sala} ({codigo})"
        )

        opcoes_destino[nome_exibicao] = local["id"]

    # --------------------------------------------------------
    # Formulário
    # --------------------------------------------------------

    with st.form("form_movimentacao"):

        destino_nome = st.selectbox(
            "Novo local",
            options=list(opcoes_destino.keys()),
        )

        motivo = st.text_input(
            "Motivo",
            placeholder="Ex.: transferência para atendimento"
        )

        observacoes = st.text_area(
            "Observações",
            placeholder="Informações adicionais (opcional)"
        )

        confirmar = st.form_submit_button(
            "Confirmar movimentação",
            type="primary",
            use_container_width=True,
        )

    # --------------------------------------------------------
    # Registrar movimentação
    # --------------------------------------------------------

    if confirmar:

        local_destino_id = opcoes_destino[destino_nome]

        try:

            registrar_movimentacao(
                equipamento_id=equipamento["id"],
                local_destino_id=local_destino_id,
                motivo=motivo,
                observacoes=observacoes,
            )

            # Guarda mensagem para mostrar após o rerun
            st.session_state["movimentacao_sucesso"] = (
                f"{equipamento['codigo']} movimentado com sucesso "
                f"para {destino_nome}."
            )

            # Fecha o diálogo e recarrega os dados
            st.rerun()

        except Exception as erro:

            st.error(
                "Não foi possível registrar a movimentação."
            )

            st.exception(erro)

@st.dialog("Histórico de movimentações")
def dialog_historico(equipamento):
    """
    Exibe todas as movimentações registradas
    para o equipamento selecionado.
    """

    modelo = equipamento.get("modelo") or {}

    st.write(
        f"**{equipamento.get('codigo')} — "
        f"{modelo.get('tipo', 'Equipamento')}**"
    )

    st.caption(
        "Movimentações registradas da mais recente "
        "para a mais antiga."
    )

    st.divider()

    try:

        movimentacoes = listar_movimentacoes_equipamento(
            equipamento["id"]
        )

    except Exception as erro:

        st.error(
            "Não foi possível carregar o histórico "
            "de movimentações."
        )

        st.exception(erro)

        return


    if not movimentacoes:

        st.info(
            "Nenhuma movimentação registrada "
            "para este equipamento."
        )

        return


    for movimentacao in movimentacoes:

        origem = movimentacao.get("origem") or {}
        destino = movimentacao.get("destino") or {}

        origem_setor = (
            origem.get("setor")
            or "Local não definido"
        )

        origem_sala = (
            origem.get("sala")
            or "-"
        )

        destino_setor = (
            destino.get("setor")
            or "Local não definido"
        )

        destino_sala = (
            destino.get("sala")
            or "-"
        )

        data_formatada = formatar_data_hora(
            movimentacao.get("data_hora")
        )


        with st.container(border=True):

            st.markdown(
                f"**{data_formatada}**"
            )

            st.write(
                f"📍 **Origem:** "
                f"{origem_setor} — {origem_sala}"
            )

            st.write(
                f"➡️ **Destino:** "
                f"{destino_setor} — {destino_sala}"
            )


            motivo = movimentacao.get("motivo")

            if motivo:

                st.write(
                    f"**Motivo:** {motivo}"
                )


            observacoes = movimentacao.get(
                "observacoes"
            )

            if observacoes:

                st.write(
                    f"**Observações:** "
                    f"{observacoes}"
                )

@st.dialog("QR Code do equipamento")
def dialog_qr_code(equipamento):
    """
    Exibe o QR Code permanente associado ao equipamento.
    """

    modelo = equipamento.get("modelo") or {}

    codigo = equipamento.get("codigo")

    st.write(
        f"**{codigo} — "
        f"{modelo.get('tipo', 'Equipamento')}**"
    )

    try:

        qr_png, url = gerar_qr_equipamento(
            codigo
        )

    except Exception as erro:

        st.error(
            "Não foi possível gerar o QR Code."
        )

        st.exception(erro)

        return


    st.image(
        qr_png,
        width=280,
    )


    st.caption(
        "O QR Code direciona permanentemente "
        "para o registro digital deste equipamento."
    )


    st.code(
        url,
        language=None,
    )


    st.download_button(
        "Baixar QR Code",
        data=qr_png,
        file_name=f"QR_{codigo}.png",
        mime="image/png",
        use_container_width=True,
    )
# ============================================================
# TÍTULO
# ============================================================

st.title("Equipamentos")

st.caption(
    "Consulte os equipamentos médico-hospitalares cadastrados "
    "e gerencie suas informações."
)

# ============================================================
# EQUIPAMENTO RECEBIDO PELA URL
# ============================================================

codigo_url = st.query_params.get("equipamento")


# ============================================================
# MENSAGEM DE SUCESSO APÓS MOVIMENTAÇÃO
# ============================================================

if "movimentacao_sucesso" in st.session_state:

    st.success(
        st.session_state.pop("movimentacao_sucesso")
    )


# ============================================================
# BUSCAR EQUIPAMENTOS
# ============================================================

try:

    equipamentos = listar_equipamentos()

except Exception as erro:

    st.error(
        "Não foi possível carregar os equipamentos."
    )

    st.exception(erro)

    st.stop()


if not equipamentos:

    st.info("Nenhum equipamento cadastrado.")

    st.stop()

# ============================================================
# VALIDAR EQUIPAMENTO RECEBIDO PELO QR / URL
# ============================================================

equipamento_url = None

if codigo_url:

    equipamento_url = next(
        (
            equipamento
            for equipamento in equipamentos
            if equipamento.get("codigo") == codigo_url
        ),
        None,
    )

    if equipamento_url:

        st.info(
            f"Equipamento acessado diretamente: **{codigo_url}**"
        )

    else:

        st.error(
            f"O equipamento **{codigo_url}** não foi encontrado."
        )

    if codigo_url:

        if st.button(
            "← Ver todos os equipamentos"
        ):

            st.query_params.clear()

            st.rerun()

# ============================================================
# FILTROS
# ============================================================

st.subheader("Filtros")

col_busca, col_status, col_setor = st.columns(
    [2, 1, 1]
)


# ------------------------------------------------------------
# Busca textual
# ------------------------------------------------------------

with col_busca:

    busca = st.text_input(
        "Buscar",
        value=codigo_url or "",
        placeholder=(
            "Código, patrimônio, número de série, "
            "equipamento, fabricante ou modelo..."
        )
    )


# ------------------------------------------------------------
# Status
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Setor
# ------------------------------------------------------------

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

    # Monta uma única string contendo os campos pesquisáveis
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
        or busca.lower().strip() in texto_busca
    )

    corresponde_status = (
        status_selecionado == "Todos"
        or equipamento.get("status")
        == status_selecionado
    )

    corresponde_setor = (
        setor_selecionado == "Todos"
        or local.get("setor")
        == setor_selecionado
    )

    if (
        corresponde_busca
        and corresponde_status
        and corresponde_setor
    ):

        equipamentos_filtrados.append(
            equipamento
        )


# ============================================================
# LISTAGEM
# ============================================================

st.divider()

st.subheader("Equipamentos cadastrados")

st.caption(
    f"{len(equipamentos_filtrados)} "
    "equipamento(s) encontrado(s)"
)


# ------------------------------------------------------------
# Criar dados amigáveis para a tabela
# ------------------------------------------------------------

linhas_tabela = []

for equipamento in equipamentos_filtrados:

    modelo = equipamento.get("modelo") or {}
    local = equipamento.get("local") or {}

    linhas_tabela.append(
        {
            "Código": equipamento.get("codigo"),
            "Patrimônio": (
                equipamento.get("patrimonio") or "-"
            ),
            "Equipamento": (
                modelo.get("tipo") or "-"
            ),
            "Fabricante": (
                modelo.get("fabricante") or "-"
            ),
            "Modelo": (
                modelo.get("modelo") or "-"
            ),
            "Setor": (
                local.get("setor") or "-"
            ),
            "Sala": (
                local.get("sala") or "-"
            ),
            "Status": (
                equipamento.get("status") or "-"
            ),
            "Criticidade": (
                equipamento.get("criticidade") or "-"
            ),
        }
    )


if linhas_tabela:

    st.dataframe(
        linhas_tabela,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "Nenhum equipamento corresponde aos filtros selecionados."
    )


# ============================================================
# FICHA INDIVIDUAL
# ============================================================

if equipamentos_filtrados:

    st.divider()

    st.subheader("Ficha do equipamento")


    # --------------------------------------------------------
    # Criar opções do seletor
    # --------------------------------------------------------

    opcoes_equipamentos = {}

    for equipamento in equipamentos_filtrados:

        modelo = equipamento.get("modelo") or {}

        codigo = (
            equipamento.get("codigo")
            or "Sem código"
        )

        tipo = (
            modelo.get("tipo")
            or "Equipamento"
        )

        nome_modelo = (
            modelo.get("modelo")
            or ""
        )

        texto = (
            f"{codigo} — "
            f"{tipo} — "
            f"{nome_modelo}"
        )

        opcoes_equipamentos[
            texto
        ] = equipamento


    equipamento_selecionado_nome = st.selectbox(
        "Selecione um equipamento",
        list(opcoes_equipamentos.keys()),
    )


    equipamento = opcoes_equipamentos[
        equipamento_selecionado_nome
    ]


    modelo = equipamento.get("modelo") or {}
    local = equipamento.get("local") or {}


    # ========================================================
    # CABEÇALHO DA FICHA
    # ========================================================

    st.markdown(
        f"### {modelo.get('tipo', 'Equipamento')}"
    )

    st.caption(
        equipamento.get("codigo") or ""
    )


    # ========================================================
    # INFORMAÇÕES PRINCIPAIS
    # ========================================================

    col1, col2, col3 = st.columns(3)


    # --------------------------------------------------------
    # Identificação
    # --------------------------------------------------------

    with col1:

        st.markdown("#### Identificação")

        st.write(
            "**Código:** "
            f"{equipamento.get('codigo') or '-'}"
        )

        st.write(
            "**Patrimônio:** "
            f"{equipamento.get('patrimonio') or '-'}"
        )

        st.write(
            "**Número de série:** "
            f"{equipamento.get('numero_serie') or '-'}"
        )

        st.write(
            "**Data de aquisição:** "
            f"{equipamento.get('data_aquisicao') or '-'}"
        )

        st.write(
            "**Data de instalação:** "
            f"{equipamento.get('data_instalacao') or '-'}"
        )


    # --------------------------------------------------------
    # Modelo
    # --------------------------------------------------------

    with col2:

        st.markdown("#### Equipamento")

        st.write(
            "**Fabricante:** "
            f"{modelo.get('fabricante') or '-'}"
        )

        st.write(
            "**Modelo:** "
            f"{modelo.get('modelo') or '-'}"
        )

        st.write(
            "**Criticidade:** "
            f"{equipamento.get('criticidade') or '-'}"
        )

        periodicidade = modelo.get(
            "periodicidade_preventiva_meses"
        )

        if periodicidade:

            st.write(
                "**Periodicidade preventiva:** "
                f"{periodicidade} meses"
            )

        else:

            st.write(
                "**Periodicidade preventiva:** -"
            )


    # --------------------------------------------------------
    # Localização
    # --------------------------------------------------------

    with col3:

        st.markdown("#### Situação atual")

        st.write(
            "**Hospital:** "
            f"{local.get('hospital') or '-'}"
        )

        st.write(
            "**Setor:** "
            f"{local.get('setor') or '-'}"
        )

        st.write(
            "**Sala:** "
            f"{local.get('sala') or '-'}"
        )

        st.write(
            "**Status:** "
            f"{equipamento.get('status') or '-'}"
        )


    # ========================================================
    # OBSERVAÇÕES
    # ========================================================

    observacoes = equipamento.get(
        "observacoes"
    )

    if observacoes:

        st.markdown("#### Observações")

        st.write(observacoes)


    # ========================================================
    # AÇÕES
    # ========================================================

    st.divider()

    st.markdown("#### Ações")

    (
        col_acao1,
        col_acao2,
        col_acao3,
        col_acao4,
        col_acao5,
    ) = st.columns(5)


    # --------------------------------------------------------
    # ALTERAR LOCALIZAÇÃO
    # --------------------------------------------------------

    with col_acao1:

        if st.button(
            "📍 Alterar localização",
            use_container_width=True,
        ):

            dialog_movimentacao(
                equipamento
            )


    # --------------------------------------------------------
    # REGISTRAR FALHA
    # --------------------------------------------------------

    with col_acao2:

        st.button(
            "⚠️ Registrar falha",
            use_container_width=True,
            disabled=True,
            help=(
                "Essa funcionalidade será implementada "
                "em uma próxima etapa."
            ),
        )


    # --------------------------------------------------------
    # MANUTENÇÃO
    # --------------------------------------------------------

    with col_acao3:

        st.button(
            "🔧 Registrar manutenção",
            use_container_width=True,
            disabled=True,
            help=(
                "Essa funcionalidade será implementada "
                "em uma próxima etapa."
            ),
        )


    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    with col_acao4:

        if st.button(
            "📜 Histórico",
            use_container_width=True,
        ):

            dialog_historico(
                equipamento
            )

    # --------------------------------------------------------
    # QR CODE
    # --------------------------------------------------------

    with col_acao5:

        if st.button(
            "🔳 QR Code",
            use_container_width=True,
        ):

            dialog_qr_code(
                equipamento
            )