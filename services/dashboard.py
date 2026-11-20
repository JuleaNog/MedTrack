from services.database import get_supabase


def carregar_dados_dashboard():
    """
    Carrega os dados necessários para o Dashboard.

    Retorna:
    - equipamentos ativos
    - falhas
    - manutenções
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
        .execute()
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
            equipamento_id,
            data_hora,
            categoria,
            descricao,
            gravidade,
            status
            """
        )
        .order("data_hora", desc=True)
        .execute()
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
            equipamento_id,
            numero_os,
            tipo,
            data_inicio,
            data_conclusao,
            descricao,
            status
            """
        )
        .order("data_inicio", desc=True)
        .execute()
    )

    # ========================================================
    # PREVENTIVAS
    # ========================================================

    preventivas_response = (
        supabase
        .rpc("listar_status_preventivas")
        .execute()
    )

    return {
        "equipamentos": equipamentos_response.data or [],
        "falhas": falhas_response.data or [],
        "manutencoes": manutencoes_response.data or [],
        "preventivas": preventivas_response.data or [],
    }