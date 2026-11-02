revoke all
on function public.concluir_manutencao(
    bigint,
    date,
    text,
    text
)
from public;


revoke all
on function public.concluir_manutencao(
    bigint,
    date,
    text,
    text
)
from anon;


grant execute
on function public.concluir_manutencao(
    bigint,
    date,
    text,
    text
)
to authenticated;