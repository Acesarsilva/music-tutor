"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Protegida, useSessao } from "@/components/Sessao";
import { api } from "@/lib/api";

type MensagemAula =
  | { origem: "music-tutor-aula"; codigo: string; tipo: "resposta"; indice: number; opcao?: number; midi?: number }
  | { origem: "music-tutor-aula"; codigo: string; tipo: "timbre"; timbre: "piano" | "violao" };

type Correcao = { certo: boolean; conceito: string; dominio: number };

function Aula({ codigo }: { codigo: string }) {
  const { perfil } = useSessao();
  const quadro = useRef<HTMLIFrameElement>(null);
  const [html, setHtml] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [placar, setPlacar] = useState({ salvas: 0, acertos: 0 });
  const [aviso, setAviso] = useState<string | null>(null);
  const [concluida, setConcluida] = useState(false);

  // O HTML é carregado uma vez, no instrumento do perfil; depois a própria aula troca o instrumento.
  const timbreInicial = useRef(perfil?.timbre);
  useEffect(() => {
    const timbre = timbreInicial.current ? `?timbre=${timbreInicial.current}` : "";
    api<string>(`/aulas/${encodeURIComponent(codigo)}${timbre}`)
      .then(setHtml)
      .catch((e) => setErro(e.message));
  }, [codigo]);

  useEffect(() => {
    async function receber(evento: MessageEvent) {
      // Só aceita mensagens do iframe desta aula.
      if (evento.source !== quadro.current?.contentWindow) return;
      const dados = evento.data as MensagemAula;
      if (!dados || dados.origem !== "music-tutor-aula" || dados.codigo !== codigo) return;
      try {
        if (dados.tipo === "resposta") {
          const r = await api<Correcao>(`/aulas/${encodeURIComponent(codigo)}/respostas`, {
            method: "POST",
            body: JSON.stringify({ indice: dados.indice, opcao: dados.opcao, midi: dados.midi }),
          });
          setPlacar((p) => ({ salvas: p.salvas + 1, acertos: p.acertos + (r.certo ? 1 : 0) }));
          setAviso(null);
        } else if (dados.tipo === "timbre") {
          await api("/eu", { method: "PATCH", body: JSON.stringify({ timbre: dados.timbre }) });
        }
      } catch (e) {
        setAviso(`Não consegui salvar seu progresso: ${e instanceof Error ? e.message : e}`);
      }
    }
    window.addEventListener("message", receber);
    return () => window.removeEventListener("message", receber);
  }, [codigo]);

  async function concluir() {
    try {
      await api(`/aulas/${encodeURIComponent(codigo)}/concluir`, { method: "POST" });
      setConcluida(true);
    } catch (e) {
      setAviso(e instanceof Error ? e.message : String(e));
    }
  }

  if (erro) return <p className="aviso erro">{erro}</p>;
  if (html === null) return <p className="carregando">Carregando a aula…</p>;

  return (
    <div className="aula">
      <div className="barra-aula">
        <Link href="/">← Painel</Link>
        <span className="nota">
          {placar.salvas === 0
            ? "Suas respostas são salvas no seu progresso."
            : `${placar.salvas} respostas salvas, ${placar.acertos} certas.`}
        </span>
        {concluida ? (
          <span className="ok">Aula concluída. A revisão fica marcada para amanhã.</span>
        ) : (
          <button onClick={concluir}>Concluir aula</button>
        )}
      </div>
      {aviso && <p className="aviso erro">{aviso}</p>}
      {/* Sem allow-same-origin: a aula não acessa a sessão nem os dados do site. */}
      <iframe ref={quadro} title={`Aula ${codigo}`} srcDoc={html} sandbox="allow-scripts" className="quadro-aula" />
    </div>
  );
}

export default function PaginaAula() {
  const { codigo } = useParams<{ codigo: string }>();
  return (
    <Protegida>
      <Aula codigo={codigo} />
    </Protegida>
  );
}
