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