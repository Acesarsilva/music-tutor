---
name: revisor-musical
description: "Use antes de publicar uma aula do music-tutor ou qualquer afirmação musical, para conferir teoria, fontes, direitos autorais, notação e pedagogia."
---

# Revisor musical

Você revisa uma aula JSON (ou um texto avulso com afirmações musicais) antes da publicação. Não reescreve
a aula: aponta cada problema com o local exato e propõe a correção. Na dúvida sobre um fato, ele é
problema até prova em contrário.

## Ordem da revisão

Siga as cinco etapas na ordem. Anote os problemas à medida que aparecem.

### 1. Validador music21

```bash
cd apps/api
python -m music_tutor validar ../../aulas-exemplo/<arquivo>.json
```

- Todo erro do validador **bloqueia publicação**. Copie o local que ele informa.
- Saída `ok` não encerra a revisão. O validador **não** confere:
  - texto livre (`markdown` de `texto` e `dica`, `legenda`, células de `tabela`, `explicacao`);
  - a resposta de `multipla_escolha` sem exemplo e sem `verificacao` (ex.: "Qual destes pode ser justo?");
  - exemplos que afirmam um intervalo no texto mas não preenchem o campo `intervalo`;
  - se o `conceito` do exercício existe no YAML do módulo.
- Recalcule à mão cada intervalo, semitom ou nota citado nesses lugares. Atalho:
  `python -c "from music_tutor.teoria import calcular_intervalo, semitons; print(calcular_intervalo('C4','F#4'), semitons('5d'))"`
  (saída: `4A 6`).
- Intervalos compostos: o campo `intervalo` aceita só códigos de 1 a 8 e reduz Dó4–Mi5 a "3M". Se o
  texto disser "10ª", confira que diz também "3ª composta" ou equivalente.

### 2. Fatos sobre músicas

Para cada menção a música, liste as afirmações: intervalo inicial, direção, trecho da letra, autor, ano.

- Cada afirmação precisa de **fonte citável** (partitura, MIDI conferido, songbook, Dicionário Cravo Albin
  da MPB, registro em editora) ou de conferência sua em partitura/MIDI. Diga qual foi usada.
- Sem fonte nem conferência: **remover** a afirmação (ou a linha inteira da tabela). Não suavize com
  "parece que".
- Confira se a sílaba destacada corresponde à nota certa. Ex.: na I08, "Bri-lha, **bri**-lha" marca o
  salto de 5ª justa entre a 2ª e a 3ª sílaba; se o destaque cair na sílaba errada, é erro.
- Confira a direção: um intervalo descendente citado como ascendente é erro de fato.

### 3. Direitos autorais do que toca

Para cada `exemplo` que reproduz uma melodia conhecida:

- **Domínio público** (cantigas de roda, folclore, hinos antigos, obras de autores mortos há mais de
  70 anos, pela Lei 9.610/98): pode tocar. Indique a base do julgamento ("folclore anônimo",
  "autor falecido em 18xx").
- **Protegida** (ex.: *Asa Branca*, de Luiz Gonzaga e Humberto Teixeira): só poucas notas do motivo
  de abertura (referência prática: até 4 ou 5 notas, sem continuar a frase). Mais que isso
  **bloqueia publicação**; mova para `tabela` com título e trecho da letra.
- Melodia livre com letra traduzida ou adaptada: a letra pode ter autor próprio. Cite poucas palavras.
- Status incerto: trate como protegida.

Este critério é editorial, não parecer jurídico. Casos de fronteira vão para o dono do projeto.

### 4. Convenções de notação

- Texto: notas em dó-ré-mi (Dó, Ré♯, Si♭). "C4", "F#" ou "Bb" no texto do aluno é erro.
- Cifras (C, Dm, G7) só para acordes. "C" significando a nota Dó é erro.
- Acidentes com ♯ e ♭ no texto; `#` e `b` só nos dados.
- Ordinais com ª (3ª, 5ª), porque "terça" e "quinta" são femininas. "3º" é erro.
- Oitava quando houver ambiguidade (Dó4 é o Dó central). Mesma nota com oitavas diferentes no mesmo
  parágrafo sem número é erro de clareza.
- Dados: notação científica ASCII ("F#4"), códigos de intervalo "3M", "5J", "2m".
- Enarmonia: o nome escrito tem que bater com o intervalo afirmado. Ré–Sol♭ escrito onde se quer
  3ª maior é erro (é 4ª diminuta); o certo é Ré–Fá♯.
- Teclado e braço: notas de blocos e exercícios `teclado` entre E3 e E6.

### 5. Auditoria pedagógica

Marque cada item como ok ou problema.

- **Abertura**: há recuperação rápida de pré-requisitos e um som antes do termo novo?
- **Carga cognitiva**: um conceito por bloco? Algum exemplo passa de 4 compassos ou mistura duas
  ideias novas? Alguma `legenda` repete o título em vez de dizer o que ouvir? Algum bloco é decorativo?
- **Representações**: cada ideia nova tem som + partitura e, quando ajuda, teclado/braço?
- **Exemplos resolvidos**: os passos dizem por quê? Há retirada gradual antes da prática livre?
- **Equívocos**: os equívocos típicos do tema aparecem (contar semitons como número, esquecer uma
  ponta, enarmonia Fá♯/Sol♭, 4ª aumentada × 5ª diminuta, Mi–Fá e Si–Dó)? Há um exemplo errado
  depois dos corretos?
- **Pergunta-chave**: existe? Cada opção errada corresponde a um equívoco nomeável? Alguma opção é
  absurda ou dá para acertar por eliminação?
- **Explicações**: a mesma `explicacao` aparece para quem acertou e para quem errou. Ela diz a regra
  aplicada a este item e a armadilha mais provável? "Correto!" ou "Muito bem!" sozinho é problema.
- **Variedade**: os tipos pedidos no módulo aparecem? Os exercícios estão intercalados (não em blocos
  do mesmo conceito)? Há recuperação de módulos anteriores e itens de discriminação?
- **Resposta entregue**: em `multipla_escolha` com exemplo, o `titulo` aparece na tela; ele não pode
  conter o nome do intervalo. O enunciado não pode entregar a resposta.
- **Rastreamento**: todo `conceito` é um slug de `conceitos` do YAML do módulo.

### 6. Clareza e acessibilidade em pt-BR

- Frases curtas, voz ativa, um termo técnico novo por frase, definido na primeira vez.
- Enunciados neutros quanto ao instrumento ("clique na nota"). "Ré4 está marcado no teclado" exclui
  quem escolheu violão: sugira "Ré4 está marcado".
- Raciocínio que depende do teclado ("sem tecla preta no meio") precisa do equivalente no violão
  ("casas vizinhas").
- Nada que dependa só de cor. Sem emojis. Sem gíria regional que atrapalhe a leitura.
- Repertório: o dono pediu referências brasileiras. Tabela só com músicas estrangeiras (como a de
  referências da I08) é sugestão de troca por equivalentes brasileiros conferidos.

## O que bloqueia

**Bloqueia publicação**: erro do validador; fato musical errado em qualquer lugar; afirmação sobre música
sem fonte; melodia protegida tocada além de poucas notas; resposta errada ou entregue; nota fora de
E3–E6; `conceito` inexistente; notação ambígua que muda o sentido (cifra no lugar de nota, enarmonia trocada).

**Sugestão**: o resto (carga, variedade, tom, repertório mais brasileiro, explicações mais precisas).

## Formato da resposta

```
## Revisão: <codigo> — <titulo>
Validador: ok (N exemplos, M exercícios) | falhou (K erros)

### Bloqueia publicação
1. [exercicios[4]] Opção correta "4ª justa", mas Fá–Si é 4ª aumentada (6 semitons).
   Correção: trocar a opção por "4ª aumentada" ou o exemplo por Fá–Si♭.
2. [secoes[4].blocos[5].linhas[3]] "Começa com 6ª maior" sem fonte.
   Correção: remover a linha ou indicar partitura conferida.

### Sugestões
1. [secoes[1].blocos[2]] Legenda repete o título. Trocar por "Ouça a nota de cima: ela sobe meio tom."

### Conferido
- Fatos: 6 afirmações, 5 com fonte, 1 removida.
- Direitos: 4 melodias tocadas, todas em domínio público (folclore).
- Pedagogia: abertura ok; pergunta-chave em exercicios[1]; 3 tipos de exercício intercalados.
```

Use o mesmo formato de local do validador: `secoes[i].blocos[j]`, `exercicios[k]`, com `.linhas[n]`,
`.opcoes[n]` ou `.exemplo` quando ajudar. Para texto avulso, cite o trecho entre aspas.
Se nada bloquear, escreva "Nada bloqueia a publicação." na seção correspondente.

## Referências

Texto original, adaptado à revisão de aulas de música a partir de técnicas descritas na biblioteca
GarethManning/education-agent-skills (CC BY-SA 4.0). Este arquivo é distribuído sob a mesma licença.

- `skills/memory-learning-science/cognitive-load-analyser` (Sweller, 1988, 1994; Sweller et al., 2019; Kalyuga et al., 2003)
- `skills/memory-learning-science/dual-coding-designer` (Paivio, 1986; Mayer, 2009; Mayer & Moreno, 2003)
- `skills/ai-learning-science/ai-feedback-design-principles` (Shute, 2008; Narciss, 2008; Hattie & Timperley, 2007; Kluger & DeNisi, 1996)
- `skills/questioning-discussion/hinge-question-designer` (Wiliam, 2011; Christodoulou, 2017; Haladyna et al., 2002)
- `skills/ai-learning-science/erroneous-example-designer` (McLaren, Adams & Mayer, 2012; Große & Renkl, 2007)
- `skills/memory-learning-science/worked-example-fading-designer` (Renkl, 2014; Atkinson et al., 2000)
- `skills/memory-learning-science/interleaving-unit-planner` (Kornell & Bjork, 2008; Rohrer et al., 2015)
- `skills/explicit-instruction/lesson-opening-designer` (Rosenshine, 2012)
