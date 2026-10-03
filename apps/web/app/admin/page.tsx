"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Protegida } from "@/components/Sessao";
import { api, NIVEIS, type Perfil } from "@/lib/api";

type Aluno = Perfil & {
  email?: string;
  confirmado?: boolean;
  ultimo_login?: string | null;
  criado_em: string;
  modulos_concluidos: number;
  respostas: number;
  ultima_resposta: string | null;
};

function data(valor?: string | null) {
  return valor ? new Date(valor).toLocaleDateString("pt-BR") : "—";
}

function Conteudo() {
  const [alunos, setAlunos] = useState<Aluno[] | null>(null);
  const [email, setEmail] = useState("");
  const [nome, setNome] = useState("");
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const carregar = useCallback(() => {
    api<Aluno[]>("/admin/alunos")
      .then(setAlunos)
      .catch((e) => setErro(e.message));
  }, []);
  useEffect(carregar, [carregar]);

  async function convidar(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setMensagem(null);
    try {
      await api("/admin/convites", { method: "POST", body: JSON.stringify({ email, nome }) });
      setMensagem(`Convite enviado para ${email}.`);
      setEmail("");
      setNome("");
      carregar();
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="painel">
      <form onSubmit={convidar} className="cartao formulario">
        <h1>Convidar aluno</h1>
        <label>
          E-mail
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Nome (opcional)
          <input maxLength={120} value={nome} onChange={(e) => setNome(e.target.value)} />
        </label>
        {mensagem && <p className="ok">{mensagem}</p>}
        {erro && <p className="aviso erro">{erro}</p>}
        <button type="submit">Enviar convite</button>
      </form>

      <section className="cartao">
        <h2>Alunos</h2>
        {!alunos ? (
          <p className="carregando">Carregando…</p>
        ) : (
          <div className="tabela-rolavel">
            <table>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>E-mail</th>
                  <th>Nível</th>
                  <th>Módulos concluídos</th>
                  <th>Respostas</th>
                  <th>Última atividade</th>
                  <th>Situação</th>
                </tr>
              </thead>
              <tbody>
                {alunos.map((a) => (
                  <tr key={a.id}>
                    <td>
                      {a.nome || "—"}
                      {a.papel === "admin" && " (admin)"}
                    </td>
                    <td>{a.email ?? "—"}</td>
                    <td>{NIVEIS[a.nivel]}</td>
                    <td>{a.modulos_concluidos}</td>
                    <td>{a.respostas}</td>
                    <td>{data(a.ultima_resposta ?? a.ultimo_login)}</td>
                    <td>{a.termos_aceitos_em ? "Ativo" : a.confirmado === false ? "Convite pendente" : "Primeiro acesso"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default function Admin() {
  return (
    <Protegida soAdmin>
      <Conteudo />
    </Protegida>
  );
}
