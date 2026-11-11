from services.database import get_supabase


def carregar_dados_dashboard():
    """
    Carrega os dados necessários para o Dashboard.

    Retorna:
    - equipamentos ativos
    - falhas pendentes
    - manutenções pendentes
    - situação das preventivas
    """

    supabase = get_supabase()

    # ========================================================
    # EQUIPAMENTOS
    # ========================================================

    equipamentos_response = (
        supabase
        .table("equipamentos")
        .select(
            """
            id,
            codigo,
            status,
            ativo,

            modelo:modelos_equipamento (
                tipo,
                fabricante,
                modelo
            )
            """
        )
        .eq(
            "ativo",
            True,
        )
        .execute()
    )


    # ========================================================
    # FALHAS ABERTAS / EM ANÁLISE
    # ========================================================

    falhas_response = (
        supabase
        .table("falhas")
        .select(
            """
            id,
            equipamento_id,
            data_hora,
            categoria,
            descricao,
            gravidade,
            status
            """
        )
        .in_(
            "status",
            [
                "ABERTA",
                "EM_ANALISE",
            ],
        )
        .order(
            "data_hora",
            desc=True,
        )
        .execute()
    )


    # ========================================================
    # MANUTENÇÕES ABERTAS / EM ANDAMENTO
    # ========================================================

    manutencoes_response = (
        supabase
        .table("manutencoes")
        .select(
            """
            id,
            equipamento_id,
            numero_os,
            tipo,
            data_inicio,
            descricao,
            status
            """
        )
        .in_(
            "status",
            [
                "ABERTA",
                "EM_ANDAMENTO",
            ],
        )
        .order(
            "data_inicio",
            desc=True,
        )
        .execute()
    )


    # ========================================================
    # PREVENTIVAS
    # ========================================================

    preventivas_response = (
        supabase
        .rpc(
            "listar_status_preventivas"
        )
        .execute()
    )


    return {
        "equipamentos": (
            equipamentos_response.data
            or []
        ),

        "falhas": (
            falhas_response.data
            or []
        ),

        "manutencoes": (
            manutencoes_response.data
            or []
        ),

        "preventivas": (
            preventivas_response.data
            or []
        ),
    }