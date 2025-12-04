#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CONFIGURAÇÃO DE LINKS: Imobiliárias de Governador Valadares
Bairros: Lagoa Santa e Santo Agostinho
"""

IMOBILIARIAS = {
    "SINGULAR_IMOVEIS": {
        "nome": "Singular Imóveis",
        "url": "https://www.singularimoveis.com.br/aluguel/apartamento--casa/governador-valadares/lagoa-santa--santo-agostinho/0-quartos/0-suite-ou-mais/0-vaga-ou-mais/0-banheiro-ou-mais/sem-portaria-24horas/sem-area-lazer/sem-dce/sem-mobilia/sem-area-privativa/sem-area-servico/sem-box-despejo/sem-circuito-tv/?valorminimo=0&valormaximo=0&pagina=1",
        "ativa": True
    },
    "PREDILETA": {
        "nome": "Imobiliária Predileta",
        "url": "https://www.imobiliariapredileta.com.br/aluguel/apartamento--casa--cobertura/governador-valadares/lagoa-santa/0-quartos/0-suite-ou-mais/0-vaga/0-banheiro-ou-mais/todos-os-condominios?valorminimo=1.000,00&valormaximo=0&pagina=1",
        "ativa": True
    },
    "COIMBRA": {
        "nome": "Coimbra Imóveis",
        "url": "https://www.coimbraimoveis.com/aluguel/apartamento--casa--cobertura/governador-valadares/lagoa-santa--lagoa-santa--lagoa-santa-2---santo-agostinho/0-quartos/0-suite-ou-mais/0-vaga/0-banheiro-ou-mais?valorminimo=0&valormaximo=0&pagina=1",
        "ativa": True
    },
    "SR_IMOVEIS": {
        "nome": "SR Imóveis",
        "url": "https://srimoveisgv.com.br/alugar/lagoa-santa_santo-agostinho/apartamento_apto.-cobertura_casa/ordem-valor/resultado-crescente/quantidade-12/",
        "ativa": True
    },
    "SOLUCAO": {
        "nome": "Solução Imobiliária",
        "url": "https://www.solucaoimobiliaria.com/buscar?availability=rent&search_type=properties&neighborhood=Lagoa%20Santa&neighborhood=Santo%20Agostinho&city=Governador%20Valadares&cursor=&order=most_relevant&direction=desc&property_type=Apartamento&property_type=Apartamento%20Cobertura&property_type=Casa",
        "ativa": True
    },
    "BETEL": {
        "nome": "Betel Imóveis",
        "url": "https://www.betelimoveismg.com.br/aluguel/apartamento+casa+cobertura/governador-valadares/lagoa-santa+lagoa-santa-2+santo-agostinho/?&pagina=1",
        "ativa": True
    },
    "SEGURANCA": {
        "nome": "Segurança Imóveis",
        "url": "https://segurancaimoveisgv.com.br/aluguel/apartamento/governador-valadares/lagoa-santa/",
        "ativa": True
    },
    "DOCARMO": {
        "nome": "Docarmo Imóveis",
        "url": "https://www.docarmoimoveis.com.br/aluguel/apartamento+casa/governador-valadares/lagoa-santa+santo-agostinho/?&pagina=1",
        "ativa": True
    },
    "CERTA": {
        "nome": "Certa Imóveis",
        "url": "https://www.certaimoveis.com.br/imoveis/aluguel/tipo_apartamento_2/tipo_casa_1/cidade_governador-valadares_2/bairro_lagoa-santa_3166/bairro_santo-agostinho_7982",
        "ativa": True
    },
    "CARLOS_AMARAL": {
        "nome": "Carlos Amaral Imóveis",
        "url": "https://www.carlosamaralimoveis.com.br/aluguel/apartamento-(cobertura)--apartamento-(duplex)--apartamento--casa--casa-+-apt/todas-as-cidades/todos-os-bairros/0-quartos/0-suite-ou-mais/0-vaga-ou-mais/0-banheiro-ou-mais/sem-portaria-24horas/sem-area-lazer/sem-dce/sem-mobilia/sem-area-privativa/sem-area-servico/sem-box-despejo/sem-circuito-tv/?valorminimo=0&valormaximo=0&pagina=1",
        "ativa": True
    },
    "ALUGUEY": {
        "nome": "Aluguey",
        "url": "https://aluguey.com.br/resultado-de-pesquisa/?status%5B%5D=&property_id=&location%5B%5D=gov-valadares&areas%5B%5D=lagoa-santa&areas%5B%5D=lagoa-santa-2&areas%5B%5D=santo-agostinho&bedrooms=&bedrooms=&type%5B%5D=apartamento&type%5B%5D=casa&feature%5B%5D=&min-price=&max-price=",
        "ativa": True
    }
}


def obter_imobiliarias_ativas():
    """Retorna apenas as imobiliárias marcadas como ativas"""
    return {
        chave: dados
        for chave, dados in IMOBILIARIAS.items()
        if dados.get("ativa", False)
    }


def listar_todas_urls():
    """Retorna lista de todas as URLs ativas"""
    return [
        dados["url"]
        for dados in IMOBILIARIAS.values()
        if dados.get("ativa", False)
    ]
