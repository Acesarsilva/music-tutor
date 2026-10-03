import { supabase } from "./supabase";

export class ErroApi extends Error {
  constructor(public status: number, mensagem: string) {
    super(mensagem);
  }
}

function base(): string {
  return (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

// Chama a API com o token do aluno logado. A API confere o token e aplica o RLS do banco.
export async function api<T = unknown>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const { data } = await supabase().auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new ErroApi(401, "Faça login para continuar.");
  const headers = new Headers(opcoes.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (opcoes.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const resposta = await fetch(`${base()}${caminho}`, { ...opcoes, headers });
  if (!resposta.ok) {
    let mensagem = `Erro ${resposta.status}`;
    try {
      const corpo = await resposta.json();
      if (typeof corpo.detail === "string") mensagem = corpo.detail;
    } catch {
      /* corpo sem JSON */
    }
    throw new ErroApi(resposta.status, mensagem);
  }
  if (resposta.status === 204) return undefined as T;
  const tipo = resposta.headers.get("Content-Type") ?? "";
  return (tipo.includes("application/json") ? await resposta.json() : await resposta.text()) as T;
}

export type Perfil = {
  id: string;
  nome: string;
  email?: string;
  papel: "aluno" | "admin";
  nivel: "iniciante" | "intermediario" | "avancado";
  timbre: "piano" | "violao";
  objetivos: string[];
  termos_aceitos_em: string | null;
};

export type ModuloPainel = {
  codigo: string;
  titulo: string;
  nivel: Perfil["nivel"];
  prerequisitos: string[];
  status: "em_andamento" | "concluido" | null;
  dominio: number;
  proxima_revisao: string | null;
  aula_disponivel: boolean;
};

export type Conceito = { conceito: string; dominio: number; acertos?: number; erros?: number; proxima_revisao?: string };

export type Painel = {
  perfil: Perfil;
  modulos: ModuloPainel[];
  revisoes: Conceito[];
  conceitos_fracos: Conceito[];
  hoje: string;
};

export const NIVEIS: Record<Perfil["nivel"], string> = {
  iniciante: "Iniciante",
  intermediario: "Intermediário",
  avancado: "Avançado",
};

// "qualidade-maior-menor" -> "Qualidade maior menor"
export function nomeConceito(conceito: string): string {
  const texto = conceito.replace(/-/g, " ");
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}
