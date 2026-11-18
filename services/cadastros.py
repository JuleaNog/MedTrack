from services.database import get_supabase


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _texto_ou_none(valor):
    """
    Remove espaços extras e converte texto vazio em None.
    """

    if valor is None:
        return None

    valor = str(valor).strip()

    return valor if valor else None


# ============================================================
# MODELOS
# ============================================================

def listar_modelos_ativos():
    """
    Retorna os modelos de equipamento ativos.
    """

    supabase = get_supabase()

    response = (
        supabase
        .table("modelos_equipamento")
        .select(
            """
            id,
            tipo,
            fabricante,
            modelo,
            periodicidade_preventiva_meses,
            fonte_periodicidade,
            referencia_documental,
            criticidade_padrao,
            ativo
            """
        )
        .eq("ativo", True)
        .order("tipo")
        .order("fabricante")
        .order("modelo")
        .execute()
    )

    return response.data or []


def cadastrar_modelo(
    tipo,
    fabricante,
    modelo,
    periodicidade_preventiva_meses=None,
    fonte_periodicidade=None,
    referencia_documental=None,
    criticidade_padrao=None,
):
    """
    Cadastra um novo modelo de equipamento.
    """

    supabase = get_supabase()

    tipo = _texto_ou_none(tipo)
    fabricante = _texto_ou_none(fabricante)
    modelo = _texto_ou_none(modelo)

    if not tipo:
        raise ValueError(
            "Informe o tipo do equipamento."
        )

    if not fabricante:
        raise ValueError(
            "Informe o fabricante."
        )

    if not modelo:
        raise ValueError(
            "Informe o modelo."
        )


    # --------------------------------------------------------
    # VERIFICAR DUPLICIDADE
    # --------------------------------------------------------

    existentes = (
        supabase
        .table("modelos_equipamento")
        .select(
            """
            id,
            tipo,
            fabricante,
            modelo
            """
        )
        .ilike(
            "tipo",
            tipo,
        )
        .ilike(
            "fabricante",
            fabricante,
        )
        .ilike(
            "modelo",
            modelo,
        )
        .limit(1)
        .execute()
    )


    if existentes.data:

        raise ValueError(
            "Já existe um modelo cadastrado "
            "com este tipo, fabricante e modelo."
        )


    dados = {
        "tipo":
            tipo,

        "fabricante":
            fabricante,

        "modelo":
            modelo,

        "periodicidade_preventiva_meses":
            periodicidade_preventiva_meses,

        "fonte_periodicidade":
            _texto_ou_none(
                fonte_periodicidade
            ),

        "referencia_documental":
            _texto_ou_none(
                referencia_documental
            ),

        "criticidade_padrao":
            _texto_ou_none(
                criticidade_padrao
            ),

        "ativo":
            True,
    }


    response = (
        supabase
        .table("modelos_equipamento")
        .insert(dados)
        .execute()
    )


    return response.data or []


# ============================================================
# EQUIPAMENTOS
# ============================================================

def cadastrar_equipamento(
    modelo_id,
    patrimonio=None,
    numero_serie=None,
    data_aquisicao=None,
    data_instalacao=None,
    local_atual_id=None,
    criticidade=None,
    observacoes=None,
):
    """
    Cadastra uma nova unidade física de equipamento.

    O código EQ-XXXXXX é gerado automaticamente
    pela função PostgreSQL.
    """

    supabase = get_supabase()


    parametros = {
        "p_modelo_id":
            modelo_id,

        "p_patrimonio":
            _texto_ou_none(
                patrimonio
            ),

        "p_numero_serie":
            _texto_ou_none(
                numero_serie
            ),

        "p_data_aquisicao":
            (
                data_aquisicao.isoformat()
                if data_aquisicao
                else None
            ),

        "p_data_instalacao":
            (
                data_instalacao.isoformat()
                if data_instalacao
                else None
            ),

        "p_local_atual_id":
            local_atual_id,

        "p_criticidade":
            _texto_ou_none(
                criticidade
            ),

        "p_observacoes":
            _texto_ou_none(
                observacoes
            ),
    }


    response = (
        supabase
        .rpc(
            "cadastrar_equipamento",
            parametros,
        )
        .execute()
    )


    return response.data or []