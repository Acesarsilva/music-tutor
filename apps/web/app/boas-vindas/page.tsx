"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { EscolhaTimbre } from "@/components/EscolhaTimbre";
import { Protegida, useSessao } from "@/components/Sessao";
import { api, type Perfil } from "@/lib/api";

function Formulario() {
  const { perfil, recarregarPerfil } = useSessao();
  const router = useRouter();
  const [nome, setNome] = useState(perfil?.nome ?? "");
  const [timbre, setTimbre] = useState<Perfil["timbre"]>(perfil?.timbre ?? "piano");
  const [aceito, setAceito] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (perfil?.termos_aceitos_em) router.replace("/");
  }, [perfil, router]);

  async function comecar(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/eu", { method: "PATCH", body: JSON.stringify({ nome: nome.trim(), timbre, aceitar_termos: true }) });
      await recarregarPerfil();
      router.replace("/");
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <form onSubmit={comecar} className="cartao formulario">
      <h1>Boas-vindas!</h1>
      <p>Antes da primeira aula, conte como quer ser chamado e em qual instrumento prefere ouvir os exemplos.</p>
      <label>
        Seu nome
        <input required maxLength={120} value={nome} onChange={(e) => setNome(e.target.value)} />
      </label>
      <EscolhaTimbre valor={timbre} aoMudar={setTimbre} />
      <label className="caixa">
        <input type="checkbox" required checked={aceito} onChange={(e) => setAceito(e.target.checked)} />
        <span>
          Li e aceito os{" "}
          <Link href="/termos" target="_blank">
            termos de uso e a política de privacidade
          </Link>
          .
        </span>
      </label>
      {erro && <p className="aviso erro">{erro}</p>}
      <button type="submit" disabled={!aceito}>
        Começar
      </button>
    </form>
  );
}

export default function BoasVindas() {
  return (
    <Protegida>
      <Formulario />
    </Protegida>
  );
}
