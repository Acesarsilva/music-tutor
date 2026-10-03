"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Protegida } from "@/components/Sessao";
import { api, nomeConceito, NIVEIS, type ModuloPainel, type Painel as DadosPainel } from "@/lib/api";

function Dominio({ valor }: { valor: number }) {
  return (
    <span className="dominio" title={`Domínio: ${valor}%`}>
      <span style={{ width: `${valor}%` }} />
    </span>
  );
}

function Modulo({ m }: { m: ModuloPainel }) {
  const situacao = m.status === "concluido" ? "Concluído" : m.status === "em_andamento" ? "Em andamento" : "";
  const conteudo = (
    <>
      <span className="codigo">{m.codigo}</span>
      <span className="titulo">{m.titulo}</span>
      <span className="situacao">{m.aula_disponivel ? situacao : "Em breve"}</span>
      <Dominio valor={m.dominio} />
    </>
  );
  return (
    <li className={`modulo ${m.status ?? "novo"} ${m.aula_disponivel ? "" : "indisponivel"}`}>
      {m.aula_disponivel ? <Link href={`/aulas/${m.codigo}`}>{conteudo}</Link> : <div>{conteudo}</div>}
    </li>
  );
}

function Conteudo() {
  const [painel, setPainel] = useState<DadosPainel | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    api<DadosPainel>("/painel")
      .then(setPainel)
      .catch((e) => setErro(e.message));
  }, []);

  if (erro) return <p className="aviso erro">{erro}</p>;
  if (!painel) return <p className="carregando">Carregando seu painel…</p>;

  const proxima =
    painel.modulos.find((m) => m.aula_disponivel && m.status === "em_andamento") ??
    painel.modulos.find((m) => m.aula_disponivel && !m.status);
  const niveis = (Object.keys(NIVEIS) as (keyof typeof NIVEIS)[]).filter((n) => painel.modulos.some((m) => m.nivel === n));

  return (
    <div className="painel">
      <section className="cartao destaque">
        <h1>Olá, {painel.perfil.nome || "aluno"}!</h1>
        {proxima ? (
          <p>
            Próxima aula:{" "}
            <Link href={`/aulas/${proxima.codigo}`} className="botao">
              {proxima.codigo} · {proxima.titulo}
            </Link>
          </p>
        ) : (
          <p>Você já abriu todas as aulas publicadas. Novas aulas aparecem aqui assim que ficarem prontas.</p>
        )}
      </section>

      <section className="cartao">
        <h2>Revisões de hoje</h2>
        {painel.revisoes.length === 0 ? (
          <p className="nota">Nada para revisar hoje.</p>
        ) : (
          <ul className="conceitos">
            {painel.revisoes.map((c) => (
              <li key={c.conceito}>
                {nomeConceito(c.conceito)} <Dominio valor={c.dominio} />
              </li>
            ))}
          </ul>
        )}
      </section>

      {painel.conceitos_fracos.length > 0 && (
        <section className="cartao">
          <h2>Pontos para reforçar</h2>
          <ul className="conceitos">
            {painel.conceitos_fracos.map((c) => (
              <li key={c.conceito}>
                {nomeConceito(c.conceito)}{" "}
                <span className="nota">
                  {c.acertos} acertos, {c.erros} erros
                </span>{" "}
                <Dominio valor={c.dominio} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="cartao">
        <h2>Sua trilha</h2>
        {niveis.map((nivel) => (
          <div key={nivel}>
            <h3>{NIVEIS[nivel]}</h3>
            <ul className="modulos">
              {painel.modulos
                .filter((m) => m.nivel === nivel)
                .map((m) => (
                  <Modulo key={m.codigo} m={m} />
                ))}
            </ul>
          </div>
        ))}
      </section>
    </div>
  );
}

export default function Painel() {
  return (
    <Protegida>
      <Conteudo />
    </Protegida>
  );
}
