#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fase3_portao_anuencia.py  —  PORTAO DE ANUENCIA

Unico ponto do plano autorizado a escrever nos bancos de regra. Nada entra e
nada sai sem o Dr. Jesus dizer sim, proposta por proposta.

TRES GARANTIAS DURAS, implementadas e nao opcionais:

  1. NADA E' APAGADO. Toda remocao vira movimentacao para a quarentena. O
     arquivo original e' copiado antes de qualquer edicao. Uma chave JSON
     removida vai para um arquivo-irmao `<nome>.removidos.json`.

  2. TODA APLICACAO E' REVERSIVEL. Cada rodada gera REVERSAO.sh, que desfaz
     exatamente o que foi feito.

  3. PROPOSTA CONTRA ARQUIVO MUDADO E' RECUSADA. Se o arquivo mudou depois de
     a proposta ter sido montada (sha256 nao bate), a proposta e' pulada e
     relatada. Nunca se escreve as cegas.

Entrada: PROPOSTAS.json
    {"propostas": [
       {"id": "P-001",
        "tipo": "ALTERAR_CHAVE",            <- ver TIPOS abaixo
        "arquivo": "/Users/jesus/.../CATALOGO-125-FATORES.json",
        "sha_esperado": "a1b2...",          <- da FASE 1; obrigatorio
        "alvo": "valor_hora",               <- chave, ou numero de linha
        "antes": 292,
        "depois": 350,
        "motivo": "fixacao judicial do caso Isaque + 20%",
        "fonte": "00-SUMARIO-DE-TUDO.md:L142",   <- onde ele ja decidiu isso
        "risco": "MEDIO"}
    ]}

TIPOS:
    ALTERAR_CHAVE      troca o valor de uma chave JSON
    REMOVER_CHAVE      tira a chave do JSON; valor vai para o .removidos.json
    ALTERAR_LINHA      substitui uma linha de arquivo de texto
    REMOVER_LINHA      remove uma linha de arquivo de texto
    ADICIONAR_LINHA    insere uma linha depois da linha `alvo`
    APOSENTAR_ARQUIVO  move o arquivo inteiro para a quarentena

Uso:
    python3 fase3_portao_anuencia.py PROPOSTAS.json --revisar     # so' mostra
    python3 fase3_portao_anuencia.py PROPOSTAS.json               # pergunta e aplica
    python3 fase3_portao_anuencia.py PROPOSTAS.json --so-risco ALTO
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

TIPOS_VALIDOS = {
    "ALTERAR_CHAVE", "REMOVER_CHAVE",
    "ALTERAR_LINHA", "REMOVER_LINHA", "ADICIONAR_LINHA",
    "APOSENTAR_ARQUIVO",
}
RISCOS = ("BAIXO", "MEDIO", "ALTO")


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as fh:
        while bloco := fh.read(65536):
            h.update(bloco)
    return h.hexdigest()


def validar(p: dict, indice: int) -> list[str]:
    erros = []
    for campo in ("id", "tipo", "arquivo", "sha_esperado", "motivo", "fonte"):
        if not p.get(campo):
            erros.append(f"proposta #{indice}: falta o campo '{campo}'")
    if p.get("tipo") not in TIPOS_VALIDOS:
        erros.append(f"proposta #{indice}: tipo '{p.get('tipo')}' invalido")
    if p.get("risco") and p["risco"] not in RISCOS:
        erros.append(f"proposta #{indice}: risco '{p['risco']}' invalido")
    if p.get("tipo") != "APOSENTAR_ARQUIVO" and p.get("alvo") in (None, ""):
        erros.append(f"proposta #{indice}: falta o campo 'alvo'")
    return erros


def achar_chave(dados, caminho_chave: str):
    """Navega 'a.b.c' e devolve (dict_pai, ultima_chave) ou (None, None)."""
    partes = caminho_chave.split(".")
    atual = dados
    for parte in partes[:-1]:
        if not isinstance(atual, dict) or parte not in atual:
            return None, None
        atual = atual[parte]
    if not isinstance(atual, dict) or partes[-1] not in atual:
        return None, None
    return atual, partes[-1]


def mostrar(p: dict, n: int, total: int, estado: str = "") -> None:
    risco = p.get("risco", "?")
    marca = {"ALTO": "!!!", "MEDIO": " ! ", "BAIXO": "   "}.get(risco, "   ")
    print("\n" + "=" * 78)
    print(f"[{n}/{total}] {p['id']}   {marca} risco {risco}   {p['tipo']}{estado}")
    print("=" * 78)
    print(f"  arquivo : {p['arquivo']}")
    if p.get("alvo") not in (None, ""):
        print(f"  alvo    : {p['alvo']}")
    if p["tipo"] != "APOSENTAR_ARQUIVO":
        print(f"  antes   : {p.get('antes')!r}")
        if p["tipo"] not in ("REMOVER_CHAVE", "REMOVER_LINHA"):
            print(f"  depois  : {p.get('depois')!r}")
    print(f"  motivo  : {p['motivo']}")
    print(f"  fonte   : {p['fonte']}")


def aplicar(p: dict, quarentena: Path, raiz_rel: Path,
            estado_inicial: dict[str, str]) -> tuple[bool, str, list[str]]:
    """
    Devolve (ok, mensagem, linhas_de_reversao).
    Copia para a quarentena ANTES de tocar em qualquer coisa.

    `estado_inicial` guarda, por arquivo, o sha que ele tinha quando esta
    rodada o tocou pela primeira vez. Serve a dois propositos:

      - varias propostas podem vir da MESMA leitura da FASE 1 e atingir o
        mesmo arquivo. A segunda traz o sha de antes da primeira. Isso e'
        legitimo e e' aceito. O que continua recusado e' um sha que nao
        corresponde nem ao estado atual nem ao inicio da rodada: ai' o
        arquivo foi mudado por fora, e escrever seria as cegas.

      - o backup e' feito UMA vez por arquivo. Sem isso, a segunda proposta
        sobrescreveria a copia da primeira e a reversao restauraria um estado
        intermediario, nao o original.
    """
    alvo = Path(p["arquivo"])
    if not alvo.exists():
        return False, "arquivo nao existe", []

    atual = sha256(alvo)
    chave_arquivo = str(alvo)
    inicial = estado_inicial.get(chave_arquivo)
    if atual != p["sha_esperado"] and p["sha_esperado"] != inicial:
        return (False,
                f"RECUSADO: o arquivo mudou desde a proposta "
                f"(esperado {p['sha_esperado'][:12]}, atual {atual[:12]})", [])

    # --- backup, uma vez por arquivo por rodada ---
    try:
        rel = alvo.relative_to(raiz_rel)
    except ValueError:
        rel = Path(str(alvo).lstrip("/"))
    copia = quarentena / rel
    primeiro_toque = chave_arquivo not in estado_inicial
    if primeiro_toque:
        copia.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(alvo, copia)
        estado_inicial[chave_arquivo] = atual
    reversao = [f'cp -p "{copia}" "{alvo}"'] if primeiro_toque else []

    tipo = p["tipo"]

    if tipo == "APOSENTAR_ARQUIVO":
        alvo.unlink()
        return True, f"movido para a quarentena: {copia}", [f'cp -p "{copia}" "{alvo}"']

    if tipo in ("ALTERAR_CHAVE", "REMOVER_CHAVE"):
        try:
            dados = json.loads(alvo.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return False, f"JSON invalido: {e}", []
        pai, chave = achar_chave(dados, str(p["alvo"]))
        if pai is None:
            return False, f"chave '{p['alvo']}' nao existe no arquivo", []
        valor_atual = pai[chave]
        if "antes" in p and valor_atual != p["antes"]:
            return (False,
                    f"RECUSADO: valor atual {valor_atual!r} nao e' o declarado "
                    f"{p['antes']!r}", [])

        if tipo == "ALTERAR_CHAVE":
            pai[chave] = p["depois"]
        else:
            removido = pai.pop(chave)
            lateral = alvo.with_suffix(alvo.suffix + ".removidos.json")
            historico = {}
            if lateral.exists():
                try:
                    historico = json.loads(lateral.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    historico = {}
            historico[str(p["alvo"])] = {
                "valor": removido,
                "removido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "proposta": p["id"],
                "motivo": p["motivo"],
                "fonte": p["fonte"],
            }
            lateral.write_text(json.dumps(historico, ensure_ascii=False, indent=2),
                               encoding="utf-8")
            reversao.append(f'# valor preservado em {lateral}')

        alvo.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        return True, "aplicado", reversao

    # --- tipos de linha ---
    linhas = alvo.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    try:
        n = int(p["alvo"])
    except (TypeError, ValueError):
        return False, f"alvo '{p['alvo']}' nao e' numero de linha", []
    if not 1 <= n <= len(linhas):
        return False, f"linha {n} fora do arquivo (tem {len(linhas)} linhas)", []

    conteudo_atual = linhas[n - 1].rstrip("\n")
    if tipo != "ADICIONAR_LINHA" and "antes" in p:
        if conteudo_atual.strip() != str(p["antes"]).strip():
            return (False,
                    f"RECUSADO: linha {n} contem {conteudo_atual!r}, "
                    f"nao {p['antes']!r}", [])

    if tipo == "ALTERAR_LINHA":
        linhas[n - 1] = str(p["depois"]).rstrip("\n") + "\n"
    elif tipo == "REMOVER_LINHA":
        del linhas[n - 1]
    elif tipo == "ADICIONAR_LINHA":
        linhas.insert(n, str(p["depois"]).rstrip("\n") + "\n")

    alvo.write_text("".join(linhas), encoding="utf-8")
    return True, "aplicado", reversao


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("propostas", help="arquivo PROPOSTAS.json")
    ap.add_argument("--revisar", action="store_true",
                    help="so' mostra as propostas; nao pergunta e nao aplica")
    ap.add_argument("--so-risco", choices=RISCOS, default="",
                    help="trata apenas propostas deste risco")
    ap.add_argument("--saida", default="~/Desktop/STEMMIA/_PORTAO",
                    help="pasta da quarentena, do registro e da reversao")
    ap.add_argument("--home", default=str(Path.home()))
    args = ap.parse_args()

    origem = Path(os.path.expanduser(args.propostas))
    if not origem.exists():
        print(f"ERRO: {origem} nao existe", file=sys.stderr)
        return 2
    try:
        pacote = json.loads(origem.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERRO: {origem} nao e' JSON valido: {e}", file=sys.stderr)
        return 2

    propostas = pacote.get("propostas", [])
    if not propostas:
        print("Nenhuma proposta no arquivo.")
        return 0

    erros = []
    for i, p in enumerate(propostas, 1):
        erros.extend(validar(p, i))
    if erros:
        print("ERRO: propostas malformadas. Nada foi tocado.", file=sys.stderr)
        for e in erros:
            print(f"  {e}", file=sys.stderr)
        return 2

    if args.so_risco:
        propostas = [p for p in propostas if p.get("risco") == args.so_risco]
        if not propostas:
            print(f"Nenhuma proposta de risco {args.so_risco}.")
            return 0

    selo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = Path(os.path.expanduser(args.saida))
    quarentena = base / "quarentena" / selo
    registro = base / "DECISOES-REGISTRADAS.jsonl"
    script_rev = base / f"REVERSAO-{selo}.sh"
    home = Path(os.path.expanduser(args.home))

    total = len(propostas)
    print("=" * 78)
    print("FASE 3 — PORTAO DE ANUENCIA")
    print("=" * 78)
    print(f"propostas  : {total}")
    print(f"modo       : {'REVISAO (nada sera escrito)' if args.revisar else 'APLICACAO'}")
    if not args.revisar:
        print(f"quarentena : {quarentena}")
        print(f"registro   : {registro}")
        print(f"reversao   : {script_rev}")
    print("\nResposta: s = sim, aplica | n = nao | a = adiar | q = parar aqui")

    if args.revisar:
        for i, p in enumerate(propostas, 1):
            mostrar(p, i, total)
        print(f"\n{total} propostas exibidas. Nada foi escrito.")
        return 0

    veredictos: list[dict] = []
    linhas_rev: list[str] = []
    estado_inicial: dict[str, str] = {}
    contagem = {"aplicado": 0, "recusado": 0, "adiado": 0, "falhou": 0}

    for i, p in enumerate(propostas, 1):
        mostrar(p, i, total)
        try:
            resposta = input("\n  aplicar? [s/n/a/q] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  interrompido — nada mais sera aplicado.")
            break

        if resposta == "q":
            print("  parado por sua ordem.")
            break
        if resposta == "a":
            contagem["adiado"] += 1
            veredictos.append({"id": p["id"], "veredicto": "ADIADO"})
            continue
        if resposta != "s":
            contagem["recusado"] += 1
            veredictos.append({"id": p["id"], "veredicto": "RECUSADO"})
            print("  recusado. Arquivo intacto.")
            continue

        ok, msg, rev = aplicar(p, quarentena, home, estado_inicial)
        if ok:
            contagem["aplicado"] += 1
            linhas_rev.extend([f"# {p['id']}: {p['motivo']}"] + rev)
            print(f"  OK — {msg}")
        else:
            contagem["falhou"] += 1
            print(f"  NAO APLICADO — {msg}")
        veredictos.append({
            "id": p["id"], "veredicto": "APROVADO",
            "resultado": "aplicado" if ok else "falhou", "detalhe": msg,
        })

    # ---- registro append-only ----
    if veredictos:
        registro.parent.mkdir(parents=True, exist_ok=True)
        with registro.open("a", encoding="utf-8") as fh:
            for v in veredictos:
                fh.write(json.dumps({
                    "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "rodada": selo,
                    "origem": str(origem),
                    **v,
                }, ensure_ascii=False) + "\n")

    if linhas_rev:
        script_rev.parent.mkdir(parents=True, exist_ok=True)
        script_rev.write_text(
            "#!/bin/bash\n"
            f"# Desfaz a rodada {selo} do portao de anuencia.\n"
            "# Restaura cada arquivo a partir da quarentena.\n"
            "set -euo pipefail\n\n" + "\n".join(linhas_rev) + "\n"
            '\necho "Reversao concluida."\n',
            encoding="utf-8")
        script_rev.chmod(0o755)

    print("\n" + "=" * 78)
    print("RESULTADO")
    print("=" * 78)
    print(f"  aplicados : {contagem['aplicado']}")
    print(f"  recusados : {contagem['recusado']}")
    print(f"  adiados   : {contagem['adiado']}")
    print(f"  falharam  : {contagem['falhou']}")
    if contagem["aplicado"]:
        print(f"\n  Para desfazer tudo:  bash {script_rev}")
        print(f"  Originais em      :  {quarentena}")
    if contagem["falhou"]:
        print("\n  Falha normalmente significa arquivo mudado desde a proposta.")
        print("  Rode a FASE 1 de novo para atualizar as impressoes digitais.")
    print(f"\n  Registro: {registro}")

    return 1 if contagem["falhou"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
