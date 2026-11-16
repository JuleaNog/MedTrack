-- ============================================================
-- AUDITORIA - MOVIMENTAÇÕES
-- ============================================================

alter table public.movimentacoes
add column if not exists registrado_por_id uuid,
add column if not exists registrado_por_email text;


-- ============================================================
-- AUDITORIA - FALHAS
-- ============================================================

alter table public.falhas
add column if not exists registrada_por_id uuid,
add column if not exists registrada_por_email text,
add column if not exists resolvida_por_id uuid,
add column if not exists resolvida_por_email text,
add column if not exists data_resolucao timestamptz;


-- ============================================================
-- AUDITORIA - MANUTENÇÕES
-- ============================================================

alter table public.manutencoes
add column if not exists aberta_por_id uuid,
add column if not exists aberta_por_email text,
add column if not exists concluida_por_id uuid,
add column if not exists concluida_por_email text,
add column if not exists concluida_em timestamptz;


-- ============================================================
-- AUDITORIA - INVENTÁRIOS
-- ============================================================

alter table public.inventarios
add column if not exists criado_por_id uuid,
add column if not exists criado_por_email text,
add column if not exists finalizado_por_id uuid,
add column if not exists finalizado_por_email text,
add column if not exists finalizado_em timestamptz;


-- ============================================================
-- AUDITORIA - ITENS DE INVENTÁRIO
-- ============================================================

alter table public.inventario_itens
add column if not exists conferido_por_id uuid,
add column if not exists conferido_por_email text;