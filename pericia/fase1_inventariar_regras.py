#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fase1_inventariar_regras.py  —  ARQUEOLOGIA DAS REGRAS

Primeira fase do plano de fixacao do fluxo. Responde a pergunta central do
Dr. Jesus: "quais correcoes eu ja criei e nao estao sendo acessadas?"

Nao altera nada. Nao apaga nada. So' le e relata.

O achado principal e' a coluna LIDO_POR: um arquivo de regra que nenhuma skill
cita e' uma correcao enterrada — existe, foi escrita, e o fluxo nunca a le.

Uso:
    python3 fase1_inventariar_regras.py
    python3 fase1_inventariar_regras.py --json INVENTARIO-REGRAS.json
    python3 fase1_inventariar_regras.py --raiz ~/Desktop/STEMMIA --raiz ~/.claude

Saida:
    1. ORFAOS        - regras que ninguem le  <- o alvo do plano
    2. DIVERGENCIAS  - mesmo nome, conteudo diferente, em lugares diferentes
    3. COPIAS        - conteudo identico duplicado
    4. CONFLITOS     - mesma chave JSON com valor diferente entre arquivos
    5. INVENTARIO    - tudo que foi encontrado, com data e impressao digital
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Onde procurar. Lista derivada dos caminhos citados pelas SKILL.md instaladas
# (auditoria de 2026-08-27) mais as pastas do lote antigo, que e' justamente
# onde correcao enterrada tende a estar.
# ---------------------------------------------------------------------------

RAIZES_PADRAO = [
    "~/.claude/skills",
    "~/.claude",
    "~/Desktop/STEMMIA",
    "~/Desktop/ACERVO-LAUDO-IDEAL",
    "~/Desktop/_MESA",
    "~/Desktop/Mesa",
    "~/Documents/Arquitetura de Memória - GPT-Claude",
]

# Pastas que nunca contem regra e so' fazem a varredura demorar.
IGNORAR_DIR = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache",
    ".pytest_cache", "dist", "build", ".DS_Store", "site-packages",
    ".ollama", "models", ".cache", "Caches",
}

EXTENSOES = {".md", ".json", ".jsonl", ".txt", ".yaml", ".yml"}

# Arquivo que nunca carrega regra: licenca, fonte, aviso legal.
IGNORAR_ARQUIVO = re.compile(
    r"^(LICENSE|LICENCE|NOTICE|COPYING|CHANGELOG|AUTHORS)"
    r"|-(OFL|OFL\.txt|LICENSE)\b|\.lock$|^package(-lock)?\.json$",
    re.IGNORECASE,
)

# Subpasta de material de apoio de skill: documentacao de biblioteca, fontes,
# exemplos. Nao e' regra do Dr. Jesus.
IGNORAR_SUBDIR = {
    "references", "reference", "canvas-fonts", "fonts", "assets",
    "examples", "example", "templates", "ooxml", "docx-js", "scripts",
}

# Nome cuja repeticao e' estrutural: todo skill tem um SKILL.md. Comparar por
# nome base aqui gera falso positivo; a comparacao util e' por pasta.
NOME_ESTRUTURAL = {
    "SKILL.md", "README.md", "CLAUDE.md", "manifest.json", "LICENSE.txt",
    "index.md", "AGENTS.md",
}

# Nome de arquivo -> que tipo de regra ele carrega.
# A ordem importa: o primeiro padrao que casar ganha.
CLASSES = [
    (r"^SKILL\.md$",                      "SKILL",        "instrucao de skill"),
    (r"^CLAUDE\.md$",                     "CLAUDE",       "instrucao de projeto"),
    (r"CATALOGO.*FATORES",                "CATALOGO",     "catalogo canonico de fatores"),
    (r"REGISTRO-FATORES",                 "REGISTRO",     "fatores detectados por caso"),
    (r"DECISOES",                         "DECISAO",      "decisao do Dr. Jesus"),
    (r"COMPLEXIDADE",                     "COMPLEXIDADE", "complexidade de um caso"),
    (r"calibracao-log",                   "CALIBRACAO",   "historico de valor-hora"),
    (r"caso-honorarios",                  "CASO",         "ficha de honorarios do caso"),
    (r"resultado-honorarios",             "RESULTADO",    "resultado calculado"),
    (r"INVENTARIO|ERROS|erros-claude",    "ERRO",         "registro de erro recorrente"),
    (r"00-MESTRE|TASKS|FILA|ONDE-ESTOU",  "FILA",         "fila de trabalho"),
    (r"HANDOFF|CHECKPOINT",               "HANDOFF",      "passagem entre sessoes"),
    (r"SUMARIO|00-LOGICA|INDICE",         "MAPA",         "mapa da logica"),
    (r"PLANO|TPMED",                      "PLANO",        "plano consultavel"),
    (r"selector-registry|schema-recibo",  "SELETOR",      "seletor de navegador"),
    (r"PADRAO|padrao-laudo",              "PADRAO",       "padrao de redacao"),
    (r"manifest\.json$",                  "MANIFEST",     "manifest de skills"),
]

INICIO_CAMINHO = r"(?:~|\$HOME|\$SJ|\$H|/Users/[A-Za-z0-9_.-]+)"
CAMINHO_DELIMITADO = re.compile(rf"[`'\"]({INICIO_CAMINHO}[^`'\"\n]*)[`'\"]")
CAMINHO_CRU = re.compile(rf"{INICIO_CAMINHO}(?:/[^\s`'\"()\[\],;:*|>]+)*")

LIMITE_JSON_BYTES = 2_000_000   # acima disso nao se tenta achatar chaves


def sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def classificar(nome: str) -> tuple[str, str]:
    for padrao, classe, desc in CLASSES:
        if re.search(padrao, nome, re.IGNORECASE):
            return classe, desc
    return "OUTRO", "nao classificado"


def digitais(caminho: Path) -> tuple[str, int, int]:
    h = hashlib.sha256()
    linhas = 0
    tamanho = 0
    with caminho.open("rb") as fh:
        while bloco := fh.read(65536):
            h.update(bloco)
            linhas += bloco.count(b"\n")
            tamanho += len(bloco)
    return h.hexdigest(), tamanho, linhas


def varrer(raizes: list[Path]) -> list[Path]:
    achados: list[Path] = []
    vistos: set[Path] = set()
    for raiz in raizes:
        if not raiz.is_dir():
            continue
        for base, dirs, arquivos in os.walk(raiz, followlinks=False):
            dirs[:] = [d for d in dirs if d not in IGNORAR_DIR and not d.startswith(".")
                       or d in (".claude",)]
            for nome in arquivos:
                p = Path(base) / nome
                if p.suffix.lower() not in EXTENSOES:
                    continue
                if IGNORAR_ARQUIVO.search(nome):
                    continue
                if IGNORAR_SUBDIR & {parte.lower() for parte in p.parts}:
                    continue
                try:
                    real = p.resolve()
                except OSError:
                    continue
                if real in vistos:
                    continue
                vistos.add(real)
                achados.append(p)
    return sorted(achados)


def expandir(bruto: str, home: Path, variaveis: dict[str, str]) -> str:
    p = bruto
    if p.startswith("~"):
        p = str(home) + p[1:]
    for nome, valor in variaveis.items():
        p = p.replace(f"${nome}", valor)
    return p.rstrip("/.,;:").strip()


def caminhos_citados(arquivos: list[Path], home: Path) -> dict[str, set[str]]:
    """
    Quem le quem. Varre SKILL.md / CLAUDE.md e devolve
    {caminho citado (normalizado) -> {skills que o citam}}.
    """
    citacoes: dict[str, set[str]] = defaultdict(set)
    for p in arquivos:
        if p.name not in ("SKILL.md", "CLAUDE.md"):
            continue
        quem = p.parent.name if p.name == "SKILL.md" else f"CLAUDE:{p.parent.name}"
        try:
            texto = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for raiz_nome in ("STEMMIA", "STEMMIA Dexter"):
            sj = home / "Desktop" / raiz_nome / "STEMMIAJUD"
            variaveis = {"HOME": str(home), "SJ": str(sj),
                         "H": str(sj / "14-cowork" / "HONORARIOS")}
            brutos = {m.group(1) for m in CAMINHO_DELIMITADO.finditer(texto)}
            brutos |= {m.group(0) for m in
                       CAMINHO_CRU.finditer(CAMINHO_DELIMITADO.sub(" ", texto))}
            for b in brutos:
                alvo = expandir(b, home, variaveis)
                if "…" in alvo or "..." in alvo:
                    continue
                citacoes[sem_acento(alvo)].add(quem)
                # tambem registra a pasta, para o caso de a skill citar o diretorio
                citacoes[sem_acento(str(Path(alvo).parent))].add(quem)
    return citacoes


def achatar_json(obj, prefixo="") -> dict[str, object]:
    """Achata so' escalares, para comparar parametro com parametro."""
    saida: dict[str, object] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            saida.update(achatar_json(v, f"{prefixo}.{k}" if prefixo else str(k)))
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        if prefixo:
            saida[prefixo] = obj
    return saida


# Chaves cujo valor e' parametro de regra — conflito nelas e' grave.
CHAVE_DE_REGRA = re.compile(
    r"valor_hora|hora|horas|fase|f[1-6]|multiplic|teto|piso|faixa|limite|"
    r"arredond|regime|ramo|custeio|gratuidade|tabela|prazo|dias|peso|score|"
    r"minimo|maximo|base|reserva|barema",
    re.IGNORECASE,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", action="append", default=[],
                    help="pasta a varrer (pode repetir). Sem isso, usa a lista padrao.")
    ap.add_argument("--home", default=str(Path.home()))
    ap.add_argument("--json", default="", help="grava o inventario completo neste arquivo")
    ap.add_argument("--limite-tabela", type=int, default=40,
                    help="quantas linhas mostrar por secao (0 = todas)")
    args = ap.parse_args()

    home = Path(os.path.expanduser(args.home))
    brutas = args.raiz or RAIZES_PADRAO
    raizes = [Path(os.path.expanduser(r)) for r in brutas]
    existentes = [r for r in raizes if r.is_dir()]

    print("=" * 78)
    print("FASE 1 — ARQUEOLOGIA DAS REGRAS")
    print("=" * 78)
    print(f"gerado em: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"home     : {home}")
    print("\nraizes:")
    for r in raizes:
        print(f"  [{'ok    ' if r.is_dir() else 'ausente'}] {r}")
    if not existentes:
        print("\nERRO: nenhuma raiz existe. Rode no Mac, ou passe --raiz.", file=sys.stderr)
        return 2

    arquivos = varrer(existentes)
    print(f"\n{len(arquivos)} arquivos candidatos a regra encontrados.")

    citacoes = caminhos_citados(arquivos, home)
    print(f"{len(citacoes)} caminhos distintos sao citados por alguma skill.\n")

    registros: list[dict] = []
    por_hash: dict[str, list[str]] = defaultdict(list)
    por_nome: dict[str, list[tuple[str, str]]] = defaultdict(list)
    chaves_json: dict[str, list[tuple[str, object]]] = defaultdict(list)

    for p in arquivos:
        try:
            sha, tamanho, linhas = digitais(p)
            mtime = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc)
        except OSError as e:
            registros.append({"caminho": str(p), "erro": str(e)})
            continue

        classe, desc = classificar(p.name)
        lido_por = sorted(citacoes.get(sem_acento(str(p)), set()))
        if not lido_por:
            lido_por = sorted(citacoes.get(sem_acento(str(p.parent)), set()))

        reg = {
            "caminho": str(p),
            "nome": p.name,
            "classe": classe,
            "descricao": desc,
            "bytes": tamanho,
            "linhas": linhas,
            "sha256": sha,
            "modificado": mtime.date().isoformat(),
            "lido_por": lido_por,
            # Orfao so' faz sentido para arquivo que carrega regra. Material
            # nao classificado entra no inventario, mas nao acusa orfandade.
            "orfao": (not lido_por
                      and classe not in ("OUTRO", "SKILL", "CLAUDE", "MANIFEST")),
        }
        registros.append(reg)
        por_hash[sha].append(str(p))
        # Nome estrutural se repete por desenho: a comparacao util e'
        # "mesma skill, conteudo diferente", nao "existem dois SKILL.md".
        chave_nome = f"{p.parent.name}/{p.name}" if p.name in NOME_ESTRUTURAL else p.name
        por_nome[chave_nome].append((sha, str(p)))

        if p.suffix.lower() == ".json" and tamanho <= LIMITE_JSON_BYTES:
            try:
                dados = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            except (json.JSONDecodeError, OSError):
                reg["json_invalido"] = True
            else:
                for chave, valor in achatar_json(dados).items():
                    if CHAVE_DE_REGRA.search(chave):
                        chaves_json[chave].append((str(p), valor))

    def corta(seq):
        return seq if args.limite_tabela == 0 else seq[: args.limite_tabela]

    # ---------------- 1. ORFAOS ----------------
    print("=" * 78)
    print("1. ORFAOS — regra existe, nenhuma skill le  <<< O ALVO DO PLANO")
    print("=" * 78)
    orfaos = [r for r in registros if r.get("orfao")]
    orfaos.sort(key=lambda r: (r["classe"], r["modificado"]), reverse=True)
    if orfaos:
        for r in corta(orfaos):
            print(f"  [{r['classe']:12s}] {r['modificado']}  {r['linhas']:>5} ln  {r['caminho']}")
        if args.limite_tabela and len(orfaos) > args.limite_tabela:
            print(f"  ... e mais {len(orfaos) - args.limite_tabela}. Use --limite-tabela 0.")
        print(f"\n  TOTAL: {len(orfaos)} arquivos de regra que o fluxo nao le.")
    else:
        print("  nenhum")

    # ---------------- 2. DIVERGENCIAS ----------------
    print("\n" + "=" * 78)
    print("2. DIVERGENCIAS — mesmo nome de arquivo, conteudo diferente")
    print("=" * 78)
    divergentes = {n: v for n, v in por_nome.items()
                   if len({sha for sha, _ in v}) > 1}
    if divergentes:
        for nome in corta(sorted(divergentes)):
            print(f"\n  {nome}  ({len(divergentes[nome])} versoes)")
            for sha, caminho in sorted(divergentes[nome], key=lambda x: x[1]):
                print(f"    {sha[:12]}  {caminho}")
        print(f"\n  TOTAL: {len(divergentes)} nomes com mais de uma versao. "
              "Uma delas e' a viva; as outras mentem.")
    else:
        print("  nenhuma")

    # ---------------- 3. COPIAS ----------------
    print("\n" + "=" * 78)
    print("3. COPIAS — conteudo identico em mais de um lugar")
    print("=" * 78)
    copias = {h: v for h, v in por_hash.items() if len(v) > 1}
    if copias:
        for h in corta(sorted(copias, key=lambda x: -len(copias[x]))):
            print(f"\n  {h[:12]}  ({len(copias[h])} copias)")
            for caminho in sorted(copias[h]):
                print(f"    {caminho}")
        print(f"\n  TOTAL: {len(copias)} conteudos duplicados.")
    else:
        print("  nenhuma")

    # ---------------- 4. CONFLITOS DE PARAMETRO ----------------
    print("\n" + "=" * 78)
    print("4. CONFLITOS — mesma chave de regra, valor diferente entre arquivos")
    print("=" * 78)
    conflitos = {}
    for chave, ocorrencias in chaves_json.items():
        valores = {repr(v) for _, v in ocorrencias}
        if len(valores) > 1 and len(ocorrencias) > 1:
            conflitos[chave] = ocorrencias
    if conflitos:
        for chave in corta(sorted(conflitos)):
            print(f"\n  {chave}")
            for caminho, valor in sorted(conflitos[chave]):
                print(f"    {valor!r:>18}  <- {caminho}")
        print(f"\n  TOTAL: {len(conflitos)} parametros em conflito. "
              "Cada um e' um numero que muda conforme o arquivo lido.")
    else:
        print("  nenhum")

    # ---------------- 5. RESUMO ----------------
    print("\n" + "=" * 78)
    print("5. RESUMO POR CLASSE")
    print("=" * 78)
    por_classe: dict[str, list[dict]] = defaultdict(list)
    for r in registros:
        if "classe" in r:
            por_classe[r["classe"]].append(r)
    print(f"{'classe':14s} {'total':>6} {'orfaos':>7}  descricao")
    for classe in sorted(por_classe, key=lambda c: -len(por_classe[c])):
        grupo = por_classe[classe]
        n_orf = sum(1 for r in grupo if r.get("orfao"))
        print(f"{classe:14s} {len(grupo):>6} {n_orf:>7}  {grupo[0]['descricao']}")

    if args.json:
        destino = Path(os.path.expanduser(args.json)).resolve()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps({
            "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "home": str(home),
            "raizes": [str(r) for r in raizes],
            "totais": {
                "arquivos": len(registros),
                "orfaos": len(orfaos),
                "divergencias": len(divergentes),
                "copias": len(copias),
                "conflitos": len(conflitos),
            },
            "orfaos": orfaos,
            "divergencias": {n: v for n, v in divergentes.items()},
            "copias": copias,
            "conflitos": {k: v for k, v in conflitos.items()},
            "inventario": registros,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON: {destino}")
        print("Esse arquivo e' a entrada da FASE 2 (proposta de correcao).")

    return 1 if (orfaos or divergentes or conflitos) else 0


if __name__ == "__main__":
    raise SystemExit(main())
