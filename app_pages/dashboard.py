from collections import Counter, defaultdict
from datetime import date, datetime
from statistics import mean

import pandas as pd
import streamlit as st

from services.dashboard import carregar_dados_dashboard


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def formatar_data(valor):
    """
    Converte YYYY-MM-DD para DD/MM/YYYY.
    """

    if not valor:
        return "-"

    try:
        data = date.fromisoformat(valor)
        return data.strftime("%d/%m/%Y")

    except (ValueError, TypeError):
        return str(valor)


def obter_dados_equipamento(equipamentos_por_id, equipamento_id):
    """
    Retorna código e tipo do equipamento.
    """

    equipamento = equipamentos_por_id.get(equipamento_id, {})
    modelo = equipamento.get("modelo") or {}

    return {
        "codigo": equipamento.get("codigo") or "-",
        "tipo": modelo.get("tipo") or "-",
    }


def calcular_mtbf_simples(falhas):
    """
    Calcula um MTBF simples e aproximado.

    Para cada equipamento com pelo menos duas falhas,
    calcula o intervalo em dias entre falhas consecutivas.

    O resultado final é a média desses intervalos.

    Este indicador não representa o MTBF completo baseado
    em tempo real de operação do equipamento.
    """

    falhas_por_equipamento = defaultdict(list)

    for falha in falhas:
        equipamento_id = falha.get("equipamento_id")
        data_hora = falha.get("data_hora")

        if not equipamento_id or not data_hora:
            continue

        try:
            data = datetime.fromisoformat(
                data_hora.replace("Z", "+00:00")
            )

        except (ValueError, TypeError, AttributeError):
            continue

        falhas_por_equipamento[equipamento_id].append(data)

    intervalos = []

    for datas in falhas_por_equipamento.values():
        if len(datas) < 2:
            continue

        datas.sort()

        for anterior, atual in zip(datas, datas[1:]):
            diferenca = atual - anterior
            dias = diferenca.total_seconds() / 86400

            if dias >= 0:
                intervalos.append(dias)

    if not intervalos:
        return None

    return mean(intervalos)


def calcular_duracao_media_corretivas(manutencoes):
    """
    Calcula a duração média, em dias,
    das manutenções corretivas concluídas.
    """

    duracoes = []

    for manutencao in manutencoes:
        if manutencao.get("tipo") != "CORRETIVA":
            continue

        if manutencao.get("status") != "CONCLUIDA":
            continue

        data_inicio = manutencao.get("data_inicio")
        data_conclusao = manutencao.get("data_conclusao")

        if not data_inicio or not data_conclusao:
            continue

        try:
            inicio = date.fromisoformat(data_inicio)
            conclusao = date.fromisoformat(data_conclusao)

        except (ValueError, TypeError):
            continue

        duracao = (conclusao - inicio).days

        if duracao >= 0:
            duracoes.append(duracao)

    if not duracoes:
        return None

    return mean(duracoes)


# ============================================================
# CABEÇALHO
# ============================================================

st.title("Dashboard")

st.caption(
    "Visão geral do parque de equipamentos "
    "e das atividades de Engenharia Clínica."
)

col_espaco, col_atualizar = st.columns([5, 1])

with col_atualizar:
    if st.button(
        "🔄 Atualizar",
        width="stretch",
    ):
        st.rerun()


# ============================================================
# CARREGAR DADOS
# ============================================================

try:
    dados = carregar_dados_dashboard()

except Exception as erro:
    st.error(
        "Não foi possível carregar os dados "
        "do Dashboard."
    )

    st.exception(erro)
    st.stop()


equipamentos = dados["equipamentos"]
falhas = dados["falhas"]
manutencoes = dados["manutencoes"]
preventivas = dados["preventivas"]


# ============================================================
# MAPA DE EQUIPAMENTOS
# ============================================================

equipamentos_por_id = {
    equipamento["id"]: equipamento
    for equipamento in equipamentos
}


# ============================================================
# CALCULAR INDICADORES
# ============================================================

equipamentos_ativos = [
    equipamento
    for equipamento in equipamentos
    if equipamento.get("ativo")
    and equipamento.get("status") != "BAIXADO"
]


preventivas_vencidas = [
    preventiva
    for preventiva in preventivas
    if preventiva.get("situacao") == "VENCIDA"
]


preventivas_proximas = [
    preventiva
    for preventiva in preventivas
    if preventiva.get("situacao")
    in (
        "PROXIMA",
        "VENCE_HOJE",
    )
]


falhas_pendentes = [
    falha
    for falha in falhas
    if falha.get("status")
    in (
        "ABERTA",
        "EM_ANALISE",
    )
]


falhas_prioritarias = [
    falha
    for falha in falhas_pendentes
    if falha.get("gravidade")
    in (
        "ALTA",
        "CRÍTICA",
    )
]


manutencoes_pendentes = [
    manutencao
    for manutencao in manutencoes
    if manutencao.get("status")
    in (
        "ABERTA",
        "EM_ANDAMENTO",
    )
]


mtbf_simples = calcular_mtbf_simples(falhas)

duracao_media_corretivas = calcular_duracao_media_corretivas(
    manutencoes
)


# ============================================================
# INDICADORES PRINCIPAIS
# ============================================================

st.subheader("Indicadores")


# ------------------------------------------------------------
# PRIMEIRA LINHA
# ------------------------------------------------------------

col1, col2, col3 = st.columns(3)


with col1:
    st.metric(
        "Equipamentos ativos",
        len(equipamentos_ativos),
        border=True,
    )


with col2:
    st.metric(
        "Preventivas vencidas",
        len(preventivas_vencidas),
        border=True,
    )


with col3:
    st.metric(
        "Preventivas ≤ 30 dias",
        len(preventivas_proximas),
        border=True,
    )


# ------------------------------------------------------------
# SEGUNDA LINHA
# ------------------------------------------------------------

col4, col5, col6 = st.columns(3)


with col4:
    st.metric(
        "Falhas abertas",
        len(falhas_pendentes),
        border=True,
        help=(
            "Falhas com status ABERTA "
            "ou EM_ANALISE."
        ),
    )


with col5:
    st.metric(
        "Falhas ALTA/CRÍTICA",
        len(falhas_prioritarias),
        border=True,
        help=(
            "Falhas com status ABERTA ou EM_ANALISE "
            "e gravidade ALTA ou CRÍTICA."
        ),
    )


with col6:
    st.metric(
        "Manutenções pendentes",
        len(manutencoes_pendentes),
        border=True,
        help=(
            "Manutenções com status ABERTA "
            "ou EM_ANDAMENTO."
        ),
    )


# ------------------------------------------------------------
# TERCEIRA LINHA
# ------------------------------------------------------------

col7, col8 = st.columns(2)


with col7:
    valor_mtbf = (
        f"{mtbf_simples:.1f} dias"
        if mtbf_simples is not None
        else "—"
    )

    st.metric(
        "MTBF simples (aprox.)",
        valor_mtbf,
        border=True,
        help=(
            "Média do intervalo entre registros de falhas "
            "consecutivas dos equipamentos que possuem pelo "
            "menos duas falhas. É um indicador aproximado, "
            "pois o sistema não registra o tempo operacional "
            "efetivo dos equipamentos."
        ),
    )


with col8:
    valor_corretivas = (
        f"{duracao_media_corretivas:.1f} dias"
        if duracao_media_corretivas is not None
        else "—"
    )

    st.metric(
        "Duração média das corretivas",
        valor_corretivas,
        border=True,
        help=(
            "Média de dias entre a data de início "
            "e a data de conclusão das manutenções "
            "corretivas concluídas."
        ),
    )


# ============================================================
# ALERTAS GERAIS
# ============================================================

st.divider()

st.subheader("Alertas")


if preventivas_vencidas:
    st.error(
        f"🚨 Existem "
        f"**{len(preventivas_vencidas)} "
        f"preventiva(s) vencida(s)**."
    )


if preventivas_proximas:
    st.warning(
        f"⚠️ Existem "
        f"**{len(preventivas_proximas)} "
        f"preventiva(s)** com vencimento "
        f"nos próximos 30 dias."
    )


if falhas_prioritarias:
    st.warning(
        f"⚠️ Existem "
        f"**{len(falhas_prioritarias)} "
        f"falha(s) aberta(s) ou em análise "
        f"com gravidade ALTA ou CRÍTICA**."
    )


if (
    not preventivas_vencidas
    and not preventivas_proximas
    and not falhas_prioritarias
):
    st.success(
        "✅ Não existem alertas prioritários "
        "no momento."
    )


# ============================================================
# PREVENTIVAS PRIORITÁRIAS
# ============================================================

st.divider()

st.subheader("Manutenções preventivas")


col_vencidas, col_proximas = st.columns(2)


# ------------------------------------------------------------
# VENCIDAS
# ------------------------------------------------------------

with col_vencidas:
    st.markdown("#### 🚨 Vencidas")

    if preventivas_vencidas:
        preventivas_vencidas_ordenadas = sorted(
            preventivas_vencidas,
            key=lambda item: item.get("dias_restantes") or 0,
        )

        linhas_vencidas = []

        for preventiva in preventivas_vencidas_ordenadas:
            dias = preventiva.get("dias_restantes") or 0

            linhas_vencidas.append(
                {
                    "Código": preventiva.get("codigo"),
                    "Equipamento": preventiva.get(
                        "tipo_equipamento"
                    ),
                    "Próxima preventiva": formatar_data(
                        preventiva.get(
                            "proxima_preventiva"
                        )
                    ),
                    "Atraso (dias)": abs(dias),
                }
            )

        st.dataframe(
            linhas_vencidas,
            hide_index=True,
            width="stretch",
        )

    else:
        st.success(
            "Nenhuma preventiva vencida."
        )


# ------------------------------------------------------------
# PRÓXIMAS
# ------------------------------------------------------------

with col_proximas:
    st.markdown("#### ⚠️ Próximos 30 dias")

    if preventivas_proximas:
        preventivas_proximas_ordenadas = sorted(
            preventivas_proximas,
            key=lambda item: item.get("dias_restantes") or 0,
        )

        linhas_proximas = []

        for preventiva in preventivas_proximas_ordenadas:
            linhas_proximas.append(
                {
                    "Código": preventiva.get("codigo"),
                    "Equipamento": preventiva.get(
                        "tipo_equipamento"
                    ),
                    "Próxima preventiva": formatar_data(
                        preventiva.get(
                            "proxima_preventiva"
                        )
                    ),
                    "Dias restantes": preventiva.get(
                        "dias_restantes"
                    ),
                }
            )

        st.dataframe(
            linhas_proximas,
            hide_index=True,
            width="stretch",
        )

    else:
        st.success(
            "Nenhuma preventiva prevista "
            "para os próximos 30 dias."
        )


# ============================================================
# DISTRIBUIÇÕES
# ============================================================

st.divider()

st.subheader("Distribuições")


col_status, col_gravidade = st.columns(2)


# ------------------------------------------------------------
# EQUIPAMENTOS POR STATUS
# ------------------------------------------------------------

with col_status:
    st.markdown("#### Equipamentos por status")

    contagem_status = Counter(
        equipamento.get(
            "status",
            "SEM_STATUS",
        )
        for equipamento in equipamentos_ativos
    )

    dados_status = pd.DataFrame(
        [
            {
                "Status": status,
                "Quantidade": quantidade,
            }
            for status, quantidade
            in contagem_status.items()
        ]
    )

    if not dados_status.empty:
        st.bar_chart(
            dados_status,
            x="Status",
            y="Quantidade",
            width="stretch",
        )

    else:
        st.info(
            "Nenhum equipamento disponível."
        )


# ------------------------------------------------------------
# FALHAS POR GRAVIDADE
# ------------------------------------------------------------

with col_gravidade:
    st.markdown("#### Falhas por gravidade")

    contagem_gravidade = Counter(
        falha.get("gravidade")
        or "NÃO INFORMADA"
        for falha in falhas
    )

    ordem_gravidade = [
        "CRÍTICA",
        "ALTA",
        "MODERADA",
        "BAIXA",
        "NÃO INFORMADA",
    ]

    dados_gravidade = pd.DataFrame(
        [
            {
                "Gravidade": gravidade,
                "Quantidade": contagem_gravidade.get(
                    gravidade,
                    0,
                ),
            }
            for gravidade in ordem_gravidade
            if contagem_gravidade.get(
                gravidade,
                0,
            ) > 0
        ]
    )

    if not dados_gravidade.empty:
        st.bar_chart(
            dados_gravidade,
            x="Gravidade",
            y="Quantidade",
            sort=False,
            width="stretch",
        )

    else:
        st.info(
            "Nenhuma falha registrada."
        )


# ============================================================
# EQUIPAMENTOS COM MAIS FALHAS
# ============================================================

st.divider()

st.subheader("Equipamentos com mais falhas")

st.caption(
    "Ranking considerando todos os registros "
    "de falha existentes no sistema."
)


contagem_falhas_equipamento = Counter(
    falha.get("equipamento_id")
    for falha in falhas
    if falha.get("equipamento_id")
)


ranking = []


for equipamento_id, quantidade in contagem_falhas_equipamento.items():
    equipamento = equipamentos_por_id.get(
        equipamento_id,
        {},
    )

    modelo = equipamento.get("modelo") or {}

    codigo = (
        equipamento.get("codigo")
        or f"ID {equipamento_id}"
    )

    tipo = (
        modelo.get("tipo")
        or "Equipamento"
    )

    ranking.append(
        {
            "Equipamento": f"{codigo} — {tipo}",
            "Falhas": quantidade,
        }
    )


ranking = sorted(
    ranking,
    key=lambda item: item["Falhas"],
    reverse=True,
)[:10]


dados_ranking = pd.DataFrame(
    ranking
)


if not dados_ranking.empty:
    st.bar_chart(
        dados_ranking,
        x="Equipamento",
        y="Falhas",
        horizontal=True,
        sort=False,
        width="stretch",
    )

else:
    st.info(
        "Ainda não existem falhas registradas."
    )


# ============================================================
# FALHAS PENDENTES
# ============================================================

st.divider()

st.subheader(
    "Falhas abertas / em análise"
)


if falhas_pendentes:
    prioridade_gravidade = {
        "CRÍTICA": 0,
        "ALTA": 1,
        "MODERADA": 2,
        "BAIXA": 3,
        None: 4,
    }

    falhas_ordenadas = sorted(
        falhas_pendentes,
        key=lambda falha: prioridade_gravidade.get(
            falha.get("gravidade"),
            4,
        ),
    )

    linhas_falhas = []

    for falha in falhas_ordenadas:
        equipamento = obter_dados_equipamento(
            equipamentos_por_id,
            falha.get("equipamento_id"),
        )

        descricao = falha.get("descricao") or "-"

        if len(descricao) > 80:
            descricao = descricao[:80] + "..."

        linhas_falhas.append(
            {
                "Código": equipamento["codigo"],
                "Equipamento": equipamento["tipo"],
                "Gravidade": falha.get("gravidade") or "-",
                "Categoria": falha.get("categoria") or "-",
                "Status": falha.get("status") or "-",
                "Descrição": descricao,
            }
        )

    st.dataframe(
        linhas_falhas,
        hide_index=True,
        width="stretch",
    )

else:
    st.success(
        "Nenhuma falha aberta ou em análise."
    )


# ============================================================
# MANUTENÇÕES PENDENTES
# ============================================================

st.divider()

st.subheader(
    "Manutenções abertas / em andamento"
)


if manutencoes_pendentes:
    linhas_manutencoes = []

    for manutencao in manutencoes_pendentes:
        equipamento = obter_dados_equipamento(
            equipamentos_por_id,
            manutencao.get("equipamento_id"),
        )

        linhas_manutencoes.append(
            {
                "OS": manutencao.get("numero_os") or "-",
                "Código": equipamento["codigo"],
                "Equipamento": equipamento["tipo"],
                "Tipo": manutencao.get("tipo") or "-",
                "Início": formatar_data(
                    manutencao.get("data_inicio")
                ),
                "Status": manutencao.get("status") or "-",
            }
        )

    st.dataframe(
        linhas_manutencoes,
        hide_index=True,
        width="stretch",
    )

else:
    st.success(
        "Nenhuma manutenção aberta "
        "ou em andamento."
    )