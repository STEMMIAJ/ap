#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TESTE RÁPIDO DE CONEXÃO
Verifica se o sistema consegue acessar as imobiliárias
"""

import requests
from imoveis_links import obter_imobiliarias_ativas

def testar_conexoes():
    """Testa conexão com cada imobiliária"""

    imobiliarias = obter_imobiliarias_ativas()

    print("\n" + "="*70)
    print("TESTE DE CONEXÃO - IMOBILIÁRIAS")
    print("="*70 + "\n")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    sucessos = 0
    falhas = 0

    for chave, dados in imobiliarias.items():
        nome = dados['nome']
        url = dados['url']

        print(f"[{chave}] {nome}")
        print(f"    URL: {url[:60]}...")

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                print(f"    ✓ Status: {response.status_code} OK")
                print(f"    ✓ Tamanho: {len(response.content)} bytes")
                sucessos += 1
            else:
                print(f"    ✗ Status: {response.status_code}")
                falhas += 1

        except requests.exceptions.Timeout:
            print(f"    ✗ TIMEOUT (servidor demorou mais de 10s)")
            falhas += 1

        except Exception as e:
            print(f"    ✗ ERRO: {str(e)[:50]}")
            falhas += 1

        print()  # Linha em branco

    # Resumo
    print("="*70)
    print("RESUMO DO TESTE")
    print("="*70)
    print(f"Total de imobiliárias: {len(imobiliarias)}")
    print(f"Conexões bem-sucedidas: {sucessos} ✓")
    print(f"Conexões com falha: {falhas} ✗")
    print(f"Taxa de sucesso: {(sucessos/len(imobiliarias)*100):.1f}%")
    print("="*70 + "\n")

    if sucessos == len(imobiliarias):
        print("🎉 Todas as imobiliárias estão acessíveis!")
        print("Você pode executar: python pesquisar_imoveis.py\n")
    elif sucessos > 0:
        print("⚠️  Algumas imobiliárias não responderam.")
        print("O script principal funcionará apenas com as que responderam.\n")
    else:
        print("❌ Nenhuma imobiliária respondeu.")
        print("Verifique sua conexão com a internet.\n")


if __name__ == "__main__":
    testar_conexoes()
