-- App do music-tutor: perfis, currículo, progresso por aluno, aulas, chat, envios e cotas.
--
-- Regras gerais:
-- - Toda tabela tem Row Level Security. O aluno lê só as próprias linhas; o administrador lê tudo.
-- - Progresso, domínio e cotas não são gravados direto pelo aluno: passam pelas funções
--   registrar_resposta, concluir_modulo e consumir_cota, que usam auth.uid() e aplicam as regras.
-- - Os privilégios são revogados e concedidos tabela a tabela, sem depender dos padrões do Supabase.

-- ------------------------------------------------------------------ Perfis

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  nome text not null default '' check (char_length(nome) <= 120),
  papel text not null default 'aluno' check (papel in ('aluno', 'admin')),
  nivel text not null default 'iniciante' check (nivel in ('iniciante', 'intermediario', 'avancado')),
  timbre text not null default 'piano' check (timbre in ('piano', 'violao')),
  objetivos text[] not null default '{}',
  termos_aceitos_em timestamptz,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (select 1 from public.profiles where id = auth.uid() and papel = 'admin')
$$;

-- Cria o perfil quando o Supabase Auth cria o usuário (convite aceito ou criação pelo painel).
create or replace function public.criar_perfil()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, nome)
  values (new.id, coalesce(left(new.raw_user_meta_data ->> 'nome', 120), ''))
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger ao_criar_usuario
  after insert on auth.users
  for each row execute function public.criar_perfil();

create or replace function public.tocar_atualizado_em()
returns trigger
language plpgsql
as $$
begin
  new.atualizado_em := now();
  return new;
end;
$$;

create trigger profiles_atualizado_em
  before update on public.profiles
  for each row execute function public.tocar_atualizado_em();

-- ------------------------------------------------------------------ Currículo

create table public.modules (
  codigo text primary key,
  titulo text not null,
  nivel text not null check (nivel in ('iniciante', 'intermediario', 'avancado')),
  assunto text not null default 'teoria',
  ordem integer not null default 0,
  prerequisitos text[] not null default '{}',
  conceitos text[] not null default '{}',
  objetivos text[] not null default '{}',
  atualizado_em timestamptz not null default now()
);

-- ------------------------------------------------------------------ Progresso

create table public.module_progress (
  user_id uuid not null references auth.users (id) on delete cascade,
  modulo text not null references public.modules (codigo) on update cascade,
  status text not null default 'em_andamento' check (status in ('em_andamento', 'concluido')),
  dominio smallint not null default 0 check (dominio between 0 and 100),
  acertos integer not null default 0,
  erros integer not null default 0,
  etapa_revisao smallint not null default 0,
  proxima_revisao date,
  iniciado_em timestamptz not null default now(),
  concluido_em timestamptz,
  atualizado_em timestamptz not null default now(),
  primary key (user_id, modulo)
);

create table public.concept_mastery (
  user_id uuid not null references auth.users (id) on delete cascade,
  conceito text not null,
  acertos integer not null default 0,
  erros integer not null default 0,
  dominio smallint not null default 0 check (dominio between 0 and 100),
  etapa_revisao smallint not null default 0,
  proxima_revisao date,
  erro_comum text,
  atualizado_em timestamptz not null default now(),
  primary key (user_id, conceito)
);

create index concept_mastery_revisao on public.concept_mastery (user_id, proxima_revisao);

create table public.quiz_attempts (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  modulo text references public.modules (codigo) on update cascade,
  conceito text not null,
  origem text not null default 'aula' check (origem in ('aula', 'chat', 'nivelamento', 'revisao')),
  pergunta text,
  resposta text,
  certo boolean not null,
  criado_em timestamptz not null default now()
);

create index quiz_attempts_usuario on public.quiz_attempts (user_id, criado_em desc);

-- ------------------------------------------------------------------ Aulas, chat, envios, notas

-- user_id nulo = camada base do módulo, compartilhada por todos os alunos.
create table public.lessons (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users (id) on delete cascade,
  modulo text references public.modules (codigo) on update cascade,
  topico text,
  timbre text check (timbre in ('piano', 'violao')),
  conteudo jsonb not null,
  html_path text,
  criado_em timestamptz not null default now()
);

create index lessons_usuario on public.lessons (user_id, criado_em desc);

create table public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  titulo text not null default '',
  criado_em timestamptz not null default now()
);

create table public.messages (
  id bigint generated always as identity primary key,
  conversation_id uuid not null references public.conversations (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  papel text not null check (papel in ('aluno', 'professor')),
  conteudo text not null,
  criado_em timestamptz not null default now()
);

create index messages_conversa on public.messages (conversation_id, id);

create table public.submissions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  arquivo_path text not null,
  formato text not null check (formato in ('musicxml', 'midi', 'pdf', 'imagem', 'texto')),
  analise jsonb,
  criado_em timestamptz not null default now()
);

create table public.learner_notes (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  nota text not null,
  criado_em timestamptz not null default now()
);

-- ------------------------------------------------------------------ Cotas e consumo

create table public.usage_daily (
  user_id uuid not null references auth.users (id) on delete cascade,
  dia date not null default current_date,
  mensagens integer not null default 0,
  aulas integer not null default 0,
  tokens_entrada bigint not null default 0,
  tokens_saida bigint not null default 0,
  primary key (user_id, dia)
);

-- ------------------------------------------------------------------ Funções de escrita

-- Intervalos da revisão espaçada, em dias, por etapa (1 a 5). Um erro volta para a etapa 1 (1 dia).
create or replace function public.dias_da_etapa(etapa integer)
returns integer
language sql
immutable
as $$
  select (array[1, 3, 7, 14, 30])[greatest(1, least(etapa, 5))]
$$;

-- Registra uma resposta do aluno logado e atualiza o domínio do conceito e do módulo.
-- Domínio é uma média móvel (peso 0,35 para a resposta nova), de 0 a 100.
create or replace function public.registrar_resposta(
  p_conceito text,
  p_certo boolean,
  p_modulo text default null,
  p_origem text default 'aula',
  p_pergunta text default null,
  p_resposta text default null
)
returns public.concept_mastery
language plpgsql
security definer
set search_path = public
as $$
declare
  v_usuario uuid := auth.uid();
  v_alvo integer := case when p_certo then 100 else 0 end;
  v_linha public.concept_mastery;
begin
  if v_usuario is null then
    raise exception 'login necessário' using errcode = '28000';
  end if;
  if p_conceito is null or char_length(p_conceito) not between 1 and 80 then
    raise exception 'conceito inválido' using errcode = '22023';
  end if;

  insert into public.quiz_attempts (user_id, modulo, conceito, origem, pergunta, resposta, certo)
  values (v_usuario, p_modulo, p_conceito, p_origem, left(p_pergunta, 2000), left(p_resposta, 2000), p_certo);

  insert into public.concept_mastery as c (user_id, conceito, acertos, erros, dominio, etapa_revisao, proxima_revisao)
  values (
    v_usuario, p_conceito,
    case when p_certo then 1 else 0 end,
    case when p_certo then 0 else 1 end,
    round(v_alvo * 0.35),
    1,
    current_date + public.dias_da_etapa(1)
  )
  on conflict (user_id, conceito) do update set
    acertos = c.acertos + case when p_certo then 1 else 0 end,
    erros = c.erros + case when p_certo then 0 else 1 end,
    dominio = round(c.dominio * 0.65 + v_alvo * 0.35),
    etapa_revisao = case when p_certo then least(c.etapa_revisao + 1, 5) else 1 end,
    proxima_revisao = current_date
      + public.dias_da_etapa(case when p_certo then least(c.etapa_revisao + 1, 5) else 1 end),
    atualizado_em = now()
  returning * into v_linha;

  if p_modulo is not null then
    insert into public.module_progress as m (user_id, modulo, dominio, acertos, erros)
    values (
      v_usuario, p_modulo, round(v_alvo * 0.35),
      case when p_certo then 1 else 0 end,
      case when p_certo then 0 else 1 end
    )
    on conflict (user_id, modulo) do update set
      dominio = round(m.dominio * 0.65 + v_alvo * 0.35),
      acertos = m.acertos + case when p_certo then 1 else 0 end,
      erros = m.erros + case when p_certo then 0 else 1 end,
      atualizado_em = now();
  end if;

  return v_linha;
end;
$$;

-- Marca o módulo como iniciado (abriu a aula) ou concluído (terminou a aula).
create or replace function public.marcar_modulo(p_modulo text, p_concluido boolean default false)
returns public.module_progress
language plpgsql
security definer
set search_path = public
as $$
declare
  v_usuario uuid := auth.uid();
  v_linha public.module_progress;
begin
  if v_usuario is null then
    raise exception 'login necessário' using errcode = '28000';
  end if;

  insert into public.module_progress as m (user_id, modulo, status, concluido_em, etapa_revisao, proxima_revisao)
  values (
    v_usuario, p_modulo,
    case when p_concluido then 'concluido' else 'em_andamento' end,
    case when p_concluido then now() end,
    case when p_concluido then 1 else 0 end,
    case when p_concluido then current_date + public.dias_da_etapa(1) end
  )
  on conflict (user_id, modulo) do update set
    status = case when p_concluido or m.status = 'concluido' then 'concluido' else 'em_andamento' end,
    concluido_em = coalesce(m.concluido_em, case when p_concluido then now() end),
    etapa_revisao = case when p_concluido and m.etapa_revisao = 0 then 1 else m.etapa_revisao end,
    proxima_revisao = coalesce(m.proxima_revisao, case when p_concluido then current_date + public.dias_da_etapa(1) end),
    atualizado_em = now()
  returning * into v_linha;

  return v_linha;
end;
$$;

-- Soma um uso do dia (p_tipo = 'mensagens' ou 'aulas') se ainda couber no limite. Devolve false se estourou.
create or replace function public.consumir_cota(p_tipo text, p_limite integer)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  v_usuario uuid := auth.uid();
  v_ok boolean;
begin
  if v_usuario is null then
    raise exception 'login necessário' using errcode = '28000';
  end if;
  if p_tipo not in ('mensagens', 'aulas') then
    raise exception 'tipo de cota inválido' using errcode = '22023';
  end if;

  insert into public.usage_daily (user_id, dia) values (v_usuario, current_date)
  on conflict (user_id, dia) do nothing;

  if p_tipo = 'mensagens' then
    update public.usage_daily set mensagens = mensagens + 1
    where user_id = v_usuario and dia = current_date and mensagens < p_limite;
  else
    update public.usage_daily set aulas = aulas + 1
    where user_id = v_usuario and dia = current_date and aulas < p_limite;
  end if;
  get diagnostics v_ok = row_count;
  return v_ok;
end;
$$;

-- ------------------------------------------------------------------ Row Level Security

alter table public.profiles enable row level security;
alter table public.modules enable row level security;
alter table public.module_progress enable row level security;
alter table public.concept_mastery enable row level security;
alter table public.quiz_attempts enable row level security;
alter table public.lessons enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.submissions enable row level security;
alter table public.learner_notes enable row level security;
alter table public.usage_daily enable row level security;

create policy "perfil: o próprio ou admin" on public.profiles
  for select to authenticated using (id = auth.uid() or public.is_admin());
create policy "perfil: o próprio atualiza" on public.profiles
  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

create policy "currículo: todos os logados leem" on public.modules
  for select to authenticated using (true);

create policy "progresso de módulo: o próprio ou admin" on public.module_progress
  for select to authenticated using (user_id = auth.uid() or public.is_admin());
create policy "domínio de conceito: o próprio ou admin" on public.concept_mastery
  for select to authenticated using (user_id = auth.uid() or public.is_admin());
create policy "respostas: o próprio ou admin" on public.quiz_attempts
  for select to authenticated using (user_id = auth.uid() or public.is_admin());
create policy "consumo: o próprio ou admin" on public.usage_daily
  for select to authenticated using (user_id = auth.uid() or public.is_admin());
create policy "notas do professor: o próprio ou admin" on public.learner_notes
  for select to authenticated using (user_id = auth.uid() or public.is_admin());

create policy "aulas: as próprias, as compartilhadas ou admin" on public.lessons
  for select to authenticated using (user_id = auth.uid() or user_id is null or public.is_admin());

create policy "conversas: as próprias" on public.conversations
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "mensagens: as próprias" on public.messages
  for select to authenticated using (user_id = auth.uid());
create policy "mensagens: o aluno escreve nas próprias conversas" on public.messages
  for insert to authenticated with check (
    user_id = auth.uid()
    and papel = 'aluno'
    and exists (select 1 from public.conversations c where c.id = conversation_id and c.user_id = auth.uid())
  );
create policy "envios: os próprios" on public.submissions
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- ------------------------------------------------------------------ Privilégios

revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke execute on all functions in schema public from anon, authenticated, public;

grant select on all tables in schema public to authenticated;
grant update (nome, timbre, objetivos, termos_aceitos_em) on public.profiles to authenticated;
grant insert, update (titulo), delete on public.conversations to authenticated;
grant insert (conversation_id, user_id, papel, conteudo) on public.messages to authenticated;
grant insert (user_id, arquivo_path, formato), delete on public.submissions to authenticated;

grant execute on function public.is_admin() to authenticated;
grant execute on function public.dias_da_etapa(integer) to authenticated;
grant execute on function public.registrar_resposta(text, boolean, text, text, text, text) to authenticated;
grant execute on function public.marcar_modulo(text, boolean) to authenticated;
grant execute on function public.consumir_cota(text, integer) to authenticated;

grant all on all tables in schema public to service_role;
grant all on all sequences in schema public to service_role;
grant execute on all functions in schema public to service_role;
