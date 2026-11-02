from datetime import date

from services.database import get_supabase


def registrar_manutencao(
    equipamento_id: int,
    tipo: str,
    data_inicio: date,
    descricao: str,
    falha_id: int | None = None,
    responsavel: str | None = None,
    empresa: str | None = None,
    observacoes: str | None = None,
):
    """
    Abre uma nova manutenção para o equipamento.

    O banco define automaticamente:
    - numero_os
    - status = ABERTA
    - created_at

    data_conclusao e intervencao permanecem vazios
    até a conclusão da manutenção.
    """

    supabase = get_supabase()

    dados = {
        "equipamento_id": equipamento_id,
        "tipo": tipo,
        "data_inicio": data_inicio.isoformat(),
        "descricao": descricao.strip(),
    }

    if falha_id is not None:
        dados["falha_id"] = falha_id

    if responsavel and responsavel.strip():
        dados["responsavel"] = responsavel.strip()

    if empresa and empresa.strip():
        dados["empresa"] = empresa.strip()

    if observacoes and observacoes.strip():
        dados["observacoes"] = observacoes.strip()

    response = (
        supabase
        .table("manutencoes")
        .insert(dados)
        .execute()
    )

    return response.data