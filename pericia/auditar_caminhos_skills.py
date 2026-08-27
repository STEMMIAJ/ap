#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auditar_caminhos_skills.py

Resolve, no Mac do Dr. Jesus, TODOS os caminhos de arquivo e TODAS as rotas de
skill citados pelas skills instaladas, e diz o que ainda presta.

Nao calcula honorarios, nao classifica custeio e nao reimplementa nada do
fluxo canonico. E' um inventario: le, resolve, confere existencia, relata.

Uso:
    python3 auditar_caminhos_skills.py
    python3 auditar_caminhos_skills.py --skills ~/.claude/skills --csv auditoria.csv
    python3 auditar_caminhos_skills.py --abrir      # abre o CSV no Mac ao final

Saida:
    1. CAMINHOS        - cada caminho citado, com EXISTE / AUSENTE / RECUPERAVEL
    2. RAIZES          - qual raiz cada skill assume (deteccao do rename)
    3. ROTAS           - nomes de skill citados como proxima etapa que nao existem
    4. FORA DA RAIZ    - o que vive fora de STEMMIA e ainda e' citado
    5. ALERTAS         - colisoes e pastas envenenadas conhecidas
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# --------------------------------------------------------------------------
# Configuracao factual, extraida das SKILL.md instaladas em 27/08/2026.
# Alterar aqui se a raiz mudar de novo.
# --------------------------------------------------------------------------

RAIZ_ATUAL = "STEMMIA"          # lote 27/08: ~/Desktop/STEMMIA/STEMMIAJUD
RAIZ_ANTIGA = "STEMMIA Dexter"  # lote 14/08: ~/Desktop/STEMMIA Dexter/STEMMIAJUD

# Pastas fora da raiz principal, com o veredito conhecido de cada uma.
# "vivo"    = citada por skill do lote novo -> continua valendo
# "suspeito"= citada so' pelo lote antigo   -> conferir se migrou
# "veneno"  = nao usar; motivo documentado no fluxo canonico
FORA_DA_RAIZ = {
    "Desktop/ACERVO-LAUDO-IDEAL": (
        "vivo",
        "citada por handoff-sessao, medir-e-liberar e organizar-exame (lote 27/08)",
    ),
    "Desktop/_MESA": (
        "suspeito",
        "so' erros-recorrentes (lote 14/08) cita; registro de erros pode ter migrado",
    ),
    "Desktop/Mesa/Painel": (
        "suspeito",
        "so' fila-unica-continuidade e entregar-abrindo (lote 14/08) citam",
    ),
    "Documents/Arquitetura de Memoria - GPT-Claude": (
        "suspeito",
        "so' cartao-de-progresso (lote 14/08) cita",
    ),
    "Desktop/Mesa/Pastas/Pericia e fluxo/PROJETO CALCULADORA HONORARIOS": (
        "veneno",
        "copia congelada de 2026-07-16; o detecta_custeio.py dela classifica "
        "CUSTEADO como GRATUIDADE (falta o patch de 18/07) e recusa proposta devida",
    ),
}

# Variaveis de shell que as skills usam sem definir no mesmo trecho.
def montar_variaveis(home: Path, raiz: str) -> dict[str, str]:
    sj = home / "Desktop" / raiz / "STEMMIAJUD"
    return {
        "HOME": str(home),
        "SJ": str(sj),
        "H": str(sj / "14-cowork" / "HONORARIOS"),
    }


# Um caminho pode vir cru no texto ou entre crases/aspas. Quando vem delimitado,
# ele pode conter espaco ("Pericia e fluxo", "STEMMIA Dexter") — por isso o
# delimitado e' extraido primeiro, inteiro, e so' depois varre-se o texto cru.
INICIO_CAMINHO = r"(?:~|\$HOME|\$SJ|\$H|/Users/[A-Za-z0-9_.-]+)"
PADRAO_DELIMITADO = re.compile(
    rf"[`'\"]({INICIO_CAMINHO}[^`'\"\n]*)[`'\"]"
)
PADRAO_CRU = re.compile(
    rf"{INICIO_CAMINHO}(?:/[^\s`'\"()\[\],;:*|>]+)*"
)

# Linhas que anunciam a proxima etapa do fluxo -> os nomes ali sao rotas.
GATILHOS_ROTA = (
    "rota", "roteamento", "rotear", "delegar", "delega",
    "proxima etapa", "próxima etapa", "proxima rota", "próxima rota",
    "skill ", "skills ", "acionar", "aciona ",
)
PADRAO_CRASE = re.compile(r"`([^`\n]{3,60})`")
PADRAO_TITULO = re.compile(r"^#{1,6}\s+(.*)$")

# Termos entre crases que nunca sao skill.
# ATENCAO: estes dois padroes NAO podem ser fundidos num so' com IGNORECASE —
# `[A-Z_]{2,}` sob IGNORECASE casa qualquer palavra minuscula e engole todas as
# rotas validas. Case-sensitive para o formato, case-insensitive para a lista.
FORMATO_NAO_E_ROTA = re.compile(r"^(?:[A-Z_]{2,}|--|-|/|~|\$|\d)")  # CONSTANTE, flag, numero
PALAVRA_NAO_E_ROTA = re.compile(
    r"^(?:python3?|node|npm|npx|pip3?|open|grep|sed|awk|cat|ls|cd|mdfind|"
    r"pandoc|soffice|unzip|zip|curl|git|ollama|pdftoppm|pdftotext|markitdown|"
    r"playwright|sharp|pandas|openpyxl|python-pptx|pptxgenjs|docx|react|"
    r"react-dom|react-icons|name|title|text|status|width|height|prefix|"
    r"offset|passed|success|returncode|numbering|thumbnails|shadow)$",
    re.IGNORECASE,
)


# Nome de skill e' kebab-case minusculo ("calculo-honorarios") ou um titulo com
# espacos ("Gerador de Roteiro Pericial"). CamelCase e snake_case sao nome de
# ferramenta (SendUserFile, available_skills), nunca rota.
FORMA_DE_SKILL = re.compile(r"^[a-z][a-z0-9-]*$")


def nao_e_rota(termo: str) -> bool:
    if FORMATO_NAO_E_ROTA.search(termo) or PALAVRA_NAO_E_ROTA.search(termo):
        return True
    if FORMA_DE_SKILL.match(termo):
        return False
    if " " in termo and all(p.isalpha() for p in termo.split()):
        return False
    return True


def normalizar(txt: str) -> str:
    """Tira acento para comparar nome de pasta sem depender de NFC/NFD."""
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", txt)
        if unicodedata.category(c) != "Mn"
    )


def expandir(bruto: str, variaveis: dict[str, str], home: Path) -> str:
    p = bruto
    if p.startswith("~"):
        p = str(home) + p[1:]
    for nome, valor in variaveis.items():
        p = p.replace(f"${nome}", valor)
    return p.rstrip("/.,;:")


def coletar_skills(dir_skills: Path) -> list[tuple[str, Path]]:
    achados = []
    for skill_md in sorted(dir_skills.rglob("SKILL.md")):
        achados.append((skill_md.parent.name, skill_md))
    return achados


def extrair_caminhos(texto: str) -> set[str]:
    """Delimitado primeiro (preserva espaco no nome da pasta), cru depois."""
    achados = {m.group(1).strip() for m in PADRAO_DELIMITADO.finditer(texto)}
    sem_delimitado = PADRAO_DELIMITADO.sub(" ", texto)
    achados |= {m.group(0) for m in PADRAO_CRU.finditer(sem_delimitado)}

    uteis = set()
    for p in achados:
        p = p.rstrip("/.,;:").strip()
        # descarta reticencia e o home puro: nao apontam para nada conferivel
        if "…" in p or "..." in p:
            continue
        resto = re.sub(INICIO_CAMINHO, "", p, count=1).strip("/")
        if not resto:
            continue
        uteis.add(p)
    return uteis


def extrair_rotas(texto: str) -> set[str]:
    """
    Um nome entre crases e' rota se a linha anuncia roteamento OU se a secao
    (titulo markdown corrente) fala de rota. A tabela de roteamento do
    triagem-pericial-browser e' `- honorarios: \\`calculo-honorarios\\`;`, que
    nao carrega gatilho na propria linha — so' no titulo acima.
    """
    rotas = set()
    secao_de_rota = False
    for linha in texto.splitlines():
        titulo = PADRAO_TITULO.match(linha)
        if titulo:
            secao_de_rota = any(g in titulo.group(1).lower() for g in GATILHOS_ROTA)
            continue
        if not (secao_de_rota or any(g in linha.lower() for g in GATILHOS_ROTA)):
            continue
        for termo in PADRAO_CRASE.findall(linha):
            termo = termo.strip()
            if nao_e_rota(termo):
                continue
            if any(c in termo for c in "/.=$<>%"):
                continue
            if " " in termo and not all(w.isalpha() for w in termo.split()):
                continue
            rotas.add(termo)
    return rotas


def classificar_fora_da_raiz(caminho_abs: str, home: Path) -> tuple[str, str] | None:
    rel = normalizar(caminho_abs).replace(normalizar(str(home)) + "/", "")
    for chave, veredito in FORA_DA_RAIZ.items():
        if normalizar(rel).startswith(normalizar(chave)):
            return veredito
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skills", default="~/.claude/skills",
                    help="pasta das skills instaladas (padrao: ~/.claude/skills)")
    ap.add_argument("--home", default=str(Path.home()),
                    help="home a usar na expansao (padrao: home do usuario atual)")
    ap.add_argument("--csv", default="", help="grava o relatorio de caminhos em CSV")
    ap.add_argument("--abrir", action="store_true",
                    help="abre o CSV no Finder/Numbers ao terminar (macOS)")
    args = ap.parse_args()

    home = Path(os.path.expanduser(args.home))
    dir_skills = Path(os.path.expanduser(args.skills))
    if not dir_skills.is_dir():
        print(f"ERRO: pasta de skills nao encontrada: {dir_skills}", file=sys.stderr)
        print("Passe o caminho certo com --skills.", file=sys.stderr)
        return 2

    var_atual = montar_variaveis(home, RAIZ_ATUAL)
    var_antiga = montar_variaveis(home, RAIZ_ANTIGA)

    skills = coletar_skills(dir_skills)
    if not skills:
        print(f"ERRO: nenhum SKILL.md dentro de {dir_skills}", file=sys.stderr)
        return 2

    instaladas = {nome for nome, _ in skills}
    linhas: list[dict] = []
    raiz_por_skill: dict[str, set[str]] = defaultdict(set)
    rotas_por_skill: dict[str, set[str]] = {}

    for nome, caminho_md in skills:
        texto = caminho_md.read_text(encoding="utf-8", errors="ignore")
        rotas_por_skill[nome] = extrair_rotas(texto)

        if RAIZ_ANTIGA in texto:
            raiz_por_skill[nome].add(RAIZ_ANTIGA)
        # negative lookahead: "Desktop/STEMMIA Dexter" NAO conta como raiz atual
        if re.search(rf"Desktop/{RAIZ_ATUAL}(?! Dexter)", texto):
            raiz_por_skill[nome].add(RAIZ_ATUAL)

        # $SJ / $H so' tem sentido se a skill definir a raiz; use a que ela cita.
        variaveis = var_antiga if RAIZ_ANTIGA in texto else var_atual

        for bruto in sorted(extrair_caminhos(texto)):
            absoluto = expandir(bruto, variaveis, home)
            existe = os.path.exists(absoluto)

            recuperado = ""
            if not existe and RAIZ_ANTIGA in absoluto:
                tentativa = absoluto.replace(RAIZ_ANTIGA, RAIZ_ATUAL)
                if os.path.exists(tentativa):
                    recuperado = tentativa

            if existe:
                status = "EXISTE"
            elif recuperado:
                status = "RECUPERAVEL"
            else:
                status = "AUSENTE"

            fora = classificar_fora_da_raiz(absoluto, home)
            linhas.append({
                "skill": nome,
                "status": status,
                "citado": bruto,
                "resolvido": absoluto,
                "corrigido_para": recuperado,
                "fora_da_raiz": fora[0] if fora else "",
                "observacao": fora[1] if fora else "",
            })

    # ---------------- 1. CAMINHOS ----------------
    print("=" * 78)
    print("1. CAMINHOS CITADOS PELAS SKILLS")
    print("=" * 78)
    ordem = {"AUSENTE": 0, "RECUPERAVEL": 1, "EXISTE": 2}
    for ln in sorted(linhas, key=lambda x: (ordem[x["status"]], x["skill"])):
        print(f"[{ln['status']:11s}] {ln['skill']:34s} {ln['resolvido']}")
        if ln["corrigido_para"]:
            print(f"{'':14s}  -> existe em: {ln['corrigido_para']}")
        if ln["observacao"]:
            print(f"{'':14s}  -> {ln['fora_da_raiz'].upper()}: {ln['observacao']}")

    total = len(linhas)
    conta = defaultdict(int)
    for ln in linhas:
        conta[ln["status"]] += 1
    print(f"\nTotal {total}: "
          f"{conta['EXISTE']} EXISTE | "
          f"{conta['RECUPERAVEL']} RECUPERAVEL | "
          f"{conta['AUSENTE']} AUSENTE")

    # ---------------- 2. RAIZES ----------------
    print("\n" + "=" * 78)
    print("2. QUAL RAIZ CADA SKILL ASSUME")
    print("=" * 78)
    antigas, novas, ambas = [], [], []
    for nome in sorted(raiz_por_skill):
        raizes = raiz_por_skill[nome]
        if raizes == {RAIZ_ANTIGA}:
            antigas.append(nome)
        elif raizes == {RAIZ_ATUAL}:
            novas.append(nome)
        else:
            ambas.append(nome)
    print(f"Raiz atual  '{RAIZ_ATUAL}' ({len(novas)}): {', '.join(novas) or '-'}")
    print(f"Raiz antiga '{RAIZ_ANTIGA}' ({len(antigas)}): {', '.join(antigas) or '-'}")
    if ambas:
        print(f"CITAM AS DUAS ({len(ambas)}): {', '.join(ambas)}  <- colisao, resolver")

    # ---------------- 3. ROTAS ----------------
    print("\n" + "=" * 78)
    print("3. ROTAS DE SKILL CITADAS QUE NAO ESTAO INSTALADAS")
    print("=" * 78)
    quebradas: dict[str, list[str]] = defaultdict(list)
    for nome, rotas in rotas_por_skill.items():
        for r in rotas:
            if r not in instaladas:
                quebradas[r].append(nome)
    if quebradas:
        for rota in sorted(quebradas):
            print(f"  {rota:34s} <- citada por {', '.join(sorted(quebradas[rota]))}")
        print("\nRota quebrada = o fluxo manda para uma skill que nao existe "
              "e a etapa morre em silencio.")
    else:
        print("  nenhuma")

    # ---------------- 4. FORA DA RAIZ ----------------
    print("\n" + "=" * 78)
    print("4. O QUE VIVE FORA DE ~/Desktop/" + RAIZ_ATUAL)
    print("=" * 78)
    agrupado: dict[str, set[str]] = defaultdict(set)
    for ln in linhas:
        if ln["fora_da_raiz"]:
            agrupado[ln["fora_da_raiz"]].add(ln["resolvido"])
    for veredito in ("vivo", "suspeito", "veneno"):
        alvos = sorted(agrupado.get(veredito, []))
        print(f"\n{veredito.upper()} ({len(alvos)}):")
        for a in alvos:
            marca = "existe" if os.path.exists(a) else "NAO EXISTE"
            print(f"  [{marca:10s}] {a}")

    # ---------------- 5. ALERTAS ----------------
    print("\n" + "=" * 78)
    print("5. ALERTAS")
    print("=" * 78)
    alertas = []
    presas_no_antigo = antigas + ambas
    if presas_no_antigo:
        alertas.append(
            f"{len(presas_no_antigo)} skill(s) ainda apontam para '{RAIZ_ANTIGA}': "
            f"{', '.join(presas_no_antigo)}. Todo comando delas falha ate' o caminho "
            "ser trocado."
        )
    if ambas:
        alertas.append(
            f"COLISAO DE RAIZ em {', '.join(ambas)}: a mesma skill cita "
            f"'{RAIZ_ANTIGA}' e '{RAIZ_ATUAL}'. Uma das duas esta' morta."
        )
    if conta["RECUPERAVEL"]:
        alertas.append(
            f"{conta['RECUPERAVEL']} caminho(s) sao consertados so' trocando "
            f"'{RAIZ_ANTIGA}' por '{RAIZ_ATUAL}'."
        )
    veneno = home / "Desktop/Mesa/Pastas/Perícia e fluxo/PROJETO CALCULADORA HONORÁRIOS"
    if veneno.exists():
        alertas.append(
            f"PASTA ENVENENADA presente: {veneno} — nao rodar nada de la'; "
            "o detecta_custeio.py dela classifica CUSTEADO como GRATUIDADE."
        )
    if quebradas:
        alertas.append(f"{len(quebradas)} rota(s) de skill apontam para nome inexistente.")
    if not alertas:
        print("  nenhum")
    for i, a in enumerate(alertas, 1):
        print(f"  {i}. {a}")

    # ---------------- CSV ----------------
    if args.csv:
        destino = Path(os.path.expanduser(args.csv)).resolve()
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
            w.writeheader()
            w.writerows(linhas)
        print(f"\nCSV: {destino}")
        if args.abrir and sys.platform == "darwin":
            subprocess.run(["open", str(destino)], check=False)

    return 1 if (presas_no_antigo or quebradas) else 0


if __name__ == "__main__":
    raise SystemExit(main())
