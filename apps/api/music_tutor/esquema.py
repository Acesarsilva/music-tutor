"""Formato de uma aula gerada (JSON). O Claude devolve exatamente este formato."""

from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class Evento(BaseModel):
    notas: list[str] = Field(
        description='Notas tocadas juntas, em notação científica ASCII ("C4", "F#4", "Bb3"). Lista vazia = pausa.'
    )
    duracao: float = Field(description="Duração em tempos, semínima = 1 (0.5 = colcheia, 2 = mínima).")
    silaba: Optional[str] = Field(
        None,
        description='Sílaba da letra cantada nesta nota, mostrada sob a partitura. Termine com "-" quando a palavra continua ("Ci-", "ran-", "da").',
    )
    dinamica: Optional[Literal["pp", "p", "mp", "mf", "f", "ff"]] = Field(
        None, description="Dinâmica a partir desta nota (vale até a próxima indicação), escrita sob a pauta e ouvida no áudio."
    )
    acento: bool = Field(False, description="Acento (>) nesta nota: soa mais forte que as vizinhas.")
    ligada: bool = Field(
        False, description="Ligadura com o evento seguinte, que precisa ter as mesmas notas: as duas durações soam como uma só."
    )
    staccato: bool = Field(False, description="Staccato (ponto sobre a nota): soa bem curta, separada da seguinte.")
    expressao: Optional[Literal["inicio", "fim"]] = Field(
        None, description="Ligadura de expressão (legato): começa nesta nota ou termina nela."
    )
    forquilha: Optional[Literal["crescendo", "diminuendo", "fim"]] = Field(
        None,
        description='Forquilha de crescendo ou diminuendo que começa nesta nota; "fim" a encerra numa nota que traz a dinâmica de chegada.',
    )


class IntervaloAfirmado(BaseModel):
    """Intervalo que o texto afirma existir no exemplo; o validador confere com music21."""

    de: str = Field(description="Nota mais grave ou primeira nota, ex.: C4")
    para: str = Field(description="Outra nota do intervalo, ex.: E4")
    codigo: str = Field(description='Código do intervalo: número + J/M/m/A/d, ex.: "3M", "5J", "2m".')


class Exemplo(BaseModel):
    id: str = Field(description="Identificador curto e único na aula, ex.: ex-3m-ré-fá")
    titulo: str
    legenda: str = Field(description="Uma ou duas frases sobre o que ouvir.")
    eventos: list[Evento]
    compasso: str = "4/4"
    anacruse: float = Field(0, description="Tempos antes do primeiro compasso completo (0 se não houver).")
    andamento: int = Field(72, description="Semínimas por minuto.")
    clave: Literal["sol", "fa"] = "sol"
    armadura: str = Field(
        "C",
        description='Armadura de clave pela tônica maior: "C" (nenhuma), "G", "D", "F", "Bb", "F#" etc. '
        "As notas dos eventos continuam com o acidente real (F#4 em Sol maior).",
    )
    intervalo: Optional[IntervaloAfirmado] = None


class BlocoTexto(BaseModel):
    tipo: Literal["texto"]
    markdown: str


class BlocoDica(BaseModel):
    tipo: Literal["dica"]
    markdown: str


class BlocoResposta(BaseModel):
    """Resposta escondida até o aluno abrir: use depois de uma pergunta para ele pensar antes."""

    tipo: Literal["resposta"]
    markdown: str
    rotulo: str = Field("Ver resposta", description="Texto do botão que abre a resposta.")


class BlocoExemplo(BaseModel):
    tipo: Literal["exemplo"]
    exemplo: Exemplo


class BlocoTabela(BaseModel):
    tipo: Literal["tabela"]
    legenda: str
    cabecalho: list[str]
    linhas: list[list[str]]


class BlocoTeclado(BaseModel):
    tipo: Literal["teclado"]
    legenda: str
    destaque: list[str] = Field(description="Notas destacadas no teclado, ex.: [\"C4\", \"E4\"].")
    de: str = Field("C4", description="Primeira tecla mostrada.")
    ate: str = Field("C5", description="Última tecla mostrada.")


Bloco = Annotated[
    Union[BlocoTexto, BlocoDica, BlocoResposta, BlocoExemplo, BlocoTabela, BlocoTeclado],
    Field(discriminator="tipo"),
]


class Secao(BaseModel):
    titulo: str
    blocos: list[Bloco]


class VerificacaoSemitons(BaseModel):
    """Confere uma pergunta do tipo "quantos semitons tem X?"."""

    tipo: Literal["semitons"]
    intervalo: str


class ExercicioMultipla(BaseModel):
    tipo: Literal["multipla_escolha"]
    enunciado: str
    exemplo: Optional[Exemplo] = Field(None, description="Partitura mostrada junto da pergunta (com áudio).")
    opcoes: list[str]
    correta: int = Field(description="Índice (a partir de 0) da opção correta.")
    explicacao: str
    conceito: str = Field(description="Conceito avaliado, ex.: intervalo-3m, semitons, qualidade-justa.")
    verificacao: Optional[VerificacaoSemitons] = None


class ExercicioPercepcao(BaseModel):
    tipo: Literal["percepcao"]
    enunciado: str
    exemplo: Exemplo = Field(description="Tocado sem mostrar a partitura até o aluno responder.")
    opcoes: list[str]
    correta: int
    explicacao: str
    conceito: str


class ExercicioTeclado(BaseModel):
    tipo: Literal["teclado"]
    enunciado: str
    nota_base: str = Field(description="Nota de partida, destacada no teclado.")
    intervalo: str = Field(description='Código do intervalo pedido, ex.: "5J".')
    direcao: Literal["acima", "abaixo"] = "acima"
    explicacao: str
    conceito: str
    de: str = "C4"
    ate: str = "C6"


Exercicio = Annotated[
    Union[ExercicioMultipla, ExercicioPercepcao, ExercicioTeclado],
    Field(discriminator="tipo"),
]


class Aula(BaseModel):
    codigo: str = Field(description="Código do módulo, ex.: I08.")
    titulo: str
    nivel: Literal["iniciante", "intermediario", "avancado"]
    resumo_curto: str = Field(description="Uma frase que aparece no topo da aula.")
    prerequisitos: list[str]
    objetivos: list[str]
    secoes: list[Secao]
    exercicios: list[Exercicio]
    resumo: list[str] = Field(description="Pontos principais para revisar.")
    pergunta_para_chat: str = Field(description="Pergunta que o aluno pode levar ao chat do professor.")
