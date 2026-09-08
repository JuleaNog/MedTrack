from services.database import get_supabase_admin


def registrar_movimentacao(
    equipamento_id: int,
    local_destino_id: int,
    motivo: str | None = None,
    observacoes: str | None = None,
):
    supabase = get_supabase_admin()

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