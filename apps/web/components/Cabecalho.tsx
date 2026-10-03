"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSessao } from "./Sessao";

export function Cabecalho() {
  const { sessao, perfil, sair } = useSessao();
  const router = useRouter();
  return (
    <header className="cabecalho">
      <Link href="/" className="marca">
        Professor de Música
      </Link>
      {sessao && (
        <nav>
          <Link href="/">Painel</Link>
          <Link href="/perfil">Perfil</Link>
          {perfil?.papel === "admin" && <Link href="/admin">Alunos</Link>}
          <button
            className="link"
            onClick={async () => {
              await sair();
              router.replace("/entrar");
            }}
          >
            Sair
          </button>
        </nav>
      )}
    </header>
  );
}
