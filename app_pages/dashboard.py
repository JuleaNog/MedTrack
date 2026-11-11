from collections import Counter
from datetime import date

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

        return data.strftime(
            "%d/%m/%Y"
        )

    except (ValueError, TypeError):
        return str(valor)


def obter_dados_equipamento(
    equipamentos_por_id,
    equipamento_id,
):
    """
    Retorna código e tipo do equipamento.
    """

    equipamento = equipamentos_por_id.get(
        equipamento_id,
        {},
    )

    modelo = equipamento.get(
        "modelo"
    ) or {}

    return {
        "codigo": (
            equipamento.get("codigo")
            or "-"
        ),

        "tipo": (
            modelo.get("tipo")
            or "-"
        ),
    }


# ============================================================
# CABEÇALHO
# ============================================================

st.title("Dashboard")

st.caption(
    "Visão geral do parque de equipamentos "
    "e das atividades de Engenharia Clínica."
)


col_titulo, col_atualizar = st.columns(
    [5, 1]
)


with col_atualizar:

    if st.button(
        "🔄 Atualizar",
        use_container_width=True,
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
    and equipamento.get("status")
    != "BAIXADO"
]


preventivas_vencidas = [
    preventiva
    for preventiva in preventivas
    if preventiva.get("situacao")
    == "VENCIDA"
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


falhas_pendentes = falhas


manutencoes_pendentes = manutencoes


# ============================================================
# INDICADORES PRINCIPAIS
# ============================================================

st.subheader("Indicadores")


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


col4, col5 = st.columns(2)


with col4:

    st.metric(
        "Falhas abertas",
        len(falhas_pendentes),
        border=True,
    )


with col5:

    st.metric(
        "Manutenções pendentes",
        len(manutencoes_pendentes),
        border=True,
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


if (
    not preventivas_vencidas
    and not preventivas_proximas
):

    st.success(
        "✅ Não existem preventivas vencidas "
        "ou previstas para os próximos 30 dias."
    )


# ============================================================
# PREVENTIVAS PRIORITÁRIAS
# ============================================================

st.divider()

st.subheader("Manutenções preventivas")


col_vencidas, col_proximas = (
    st.columns(2)
)


# ------------------------------------------------------------
# VENCIDAS
# ------------------------------------------------------------

with col_vencidas:

    st.markdown(
        "#### 🚨 Vencidas"
    )


    if preventivas_vencidas:

        preventivas_vencidas = sorted(
            preventivas_vencidas,
            key=lambda item: (
                item.get(
                    "dias_restantes"
                )
                or 0
            ),
        )


        linhas = []


        for preventiva in preventivas_vencidas:

            dias = (
                preventiva.get(
                    "dias_restantes"
                )
                or 0
            )

            linhas.append(
                {
                    "Código": (
                        preventiva.get(
                            "codigo"
                        )
                    ),

                    "Equipamento": (
                        preventiva.get(
                            "tipo_equipamento"
                        )
                    ),

                    "Próxima preventiva": (
                        formatar_data(
                            preventiva.get(
                                "proxima_preventiva"
                            )
                        )
                    ),

                    "Atraso (dias)": (
                        abs(dias)
                    ),
                }
            )


        st.dataframe(
            linhas,
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

    st.markdown(
        "#### ⚠️ Próximos 30 dias"
    )


    if preventivas_proximas:

        preventivas_proximas = sorted(
            preventivas_proximas,
            key=lambda item: (
                item.get(
                    "dias_restantes"
                )
                or 0
            ),
        )


        linhas = []


        for preventiva in preventivas_proximas:

            linhas.append(
                {
                    "Código": (
                        preventiva.get(
                            "codigo"
                        )
                    ),

                    "Equipamento": (
                        preventiva.get(
                            "tipo_equipamento"
                        )
                    ),

                    "Próxima preventiva": (
                        formatar_data(
                            preventiva.get(
                                "proxima_preventiva"
                            )
                        )
                    ),

                    "Dias restantes": (
                        preventiva.get(
                            "dias_restantes"
                        )
                    ),
                }
            )


        st.dataframe(
            linhas,
            hide_index=True,
            width="stretch",
        )


    else:

        st.success(
            "Nenhuma preventiva prevista "
            "para os próximos 30 dias."
        )


# ============================================================
# DISTRIBUIÇÃO POR STATUS
# ============================================================

st.divider()

st.subheader(
    "Distribuição dos equipamentos"
)


contagem_status = Counter(
    equipamento.get(
        "status",
        "SEM_STATUS",
    )
    for equipamento
    in equipamentos_ativos
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
        "Nenhum equipamento disponível "
        "para gerar o gráfico."
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

        key=lambda falha: (
            prioridade_gravidade.get(
                falha.get(
                    "gravidade"
                ),
                4,
            )
        ),
    )


    linhas_falhas = []


    for falha in falhas_ordenadas:

        equipamento = (
            obter_dados_equipamento(
                equipamentos_por_id,
                falha.get(
                    "equipamento_id"
                ),
            )
        )


        descricao = (
            falha.get("descricao")
            or "-"
        )


        if len(descricao) > 80:

            descricao = (
                descricao[:80]
                + "..."
            )


        linhas_falhas.append(
            {
                "Código": (
                    equipamento[
                        "codigo"
                    ]
                ),

                "Equipamento": (
                    equipamento[
                        "tipo"
                    ]
                ),

                "Gravidade": (
                    falha.get(
                        "gravidade"
                    )
                    or "-"
                ),

                "Categoria": (
                    falha.get(
                        "categoria"
                    )
                    or "-"
                ),

                "Status": (
                    falha.get(
                        "status"
                    )
                ),

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

        equipamento = (
            obter_dados_equipamento(
                equipamentos_por_id,
                manutencao.get(
                    "equipamento_id"
                ),
            )
        )


        linhas_manutencoes.append(
            {
                "OS": (
                    manutencao.get(
                        "numero_os"
                    )
                    or "-"
                ),

                "Código": (
                    equipamento[
                        "codigo"
                    ]
                ),

                "Equipamento": (
                    equipamento[
                        "tipo"
                    ]
                ),

                "Tipo": (
                    manutencao.get(
                        "tipo"
                    )
                    or "-"
                ),

                "Início": (
                    formatar_data(
                        manutencao.get(
                            "data_inicio"
                        )
                    )
                ),

                "Status": (
                    manutencao.get(
                        "status"
                    )
                    or "-"
                ),
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