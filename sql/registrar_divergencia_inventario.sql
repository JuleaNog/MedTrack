create or replace function public.registrar_divergencia_inventario(
    p_inventario_id bigint,
    p_equipamento_id bigint,
    p_local_encontrado_id bigint
)
returns void
language plpgsql
security invoker
set search_path = public
as $$
declare

    v_status text;

    v_local_inventario bigint;

    v_local_esperado bigint;

begin

    select
        i.status,
        i.local_id

    into
        v_status,
        v_local_inventario

    from public.inventarios i

    where i.id = p_inventario_id;


    if not found then

        raise exception
        'Inventário não encontrado.';

    end if;


    if v_status <> 'ABERTO' then

        raise exception
        'O inventário não está aberto.';

    end if;


    select
        ii.local_esperado_id

    into
        v_local_esperado

    from public.inventario_itens ii

    where ii.inventario_id = p_inventario_id
      and ii.equipamento_id = p_equipamento_id;


    if not found then

        raise exception
        'Equipamento não pertence à lista prevista deste inventário.';

    end if;


    if v_local_esperado <> v_local_inventario then

        raise exception
        'O equipamento não fazia parte da lista originalmente prevista.';

    end if;


    if p_local_encontrado_id = v_local_esperado then

        raise exception
        'O local encontrado é igual ao local esperado.';

    end if;


    if not exists (

        select 1

        from public.locais l

        where l.id = p_local_encontrado_id
          and l.ativo = true

    ) then

        raise exception
        'Local encontrado inválido.';

    end if;


    update public.inventario_itens

    set
        local_encontrado_id =
            p_local_encontrado_id,

        data_hora = now(),

        resultado = 'DIVERGENTE'

    where inventario_id = p_inventario_id
      and equipamento_id = p_equipamento_id;

end;
$$;