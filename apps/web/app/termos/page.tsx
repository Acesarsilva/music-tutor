import type { Metadata } from "next";

export const metadata: Metadata = { title: "Termos de uso e privacidade · Professor de Música" };

const CONTATO = process.env.NEXT_PUBLIC_CONTATO_PRIVACIDADE;

export default function Termos() {
  return (
    <article className="cartao texto">
      <h1>Termos de uso e política de privacidade</h1>

      <h2>O serviço</h2>
      <p>
        O Professor de Música oferece aulas de teoria musical com exemplos em áudio, exercícios e um professor virtual
        baseado em inteligência artificial. O acesso é gratuito e feito por convite. As explicações são revisadas por
        regras de teoria musical, mas podem conter erros; use o bom senso e pergunte quando algo não fizer sentido.
      </p>

      <h2>Sua conta</h2>
      <p>
        A conta é pessoal. Guarde sua senha e não a compartilhe. Podemos suspender contas usadas para abuso, como envio
        automatizado de mensagens ou tentativa de acessar dados de outras pessoas. Existe um limite diário de uso por
        aluno.
      </p>

      <h2>Quais dados guardamos</h2>
      <ul>
        <li>Nome, e-mail e a senha (guardada só em forma criptografada, por hash).</li>
        <li>Preferências, como o instrumento dos exemplos e seus objetivos de estudo.</li>
        <li>Progresso: aulas abertas e concluídas, respostas dos exercícios, domínio de cada conceito e revisões.</li>
        <li>Conversas com o professor virtual, composições que você enviar e anotações do professor sobre seu estudo.</li>
        <li>Contagem de uso diário, para aplicar os limites.</li>
      </ul>

      <h2>Para que usamos</h2>
      <p>
        Só para dar as aulas e personalizar seu estudo: escolher a próxima aula, os exercícios e as revisões. Não
        vendemos nem compartilhamos seus dados para publicidade. A base legal é a execução do serviço que você pediu
        ao aceitar o convite (LGPD, art. 7º, V).
      </p>

      <h2>Quem processa os dados</h2>
      <p>
        Os dados ficam no Supabase (banco de dados e login). O site roda na Vercel e o servidor em um provedor de
        nuvem. Para gerar respostas e aulas, o texto da conversa e um resumo do seu progresso são enviados à Anthropic,
        empresa que fornece o modelo Claude. Esses serviços podem guardar os dados fora do Brasil, com as garantias
        previstas na LGPD.
      </p>

      <h2>Seus direitos</h2>
      <p>
        Na página do seu perfil você pode baixar todos os seus dados e excluir sua conta a qualquer momento; a exclusão
        apaga o progresso e as conversas. Para corrigir dados ou tirar dúvidas sobre privacidade,{" "}
        {CONTATO ? <>escreva para {CONTATO}</> : <>responda ao e-mail do seu convite</>}.
      </p>

      <h2>Mudanças</h2>
      <p>Se estes termos mudarem, você verá o novo texto e precisará aceitá-lo de novo para continuar.</p>
    </article>
  );
}
