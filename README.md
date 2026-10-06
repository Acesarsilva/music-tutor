# music-tutor

Professor de teoria musical com aulas interativas em HTML, geradas e validadas por um agente.

O plano completo do projeto está no documento "Plano: Agente Professor de Teoria Musical".
O repositório tem o gerador de aulas e o app: site com login por convite, painel e aulas, e a API que registra
o progresso de cada aluno.

## Como uma aula é feita

1. O módulo do currículo (`curriculo/teoria/<nivel>/<codigo>-<nome>.yaml`) descreve objetivos, conceitos e escopo.
2. O Claude escreve a aula em JSON, no formato de `apps/api/music_tutor/esquema.py`.
3. `validacao.py` confere com **music21** cada nota, intervalo afirmado, resposta de exercício e contagem de semitons.
   Se algo não bate, os erros voltam ao Claude para correção (até duas vezes).
4. `render.py` junta o JSON ao template (`templates-aula/`) e gera um HTML único, leve, com partitura (abcjs pela CDN),
   som de piano ou violão sintetizado no navegador, teclado clicável e exercícios com correção imediata.

## Estrutura

```
apps/web/            site Next.js: login, convite, painel do aluno, aula, perfil e administração
apps/api/            backend Python: API do app (music_tutor/app), teoria, validação, gerador e CLI
supabase/            migrações do banco (tabelas, RLS e funções de progresso)
curriculo/teoria/    um YAML por módulo do currículo
templates-aula/      template HTML, CSS e JavaScript das aulas
aulas-exemplo/       aulas I01 a I16 e M01 a M18 e A01 a A12 (I08 é a piloto) (JSON validado e HTML gerado)
.claude/skills/      skills do Claude para escrever, revisar e dar aulas (CC BY-SA 4.0)
```

## Rodando

```bash
cd apps/api
pip install -e ".[dev]"
pytest

# confere a teoria de uma aula
python -m music_tutor validar ../../aulas-exemplo/I08-intervalos-simples.json

# gera o HTML (timbre inicial piano ou violao)
python -m music_tutor renderizar ../../aulas-exemplo/I08-intervalos-simples.json -o aula.html --timbre violao

# gera uma aula nova com o Claude (precisa de ANTHROPIC_API_KEY)
python -m music_tutor gerar I08 -o aula.json --html aula.html --perfil perfil.json
```

O modelo usado na geração pode ser trocado com a variável `MUSIC_TUTOR_MODELO` (padrão `claude-opus-5-5`).

Exemplo de `perfil.json`:

```json
{"nivel": "iniciante", "timbre": "violao", "pontos_fracos": ["qualidade-maior-menor"]}
```

## Site das aulas (primeiro lançamento)

O primeiro lançamento é um site estático, sem login: uma página com a lista de aulas por nível e uma página por
aula, com partitura, áudio e exercícios corrigidos no navegador. Entra toda aula com JSON em `aulas-exemplo/`.

```bash
python -m music_tutor site -o dist     # gera o site em dist/
python -m http.server -d dist 8000     # abre em http://localhost:8000
```

Na Vercel: importe o repositório com a raiz do projeto na raiz do repositório (Root Directory vazio). O
`vercel.json` já define a instalação, o build e a pasta `dist`. Cada aula nova que entra na main publica
sozinha; cada PR ganha uma prévia.

## O app (fase seguinte)

```
navegador ── login (Supabase Auth) ──> token
    │
    └── site Next.js ── token ──> API FastAPI ── RLS como o aluno ──> Postgres do Supabase
                                     └── monta a aula no timbre do aluno e corrige as respostas
```

- **Login**: só por convite. O administrador convida pelo site (página Alunos), o aluno recebe o e-mail, cria a
  senha em `/definir-senha`, aceita os termos e escolhe piano ou violão.
- **Aulas**: a API monta o HTML da aula e o site mostra num iframe isolado (`sandbox="allow-scripts"`). A aula
  avisa o site por `postMessage` quando o aluno responde ou troca de instrumento; o site manda para a API, que
  **corrige no servidor** e grava a resposta.
- **Progresso**: cada resposta atualiza o domínio do conceito e do módulo (média móvel de 0 a 100) e agenda a
  revisão (1, 3, 7, 14 e 30 dias; um erro volta para 1 dia). O painel mostra a trilha, as revisões do dia e os
  pontos para reforçar.
- **Segurança**: toda tabela tem RLS. A API conversa com o banco no papel `authenticated`, com as claims do token,
  então vale o mesmo isolamento do Supabase. O aluno só lê os próprios dados e não grava progresso direto: as
  escritas passam pelas funções `registrar_resposta`, `marcar_modulo` e `consumir_cota`.
- **LGPD**: termos aceitos no primeiro acesso, e na página Perfil o aluno baixa os dados e exclui a conta.

### Rodando o app localmente

```bash
# API (precisa de um Postgres com as migrações; veja supabase/testes/supabase_simulado.sql)
cd apps/api
cp .env.exemplo .env   # e preencha
uvicorn music_tutor.app.main:app --reload

# testes da API e do RLS num Postgres local
TEST_DATABASE_URL=postgresql://postgres@localhost:5432/postgres pytest

# site
cd apps/web
cp .env.exemplo .env.local   # e preencha
npm install && npm run dev
```

### Publicando

1. **Supabase**: crie o projeto (região São Paulo), rode `supabase/migrations/*.sql` no SQL Editor (ou
   `supabase db push`) e depois `DATABASE_URL=... python -m music_tutor sincronizar-curriculo`.
   Em Authentication, desligue "Allow new users to sign up", defina a Site URL como o endereço do site e
   adicione `<site>/definir-senha` às Redirect URLs.
2. **API** no Render ou Fly.io: imagem de `apps/api/Dockerfile` (contexto na raiz do repositório), com as
   variáveis de `apps/api/.env.exemplo`.
3. **Site** na Vercel: Root Directory `apps/web`, com as variáveis de `apps/web/.env.exemplo`.
4. **Primeiro administrador**: convide a si mesmo pelo painel do Supabase e rode
   `update public.profiles set papel = 'admin' where id = (select id from auth.users where email = '<seu e-mail>');`

## Convenções

- Notas no texto em dó-ré-mi (Dó, Ré♯, Si♭); cifras (C, Dm, G7) só para acordes.
- Nos dados, notas em notação científica ASCII: `C4`, `F#4`, `Bb3` (Dó4 é o Dó central).
- Intervalos por código: número + `J`/`M`/`m`/`A`/`d`, por exemplo `3M`, `5J`, `2m`.
- Mudanças entram por branch `feature/<assunto>` e pull request.
