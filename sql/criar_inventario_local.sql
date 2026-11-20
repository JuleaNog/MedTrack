create or replace function public.criar_inventario_local(
    p_nome text,
    p_local_id bigint,
    p_observacoes text default null
)
returns table (
    inventario_id bigint,
    quantidade_prevista bigint
)
language plpgsql
security invoker
set search_path = public
as $$
declare

    v_local public.locais%rowtype;
    v_inventario_id bigint;
    v_quantidade bigint;

begin

    -- ========================================================
    -- VALIDAR NOME
    -- ========================================================

    if p_nome is null
       or trim(p_nome) = '' then

        raise exception
            'Informe o nome do inventário.';

    end if;


    -- ========================================================
    -- VALIDAR LOCAL
    -- ========================================================

    select l.*
    into v_local
    from public.locais as l
    where l.id = p_local_id
      and l.ativo = true;


    if not found then

        raise exception
            'Local não encontrado ou inativo.';

    end if;


    -- ========================================================
    -- VERIFICAR INVENTÁRIO ABERTO NO MESMO LOCAL
    -- ========================================================

    if exists (
        select 1
        from public.inventarios as i
        where i.local_id = p_local_id
          and i.status = 'ABERTO'
    ) then

        raise exception
            'Já existe um inventário aberto para este local.';

    end if;


    -- ========================================================
    -- CRIAR INVENTÁRIO
    -- ========================================================

    insert into public.inventarios (
        nome,
        setor,
        local_id,
        data_inicio,
        status,
        observacoes
    )
    values (
        trim(p_nome),
        v_local.setor,
        p_local_id,
        current_date,
        'ABERTO',
        nullif(
            trim(p_observacoes),
            ''
        )
    )
    returning id
    into v_inventario_id;


    -- ========================================================
    -- CRIAR SNAPSHOT DOS EQUIPAMENTOS ESPERADOS
    -- ========================================================

    insert into public.inventario_itens (
        inventario_id,
        equipamento_id,
        local_esperado_id,
        local_encontrado_id,
        resultado
    )
    select
        v_inventario_id,
        e.id,
        e.local_atual_id,
        null,
        'PENDENTE'

    from public.equipamentos as e

    where e.local_atual_id = p_local_id
      and e.ativo = true
      and e.status <> 'BAIXADO';


    -- ========================================================
    -- QUANTIDADE PREVISTA
    -- ========================================================

    select count(*)
    into v_quantidade

    from public.inventario_itens as ii

    where ii.inventario_id = v_inventario_id;


    -- ========================================================
    -- RETORNO
    -- ========================================================

    return query

    select
        v_inventario_id,
        v_quantidade;

end;
$$;