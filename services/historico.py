from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from services.database import get_supabase


FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _converter_data(valor, fim_do_dia=False):
    """
    Converte datas vindas do Supabase para datetime.

    Datas com horário preservam o horário real.
    Datas sem horário recebem um horário apenas para permitir
    a ordenação interna da linha do tempo.
    """

    if not valor:
        return None

    try:

        valor = str(valor)

        # Data com horário
        if "T" in valor:

            data = datetime.fromisoformat(
                valor.replace(
                    "Z",
                    "+00:00",
                )
            )

            if data.tzinfo is None:

                data = data.replace(
                    tzinfo=FUSO_HORARIO
                )

            return data.astimezone(
                FUSO_HORARIO
            )

        # Data sem horário
        data = date.fromisoformat(
            valor
        )

        horario = (
            time(23, 59, 59)
            if fim_do_dia
            else time(0, 0, 0)
        )

        return datetime.combine(
            data,
            horario,
            tzinfo=FUSO_HORARIO,
        )

    except (ValueError, TypeError):

        return None


def _formatar_local(local):
    """
    Retorna o local em formato amigável.
    """

    if not local:
        return "-"

    setor = (
        local.get("setor")
        or "-"
    )

    sala = (
        local.get("sala")
        or "-"
    )

    return f"{setor} — {sala}"


# ============================================================
# HISTÓRICO COMPLETO
# ============================================================

def listar_historico_equipamento(
    equipamento_id: int,
):
    """
    Reúne em uma única linha do tempo:

    - movimentações
    - falhas
    - manutenções
    - eventos de inventário

    Os eventos são retornados do mais recente
    para o mais antigo.
    """

    supabase = get_supabase()

    eventos = []


    # ========================================================
    # MOVIMENTAÇÕES
    # ========================================================

    movimentacoes_response = (
        supabase
        .table("movimentacoes")
        .select(
            """
            id,
            data_hora,
            motivo,
            observacoes,

            origem:locais!movimentacoes_local_origem_id_fkey (
                id,
                setor,
                sala,
                codigo
            ),

            destino:locais!movimentacoes_local_destino_id_fkey (
                id,
                setor,
                sala,
                codigo
            )
            """
        )
        .eq(
            "equipamento_id",
            equipamento_id,
        )
        .execute()
    )


    for movimentacao in (
        movimentacoes_response.data
        or []
    ):

        data_evento = _converter_data(
            movimentacao.get(
                "data_hora"
            )
        )

        if not data_evento:
            continue


        origem = (
            movimentacao.get(
                "origem"
            )
            or {}
        )

        destino = (
            movimentacao.get(
                "destino"
            )
            or {}
        )


        detalhes = {
            "Origem":
                _formatar_local(
                    origem
                ),

            "Destino":
                _formatar_local(
                    destino
                ),
        }


        if movimentacao.get(
            "motivo"
        ):

            detalhes["Motivo"] = (
                movimentacao[
                    "motivo"
                ]
            )


        if movimentacao.get(
            "observacoes"
        ):

            detalhes["Observações"] = (
                movimentacao[
                    "observacoes"
                ]
            )


        eventos.append(
            {
                "categoria":
                    "MOVIMENTACAO",

                "icone":
                    "📍",

                "titulo":
                    "Movimentação",

                "resumo":
                    (
                        f"{_formatar_local(origem)} "
                        f"→ "
                        f"{_formatar_local(destino)}"
                    ),

                "data_ordem":
                    data_evento,

                "mostrar_hora":
                    True,

                "detalhes":
                    detalhes,
            }
        )


    # ========================================================
    # FALHAS
    # ========================================================

    falhas_response = (
        supabase
        .table("falhas")
        .select(
            """
            id,
            data_hora,
            categoria,
            descricao,
            gravidade,
            status
            """
        )
        .eq(
            "equipamento_id",
            equipamento_id,
        )
        .execute()
    )


    for falha in (
        falhas_response.data
        or []
    ):

        data_evento = _converter_data(
            falha.get(
                "data_hora"
            )
        )


        if not data_evento:
            continue


        categoria = (
            falha.get(
                "categoria"
            )
            or "Sem categoria"
        )

        gravidade = (
            falha.get(
                "gravidade"
            )
            or "Sem gravidade"
        )


        detalhes = {
            "Status":
                falha.get(
                    "status"
                )
                or "-",

            "Categoria":
                categoria,

            "Gravidade":
                gravidade,

            "Descrição":
                falha.get(
                    "descricao"
                )
                or "-",
        }


        eventos.append(
            {
                "categoria":
                    "FALHA",

                "icone":
                    "⚠️",

                "titulo":
                    "Falha registrada",

                "resumo":
                    f"{categoria} — {gravidade}",

                "data_ordem":
                    data_evento,

                "mostrar_hora":
                    True,

                "detalhes":
                    detalhes,
            }
        )


    # ========================================================
    # MANUTENÇÕES
    # ========================================================

    manutencoes_response = (
        supabase
        .table("manutencoes")
        .select(
            """
            id,
            numero_os,
            tipo,
            data_inicio,
            data_conclusao,
            descricao,
            intervencao,
            responsavel,
            empresa,
            status,
            observacoes,
            falha_id
            """
        )
        .eq(
            "equipamento_id",
            equipamento_id,
        )
        .execute()
    )


    for manutencao in (
        manutencoes_response.data
        or []
    ):

        numero_os = (
            manutencao.get(
                "numero_os"
            )
            or "Sem OS"
        )

        tipo = (
            manutencao.get(
                "tipo"
            )
            or "-"
        )


        # ----------------------------------------------------
        # EVENTO: INÍCIO DA MANUTENÇÃO
        # ----------------------------------------------------

        data_inicio = _converter_data(
            manutencao.get(
                "data_inicio"
            )
        )


        if data_inicio:

            detalhes_inicio = {
                "OS":
                    numero_os,

                "Tipo":
                    tipo,

                "Status atual":
                    manutencao.get(
                        "status"
                    )
                    or "-",

                "Descrição":
                    manutencao.get(
                        "descricao"
                    )
                    or "-",
            }


            if manutencao.get(
                "responsavel"
            ):

                detalhes_inicio[
                    "Responsável"
                ] = manutencao[
                    "responsavel"
                ]


            if manutencao.get(
                "empresa"
            ):

                detalhes_inicio[
                    "Empresa"
                ] = manutencao[
                    "empresa"
                ]


            if manutencao.get(
                "falha_id"
            ):

                detalhes_inicio[
                    "Falha vinculada"
                ] = (
                    f"#{manutencao['falha_id']}"
                )


            eventos.append(
                {
                    "categoria":
                        "MANUTENCAO",

                    "icone":
                        "🔧",

                    "titulo":
                        "Manutenção iniciada",

                    "resumo":
                        f"{numero_os} — {tipo}",

                    "data_ordem":
                        data_inicio,

                    "mostrar_hora":
                        False,

                    "detalhes":
                        detalhes_inicio,
                }
            )


        # ----------------------------------------------------
        # EVENTO: CONCLUSÃO DA MANUTENÇÃO
        # ----------------------------------------------------

        if (
            manutencao.get(
                "status"
            ) == "CONCLUIDA"
            and manutencao.get(
                "data_conclusao"
            )
        ):

            data_conclusao = (
                _converter_data(
                    manutencao[
                        "data_conclusao"
                    ],
                    fim_do_dia=True,
                )
            )


            if data_conclusao:

                detalhes_conclusao = {
                    "OS":
                        numero_os,

                    "Tipo":
                        tipo,

                    "Intervenção realizada":
                        manutencao.get(
                            "intervencao"
                        )
                        or "-",
                }


                if manutencao.get(
                    "falha_id"
                ):

                    detalhes_conclusao[
                        "Falha vinculada"
                    ] = (
                        f"#{manutencao['falha_id']}"
                    )


                if manutencao.get(
                    "observacoes"
                ):

                    detalhes_conclusao[
                        "Observações"
                    ] = manutencao[
                        "observacoes"
                    ]


                eventos.append(
                    {
                        "categoria":
                            "MANUTENCAO",

                        "icone":
                            "✅",

                        "titulo":
                            "Manutenção concluída",

                        "resumo":
                            (
                                f"{numero_os} "
                                f"— {tipo}"
                            ),

                        "data_ordem":
                            data_conclusao,

                        "mostrar_hora":
                            False,

                        "detalhes":
                            detalhes_conclusao,
                    }
                )


    # ========================================================
    # INVENTÁRIOS
    # ========================================================

    inventarios_response = (
        supabase
        .table("inventario_itens")
        .select(
            """
            id,
            data_hora,
            created_at,
            resultado,
            observacoes,

            inventario:inventarios!inventario_itens_inventario_id_fkey (
                id,
                nome,
                data_inicio,
                data_fim,
                status
            ),

            esperado:locais!inventario_itens_local_esperado_id_fkey (
                id,
                setor,
                sala,
                codigo
            ),

            encontrado:locais!inventario_itens_local_encontrado_id_fkey (
                id,
                setor,
                sala,
                codigo
            )
            """
        )
        .eq(
            "equipamento_id",
            equipamento_id,
        )
        .execute()
    )


    for item in (
        inventarios_response.data
        or []
    ):

        resultado = item.get(
            "resultado"
        )


        # PENDENTE ainda não representa
        # um evento concluído de inventário.
        if resultado == "PENDENTE":
            continue


        inventario = (
            item.get(
                "inventario"
            )
            or {}
        )


        mostrar_hora = True


        # Itens encontrados possuem data_hora.
        if item.get(
            "data_hora"
        ):

            data_evento = (
                _converter_data(
                    item[
                        "data_hora"
                    ]
                )
            )


        # NÃO ENCONTRADO é definido
        # na finalização do inventário.
        elif (
            resultado
            == "NAO_ENCONTRADO"
            and inventario.get(
                "data_fim"
            )
        ):

            data_evento = (
                _converter_data(
                    inventario[
                        "data_fim"
                    ],
                    fim_do_dia=True,
                )
            )

            mostrar_hora = False


        else:

            data_evento = (
                _converter_data(
                    item.get(
                        "created_at"
                    )
                )
            )


        if not data_evento:
            continue


        titulos = {
            "CORRETO":
                "Inventário — conferido",

            "DIVERGENTE":
                "Inventário — divergência",

            "NAO_PREVISTO":
                "Inventário — não previsto",

            "NAO_ENCONTRADO":
                "Inventário — não encontrado",
        }


        detalhes = {
            "Inventário":
                inventario.get(
                    "nome"
                )
                or "-",

            "Resultado":
                resultado,

            "Local esperado":
                _formatar_local(
                    item.get(
                        "esperado"
                    )
                ),

            "Local encontrado":
                (
                    _formatar_local(
                        item.get(
                            "encontrado"
                        )
                    )
                    if item.get(
                        "encontrado"
                    )
                    else "-"
                ),
        }


        if item.get(
            "observacoes"
        ):

            detalhes[
                "Observações"
            ] = item[
                "observacoes"
            ]


        eventos.append(
            {
                "categoria":
                    "INVENTARIO",

                "icone":
                    "📦",

                "titulo":
                    titulos.get(
                        resultado,
                        "Inventário",
                    ),

                "resumo":
                    inventario.get(
                        "nome"
                    )
                    or "Inventário",

                "data_ordem":
                    data_evento,

                "mostrar_hora":
                    mostrar_hora,

                "detalhes":
                    detalhes,
            }
        )


    # ========================================================
    # ORDENAR
    # ========================================================

    eventos.sort(
        key=lambda evento:
            evento["data_ordem"],
        reverse=True,
    )


    return eventos