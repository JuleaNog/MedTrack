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

    select i.status

    into v_status

    from public.inventarios i

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


    -- Tudo que ainda estava pendente
    -- passa a ser não encontrado.

    update public.inventario_itens

    set resultado = 'NAO_ENCONTRADO'

    where inventario_id = p_inventario_id

      and resultado = 'PENDENTE';


    -- Fecha o inventário.

    update public.inventarios

    set
        status = 'FINALIZADO',
        data_fim = current_date

    where id = p_inventario_id;


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

    from public.inventario_itens ii

    where ii.inventario_id =
        p_inventario_id;

end;
$$;