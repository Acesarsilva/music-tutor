"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState, type FormEvent } from "react";
import { useSessao } from "@/components/Sessao";
import { supabase } from "@/lib/supabase";

function voltarSeguro(valor: string | null): string {
  // Só caminhos internos, para o link de login não virar um redirecionamento para outro site.
  return valor && valor.startsWith("/") && !valor.startsWith("//") ? valor : "/";
}

function Formulario() {
  const router = useRouter();
  const destino = voltarSeguro(useSearchParams().get("voltar"));
  const { sessao, carregando } = useSessao();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (!carregando && sessao) router.replace(destino);
  }, [carregando, sessao, destino, router]);

  async function entrar(e: FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    const { error } = await supabase().auth.signInWithPassword({ email, password: senha });
    setEnviando(false);
    if (error) setErro(error.message === "Invalid login credentials" ? "E-mail ou senha incorretos." : error.message);
    else router.replace(destino);
  }

  return (
    <form onSubmit={entrar} className="cartao formulario">
      <h1>Entrar</h1>
      <label>
        E-mail
        <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      <label>
        Senha
        <input
          type="password"
          autoComplete="current-password"
          required
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
        />
      </label>
      {erro && <p className="aviso erro">{erro}</p>}
      <button type="submit" disabled={enviando}>
        {enviando ? "Entrando…" : "Entrar"}
      </button>
      <p className="nota">
        <Link href="/esqueci-senha">Esqueci minha senha</Link>
      </p>
      <p className="nota">O cadastro é feito por convite. Se você recebeu um, use o link do e-mail.</p>
    </form>
  );
}

export default function Entrar() {
  return (
    <Suspense>
      <Formulario />
    </Suspense>
  );
}
