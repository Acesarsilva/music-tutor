---
name: redator-de-aula
description: "Use ao escrever ou ajustar uma aula JSON do music-tutor, da abertura aos exercícios, com repertório brasileiro e validação obrigatória com music21."
---

# Redator de aula

Você escreve uma aula no formato `Aula` de `apps/api/music_tutor/esquema.py`, a partir do módulo do
currículo (`curriculo/teoria/<nivel>/<codigo>-<nome>.yaml`). Use `aulas-exemplo/I08-intervalos-simples.json`
como referência de tom e formato, não de conteúdo. A aula só está pronta quando passa no validador.

## 1. Antes de escrever

- Leia o YAML do módulo: `objetivos`, `conceitos`, `fora_do_escopo`, `exemplos_semente`, `exercicios`.
- Cada exercício leva `conceito` com um slug **exatamente igual** a um item de `conceitos` do módulo.
  É por ele que o app mede o domínio de cada aluno. Slug inventado quebra o acompanhamento.
- Liste os pré-requisitos de que a aula depende (ex.: para acordes, 3ª maior e 3ª menor).
- Liste 2 a 4 equívocos prováveis do tema (veja a seção 5). Eles orientam o exemplo errado e as opções erradas.

## 2. Abertura: lembrar, ouvir, depois nomear

A primeira seção tem três partes curtas.

1. **Aquecimento de memória** (bloco `texto`): 2 ou 3 perguntas rápidas sobre o que a aula vai usar,
   sem consulta. Ex. para acordes: "Quantos semitons tem uma 3ª maior? E uma 3ª menor? Que notas formam
   Dó–Mi–Sol?". Logo depois, um bloco `resposta` (fica escondido até o aluno abrir) com as respostas.
2. **Som antes do nome** (bloco `exemplo`): toque o fenômeno antes de dar o termo. A `legenda` pede uma
   observação, não uma definição. Ex.: tocar C (Dó–Mi–Sol) e depois Cm (Dó–Mi♭–Sol) e perguntar
   "Qual dos dois soa mais escuro? Só uma nota mudou." O termo "acorde menor" vem no bloco seguinte.
3. **Ponte e objetivo** (bloco `texto`, 2 frases): ligue o que foi lembrado ao que vem agora e diga o que
   o aluno saberá fazer no fim ("Ao final, você monta qualquer acorde maior ou menor a partir da fundamental.").

## 3. Um conceito por bloco

- Cada seção trata de uma ideia. Cada bloco `texto` explica um passo, em frases curtas.
- Exemplos de 1 a 4 compassos. Andamento lento (60 a 80) para intervalos e acordes novos.
- Não junte conceitos novos no mesmo exemplo: primeiro a 3ª maior sozinha, depois a 3ª menor sozinha,
  depois as duas lado a lado para comparar.
- O que está em `fora_do_escopo` aparece no máximo em uma `dica` de uma frase (como o trítono na I08).

## 4. Partitura, som, teclado e legenda juntos

Para cada ideia nova, combine representações que se completam:

- `exemplo`: partitura + áudio. A `legenda` diz **o que ouvir**, em uma linha
  ("A nota de cima desce meio tom e o acorde escurece."), não repete o título.
- `teclado`: mostra **onde** estão as notas. Vira braço de violão quando o aluno escolhe "Violão".
  Todas as notas de `destaque`, `de` e `ate` ficam entre E3 e E6.
- `tabela`: só para comparar ou organizar (qualidade × semitons, intervalo × música de referência).
- Nada decorativo. Se um bloco não acrescenta informação, corte.
- `dica` fica sempre visível: use para lembretes. Resposta de pergunta feita ao aluno vai em `resposta`.
- Não explique na aula decisões editoriais (fontes, direitos autorais). O aluno só vê o conteúdo.
- Fale em contar **notas** ("Ré, Mi, Fá: três notas"), não "nomes": o aluno já conhece as notas.
- Em música cantada, dê a cada nota a sua `silaba` ("Ci-", "ran-", "da"; "de~o" junta duas palavras), que aparece sob a
  partitura. O ritmo segue a prosódia: sílaba tônica no tempo forte, anacruse quando a letra começa em sílaba fraca.
- Escreva para os dois instrumentos: "clique na nota", "a nota marcada". Quando o raciocínio depender
  do teclado ("não há tecla preta entre Mi e Fá"), dê o equivalente no violão ("no braço, são casas vizinhas").

## 5. Exemplo resolvido, depois retirada gradual

1. **Exemplo resolvido completo** (bloco `texto` + `exemplo`): todos os passos, cada um com o porquê.
   Ex. Ré–Fá♯: "Passo 1: conte as notas Ré, Mi, Fá: 3, é uma 3ª. O ♯ não muda o número.
   Passo 2: conte os semitons Ré–Ré♯–Mi–Fá–Fá♯: 4. Passo 3: 3ª com 4 semitons é maior."
2. **Pergunta de autoexplicação** logo depois: "Por que o sustenido não entrou na contagem do passo 1?"
   Responda num bloco `resposta` logo em seguida.
3. **Exemplo com o último passo em branco**: "Lá–Dó: Lá, Si, Dó = 3ª; Lá–Lá♯–Si–Dó = 3 semitons.
   Maior ou menor? Pense antes de abrir a resposta." Depois, um com dois passos em branco.
4. Só então os exercícios independentes.

Para nível avançado, encurte: um exemplo resolvido basta, e o restante vira prática.

## 6. Exemplo errado (depois dos corretos)

Inclua um bloco `texto` com uma resolução que tem **um** erro realista, seguido de um bloco `resposta` com a
correção e o motivo. Peça: achar o passo errado, dizer por que está errado e corrigir. Equívocos úteis:

- **Contar semitons em vez de notas para o número**: "Ré–Fá♯ tem 4 semitons, então é uma 4ª."
- **Não contar as duas pontas**: "De Dó a Sol: Ré, Mi, Fá, Sol, são 4, é uma 4ª."
- **Enarmonia**: "Dó–Fá♯ e Dó–Sol♭ são o mesmo intervalo." Soam igual, mas o primeiro é 4ª aumentada e
  o segundo 5ª diminuta; o nome da nota decide o número.
- **Mi–Fá e Si–Dó**: "Entre Mi e Fá há um tom, como entre Dó e Ré." Não há nota entre elas: é semitom.
- **Toda 5ª entre notas naturais é justa**: Si–Fá é 5ª diminuta (6 semitons).

Use o erro só depois que o aluno viu o procedimento certo; antes disso, ele pode aprender o erro.

## 7. Exercícios (8 a 14)

**Mistura**: combine `multipla_escolha`, `percepcao` e `teclado` como o módulo pede. Não agrupe por tipo
nem por conceito: alterne (3ª maior, 5ª justa, 3ª menor, percepção, construir no teclado...). Inclua
1 ou 2 itens de recuperação de módulos anteriores (ex.: tom e semitom, escala maior) e itens de
**discriminação** ("4ª justa ou 5ª justa?").

**Pergunta-chave** (pelo menos uma, entre as primeiras): testa o conceito central, e cada opção errada
corresponde a um equívoco específico. Ex.: exemplo Ré4–Fá♯4 com `intervalo` 3M:

| Opção | O que revela |
|---|---|
| 3ª maior | correta |
| 3ª menor | ignorou o ♯ ou decorou "Ré–Fá é menor" |
| 4ª justa | usou os 4 semitons como número |
| 5ª justa | contou teclas/casas (Ré, Ré♯, Mi, Fá, Fá♯) como notas |

**Explicação**: o app mostra a mesma `explicacao` para quem acertou e para quem errou, e só há uma
tentativa. Então ela diz a regra aplicada a este item e nomeia a armadilha da opção errada mais provável.
Uma a três frases, sem elogio genérico. Ex.: "Ré, Mi, Fá: três notas, é uma 3ª. São 4 semitons, então é
maior. Se você marcou 4ª, contou semitons em vez de notas."

**Regras do formato** (o validador cobra):
- De 2 a 5 opções, sem repetidas; `correta` é índice a partir de 0.
- Se a pergunta mostra um exemplo com `intervalo`, a opção correta é exatamente o nome do intervalo:
  "3ª maior", "5ª justa", "uníssono" (com ª).
- `percepcao` exige `intervalo` no exemplo. A legenda só aparece depois da resposta e pode dizer o nome.
- Em `multipla_escolha` com exemplo, o `titulo` aparece na tela: não ponha a resposta nele ("Ré e Fá♯").
- Perguntas de semitons levam `verificacao` (`{"tipo": "semitons", "intervalo": "3M"}`) e a opção
  correta contém só o número certo ("4 semitons").
- `teclado`: `nota_base` e a nota-alvo dentro de `de`/`ate` e entre E3 e E6.

## 8. Notação e repertório

- Texto: dó-ré-mi (Dó, Ré♯, Si♭), com ♯ e ♭ de verdade. Cifras (C, Dm, G7) só para acordes.
  Oitava quando importa: Dó4 é o Dó central.
- Dados: notação científica ASCII ("C4", "F#4", "Bb3"); códigos de intervalo "3M", "5J", "2m", de 1 a 8.
  O campo `intervalo` reduz intervalos compostos (Dó4–Mi5 vira "3M"); se o texto fala de 10ª, diga
  "10ª maior (3ª maior composta)".
- Referências: músicas brasileiras conhecidas de qualquer estilo (cantigas de roda, folclore, samba,
  choro, bossa nova, MPB, forró, sertanejo, pop).
- **Tocado** (`exemplo`): só melodia em domínio público (cantigas, folclore, hinos antigos) ou poucas notas.
- **Citado** (`tabela`): música protegida pode aparecer pelo título e pelas palavras do trecho, sem tocar.
- Nunca afirme "esta música começa com uma 6ª maior" sem ter conferido em partitura ou MIDI. Na dúvida,
  não cite. O mesmo vale para autor e ano.

## 9. Validar e corrigir

```bash
cd apps/api
python -m music_tutor validar ../../aulas-exemplo/<arquivo>.json
python -m music_tutor renderizar ../../aulas-exemplo/<arquivo>.json -o /tmp/aula.html --timbre violao
```

Corrija **todos** os erros e rode de novo até sair `ok`. O validador aponta o lugar
(`secoes[2].blocos[1]`, `exercicios[4]`). Ele não lê texto livre: confira à mão cada intervalo, semitom ou
nota citado em `markdown`, `legenda`, `tabela` e `explicacao`, por exemplo com
`python -c "from music_tutor.teoria import calcular_intervalo; print(calcular_intervalo('B3','F4'))"`.
Abra o HTML nos dois timbres.

## 10. Checklist final

- [ ] Abertura com aquecimento de memória, som antes do nome e objetivo em uma frase.
- [ ] Um conceito por bloco; exemplos de até 4 compassos.
- [ ] Toda ideia nova tem exemplo com legenda "o que ouvir" e, quando ajuda, teclado.
- [ ] Exemplo resolvido, pergunta de autoexplicação e retirada gradual de passos.
- [ ] Um exemplo errado com um único erro realista, depois dos exemplos corretos.
- [ ] 8 a 14 exercícios intercalados, com recuperação de módulos anteriores.
- [ ] Pelo menos uma pergunta-chave com cada opção errada ligada a um equívoco.
- [ ] Explicações dizem por quê e nomeiam a armadilha mais provável.
- [ ] `conceito` de cada exercício existe no YAML do módulo.
- [ ] Enunciados neutros quanto ao instrumento; notas de teclado entre E3 e E6.
- [ ] Notação: dó-ré-mi no texto, cifras só para acordes, ASCII nos dados.
- [ ] Repertório brasileiro; tocado só em domínio público ou poucas notas; fatos conferidos.
- [ ] `python -m music_tutor validar` sem erros; HTML conferido em piano e violão.
- [ ] `resumo` com 4 a 6 pontos e `pergunta_para_chat` que convide à prática no chat.

## Referências

Texto original, adaptado ao ensino de música a partir de técnicas descritas na biblioteca
GarethManning/education-agent-skills (CC BY-SA 4.0). Este arquivo é distribuído sob a mesma licença.

- `skills/explicit-instruction/lesson-opening-designer` (Rosenshine, 2012; Ausubel, 1960; Agarwal et al., 2012)
- `skills/memory-learning-science/cognitive-load-analyser` (Sweller, 1988, 1994; Sweller et al., 2019; Kalyuga et al., 2003)
- `skills/memory-learning-science/dual-coding-designer` (Paivio, 1986; Mayer, 2009)
- `skills/memory-learning-science/worked-example-fading-designer` (Sweller & Cooper, 1985; Renkl, 2014; van Merriënboer & Kirschner, 2018)
- `skills/ai-learning-science/digital-worked-example-sequence` (Renkl, Atkinson & Große, 2004; Wylie & Chi, 2014)
- `skills/ai-learning-science/self-explanation-prompt-designer` (Chi et al., 1989, 1994)
- `skills/ai-learning-science/erroneous-example-designer` (McLaren, Adams & Mayer, 2012; Große & Renkl, 2007)
- `skills/memory-learning-science/retrieval-practice-generator` (Roediger & Butler, 2011; Karpicke & Roediger, 2008)
- `skills/memory-learning-science/interleaving-unit-planner` (Kornell & Bjork, 2008; Rohrer et al., 2015)
- `skills/questioning-discussion/hinge-question-designer` (Wiliam, 2011; Christodoulou, 2017)
- `skills/ai-learning-science/ai-feedback-design-principles` (Shute, 2008; Hattie & Timperley, 2007; Kluger & DeNisi, 1996)
