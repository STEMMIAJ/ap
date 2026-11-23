#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fluxo.py  —  FONTE UNICA DO FLUXO: valida e gera as vistas

O problema que isto resolve nao e' bug: e' estrutura. A mesma regra esta'
escrita em SKILL.md, em JSON, em .md e em codigo Python. Cinco copias de
qualquer coisa divergem — nao por descuido, por desenho. Nao ha' remendo que
conserte isso, porque nao ha' origem.

A inversao: FLUXO.json e' a unica fonte. Todo o resto e' GERADO. Divergir
deixa de ser questao de disciplina e passa a ser impossivel por construcao,
porque so' existe um lugar onde a regra mora.

A trava central e' a INVARIANTE 6: um valor de dinheiro ou de hora nao pode
ser escrito dentro de um enunciado. Escreve-se {param:id}, e o valor vive uma
unica vez em `parametros`. Sem isso, o arquivo unico viraria o sexto lugar
onde o mesmo numero aparece.

Uso:
    python3 fluxo.py validar FLUXO.json
    python3 fluxo.py ver FLUXO.json                      # Markdown no terminal
    python3 fluxo.py ver FLUXO.json --saida FLUXO.md     # grava a vista
    python3 fluxo.py parametros FLUXO.json --saida params.json   # para o calculo ler

Codigo de saida: 0 se a fonte esta' consistente, 1 se nao.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PLACEHOLDER = re.compile(r"\{param:([A-Za-z0-9_]+)\}")

# Literal proibido dentro de um enunciado: o valor tem que vir de `parametros`.
# Datas, artigos de lei e numeros escritos em palavra seguem permitidos.
LITERAL_DINHEIRO = re.compile(r"R\$\s*\d")
LITERAL_HORA = re.compile(r"\b\d+(?:[,.]\d+)?\s*(?:h|hora|horas)\b", re.IGNORECASE)

STATUS_REGRA = {"vigente", "pendente_de_decisao", "aposentada"}


def carregar(caminho: Path) -> dict:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERRO: {caminho} nao existe", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as e:
        print(f"ERRO: {caminho} nao e' JSON valido: {e}", file=sys.stderr)
        raise SystemExit(2)


def validar(fluxo: dict) -> list[str]:
    falhas: list[str] = []
    parametros = fluxo.get("parametros", {})
    etapas = fluxo.get("etapas", [])
    regras = fluxo.get("regras", [])
    pendencias = fluxo.get("pendencias", [])

    ids_etapa = {e.get("id") for e in etapas}
    ids_regra = [r.get("id") for r in regras]
    ids_pend = {p.get("id") for p in pendencias}

    # --- 1. ids unicos ---
    for nome, seq in (("regra", ids_regra),
                      ("etapa", [e.get("id") for e in etapas]),
                      ("pendencia", [p.get("id") for p in pendencias])):
        for ident, n in Counter(seq).items():
            if n > 1:
                falhas.append(f"[1 unicidade] id de {nome} repetido {n}x: {ident}")

    # --- 2. procedencia obrigatoria ---
    for chave, p in parametros.items():
        proc = p.get("procedencia") or {}
        if not proc.get("arquivo") or not proc.get("ancora"):
            falhas.append(f"[2 procedencia] parametro '{chave}' sem arquivo+ancora")
    for r in regras:
        proc = r.get("procedencia") or {}
        if not proc.get("arquivo") or not proc.get("ancora"):
            falhas.append(f"[2 procedencia] regra '{r.get('id')}' sem arquivo+ancora")

    # --- 3. regra aponta para etapa existente ---
    for r in regras:
        if r.get("etapa") not in ids_etapa:
            falhas.append(f"[3 etapa] regra '{r.get('id')}' aponta para etapa "
                          f"inexistente: {r.get('etapa')}")

    # --- 4. etapa e regra concordam nos dois sentidos ---
    conjunto_regras = set(ids_regra)
    for e in etapas:
        for rid in e.get("regras", []):
            if rid not in conjunto_regras:
                falhas.append(f"[4 bidirecional] etapa '{e.get('id')}' lista regra "
                              f"inexistente: {rid}")
            else:
                dona = next(x for x in regras if x.get("id") == rid)
                if dona.get("etapa") != e.get("id"):
                    falhas.append(f"[4 bidirecional] etapa '{e.get('id')}' lista "
                                  f"'{rid}', mas a regra declara etapa "
                                  f"'{dona.get('etapa')}'")
    for r in regras:
        dona = next((e for e in etapas if e.get("id") == r.get("etapa")), None)
        if dona and r.get("id") not in dona.get("regras", []):
            falhas.append(f"[4 bidirecional] regra '{r.get('id')}' declara etapa "
                          f"'{r.get('etapa')}', que nao a lista")

    # --- 5. ordem das etapas unica e contigua ---
    ordens = sorted(e.get("ordem") for e in etapas if e.get("ordem") is not None)
    if len(ordens) != len(etapas):
        falhas.append("[5 ordem] ha' etapa sem 'ordem'")
    elif ordens != list(range(1, len(etapas) + 1)):
        falhas.append(f"[5 ordem] ordem nao e' 1..{len(etapas)} sem furo: {ordens}")

    # --- 6. nenhum literal de valor dentro de enunciado  <<< A TRAVA CENTRAL ---
    for r in regras:
        texto = r.get("enunciado", "")
        if LITERAL_DINHEIRO.search(texto):
            falhas.append(f"[6 literal] regra '{r.get('id')}' escreve valor em "
                          f"dinheiro no enunciado. Use {{param:id}}.")
        achado = LITERAL_HORA.search(texto)
        if achado:
            falhas.append(f"[6 literal] regra '{r.get('id')}' escreve hora no "
                          f"enunciado ({achado.group(0)!r}). Use {{param:id}}.")

    # --- 7. todo placeholder resolve ---
    for r in regras:
        for ident in PLACEHOLDER.findall(r.get("enunciado", "")):
            if ident not in parametros:
                falhas.append(f"[7 placeholder] regra '{r.get('id')}' usa "
                              f"{{param:{ident}}}, que nao existe em parametros")

    # --- 8. usa_parametros resolve ---
    for r in regras:
        for ident in r.get("usa_parametros", []):
            if ident not in parametros:
                falhas.append(f"[8 usa_parametros] regra '{r.get('id')}' declara "
                              f"parametro inexistente: {ident}")

    # --- 9. status valido e pendencia amarrada ---
    for r in regras:
        st = r.get("status")
        if st not in STATUS_REGRA:
            falhas.append(f"[9 status] regra '{r.get('id')}' tem status invalido: {st}")
        if st == "pendente_de_decisao":
            pend = r.get("pendencia")
            if not pend:
                falhas.append(f"[9 status] regra '{r.get('id')}' esta' pendente "
                              "sem apontar a pendencia")
            elif pend not in ids_pend:
                falhas.append(f"[9 status] regra '{r.get('id')}' aponta pendencia "
                              f"inexistente: {pend}")
        if st == "aposentada" and not r.get("aposentada_por"):
            falhas.append(f"[9 status] regra '{r.get('id')}' aposentada sem "
                          "'aposentada_por' apontando a decisao do perito")

    # --- 10. parametro orfao: declarado e nunca usado ---
    usados = set()
    for r in regras:
        usados |= set(PLACEHOLDER.findall(r.get("enunciado", "")))
        usados |= set(r.get("usa_parametros", []))
    for chave, p in parametros.items():
        if chave not in usados and p.get("status") == "vigente":
            falhas.append(f"[10 orfao] parametro '{chave}' e' vigente e nenhuma "
                          "regra o usa. Ou amarre a uma regra, ou aposente.")

    return falhas


def substituir(texto: str, parametros: dict) -> str:
    def troca(m):
        ident = m.group(1)
        p = parametros.get(ident)
        if not p:
            return m.group(0)
        valor, unidade = p.get("valor"), p.get("unidade", "")
        if unidade == "BRL/h":
            return f"R$ {valor:,.2f}/h".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{valor} {unidade}".strip()
    return PLACEHOLDER.sub(troca, texto)


def ver(fluxo: dict) -> str:
    parametros = fluxo.get("parametros", {})
    meta = fluxo.get("meta", {})
    linhas = [
        f"# {meta.get('titulo', 'Fluxo')}",
        "",
        "> **Esta vista é GERADA.** Não edite este arquivo: edite `FLUXO.json` "
        "e gere de novo. Editar aqui recria a divergência.",
        "",
        f"Gerado em {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} "
        f"· versão {meta.get('versao')} · estado: {meta.get('estado', '?')}",
        "",
        "## Parâmetros",
        "",
        "Cada número vive aqui, uma vez só.",
        "",
        "| id | valor | status | n | procedência |",
        "|---|---|---|---|---|",
    ]
    for chave, p in parametros.items():
        unidade = p.get("unidade", "")
        n = p.get("n_observacoes", "")
        anc = (p.get("procedencia") or {}).get("ancora", "")
        linhas.append(f"| `{chave}` | {p.get('valor')} {unidade} | "
                      f"{p.get('status')} | {n} | {anc[:60]} |")

    regras = fluxo.get("regras", [])
    linhas += ["", "## Etapas, em ordem", ""]
    for e in sorted(fluxo.get("etapas", []), key=lambda x: x.get("ordem", 0)):
        portao = f" · portão **{e['portao']}**" if e.get("portao") else ""
        linhas += [f"### {e.get('ordem')}. {e.get('nome')}  (`{e.get('id')}`){portao}", ""]
        if e.get("entra"):
            linhas.append(f"**Entra:** {' · '.join(e['entra'])}")
        if e.get("sai"):
            linhas.append(f"**Sai:** {' · '.join(e['sai'])}")
        linhas.append("")
        for rid in e.get("regras", []):
            r = next((x for x in regras if x.get("id") == rid), None)
            if not r:
                continue
            marca = {"vigente": "", "pendente_de_decisao": " ⟨PENDENTE⟩",
                     "aposentada": " ⟨APOSENTADA⟩"}.get(r.get("status"), "")
            linhas.append(f"- **{r.get('tipo')}**{marca} — "
                          f"{substituir(r.get('enunciado', ''), parametros)}")
            if r.get("proibe"):
                for item in r["proibe"]:
                    linhas.append(f"    - proibido: {item}")
            if r.get("sinais_privado"):
                linhas.append(f"    - sinais privado: "
                              + " · ".join(f"`{s}`" for s in r["sinais_privado"]))
            if r.get("sinais_publico"):
                linhas.append(f"    - sinais público: "
                              + " · ".join(f"`{s}`" for s in r["sinais_publico"]))
            linhas.append(f"    - fonte: {(r.get('procedencia') or {}).get('ancora', '')}")
        linhas.append("")

    pend = [p for p in fluxo.get("pendencias", []) if p.get("status") == "aberta"]
    if pend:
        linhas += ["## Pendências abertas — decisão do perito", ""]
        for p in pend:
            linhas += [f"**{p.get('id')}** — {p.get('pergunta')}",
                       f"  - impacto: {p.get('impacto')}", ""]

    apos = fluxo.get("aposentadas", [])
    linhas += ["## Regras aposentadas", ""]
    if apos:
        for a in apos:
            linhas.append(f"- `{a.get('id')}` — {a.get('enunciado', '')} "
                          f"(por: {a.get('aposentada_por', '?')})")
    else:
        linhas.append("Nenhuma. Toda aposentadoria passa pelo portão de anuência.")
    return "\n".join(linhas) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["validar", "ver", "parametros"])
    ap.add_argument("arquivo", help="FLUXO.json")
    ap.add_argument("--saida", default="", help="grava em arquivo em vez da tela")
    args = ap.parse_args()

    caminho = Path(args.arquivo).expanduser()
    fluxo = carregar(caminho)

    if args.acao == "validar":
        falhas = validar(fluxo)
        print("=" * 74)
        print("VALIDACAO DA FONTE UNICA")
        print("=" * 74)
        print(f"arquivo    : {caminho}")
        print(f"parametros : {len(fluxo.get('parametros', {}))}")
        print(f"etapas     : {len(fluxo.get('etapas', []))}")
        print(f"regras     : {len(fluxo.get('regras', []))}")
        print(f"pendencias : {sum(1 for p in fluxo.get('pendencias', []) if p.get('status') == 'aberta')} abertas")
        print()
        if falhas:
            print(f"{len(falhas)} FALHA(S):\n")
            for f in falhas:
                print(f"  {f}")
            print("\nA fonte nao esta' consistente. Nao gere vista nem parametro "
                  "a partir dela.")
            return 1
        print("CONSISTENTE. As 10 invariantes passam.")
        print("  1 ids unicos                      6 nenhum literal de valor em enunciado")
        print("  2 procedencia em tudo             7 todo placeholder resolve")
        print("  3 regra aponta etapa real         8 usa_parametros resolve")
        print("  4 etapa e regra concordam         9 status valido, pendencia amarrada")
        print("  5 ordem contigua                 10 nenhum parametro vigente orfao")
        return 0

    if args.acao == "ver":
        texto = ver(fluxo)
    else:
        texto = json.dumps({
            "_gerado_por": "fluxo.py parametros — NAO EDITAR, edite FLUXO.json",
            "_gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **{k: v.get("valor") for k, v in fluxo.get("parametros", {}).items()
               if v.get("status") == "vigente"},
        }, ensure_ascii=False, indent=2) + "\n"

    if args.saida:
        destino = Path(args.saida).expanduser()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")
        print(f"gerado: {destino}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
