import streamlit as st

from datetime import date, datetime
from zoneinfo import ZoneInfo

from services.equipamentos import listar_equipamentos
from services.locais import listar_locais_ativos

from services.falhas import (
    registrar_falha,
    listar_falhas_pendentes_equipamento,
)

from services.manutencoes import (
    registrar_manutencao,
    listar_manutencoes_pendentes_equipamento,
    concluir_manutencao,
    obter_status_preventiva,
)

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

@st.dialog("Registrar falha")
def dialog_registrar_falha(equipamento):
    """
    Registra uma nova falha associada
    ao equipamento selecionado.
    """

    modelo = equipamento.get("modelo") or {}
    local = equipamento.get("local") or {}

    codigo = equipamento.get("codigo")
    tipo = modelo.get("tipo") or "Equipamento"

    st.write(
        f"**{codigo} — {tipo}**"
    )

    st.write(
        f"Local atual: **"
        f"{local.get('setor') or 'Não definido'} / "
        f"{local.get('sala') or 'Não definida'}**"
    )

    st.write(
        f"Status atual: **"
        f"{equipamento.get('status') or '-'}**"
    )

    st.divider()

    categorias = [
        "Não informada",
        "ELÉTRICA",
        "ELETRÔNICA",
        "MECÂNICA",
        "SOFTWARE",
        "ACESSÓRIO",
        "DESEMPENHO",
        "OUTRA",
    ]

    gravidades = [
        "Não informada",
        "BAIXA",
        "MODERADA",
        "ALTA",
        "CRÍTICA",
    ]

    with st.form("form_registrar_falha"):

        categoria = st.selectbox(
            "Categoria",
            categorias,
        )

        gravidade = st.selectbox(
            "Gravidade",
            gravidades,
        )

        descricao = st.text_area(
            "Descrição da falha *",
            placeholder=(
                "Descreva o problema observado no equipamento..."
            ),
            height=130,
        )

        confirmar = st.form_submit_button(
            "Registrar falha",
            type="primary",
            use_container_width=True,
        )

    if confirmar:

        if not descricao.strip():

            st.warning(
                "Informe uma descrição para a falha."
            )

            return

        categoria_banco = (
            None
            if categoria == "Não informada"
            else categoria
        )

        gravidade_banco = (
            None
            if gravidade == "Não informada"
            else gravidade
        )

        try:

            registrar_falha(
                equipamento_id=equipamento["id"],
                descricao=descricao,
                categoria=categoria_banco,
                gravidade=gravidade_banco,
            )

            st.session_state["falha_sucesso"] = (
                f"Falha registrada com sucesso "
                f"para o equipamento {codigo}."
            )

            st.rerun()

        except Exception as erro:

            st.error(
                "Não foi possível registrar a falha."
            )

            st.exception(erro)

@st.dialog("Registrar manutenção")
def dialog_registrar_manutencao(equipamento):
    """
    Abre uma nova manutenção para
    o equipamento selecionado.
    """

    modelo = equipamento.get("modelo") or {}
    local = equipamento.get("local") or {}

    codigo = equipamento.get("codigo")
    tipo_equipamento = (
        modelo.get("tipo")
        or "Equipamento"
    )

    # ========================================================
    # CABEÇALHO
    # ========================================================

    st.write(
        f"**{codigo} — {tipo_equipamento}**"
    )

    st.write(
        f"Local atual: **"
        f"{local.get('setor') or 'Não definido'} / "
        f"{local.get('sala') or 'Não definida'}**"
    )

    st.write(
        f"Status atual: **"
        f"{equipamento.get('status') or '-'}**"
    )

    st.divider()

    # ========================================================
    # TIPO DE MANUTENÇÃO
    # ========================================================

    tipos_manutencao = [
        "PREVENTIVA",
        "CORRETIVA",
        "CALIBRACAO",
        "INSPECAO",
    ]

    tipo = st.selectbox(
        "Tipo de manutenção *",
        tipos_manutencao,
    )

    # ========================================================
    # FALHA ASSOCIADA
    # ========================================================

    falha_id = None

    if tipo == "CORRETIVA":

        st.markdown(
            "##### Falha associada"
        )

        try:

            falhas = (
                listar_falhas_pendentes_equipamento(
                    equipamento["id"]
                )
            )

        except Exception as erro:

            st.error(
                "Não foi possível carregar "
                "as falhas do equipamento."
            )

            st.exception(erro)

            return


        opcoes_falha = {
            "Nenhuma falha vinculada": None
        }


        for falha in falhas:

            categoria = (
                falha.get("categoria")
                or "Sem categoria"
            )

            gravidade = (
                falha.get("gravidade")
                or "Sem gravidade"
            )

            descricao_falha = (
                falha.get("descricao")
                or ""
            )

            # Evita textos muito grandes no selectbox
            if len(descricao_falha) > 55:
                descricao_falha = (
                    descricao_falha[:55]
                    + "..."
                )

            texto_falha = (
                f"Falha #{falha['id']} — "
                f"{categoria} — "
                f"{gravidade} — "
                f"{descricao_falha}"
            )

            opcoes_falha[
                texto_falha
            ] = falha["id"]


        falha_selecionada = st.selectbox(
            "Vincular a uma falha",
            options=list(
                opcoes_falha.keys()
            ),
        )

        falha_id = opcoes_falha[
            falha_selecionada
        ]


        if not falhas:

            st.info(
                "Este equipamento não possui "
                "falhas abertas ou em análise."
            )

    # ========================================================
    # FORMULÁRIO
    # ========================================================

    with st.form(
        "form_registrar_manutencao"
    ):

        data_inicio = st.date_input(
            "Data de início *",
            value=date.today(),
            format="DD/MM/YYYY",
        )

        descricao = st.text_area(
            "Descrição / serviço previsto *",
            placeholder=(
                "Descreva o motivo da manutenção "
                "ou o serviço a ser realizado..."
            ),
            height=120,
        )

        responsavel = st.text_input(
            "Responsável",
            placeholder=(
                "Nome do técnico ou responsável"
            ),
        )

        empresa = st.text_input(
            "Empresa",
            placeholder=(
                "Empresa responsável pelo serviço, "
                "quando aplicável"
            ),
        )

        observacoes = st.text_area(
            "Observações",
            placeholder=(
                "Informações adicionais (opcional)"
            ),
            height=80,
        )

        confirmar = st.form_submit_button(
            "Registrar manutenção",
            type="primary",
            use_container_width=True,
        )

    # ========================================================
    # SALVAR
    # ========================================================

    if confirmar:

        if not descricao.strip():

            st.warning(
                "Informe a descrição da manutenção."
            )

            return


        try:

            manutencao_criada = registrar_manutencao(
                equipamento_id=equipamento["id"],
                tipo=tipo,
                data_inicio=data_inicio,
                descricao=descricao,
                falha_id=falha_id,
                responsavel=responsavel,
                empresa=empresa,
                observacoes=observacoes,
            )


            numero_os_gerada = None

            if manutencao_criada:

                numero_os_gerada = (
                    manutencao_criada[0].get(
                        "numero_os"
                    )
                )


            if numero_os_gerada:

                mensagem = (
                    f"Manutenção {tipo} registrada com sucesso. "
                    f"OS: {numero_os_gerada}"
                )

            else:

                mensagem = (
                    f"Manutenção {tipo} registrada com sucesso "
                    f"para {codigo}."
                )


            st.session_state[
                "toast_manutencao_sucesso"
            ] = mensagem


            st.rerun()


        except Exception as erro:

            st.error(
                "Não foi possível registrar "
                "a manutenção."
            )

            st.exception(erro)

@st.dialog("Concluir manutenção")
def dialog_concluir_manutencao(equipamento):
    """
    Permite selecionar e concluir uma manutenção
    aberta do equipamento.
    """

    modelo = equipamento.get("modelo") or {}

    codigo = equipamento.get("codigo")

    tipo_equipamento = (
        modelo.get("tipo")
        or "Equipamento"
    )


    # ========================================================
    # CABEÇALHO
    # ========================================================

    st.write(
        f"**{codigo} — {tipo_equipamento}**"
    )

    st.caption(
        "Selecione uma manutenção aberta "
        "para registrar sua conclusão."
    )

    st.divider()


    # ========================================================
    # BUSCAR MANUTENÇÕES PENDENTES
    # ========================================================

    try:

        manutencoes = (
            listar_manutencoes_pendentes_equipamento(
                equipamento["id"]
            )
        )

    except Exception as erro:

        st.error(
            "Não foi possível carregar "
            "as manutenções pendentes."
        )

        st.exception(erro)

        return


    if not manutencoes:

        st.info(
            "Este equipamento não possui "
            "manutenções abertas ou em andamento."
        )

        return


    # ========================================================
    # SELECT DA MANUTENÇÃO
    # ========================================================

    opcoes = {}


    for manutencao in manutencoes:

        data_inicio_texto = "-"

        if manutencao.get("data_inicio"):

            try:

                data_obj = date.fromisoformat(
                    manutencao["data_inicio"]
                )

                data_inicio_texto = (
                    data_obj.strftime(
                        "%d/%m/%Y"
                    )
                )

            except ValueError:

                data_inicio_texto = (
                    manutencao["data_inicio"]
                )


        texto = (
            f"{manutencao.get('numero_os') or 'Sem OS'}"
            f" — {manutencao.get('tipo')}"
            f" — início {data_inicio_texto}"
        )

        opcoes[texto] = manutencao


    manutencao_nome = st.selectbox(
        "Manutenção *",
        options=list(
            opcoes.keys()
        ),
    )


    manutencao = opcoes[
        manutencao_nome
    ]


    # ========================================================
    # DETALHES DA MANUTENÇÃO
    # ========================================================

    st.markdown(
        "##### Detalhes"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.write(
            "**OS:** "
            f"{manutencao.get('numero_os') or '-'}"
        )

        st.write(
            "**Tipo:** "
            f"{manutencao.get('tipo') or '-'}"
        )


    with col2:

        st.write(
            "**Status:** "
            f"{manutencao.get('status') or '-'}"
        )

        st.write(
            "**Responsável:** "
            f"{manutencao.get('responsavel') or '-'}"
        )


    st.write(
        "**Descrição inicial:** "
        f"{manutencao.get('descricao') or '-'}"
    )


    # ========================================================
    # MOSTRAR FALHA VINCULADA
    # ========================================================

    falha = (
        manutencao.get("falha")
        or {}
    )


    if falha:

        st.markdown(
            "##### Falha vinculada"
        )

        st.write(
            f"**Falha #{falha.get('id')}**"
        )

        st.write(
            "**Categoria:** "
            f"{falha.get('categoria') or '-'}"
        )

        st.write(
            "**Gravidade:** "
            f"{falha.get('gravidade') or '-'}"
        )

        st.write(
            "**Descrição:** "
            f"{falha.get('descricao') or '-'}"
        )

        st.info(
            "Ao concluir esta manutenção corretiva, "
            "a falha vinculada será marcada como RESOLVIDA."
        )


    # ========================================================
    # PREPARAR DATA MÍNIMA
    # ========================================================

    try:

        data_inicio = date.fromisoformat(
            manutencao["data_inicio"]
        )

    except (ValueError, TypeError):

        data_inicio = date.today()


    data_padrao = max(
        date.today(),
        data_inicio,
    )


    st.divider()


    # ========================================================
    # FORMULÁRIO DE CONCLUSÃO
    # ========================================================

    with st.form(
        "form_concluir_manutencao"
    ):

        data_conclusao = st.date_input(
            "Data de conclusão *",
            value=data_padrao,
            min_value=data_inicio,
            format="DD/MM/YYYY",
        )


        intervencao = st.text_area(
            "Intervenção realizada *",
            placeholder=(
                "Descreva o serviço efetivamente "
                "realizado no equipamento..."
            ),
            height=140,
        )


        observacoes = st.text_area(
            "Observações da conclusão",
            placeholder=(
                "Informações adicionais sobre "
                "a conclusão do serviço (opcional)"
            ),
            height=80,
        )


        confirmar = st.form_submit_button(
            "Concluir manutenção",
            type="primary",
            use_container_width=True,
        )


    # ========================================================
    # SALVAR CONCLUSÃO
    # ========================================================

    if confirmar:

        if not intervencao.strip():

            st.warning(
                "Informe a intervenção realizada."
            )

            return


        try:

            resultado = concluir_manutencao(
                manutencao_id=manutencao["id"],
                data_conclusao=data_conclusao,
                intervencao=intervencao,
                observacoes=observacoes,
            )


            numero_os = (
                manutencao.get("numero_os")
                or "Manutenção"
            )


            falha_resolvida = None

            if resultado:

                falha_resolvida = (
                    resultado[0].get(
                        "falha_resolvida_id"
                    )
                )


            if falha_resolvida:

                mensagem = (
                    f"{numero_os} concluída com sucesso. "
                    f"Falha #{falha_resolvida} resolvida."
                )

            else:

                mensagem = (
                    f"{numero_os} concluída com sucesso."
                )


            st.session_state[
                "toast_conclusao_manutencao"
            ] = mensagem


            st.rerun()


        except Exception as erro:

            st.error(
                "Não foi possível concluir "
                "a manutenção."
            )

            st.exception(erro)

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

codigo_url = (
    st.query_params.get("equipamento")
    or st.session_state.get( #protege caso o usuário tenha vindo do QR Code e a página tenha sido recarregada
        "equipamento_pendente"
    )
)

# ============================================================
# MENSAGEM DE SUCESSO APÓS MOVIMENTAÇÃO
# ============================================================

if "movimentacao_sucesso" in st.session_state:

    st.success(
        st.session_state.pop("movimentacao_sucesso")
    )

if "falha_sucesso" in st.session_state:

    st.success(
        st.session_state.pop(
            "falha_sucesso"
        )
    )

if "toast_manutencao_sucesso" in st.session_state:

    st.toast(
        st.session_state.pop(
            "toast_manutencao_sucesso"
        ),
        icon="✅",
    )

if "toast_conclusao_manutencao" in st.session_state:

    st.toast(
        st.session_state.pop(
            "toast_conclusao_manutencao"
        ),
        icon="✅",
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

            st.session_state.pop(
                "equipamento_pendente",
                None,
            )

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
    # STATUS DA MANUTENÇÃO PREVENTIVA
    # ========================================================

    try:

        preventiva = obter_status_preventiva(
            equipamento["id"]
        )

    except Exception as erro:

        preventiva = None

        st.warning(
            "Não foi possível calcular "
            "a próxima manutenção preventiva."
        )
    
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
    # MANUTENÇÃO PREVENTIVA
    # ========================================================

    st.markdown("#### Manutenção preventiva")


    if not preventiva:

        st.info(
            "Não foi possível obter informações "
            "sobre a manutenção preventiva."
        )


    else:

        situacao = preventiva.get(
            "situacao"
        )

        periodicidade = preventiva.get(
            "periodicidade_meses"
        )

        ultima = preventiva.get(
            "ultima_preventiva"
        )

        proxima = preventiva.get(
            "proxima_preventiva"
        )

        dias = preventiva.get(
            "dias_restantes"
        )


        # ====================================================
        # SEM PERIODICIDADE
        # ====================================================

        if situacao == "SEM_PERIODICIDADE":

            st.info(
                "Este modelo não possui periodicidade "
                "de manutenção preventiva cadastrada."
            )


        # ====================================================
        # SEM HISTÓRICO
        # ====================================================

        elif situacao == "SEM_HISTORICO":

            st.info(
                f"Periodicidade cadastrada: "
                f"**{periodicidade} meses**. "
                "Ainda não existe uma manutenção "
                "preventiva concluída para calcular "
                "a próxima data."
            )


        # ====================================================
        # COM HISTÓRICO
        # ====================================================

        else:

            col_prev1, col_prev2, col_prev3 = (
                st.columns(3)
            )


            with col_prev1:

                st.metric(
                    "Última preventiva",
                    formatar_data_hora(
                        ultima
                    ),
                )


            with col_prev2:

                st.metric(
                    "Periodicidade",
                    f"{periodicidade} meses",
                )


            with col_prev3:

                st.metric(
                    "Próxima preventiva",
                    formatar_data_hora(
                        proxima
                    ),
                )


            # ================================================
            # STATUS VISUAL
            # ================================================

            if situacao == "VENCIDA":

                dias_vencidos = abs(
                    dias
                )

                st.error(
                    f"🚨 Manutenção preventiva VENCIDA "
                    f"há **{dias_vencidos} dia(s)**."
                )


            elif situacao == "VENCE_HOJE":

                st.error(
                    "🚨 A manutenção preventiva "
                    "vence **hoje**."
                )


            elif situacao == "PROXIMA":

                st.warning(
                    f"⚠️ Próxima manutenção preventiva "
                    f"em **{dias} dia(s)**."
                )


            elif situacao == "EM_DIA":

                st.success(
                    f"✅ Manutenção preventiva em dia. "
                    f"Próxima em **{dias} dia(s)**."
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


    # --------------------------------------------------------
    # Verificar se o equipamento está baixado/inativo
    # --------------------------------------------------------

    equipamento_baixado = (
        equipamento.get("status") == "BAIXADO"
        or not equipamento.get(
            "ativo",
            True,
        )
    )


    # ========================================================
    # PRIMEIRA LINHA DE AÇÕES
    # ========================================================

    col_acao1, col_acao2, col_acao3 = (
        st.columns(3)
    )


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

        if st.button(
            "⚠️ Registrar falha",
            use_container_width=True,
            disabled=equipamento_baixado,
            help=(
                "Não é possível registrar novas falhas "
                "para equipamentos baixados ou inativos."
                if equipamento_baixado
                else None
            ),
        ):

            dialog_registrar_falha(
                equipamento
            )


    # --------------------------------------------------------
    # REGISTRAR MANUTENÇÃO
    # --------------------------------------------------------

    with col_acao3:

        if st.button(
            "🔧 Registrar manutenção",
            use_container_width=True,
            disabled=equipamento_baixado,
            help=(
                "Não é possível registrar manutenção "
                "para equipamentos baixados ou inativos."
                if equipamento_baixado
                else None
            ),
        ):

            dialog_registrar_manutencao(
                equipamento
            )


    # ========================================================
    # SEGUNDA LINHA DE AÇÕES
    # ========================================================

    col_acao4, col_acao5, col_acao6 = (
        st.columns(3)
    )


    # --------------------------------------------------------
    # CONCLUIR MANUTENÇÃO
    # --------------------------------------------------------

    with col_acao4:

        if st.button(
            "✅ Concluir manutenção",
            use_container_width=True,
        ):

            dialog_concluir_manutencao(
                equipamento
            )


    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    with col_acao5:

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

    with col_acao6:

        if st.button(
            "🔳 QR Code",
            use_container_width=True,
        ):

            dialog_qr_code(
                equipamento
            )