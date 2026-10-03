"""Linha de comando: validar, renderizar e gerar aulas.

    python -m music_tutor validar aulas-exemplo/I08-intervalos-simples.json
    python -m music_tutor renderizar aulas-exemplo/I08-intervalos-simples.json -o aula.html --timbre violao
    python -m music_tutor gerar I08 -o aula.json            (precisa de ANTHROPIC_API_KEY)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .esquema import Aula
from .render import AulaInvalida, renderizar
from .validacao import validar_aula


def _ler_aula(caminho: str) -> Aula:
    return Aula.model_validate_json(Path(caminho).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="music_tutor")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_val = sub.add_parser("validar", help="confere a teoria de uma aula em JSON")
    p_val.add_argument("aula")

    p_ren = sub.add_parser("renderizar", help="gera o HTML de uma aula em JSON")
    p_ren.add_argument("aula")
    p_ren.add_argument("-o", "--saida", required=True)
    p_ren.add_argument("--timbre", choices=["piano", "violao"], default="piano")
    p_ren.add_argument("--fragmento", action="store_true", help="sem doctype/html/head/body")

    p_ger = sub.add_parser("gerar", help="gera uma aula com o Claude a partir do currículo")
    p_ger.add_argument("codigo", help="código do módulo, ex.: I08")
    p_ger.add_argument("-o", "--saida", required=True, help="arquivo JSON de saída")
    p_ger.add_argument("--perfil", help="JSON com o perfil do aluno")
    p_ger.add_argument("--html", help="também renderiza o HTML neste caminho")

    args = parser.parse_args(argv)

    if args.comando == "validar":
        resultado = validar_aula(_ler_aula(args.aula))
        if resultado.ok:
            print(f"ok: {len(resultado.exemplos)} exemplos e {len(resultado.exercicios)} exercícios conferidos")
            return 0
        print("problemas encontrados:", *resultado.erros, sep="\n- ", file=sys.stderr)
        return 1

    if args.comando == "renderizar":
        try:
            html = renderizar(_ler_aula(args.aula), timbre=args.timbre, fragmento=args.fragmento)
        except AulaInvalida as e:
            print(e, file=sys.stderr)
            return 1
        Path(args.saida).write_text(html, encoding="utf-8")
        print(f"HTML salvo em {args.saida}")
        return 0

    if args.comando == "gerar":
        from .gerador import gerar_aula

        perfil = json.loads(Path(args.perfil).read_text(encoding="utf-8")) if args.perfil else None
        aula = gerar_aula(args.codigo, perfil=perfil)
        Path(args.saida).write_text(aula.model_dump_json(indent=2), encoding="utf-8")
        print(f"aula salva em {args.saida}")
        if args.html:
            timbre = (perfil or {}).get("timbre", "piano")
            Path(args.html).write_text(renderizar(aula, timbre=timbre), encoding="utf-8")
            print(f"HTML salvo em {args.html}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
