create or replace function public.finalizar_inventario(
    p_inventario_id bigint
)
returns table (
    inventario_id bigint,
    total bigint,
    corretos bigint,
    divergentes bigint,
    nao_encontrados bigint,
    nao_previstos bigint
)
language plpgsql
security invoker
set search_path = public
as $$
declare

    v_status text;

begin

    -- ========================================================
    -- VALIDAR INVENTÁRIO
    -- ========================================================

    select i.status
    into v_status
    from public.inventarios as i
    where i.id = p_inventario_id
    for update;


    if not found then

        raise exception
            'Inventário não encontrado.';

    end if;


    if v_status <> 'ABERTO' then

        raise exception
            'Este inventário já foi finalizado.';

    end if;


    -- ========================================================
    -- PENDENTES -> NÃO ENCONTRADOS
    -- ========================================================

    update public.inventario_itens as ii

    set resultado = 'NAO_ENCONTRADO'

    where ii.inventario_id = p_inventario_id
      and ii.resultado = 'PENDENTE';


    -- ========================================================
    -- FINALIZAR INVENTÁRIO
    -- ========================================================

    update public.inventarios as i

    set
        status = 'FINALIZADO',
        data_fim = current_date

    where i.id = p_inventario_id;


    -- ========================================================
    -- RESUMO
    -- ========================================================

    return query

    select
        p_inventario_id,
        count(*),

        count(*) filter (
            where ii.resultado = 'CORRETO'
        ),

        count(*) filter (
            where ii.resultado = 'DIVERGENTE'
        ),

        count(*) filter (
            where ii.resultado = 'NAO_ENCONTRADO'
        ),

        count(*) filter (
            where ii.resultado = 'NAO_PREVISTO'
        )

    from public.inventario_itens as ii

    where ii.inventario_id = p_inventario_id;

end;
$$;