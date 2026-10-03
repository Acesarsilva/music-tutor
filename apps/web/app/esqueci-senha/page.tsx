"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { supabase } from "@/lib/supabase";

export default function EsqueciSenha() {
  const [email, setEmail] = useState("");
  const [enviado, setEnviado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    const { error } = await supabase().auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/definir-senha`,
    });
    if (error) setErro(error.message);
    else setEnviado(true);
  }

  return (
    <form onSubmit={enviar} className="cartao formulario">
      <h1>Recuperar senha</h1>
      {enviado ? (
        <p>Se houver uma conta com esse e-mail, você vai receber um link para criar uma nova senha.</p>
      ) : (
        <>
          <label>
            E-mail
            <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          {erro && <p className="aviso erro">{erro}</p>}
          <button type="submit">Enviar link</button>
        </>
      )}
      <p className="nota">
        <Link href="/entrar">Voltar para o login</Link>
      </p>
    </form>
  );
}
