"use client";

import type { Perfil } from "@/lib/api";

export function EscolhaTimbre({ valor, aoMudar }: { valor: Perfil["timbre"]; aoMudar: (t: Perfil["timbre"]) => void }) {
  return (
    <fieldset className="timbres">
      <legend>Instrumento dos exemplos</legend>
      {(["piano", "violao"] as const).map((t) => (
        <label key={t} className={valor === t ? "escolhido" : ""}>
          <input type="radio" name="timbre" value={t} checked={valor === t} onChange={() => aoMudar(t)} />
          {t === "piano" ? "Piano" : "Violão"}
        </label>
      ))}
    </fieldset>
  );
}
