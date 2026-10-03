"use client";

import type { Session } from "@supabase/supabase-js";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type Perfil } from "@/lib/api";
import { supabase } from "@/lib/supabase";

type EstadoSessao = {
  carregando: boolean;
  sessao: Session | null;
  perfil: Perfil | null;
  erro: string | null;
  recarregarPerfil: () => Promise<void>;
  sair: () => Promise<void>;
};

const Contexto = createContext<EstadoSessao | null>(null);

export function ProvedorSessao({ children }: { children: ReactNode }) {
  const [carregando, setCarregando] = useState(true);
  const [sessao, setSessao] = useState<Session | null>(null);
  const [perfil, setPerfil] = useState<Perfil | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const recarregarPerfil = useCallback(async () => {
    try {
      setPerfil(await api<Perfil>("/eu"));
      setErro(null);
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    let cliente;
    try {
      cliente = supabase();
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
      setCarregando(false);
      return;
    }
    cliente.auth.getSession().then(async ({ data }) => {
      setSessao(data.session);
      if (data.session) await recarregarPerfil();
      setCarregando(false);
    });
    const { data } = cliente.auth.onAuthStateChange((evento, nova) => {
      setSessao(nova);
      if (!nova) setPerfil(null);
      else if (evento === "SIGNED_IN") void recarregarPerfil();
    });
    return () => data.subscription.unsubscribe();
  }, [recarregarPerfil]);

  const sair = useCallback(async () => {
    await supabase().auth.signOut();
    setPerfil(null);
  }, []);

  return (
    <Contexto.Provider value={{ carregando, sessao, perfil, erro, recarregarPerfil, sair }}>
      {children}
    </Contexto.Provider>
  );
}

export function useSessao(): EstadoSessao {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("useSessao fora do ProvedorSessao");
  return valor;
}

// Só mostra o conteúdo para quem entrou e já aceitou os termos; manda os outros para a página certa.
export function Protegida({ children, soAdmin = false }: { children: ReactNode; soAdmin?: boolean }) {
  const { carregando, sessao, perfil, erro } = useSessao();
  const router = useRouter();
  const caminho = usePathname();

  useEffect(() => {
    if (carregando) return;
    if (!sessao) router.replace(`/entrar?voltar=${encodeURIComponent(caminho)}`);
    else if (perfil && !perfil.termos_aceitos_em && caminho !== "/boas-vindas") router.replace("/boas-vindas");
  }, [carregando, sessao, perfil, caminho, router]);

  if (erro && !perfil) return <p className="aviso erro">{erro}</p>;
  if (carregando || !sessao || !perfil) return <p className="carregando">Carregando…</p>;
  if (!perfil.termos_aceitos_em && caminho !== "/boas-vindas") return <p className="carregando">Carregando…</p>;
  if (soAdmin && perfil.papel !== "admin") return <p className="aviso">Esta página é só para o administrador.</p>;
  return <>{children}</>;
}
