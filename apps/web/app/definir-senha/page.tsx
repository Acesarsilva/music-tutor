"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { useSessao } from "@/components/Sessao";
import { supabase } from "@/lib/supabase";

// Destino dos links de convite e de recuperação de senha: o Supabase já abre a sessão pelo link.
export default function DefinirSenha() {
  const { carregando, sessao } = useSessao();
  const router = useRouter();
  const [senha, setSenha] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  async function salvar(e: FormEvent) {
    e.preventDefault();
    if (senha.length < 8) return setErro("Use pelo menos 8 caracteres.");
    if (senha !== confirmacao) return setErro("As duas senhas não são iguais.");
    setSalvando(true);
    const { error } = await supabase().auth.updateUser({ password: senha });
    setSalvando(false);
    if (error) setErro(error.message);
    else router.replace("/");
  }

  if (carregando) return <p className="carregando">Carregando…</p>;
  if (!sessao)
    return (
      <div className="cartao formulario">
        <h1>Link expirado</h1>
        <p>Este link não vale mais. Peça um novo convite ou recupere a senha.</p>
        <Link href="/esqueci-senha">Recuperar senha</Link>
      </div>
    );

  return (
    <form onSubmit={salvar} className="cartao formulario">
      <h1>Crie sua senha</h1>
      <p className="nota">Conta: {sessao.user.email}</p>
      <label>
        Nova senha
        <input type="password" autoComplete="new-password" required value={senha} onChange={(e) => setSenha(e.target.value)} />
      </label>
      <label>
        Repita a senha
        <input
          type="password"
          autoComplete="new-password"
          required
          value={confirmacao}
          onChange={(e) => setConfirmacao(e.target.value)}
        />
      </label>
      {erro && <p className="aviso erro">{erro}</p>}
      <button type="submit" disabled={salvando}>
        {salvando ? "Salvando…" : "Salvar senha"}
      </button>
    </form>
  );
}
