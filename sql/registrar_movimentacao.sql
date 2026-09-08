create or replace function public.registrar_movimentacao( -- usado direto nas querys do supabase
    p_equipamento_id bigint,
    p_local_destino_id bigint,
    p_motivo text default null,
    p_observacoes text default null
)
returns table (
    movimentacao_id bigint,
    equipamento_id bigint,
    local_origem_id bigint,
    local_destino_id bigint,
    data_hora timestamptz
)
language plpgsql
security invoker
set search_path = public
as $$
declare
    v_local_origem_id bigint;
    v_movimentacao_id bigint;
    v_data_hora timestamptz := now();
begin

    -- Busca e bloqueia temporariamente o equipamento
    -- durante a alteração.
    select e.local_atual_id
    into v_local_origem_id
    from public.equipamentos e
    where e.id = p_equipamento_id
    for update;


    if not found then
        raise exception 'Equipamento não encontrado.';
    end if;


    -- Confere se o destino existe.
    if not exists (
        select 1
        from public.locais
        where id = p_local_destino_id
          and ativo = true
    ) then
        raise exception 'Local de destino inválido ou inativo.';
    end if;


    -- Não permite "transferir" para o mesmo local.
    if v_local_origem_id is not distinct from p_local_destino_id then
        raise exception 'O equipamento já está neste local.';
    end if;


    -- Registra o histórico.
    insert into public.movimentacoes (
        equipamento_id,
        local_origem_id,
        local_destino_id,
        data_hora,
        motivo,
        observacoes
    )
    values (
        p_equipamento_id,
        v_local_origem_id,
        p_local_destino_id,
        v_data_hora,
        nullif(trim(p_motivo), ''),
        nullif(trim(p_observacoes), '')
    )
    returning id
    into v_movimentacao_id;


    -- Atualiza o estado atual do equipamento.
    update public.equipamentos
    set local_atual_id = p_local_destino_id
    where id = p_equipamento_id;


    return query
    select
        v_movimentacao_id,
        p_equipamento_id,
        v_local_origem_id,
        p_local_destino_id,
        v_data_hora;

end;
$$;