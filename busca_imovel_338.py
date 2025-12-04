#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏠 SISTEMA COMPLETO DE BUSCA - RUA RAINIER BARBOSA 338

Script principal que integra todas as funcionalidades:
1. Monitoramento em sites de imóveis
2. Busca profunda de documentos
3. Histórico de verificações
"""

import sys
import os
from datetime import datetime


def menu_principal():
    """Exibe menu principal"""

    print("\n" + "="*70)
    print("🏠 SISTEMA DE BUSCA - RUA RAINIER BARBOSA 338")
    print("="*70)
    print("\nImóvel: Rua Rainier Barbosa, 338")
    print("Bairro: Santo Agostinho - Governador Valadares/MG")
    print("CEP: 35065-002")
    print("\n" + "="*70)
    print("\n📋 ESCOLHA UMA OPÇÃO:\n")
    print("  1️⃣  Monitorar se o imóvel está à venda/aluguel online")
    print("  2️⃣  Buscar documentos públicos (escrituras, contratos, etc.)")
    print("  3️⃣  Monitoramento contínuo (verifica a cada X horas)")
    print("  4️⃣  Ver histórico de monitoramentos")
    print("  5️⃣  Buscar em todas as imobiliárias de GV")
    print("  0️⃣  Sair")
    print("\n" + "="*70)

    escolha = input("\n👉 Digite o número da opção: ").strip()
    return escolha


def executar_monitoramento_unico():
    """Executa monitoramento único"""
    print("\n🔍 Iniciando monitoramento único...\n")
    from monitorar_imovel_especifico import monitoramento_unico
    monitoramento_unico()


def executar_busca_documentos():
    """Executa busca de documentos"""
    print("\n📄 Iniciando busca de documentos...\n")
    from buscar_documentos_imovel import BuscadorDocumentos
    buscador = BuscadorDocumentos()
    buscador.executar_busca_completa()


def executar_monitoramento_continuo():
    """Executa monitoramento contínuo"""
    print("\n" + "="*70)
    print("🔄 MONITORAMENTO CONTÍNUO")
    print("="*70)
    print("\nEste modo verifica periodicamente se o imóvel aparece online.")
    print("O programa ficará rodando até você pressionar Ctrl+C")
    print("\n" + "="*70)

    intervalo = input("\n⏱️  Intervalo entre verificações (horas) [padrão: 24]: ").strip()

    if not intervalo:
        intervalo = 24
    else:
        try:
            intervalo = int(intervalo)
        except:
            print("❌ Valor inválido. Usando 24 horas.")
            intervalo = 24

    print(f"\n✅ Iniciando monitoramento contínuo a cada {intervalo} hora(s)...")
    print("   Pressione Ctrl+C para parar\n")

    from monitorar_imovel_especifico import monitoramento_continuo
    monitoramento_continuo(intervalo)


def ver_historico():
    """Exibe histórico de monitoramentos"""
    import json

    arquivo = "historico_monitoramento_338.json"

    if not os.path.exists(arquivo):
        print("\n❌ Nenhum histórico encontrado.")
        print("   Execute primeiro o monitoramento (opção 1 ou 3)")
        return

    with open(arquivo, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    print("\n" + "="*70)
    print("📊 HISTÓRICO DE MONITORAMENTOS")
    print("="*70)
    print(f"\nImóvel: {dados['imovel']['endereco']}")
    print(f"Total de verificações: {dados['total_verificacoes']}")
    print(f"Última verificação: {dados['ultima_verificacao']}")
    print("\n" + "="*70)

    if dados['total_verificacoes'] > 0:
        print("\n📋 ÚLTIMAS VERIFICAÇÕES:\n")
        for idx, verificacao in enumerate(reversed(dados['historico'][-5:]), 1):
            timestamp = datetime.fromisoformat(verificacao['timestamp'])
            status = "✅ ENCONTRADO" if verificacao['encontrado'] else "⚪ Não encontrado"

            print(f"  {idx}. {timestamp.strftime('%d/%m/%Y %H:%M:%S')} - {status}")

    print("\n" + "="*70 + "\n")


def buscar_imobiliarias_locais():
    """Busca nas imobiliárias locais"""
    print("\n🏢 Buscando nas imobiliárias locais de Governador Valadares...\n")
    from pesquisar_imoveis import main
    main()


def main():
    """Função principal"""

    while True:
        escolha = menu_principal()

        if escolha == "1":
            executar_monitoramento_unico()
            input("\n⏎ Pressione Enter para voltar ao menu...")

        elif escolha == "2":
            executar_busca_documentos()
            input("\n⏎ Pressione Enter para voltar ao menu...")

        elif escolha == "3":
            try:
                executar_monitoramento_continuo()
            except KeyboardInterrupt:
                print("\n\n⛔ Monitoramento interrompido.")
            input("\n⏎ Pressione Enter para voltar ao menu...")

        elif escolha == "4":
            ver_historico()
            input("\n⏎ Pressione Enter para voltar ao menu...")

        elif escolha == "5":
            buscar_imobiliarias_locais()
            input("\n⏎ Pressione Enter para voltar ao menu...")

        elif escolha == "0":
            print("\n👋 Encerrando sistema. Até logo!")
            sys.exit(0)

        else:
            print("\n❌ Opção inválida. Tente novamente.")
            input("\n⏎ Pressione Enter para continuar...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ Sistema encerrado pelo usuário.")
        sys.exit(0)
