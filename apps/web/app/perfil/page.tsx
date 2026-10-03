"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { EscolhaTimbre } from "@/components/EscolhaTimbre";
import { Protegida, useSessao } from "@/components/Sessao";
import { api, NIVEIS, type Perfil } from "@/lib/api";

function Conteudo() {
  const { perfil, recarregarPerfil, sair } = useSessao();
  const router = useRouter();
  const [nome, setNome] = useState(perfil!.nome);
  const [timbre, setTimbre] = useState<Perfil["timbre"]>(perfil!.timbre);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [confirmacao, setConfirmacao] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  async function salvar(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/eu", { method: "PATCH", body: JSON.stringify({ nome: nome.trim(), timbre }) });
      await recarregarPerfil();
      setMensagem("Perfil salvo.");
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    }
  }

  async function baixarDados() {
    const dados = await api("/eu/dados");
    const url = URL.createObjectURL(new Blob([JSON.stringify(dados, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "meus-dados-professor-de-musica.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  async function excluirConta() {
    try {
      await api("/eu", { method: "DELETE", body: JSON.stringify({ confirmo: confirmacao }) });
      await sair();
      router.replace("/entrar");
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="painel">
      <form onSubmit={salvar} className="cartao formulario">
        <h1>Seu perfil</h1>
        <p className="nota">
          {perfil!.email} · nível {NIVEIS[perfil!.nivel].toLowerCase()}
        </p>
        <label>
          Nome
          <input required maxLength={120} value={nome} onChange={(e) => setNome(e.target.value)} />
        </label>
        <EscolhaTimbre valor={timbre} aoMudar={setTimbre} />
        {mensagem && <p className="ok">{mensagem}</p>}
        <button type="submit">Salvar</button>
      </form>

      <section className="cartao formulario">
        <h2>Seus dados</h2>
        <p>Você pode baixar tudo o que o app guarda sobre você: perfil, progresso, respostas e conversas.</p>
        <button type="button" className="secundario" onClick={baixarDados}>
          Baixar meus dados
        </button>
        <h3>Excluir conta</h3>
        <p>A conta e todo o seu progresso são apagados para sempre. Para confirmar, digite EXCLUIR.</p>
        <input value={confirmacao} onChange={(e) => setConfirmacao(e.target.value)} aria-label="Confirmação" />
        {erro && <p className="aviso erro">{erro}</p>}
        <button type="button" className="perigo" disabled={confirmacao !== "EXCLUIR"} onClick={excluirConta}>
          Excluir minha conta
        </button>
      </section>
    </div>
  );
}

export default function PaginaPerfil() {
  return (
    <Protegida>
      <Conteudo />
    </Protegida>
  );
}
