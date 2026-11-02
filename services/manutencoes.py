from datetime import date

from services.database import get_supabase


# ============================================================
# REGISTRAR MANUTENÇÃO
# ============================================================

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
    Abre uma nova manutenção.

    O banco gera automaticamente:
    - numero_os
    - status = ABERTA
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


# ============================================================
# LISTAR MANUTENÇÕES PENDENTES
# ============================================================

def listar_manutencoes_pendentes_equipamento(
    equipamento_id: int,
):
    """
    Retorna manutenções ABERTAS ou EM_ANDAMENTO
    de um determinado equipamento.
    """

    supabase = get_supabase()

    response = (
        supabase
        .table("manutencoes")
        .select(
            """
            id,
            numero_os,
            tipo,
            data_inicio,
            descricao,
            responsavel,
            empresa,
            status,
            observacoes,
            falha_id,

            falha:falhas!manutencoes_falha_id_fkey (
                id,
                categoria,
                descricao,
                gravidade,
                status
            )
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
                "EM_ANDAMENTO",
            ],
        )
        .order(
            "data_inicio",
            desc=True,
        )
        .execute()
    )

    return response.data


# ============================================================
# CONCLUIR MANUTENÇÃO
# ============================================================

def concluir_manutencao(
    manutencao_id: int,
    data_conclusao: date,
    intervencao: str,
    observacoes: str | None = None,
):
    """
    Conclui uma manutenção através da função PostgreSQL.

    Se for uma manutenção CORRETIVA vinculada a uma falha,
    a falha também será marcada como RESOLVIDA.
    """

    supabase = get_supabase()

    response = (
        supabase
        .rpc(
            "concluir_manutencao",
            {
                "p_manutencao_id": manutencao_id,
                "p_data_conclusao": (
                    data_conclusao.isoformat()
                ),
                "p_intervencao": intervencao.strip(),
                "p_observacoes": observacoes,
            },
        )
        .execute()
    )

    return response.data