-- ============================================================
-- CADASTRO DE EQUIPAMENTO
-- ============================================================

create or replace function public.cadastrar_equipamento(
    p_modelo_id bigint,
    p_patrimonio text default null,
    p_numero_serie text default null,
    p_data_aquisicao date default null,
    p_data_instalacao date default null,
    p_local_atual_id bigint default null,
    p_criticidade text default null,
    p_observacoes text default null
)
returns table (
    equipamento_id bigint,
    codigo text
)
language plpgsql
security invoker
set search_path = public
as $$
declare

    v_modelo_ativo boolean;
    v_local_ativo boolean;

    v_proximo_numero bigint;
    v_codigo text;
    v_equipamento_id bigint;

begin

    -- ========================================================
    -- VALIDAR MODELO
    -- ========================================================

    select m.ativo
    into v_modelo_ativo
    from public.modelos_equipamento m
    where m.id = p_modelo_id;


    if not found then

        raise exception
            'Modelo de equipamento não encontrado.';

    end if;


    if not coalesce(v_modelo_ativo, false) then

        raise exception
            'O modelo selecionado está inativo.';

    end if;


    -- ========================================================
    -- VALIDAR LOCAL
    -- ========================================================

    if p_local_atual_id is not null then

        select l.ativo
        into v_local_ativo
        from public.locais l
        where l.id = p_local_atual_id;


        if not found then

            raise exception
                'Local não encontrado.';

        end if;


        if not coalesce(v_local_ativo, false) then

            raise exception
                'O local selecionado está inativo.';

        end if;

    end if;


    -- ========================================================
    -- EVITAR DOIS CADASTROS GERANDO O MESMO CÓDIGO
    -- ========================================================

    perform pg_advisory_xact_lock(
        hashtext(
            'medtrack_codigo_equipamento'
        )
    );


    -- ========================================================
    -- GERAR PRÓXIMO CÓDIGO
    -- ========================================================

    select
        coalesce(
            max(
                substring(
                    e.codigo
                    from 'EQ-([0-9]+)'
                )::bigint
            ),
            0
        ) + 1

    into v_proximo_numero

    from public.equipamentos e

    where e.codigo ~ '^EQ-[0-9]+$';


    v_codigo :=
        'EQ-'
        || lpad(
            v_proximo_numero::text,
            6,
            '0'
        );


    -- ========================================================
    -- CADASTRAR EQUIPAMENTO
    -- ========================================================

    insert into public.equipamentos (
        codigo,
        patrimonio,
        modelo_id,
        numero_serie,
        data_aquisicao,
        data_instalacao,
        local_atual_id,
        status,
        criticidade,
        observacoes,
        ativo
    )
    values (
        v_codigo,

        nullif(
            trim(p_patrimonio),
            ''
        ),

        p_modelo_id,

        nullif(
            trim(p_numero_serie),
            ''
        ),

        p_data_aquisicao,

        p_data_instalacao,

        p_local_atual_id,

        'OPERACIONAL',

        nullif(
            trim(p_criticidade),
            ''
        ),

        nullif(
            trim(p_observacoes),
            ''
        ),

        true
    )

    returning
        equipamentos.id

    into
        v_equipamento_id;


    -- ========================================================
    -- RETORNO
    -- ========================================================

    return query

    select
        v_equipamento_id,
        v_codigo;

end;
$$;