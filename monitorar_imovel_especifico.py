#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MONITORAMENTO DE IMÓVEL ESPECÍFICO
Rua Rainier Barbosa, 338 - Santo Agostinho - Governador Valadares/MG

Este script monitora continuamente se o imóvel aparece em sites de imóveis.
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
from typing import List, Dict
import re

# Configuração do imóvel alvo
IMOVEL_ALVO = {
    "endereco": "Rainier Barbosa 338",
    "endereco_alternativo": "Rainer Barbosa 338",
    "numero": "338",
    "rua": "Rainier Barbosa",
    "bairro": "Santo Agostinho",
    "cidade": "Governador Valadares",
    "estado": "MG",
    "cep": "35065-002"
}

# Sites para monitorar
SITES_MONITORAMENTO = [
    {
        "nome": "VivaReal",
        "url_busca": "https://www.vivareal.com.br/venda/minas-gerais/governador-valadares/santo-agostinho/",
        "url_aluguel": "https://www.vivareal.com.br/aluguel/minas-gerais/governador-valadares/santo-agostinho/"
    },
    {
        "nome": "ZapImóveis",
        "url_busca": "https://www.zapimoveis.com.br/venda/imoveis/mg+governador-valadares+santo-agostinho/",
        "url_aluguel": "https://www.zapimoveis.com.br/aluguel/imoveis/mg+governador-valadares+santo-agostinho/"
    },
    {
        "nome": "OLX",
        "url_busca": "https://www.olx.com.br/imoveis/venda/estado-mg/governador-valadares",
        "url_aluguel": "https://www.olx.com.br/imoveis/aluguel/estado-mg/governador-valadares"
    },
    {
        "nome": "Imovelweb",
        "url_busca": "https://www.imovelweb.com.br/imoveis-venda-governador-valadares-santo-agostinho.html",
        "url_aluguel": "https://www.imovelweb.com.br/imoveis-aluguel-governador-valadares-santo-agostinho.html"
    }
]


class MonitoradorImovel:
    """Monitora se um imóvel específico aparece online"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.historico = []

    def verificar_todas_fontes(self) -> Dict:
        """Verifica o imóvel em todas as fontes configuradas"""

        print(f"\n{'='*70}")
        print(f"🔍 MONITORAMENTO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"Imóvel: {IMOVEL_ALVO['endereco']}")
        print(f"Bairro: {IMOVEL_ALVO['bairro']} - {IMOVEL_ALVO['cidade']}/{IMOVEL_ALVO['estado']}")
        print(f"{'='*70}\n")

        resultado_geral = {
            "timestamp": datetime.now().isoformat(),
            "imovel": IMOVEL_ALVO,
            "encontrado": False,
            "resultados": []
        }

        # 1. Verifica sites grandes de imóveis
        print("📊 Verificando sites de classificados...")
        for site in SITES_MONITORAMENTO:
            for tipo_url in ["url_busca", "url_aluguel"]:
                if tipo_url in site:
                    resultado = self.verificar_site(site["nome"], site[tipo_url], tipo_url)
                    resultado_geral["resultados"].append(resultado)
                    if resultado.get("encontrado"):
                        resultado_geral["encontrado"] = True
                    time.sleep(3)  # Pausa entre requisições

        # 2. Verifica imobiliárias locais (usando o sistema anterior)
        print("\n🏢 Verificando imobiliárias locais...")
        resultado_local = self.verificar_imobiliarias_locais()
        resultado_geral["resultados"].append(resultado_local)
        if resultado_local.get("encontrado"):
            resultado_geral["encontrado"] = True

        # 3. Busca no Google
        print("\n🔎 Fazendo busca no Google...")
        resultado_google = self.buscar_google()
        resultado_geral["resultados"].append(resultado_google)

        return resultado_geral

    def verificar_site(self, nome_site: str, url: str, tipo: str) -> Dict:
        """Verifica um site específico"""

        print(f"\n  → {nome_site} ({tipo.replace('url_', '')})...")

        try:
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code == 200:
                html_content = response.text.lower()

                # Procura pelo número 338 e variações do nome da rua
                padroes = [
                    r'rainier\s*barbosa\s*338',
                    r'rainer\s*barbosa\s*338',
                    r'rainier\s*barbosa,?\s*n[ºo°]?\s*338',
                    r'338\s*rainier\s*barbosa'
                ]

                encontrado = False
                for padrao in padroes:
                    if re.search(padrao, html_content):
                        encontrado = True
                        break

                if encontrado:
                    print(f"    ✅ IMÓVEL ENCONTRADO!")
                    return {
                        "site": nome_site,
                        "tipo": tipo,
                        "encontrado": True,
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "status": "ALERTA: Imóvel encontrado neste site!"
                    }
                else:
                    print(f"    ⚪ Não encontrado")
                    return {
                        "site": nome_site,
                        "tipo": tipo,
                        "encontrado": False,
                        "url": url,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                print(f"    ⚠️  Erro HTTP {response.status_code}")
                return {
                    "site": nome_site,
                    "tipo": tipo,
                    "erro": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            print(f"    ❌ Erro: {str(e)[:50]}")
            return {
                "site": nome_site,
                "tipo": tipo,
                "erro": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def verificar_imobiliarias_locais(self) -> Dict:
        """Verifica nas imobiliárias locais de GV"""

        from imoveis_links import IMOBILIARIAS

        encontrados = []

        for chave, dados in IMOBILIARIAS.items():
            if not dados.get("ativa"):
                continue

            try:
                response = requests.get(dados["url"], headers=self.headers, timeout=10)

                if response.status_code == 200:
                    html_content = response.text.lower()

                    # Procura pelo endereço
                    if "338" in html_content and ("rainier" in html_content or "rainer" in html_content):
                        print(f"    ✅ Possível match em: {dados['nome']}")
                        encontrados.append({
                            "imobiliaria": dados["nome"],
                            "url": dados["url"]
                        })

            except Exception as e:
                continue

        if encontrados:
            return {
                "fonte": "imobiliarias_locais",
                "encontrado": True,
                "detalhes": encontrados,
                "timestamp": datetime.now().isoformat()
            }
        else:
            print("    ⚪ Não encontrado nas imobiliárias locais")
            return {
                "fonte": "imobiliarias_locais",
                "encontrado": False,
                "timestamp": datetime.now().isoformat()
            }

    def buscar_google(self) -> Dict:
        """Simula uma busca no Google (apenas retorna sugestão de busca manual)"""

        query = f'"Rainier Barbosa 338" OR "Rainer Barbosa 338" Governador Valadares'
        url_google = f"https://www.google.com/search?q={query.replace(' ', '+')}"

        print(f"    💡 Busca sugerida no Google:")
        print(f"    {url_google}")

        return {
            "fonte": "google",
            "sugestao_busca": query,
            "url": url_google,
            "nota": "Execute esta busca manualmente no navegador",
            "timestamp": datetime.now().isoformat()
        }

    def salvar_historico(self, resultado: Dict):
        """Salva o histórico de monitoramento"""

        self.historico.append(resultado)

        arquivo = "historico_monitoramento_338.json"

        dados_salvar = {
            "imovel": IMOVEL_ALVO,
            "total_verificacoes": len(self.historico),
            "ultima_verificacao": datetime.now().isoformat(),
            "historico": self.historico
        }

        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_salvar, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Histórico salvo em: {arquivo}")

    def exibir_resumo(self, resultado: Dict):
        """Exibe resumo do monitoramento"""

        print(f"\n{'='*70}")
        print("📊 RESUMO DO MONITORAMENTO")
        print(f"{'='*70}")

        if resultado["encontrado"]:
            print("\n🎯 STATUS: IMÓVEL ENCONTRADO!")
            print("\n⚠️  ALERTAS:")
            for r in resultado["resultados"]:
                if r.get("encontrado"):
                    print(f"  • {r.get('site', r.get('fonte'))}: {r.get('url', 'Ver detalhes no JSON')}")
        else:
            print("\n⚪ STATUS: Imóvel não encontrado")
            print("   O imóvel não está listado publicamente no momento.")

        print(f"\nTotal de fontes verificadas: {len(resultado['resultados'])}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        print(f"{'='*70}\n")


def monitoramento_unico():
    """Executa uma verificação única"""

    monitor = MonitoradorImovel()
    resultado = monitor.verificar_todas_fontes()
    monitor.exibir_resumo(resultado)
    monitor.salvar_historico(resultado)

    return resultado


def monitoramento_continuo(intervalo_horas: int = 24):
    """Executa monitoramento contínuo com intervalo especificado"""

    print(f"🔄 Iniciando monitoramento contínuo...")
    print(f"   Intervalo: {intervalo_horas} hora(s)")
    print(f"   Pressione Ctrl+C para parar\n")

    monitor = MonitoradorImovel()
    contador = 1

    try:
        while True:
            print(f"\n{'#'*70}")
            print(f"VERIFICAÇÃO #{contador}")
            print(f"{'#'*70}")

            resultado = monitor.verificar_todas_fontes()
            monitor.exibir_resumo(resultado)
            monitor.salvar_historico(resultado)

            # Se encontrou, envia alerta
            if resultado["encontrado"]:
                print("\n" + "🔔"*30)
                print("🚨 ALERTA: IMÓVEL ENCONTRADO!")
                print("🔔"*30 + "\n")

            contador += 1

            # Aguarda próximo ciclo
            print(f"\n⏳ Aguardando {intervalo_horas}h para próxima verificação...")
            print(f"   Próxima verificação: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
            time.sleep(intervalo_horas * 3600)

    except KeyboardInterrupt:
        print("\n\n⛔ Monitoramento interrompido pelo usuário.")
        print(f"Total de verificações realizadas: {contador - 1}")


if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("🏠 MONITORAMENTO DE IMÓVEL ESPECÍFICO")
    print("="*70)
    print(f"Endereço: Rua Rainier Barbosa, 338")
    print(f"Bairro: Santo Agostinho - Governador Valadares/MG")
    print("="*70 + "\n")

    if len(sys.argv) > 1 and sys.argv[1] == "--continuo":
        # Modo contínuo (verifica a cada 24h)
        intervalo = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        monitoramento_continuo(intervalo)
    else:
        # Modo único (verifica uma vez)
        print("💡 Executando verificação única...")
        print("   (Use --continuo [horas] para monitoramento contínuo)\n")
        monitoramento_unico()
