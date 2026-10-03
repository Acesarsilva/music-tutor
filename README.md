# music-tutor

Professor de teoria musical com aulas interativas em HTML, geradas e validadas por um agente.

O plano completo do projeto está no documento "Plano: Agente Professor de Teoria Musical".
Este repositório começa pela peça central: o gerador de aulas.

## Como uma aula é feita

1. O módulo do currículo (`curriculo/teoria/<nivel>/<codigo>-<nome>.yaml`) descreve objetivos, conceitos e escopo.
2. O Claude escreve a aula em JSON, no formato de `apps/api/music_tutor/esquema.py`.
3. `validacao.py` confere com **music21** cada nota, intervalo afirmado, resposta de exercício e contagem de semitons.
   Se algo não bate, os erros voltam ao Claude para correção (até duas vezes).
4. `render.py` junta o JSON ao template (`templates-aula/`) e gera um HTML único, leve, com partitura (abcjs pela CDN),
   som de piano ou violão sintetizado no navegador, teclado clicável e exercícios com correção imediata.

## Estrutura

```
apps/api/            backend Python: teoria, validação, gerador e CLI
curriculo/teoria/    um YAML por módulo do currículo
templates-aula/      template HTML, CSS e JavaScript das aulas
aulas-exemplo/       aula piloto I08 (JSON validado e HTML gerado)
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

## Convenções

- Notas no texto em dó-ré-mi (Dó, Ré♯, Si♭); cifras (C, Dm, G7) só para acordes.
- Nos dados, notas em notação científica ASCII: `C4`, `F#4`, `Bb3` (Dó4 é o Dó central).
- Intervalos por código: número + `J`/`M`/`m`/`A`/`d`, por exemplo `3M`, `5J`, `2m`.
- Mudanças entram por branch `feature/<assunto>` e pull request.
