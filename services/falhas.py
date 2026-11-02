from services.database import get_supabase


def registrar_falha(
    equipamento_id: int,
    descricao: str,
    categoria: str | None = None,
    gravidade: str | None = None,
):
    """
    Registra uma nova falha para o equipamento.

    O banco define automaticamente:
    - data_hora
    - status = ABERTA
    - created_at
    """

    supabase = get_supabase()

    dados = {
        "equipamento_id": equipamento_id,
        "descricao": descricao.strip(),
    }

    if categoria:
        dados["categoria"] = categoria

    if gravidade:
        dados["gravidade"] = gravidade

    response = (
        supabase
        .table("falhas")
        .insert(dados)
        .execute()
    )

    return response.data

def listar_falhas_pendentes_equipamento(
    equipamento_id: int,
):
    """
    Retorna as falhas ABERTAS ou EM_ANALISE
    de um determinado equipamento.
    """

    supabase = get_supabase()

    response = (
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

    return response.data