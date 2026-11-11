create or replace function public.listar_status_preventivas()
returns table (
    equipamento_id bigint,
    codigo text,
    tipo_equipamento text,
    fabricante text,
    modelo text,
    periodicidade_meses integer,
    ultima_preventiva date,
    proxima_preventiva date,
    dias_restantes integer,
    situacao text
)
language sql
security invoker
set search_path = public
stable
as $$

    with base as (

        select
            e.id as equipamento_id,
            e.codigo,
            me.tipo as tipo_equipamento,
            me.fabricante,
            me.modelo,
            me.periodicidade_preventiva_meses
                as periodicidade_meses,

            max(m.data_conclusao)
            filter (
                where m.tipo = 'PREVENTIVA'
                  and m.status = 'CONCLUIDA'
                  and m.data_conclusao is not null
            ) as ultima_preventiva

        from public.equipamentos e

        join public.modelos_equipamento me
            on me.id = e.modelo_id

        left join public.manutencoes m
            on m.equipamento_id = e.id

        where e.ativo = true
          and e.status <> 'BAIXADO'

        group by
            e.id,
            e.codigo,
            me.tipo,
            me.fabricante,
            me.modelo,
            me.periodicidade_preventiva_meses
    ),

    calculo as (

        select
            b.*,

            case
                when b.periodicidade_meses is not null
                 and b.ultima_preventiva is not null
                then (
                    b.ultima_preventiva
                    +
                    make_interval(
                        months => b.periodicidade_meses
                    )
                )::date

                else null
            end as proxima_preventiva

        from base b
    )

    select
        c.equipamento_id,
        c.codigo,
        c.tipo_equipamento,
        c.fabricante,
        c.modelo,
        c.periodicidade_meses,
        c.ultima_preventiva,
        c.proxima_preventiva,

        case
            when c.proxima_preventiva is not null
            then c.proxima_preventiva - current_date

            else null
        end as dias_restantes,

        case

            when c.periodicidade_meses is null
            then 'SEM_PERIODICIDADE'

            when c.ultima_preventiva is null
            then 'SEM_HISTORICO'

            when c.proxima_preventiva < current_date
            then 'VENCIDA'

            when c.proxima_preventiva = current_date
            then 'VENCE_HOJE'

            when c.proxima_preventiva <= current_date + 30
            then 'PROXIMA'

            else 'EM_DIA'

        end as situacao

    from calculo c

    order by
        c.proxima_preventiva nulls last;

$$;