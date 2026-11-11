create or replace function public.registrar_item_inventario(
    p_inventario_id bigint,
    p_codigo_equipamento text
)
returns table (
    equipamento_id bigint,
    codigo text,
    resultado text
)
language plpgsql
security invoker
set search_path = public
as $$
declare

    v_local_inventario bigint;

    v_status_inventario text;

    v_equipamento_id bigint;

    v_local_oficial bigint;

    v_item_id bigint;

    v_local_esperado bigint;

    v_resultado text;

begin

    -- ========================================================
    -- INVENTÁRIO
    -- ========================================================

    select
        i.local_id,
        i.status

    into
        v_local_inventario,
        v_status_inventario

    from public.inventarios i

    where i.id = p_inventario_id;


    if not found then

        raise exception
        'Inventário não encontrado.';

    end if;


    if v_status_inventario <> 'ABERTO' then

        raise exception
        'Este inventário já foi finalizado.';

    end if;


    -- ========================================================
    -- EQUIPAMENTO
    -- ========================================================

    select
        e.id,
        e.local_atual_id

    into
        v_equipamento_id,
        v_local_oficial

    from public.equipamentos e

    where upper(e.codigo)
        = upper(trim(p_codigo_equipamento));


    if not found then

        raise exception
        'Equipamento não encontrado.';

    end if;


    -- ========================================================
    -- VERIFICAR SE JÁ ERA PREVISTO
    -- ========================================================

    select
        ii.id,
        ii.local_esperado_id

    into
        v_item_id,
        v_local_esperado

    from public.inventario_itens ii

    where ii.inventario_id = p_inventario_id
      and ii.equipamento_id = v_equipamento_id;


    -- ========================================================
    -- ITEM JÁ EXISTIA NO SNAPSHOT
    -- ========================================================

    if v_item_id is not null then

        -- Era esperado neste local.
        if v_local_esperado = v_local_inventario then

            v_resultado := 'CORRETO';

        else

            -- Caso raro: item previamente inserido como
            -- não previsto e conferido novamente.
            v_resultado := 'NAO_PREVISTO';

        end if;


        update public.inventario_itens

        set
            local_encontrado_id =
                v_local_inventario,

            data_hora = now(),

            resultado = v_resultado

        where id = v_item_id;


    -- ========================================================
    -- EQUIPAMENTO NÃO ESTAVA NA LISTA ORIGINAL
    -- ========================================================

    else

        v_resultado := 'NAO_PREVISTO';


        insert into public.inventario_itens (
            inventario_id,
            equipamento_id,
            local_esperado_id,
            local_encontrado_id,
            data_hora,
            resultado
        )

        values (
            p_inventario_id,
            v_equipamento_id,
            v_local_oficial,
            v_local_inventario,
            now(),
            v_resultado
        );

    end if;


    return query

    select
        v_equipamento_id,
        trim(p_codigo_equipamento),
        v_resultado;

end;
$$;