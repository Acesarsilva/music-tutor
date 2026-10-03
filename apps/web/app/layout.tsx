import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Cabecalho } from "@/components/Cabecalho";
import { ProvedorSessao } from "@/components/Sessao";
import "./globals.css";

export const metadata: Metadata = {
  title: "Professor de Música",
  description: "Aulas de teoria musical com áudio, exercícios e acompanhamento do seu progresso.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <ProvedorSessao>
          <Cabecalho />
          <main>{children}</main>
        </ProvedorSessao>
      </body>
    </html>
  );
}
