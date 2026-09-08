from services.database import get_supabase


def listar_equipamentos():
    supabase = get_supabase()

    response = (
        supabase
        .table("equipamentos")
        .select(
            """
            id,
            codigo,
            patrimonio,
            numero_serie,
            data_aquisicao,
            data_instalacao,
            status,
            criticidade,
            observacoes,
            ativo,
            modelo:modelos_equipamento (
                id,
                tipo,
                fabricante,
                modelo,
                periodicidade_preventiva_meses
            ),
            local:locais (
                id,
                hospital,
                bloco,
                ala,
                setor,
                sala,
                codigo
            )
            """
        )
        .order("codigo")
        .execute()
    )

    return response.data


def buscar_equipamento_por_id(equipamento_id: int):
    supabase = get_supabase()

    response = (
        supabase
        .table("equipamentos")
        .select(
            """
            id,
            codigo,
            patrimonio,
            numero_serie,
            data_aquisicao,
            data_instalacao,
            status,
            criticidade,
            observacoes,
            ativo,
            modelo:modelos_equipamento (
                id,
                tipo,
                fabricante,
                modelo,
                periodicidade_preventiva_meses
            ),
            local:locais (
                id,
                hospital,
                bloco,
                ala,
                setor,
                sala,
                codigo
            )
            """
        )
        .eq("id", equipamento_id)
        .single()
        .execute()
    )

    return response.data