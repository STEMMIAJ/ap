#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SISTEMA DE BUSCA DE IMÓVEIS
Pesquisa automática em imobiliárias de Governador Valadares
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
from typing import List, Dict
import re

from imoveis_links import IMOBILIARIAS, obter_imobiliarias_ativas


class BuscadorImoveis:
    """Classe principal para buscar imóveis nas imobiliárias"""

    def __init__(self):
        self.resultados = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def buscar_em_todas(self):
        """Busca em todas as imobiliárias ativas"""
        imobiliarias = obter_imobiliarias_ativas()

        print(f"\n{'='*60}")
        print(f"INICIANDO BUSCA EM {len(imobiliarias)} IMOBILIÁRIAS")
        print(f"{'='*60}\n")

        for chave, dados in imobiliarias.items():
            self.buscar_em_site(chave, dados)
            time.sleep(2)  # Pausa de 2 segundos entre requisições

        return self.resultados

    def buscar_em_site(self, chave: str, dados: Dict):
        """Busca imóveis em um site específico"""
        nome = dados['nome']
        url = dados['url']

        print(f"\n[{chave}] Buscando em: {nome}")
        print(f"URL: {url[:80]}...")

        try:
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code == 200:
                print(f"✓ Conexão bem-sucedida (Status: {response.status_code})")

                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extrai informações básicas da página
                imoveis_encontrados = self.extrair_imoveis(soup, nome, url)

                resultado = {
                    'imobiliaria': nome,
                    'chave': chave,
                    'url': url,
                    'status': 'sucesso',
                    'timestamp': datetime.now().isoformat(),
                    'imoveis_encontrados': imoveis_encontrados,
                    'total_imoveis': len(imoveis_encontrados)
                }

                self.resultados.append(resultado)
                print(f"✓ {len(imoveis_encontrados)} imóveis encontrados")

            else:
                print(f"✗ Erro HTTP: {response.status_code}")
                self.resultados.append({
                    'imobiliaria': nome,
                    'chave': chave,
                    'url': url,
                    'status': 'erro_http',
                    'codigo_erro': response.status_code,
                    'timestamp': datetime.now().isoformat()
                })

        except requests.exceptions.Timeout:
            print(f"✗ Timeout: Servidor não respondeu em 15 segundos")
            self.resultados.append({
                'imobiliaria': nome,
                'chave': chave,
                'url': url,
                'status': 'timeout',
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            print(f"✗ Erro: {str(e)}")
            self.resultados.append({
                'imobiliaria': nome,
                'chave': chave,
                'url': url,
                'status': 'erro',
                'mensagem_erro': str(e),
                'timestamp': datetime.now().isoformat()
            })

    def extrair_imoveis(self, soup: BeautifulSoup, imobiliaria: str, url: str) -> List[Dict]:
        """
        Extrai informações dos imóveis do HTML.
        NOTA: Cada site tem estrutura HTML diferente.
        Esta é uma implementação genérica que tenta identificar padrões comuns.
        """
        imoveis = []

        # Seletores comuns para cards de imóveis
        seletores_possiveis = [
            '.property-card',
            '.imovel-card',
            '.listing-card',
            '.property-item',
            'article.property',
            'div[class*="property"]',
            'div[class*="imovel"]',
            'div[class*="card"]'
        ]

        cards_encontrados = []
        for seletor in seletores_possiveis:
            cards = soup.select(seletor)
            if cards and len(cards) > cards_encontrados.__len__():
                cards_encontrados = cards

        for idx, card in enumerate(cards_encontrados[:50], 1):  # Limita a 50 primeiros
            imovel = self.extrair_dados_card(card, idx)
            if imovel:
                imovel['imobiliaria'] = imobiliaria
                imoveis.append(imovel)

        # Se não encontrou cards, tenta contar de outra forma
        if not imoveis:
            # Busca por padrões de preço (indicam imóveis)
            precos = soup.find_all(text=re.compile(r'R\$\s*[\d.,]+'))
            if precos:
                return [{
                    'info': 'Página carregada com sucesso',
                    'indicio_imoveis': len(precos),
                    'nota': 'Necessário ajustar seletores CSS para este site'
                }]

        return imoveis

    def extrair_dados_card(self, card, indice: int) -> Dict:
        """Extrai dados de um card individual de imóvel"""
        try:
            # Tenta extrair preço
            preco_text = None
            for seletor in ['.price', '.valor', '.preco', '[class*="price"]', '[class*="valor"]']:
                elem = card.select_one(seletor)
                if elem:
                    preco_text = elem.get_text(strip=True)
                    break

            # Tenta extrair título/endereço
            titulo = None
            for seletor in ['h2', 'h3', '.title', '.titulo', '[class*="title"]']:
                elem = card.select_one(seletor)
                if elem:
                    titulo = elem.get_text(strip=True)
                    break

            # Tenta extrair link
            link = None
            link_elem = card.find('a', href=True)
            if link_elem:
                link = link_elem['href']

            if preco_text or titulo:  # Só retorna se encontrou algo relevante
                return {
                    'indice': indice,
                    'titulo': titulo,
                    'preco': preco_text,
                    'link': link,
                    'html_snippet': str(card)[:200] + '...'  # Primeiros 200 caracteres
                }

        except Exception as e:
            return {'indice': indice, 'erro_extracao': str(e)}

        return None

    def salvar_resultados(self, arquivo: str = 'resultados_imoveis.json'):
        """Salva os resultados em arquivo JSON"""
        dados_completos = {
            'data_busca': datetime.now().isoformat(),
            'total_imobiliarias_consultadas': len(self.resultados),
            'resultados': self.resultados
        }

        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_completos, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"✓ Resultados salvos em: {arquivo}")
        print(f"{'='*60}")

    def exibir_resumo(self):
        """Exibe um resumo dos resultados"""
        print(f"\n{'='*60}")
        print("RESUMO DA BUSCA")
        print(f"{'='*60}")

        total_imoveis = sum(
            r.get('total_imoveis', 0)
            for r in self.resultados
        )

        sucesso = sum(1 for r in self.resultados if r.get('status') == 'sucesso')
        erros = len(self.resultados) - sucesso

        print(f"\nImobiliárias consultadas: {len(self.resultados)}")
        print(f"Consultas bem-sucedidas: {sucesso}")
        print(f"Consultas com erro: {erros}")
        print(f"Total de imóveis encontrados: {total_imoveis}")

        print(f"\n{'='*60}\n")


def main():
    """Função principal"""
    buscador = BuscadorImoveis()

    # Busca em todas as imobiliárias
    buscador.buscar_em_todas()

    # Exibe resumo
    buscador.exibir_resumo()

    # Salva resultados
    buscador.salvar_resultados()


if __name__ == "__main__":
    main()
