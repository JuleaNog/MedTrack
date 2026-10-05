from services.database import get_supabase


def registrar_movimentacao(
    equipamento_id: int,
    local_destino_id: int,
    motivo: str | None = None,
    observacoes: str | None = None,
):
    """
    Registra a movimentação utilizando
    a sessão do usuário autenticado.
    """

    supabase = get_supabase()

    response = (
        supabase
        .rpc(
            "registrar_movimentacao",
            {
                "p_equipamento_id": equipamento_id,
                "p_local_destino_id": local_destino_id,
                "p_motivo": motivo,
                "p_observacoes": observacoes,
            },
        )
        .execute()
    )

    return response.data


def listar_movimentacoes_equipamento(
    equipamento_id: int,
):
    """
    Lista o histórico de movimentações.
    """

    supabase = get_supabase()

    response = (
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
        .order(
            "data_hora",
            desc=True,
        )
        .execute()
    )

    return response.data