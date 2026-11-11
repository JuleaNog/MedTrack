from services.database import get_supabase


# ============================================================
# CRIAR INVENTÁRIO
# ============================================================

def criar_inventario(
    nome: str,
    local_id: int,
    observacoes: str | None = None,
):
    supabase = get_supabase()

    response = (
        supabase
        .rpc(
            "criar_inventario_local",
            {
                "p_nome": nome.strip(),
                "p_local_id": local_id,
                "p_observacoes": observacoes,
            },
        )
        .execute()
    )

    return response.data


# ============================================================
# LISTAR INVENTÁRIOS
# ============================================================

def listar_inventarios():
    supabase = get_supabase()

    response = (
        supabase
        .table("inventarios")
        .select(
            """
            id,
            nome,
            setor,
            data_inicio,
            data_fim,
            status,
            observacoes,

            local:locais!inventarios_local_id_fkey (
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
        .order(
            "id",
            desc=True,
        )
        .execute()
    )

    return response.data or []


# ============================================================
# LISTAR APENAS INVENTÁRIOS ABERTOS
# ============================================================

def listar_inventarios_abertos():
    supabase = get_supabase()

    response = (
        supabase
        .table("inventarios")
        .select(
            """
            id,
            nome,
            setor,
            data_inicio,
            status,

            local:locais!inventarios_local_id_fkey (
                id,
                setor,
                sala,
                codigo
            )
            """
        )
        .eq(
            "status",
            "ABERTO",
        )
        .order(
            "id",
            desc=True,
        )
        .execute()
    )

    return response.data or []


# ============================================================
# LISTAR ITENS
# ============================================================

def listar_itens_inventario(
    inventario_id: int,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("inventario_itens")
        .select(
            """
            id,
            equipamento_id,
            data_hora,
            resultado,
            observacoes,

            equipamento:equipamentos!inventario_itens_equipamento_id_fkey (
                id,
                codigo,
                status,

                modelo:modelos_equipamento (
                    tipo,
                    fabricante,
                    modelo
                )
            ),

            esperado:locais!inventario_itens_local_esperado_id_fkey (
                id,
                setor,
                sala,
                codigo
            ),

            encontrado:locais!inventario_itens_local_encontrado_id_fkey (
                id,
                setor,
                sala,
                codigo
            )
            """
        )
        .eq(
            "inventario_id",
            inventario_id,
        )
        .order(
            "id",
        )
        .execute()
    )

    return response.data or []


# ============================================================
# REGISTRAR EQUIPAMENTO ENCONTRADO
# ============================================================

def registrar_equipamento_inventario(
    inventario_id: int,
    codigo_equipamento: str,
):
    supabase = get_supabase()

    response = (
        supabase
        .rpc(
            "registrar_item_inventario",
            {
                "p_inventario_id":
                    inventario_id,

                "p_codigo_equipamento":
                    codigo_equipamento.strip(),
            },
        )
        .execute()
    )

    return response.data


# ============================================================
# REGISTRAR DIVERGÊNCIA
# ============================================================

def registrar_divergencia(
    inventario_id: int,
    equipamento_id: int,
    local_encontrado_id: int,
):
    supabase = get_supabase()

    response = (
        supabase
        .rpc(
            "registrar_divergencia_inventario",
            {
                "p_inventario_id":
                    inventario_id,

                "p_equipamento_id":
                    equipamento_id,

                "p_local_encontrado_id":
                    local_encontrado_id,
            },
        )
        .execute()
    )

    return response.data


# ============================================================
# FINALIZAR
# ============================================================

def finalizar_inventario(
    inventario_id: int,
):
    supabase = get_supabase()

    response = (
        supabase
        .rpc(
            "finalizar_inventario",
            {
                "p_inventario_id":
                    inventario_id,
            },
        )
        .execute()
    )

    return response.data