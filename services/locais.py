from services.database import get_supabase


def listar_locais_ativos():
    supabase = get_supabase()

    response = (
        supabase
        .table("locais")
        .select(
            """
            id,
            hospital,
            bloco,
            ala,
            setor,
            sala,
            codigo
            """
        )
        .eq("ativo", True)
        .order("setor")
        .order("sala")
        .execute()
    )

    return response.data