create or replace function public.obter_status_preventiva(
    p_equipamento_id bigint
)
returns table (
    ultima_preventiva date,
    periodicidade_meses integer,
    proxima_preventiva date,
    dias_restantes integer,
    situacao text
)
language plpgsql
security invoker
set search_path = public
as $$
declare

    v_periodicidade integer;

    v_ultima_preventiva date;

    v_proxima_preventiva date;

    v_dias_restantes integer;

    v_situacao text;

begin

    -- ========================================================
    -- BUSCAR PERIODICIDADE DO MODELO
    -- ========================================================

    select
        m.periodicidade_preventiva_meses

    into
        v_periodicidade

    from public.equipamentos e

    join public.modelos_equipamento m
        on m.id = e.modelo_id

    where e.id = p_equipamento_id;


    if not found then

        raise exception
        'Equipamento não encontrado.';

    end if;


    -- ========================================================
    -- MODELO SEM PERIODICIDADE DEFINIDA
    -- ========================================================

    if v_periodicidade is null then

        return query

        select
            null::date,
            null::integer,
            null::date,
            null::integer,
            'SEM_PERIODICIDADE'::text;

        return;

    end if;


    -- ========================================================
    -- BUSCAR ÚLTIMA PREVENTIVA CONCLUÍDA
    -- ========================================================

    select
        max(m.data_conclusao)

    into
        v_ultima_preventiva

    from public.manutencoes m

    where m.equipamento_id = p_equipamento_id

      and m.tipo = 'PREVENTIVA'

      and m.status = 'CONCLUIDA'

      and m.data_conclusao is not null;


    -- ========================================================
    -- NÃO EXISTE PREVENTIVA CONCLUÍDA
    -- ========================================================

    if v_ultima_preventiva is null then

        return query

        select
            null::date,
            v_periodicidade,
            null::date,
            null::integer,
            'SEM_HISTORICO'::text;

        return;

    end if;


    -- ========================================================
    -- CALCULAR PRÓXIMA PREVENTIVA
    -- ========================================================

    v_proxima_preventiva := (

        v_ultima_preventiva
        +
        make_interval(
            months => v_periodicidade
        )

    )::date;


    -- ========================================================
    -- CALCULAR QUANTOS DIAS FALTAM
    -- ========================================================

    v_dias_restantes :=
        v_proxima_preventiva
        -
        current_date;


    -- ========================================================
    -- CLASSIFICAR SITUAÇÃO
    -- ========================================================

    if v_dias_restantes < 0 then

        v_situacao := 'VENCIDA';


    elsif v_dias_restantes = 0 then

        v_situacao := 'VENCE_HOJE';


    elsif v_dias_restantes <= 30 then

        v_situacao := 'PROXIMA';


    else

        v_situacao := 'EM_DIA';

    end if;


    -- ========================================================
    -- RETORNO
    -- ========================================================

    return query

    select
        v_ultima_preventiva,
        v_periodicidade,
        v_proxima_preventiva,
        v_dias_restantes,
        v_situacao;

end;
$$;