# 🏠 Sistema de Busca de Imóveis - Governador Valadares

Sistema automatizado completo para pesquisar imóveis para aluguel nos bairros **Lagoa Santa** e **Santo Agostinho** em Governador Valadares/MG.

## 🎯 NOVO: Monitoramento de Imóvel Específico

Agora com sistema dedicado para monitorar o imóvel **Rua Rainier Barbosa, 338** e buscar documentos públicos relacionados!

## 📋 Imobiliárias Incluídas

O sistema pesquisa em **11 imobiliárias**:

1. ✅ Singular Imóveis
2. ✅ Imobiliária Predileta
3. ✅ Coimbra Imóveis
4. ✅ SR Imóveis
5. ✅ Solução Imobiliária
6. ✅ Betel Imóveis
7. ✅ Segurança Imóveis
8. ✅ Docarmo Imóveis
9. ✅ Certa Imóveis
10. ✅ Carlos Amaral Imóveis
11. ✅ Aluguey

## 🚀 Como Usar

### 🆕 SISTEMA PRINCIPAL - Monitoramento Integrado

**Para monitorar o imóvel Rainier Barbosa 338:**

```bash
python busca_imovel_338.py
```

Menu interativo com opções:
1. Monitorar se o imóvel está à venda/aluguel online
2. Buscar documentos públicos (escrituras, contratos, etc.)
3. Monitoramento contínuo (verifica a cada X horas)
4. Ver histórico de monitoramentos
5. Buscar em todas as imobiliárias de GV

---

### 📦 Sistema Geral de Busca

### 1️⃣ Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2️⃣ Executar a Busca Geral

```bash
python pesquisar_imoveis.py
```

### 3️⃣ Ver os Resultados

Após a execução, será criado o arquivo `resultados_imoveis.json` com todos os dados coletados.

---

### 🎯 Scripts Específicos

**Monitorar imóvel específico (execução única):**
```bash
python monitorar_imovel_especifico.py
```

**Monitorar continuamente (a cada 24 horas):**
```bash
python monitorar_imovel_especifico.py --continuo 24
```

**Buscar documentos públicos:**
```bash
python buscar_documentos_imovel.py
```

**Testar conexão com imobiliárias:**
```bash
python testar_conexao.py
```

## 📁 Estrutura dos Arquivos

```
ap/
├── 🆕 busca_imovel_338.py              # ⭐ SISTEMA PRINCIPAL - Menu interativo
├── 🆕 monitorar_imovel_especifico.py   # Monitora se o imóvel 338 está online
├── 🆕 buscar_documentos_imovel.py      # Busca documentos públicos do imóvel 338
├── imoveis_links.py                    # Configuração de URLs das imobiliárias
├── pesquisar_imoveis.py                # Script de busca geral em imobiliárias
├── testar_conexao.py                   # Testa conexão com os sites
├── requirements.txt                    # Dependências Python
├── README.md                           # Este arquivo
│
├── 📊 Arquivos gerados automaticamente:
├── resultados_imoveis.json             # Resultados da busca geral
├── historico_monitoramento_338.json    # Histórico de monitoramentos do 338
└── relatorio_busca_documentos_*.json   # Relatórios de busca de documentos
```

## 🔧 Funcionalidades

### 🆕 Sistema de Monitoramento Específico (Rainier Barbosa 338):
- ✅ Monitoramento em sites de classificados (VivaReal, ZAP, OLX, etc.)
- ✅ Verificação em 11 imobiliárias locais de Governador Valadares
- ✅ Busca de documentos públicos (processos, diários oficiais)
- ✅ Informações sobre cartórios e IPTU
- ✅ Monitoramento contínuo automático (agenda verificações)
- ✅ Histórico completo de verificações
- ✅ Alertas quando o imóvel é encontrado
- ✅ Menu interativo fácil de usar

### Sistema Geral de Busca:
- ✅ Busca automática em múltiplas imobiliárias
- ✅ Extração de dados dos imóveis (preço, título, link)
- ✅ Tratamento de erros e timeouts
- ✅ Salvamento em JSON estruturado
- ✅ Relatório resumido no terminal
- ✅ Intervalo entre requisições (respeita os servidores)

## 📊 Exemplo de Saída

```json
{
  "data_busca": "2024-12-04T10:30:00",
  "total_imobiliarias_consultadas": 11,
  "resultados": [
    {
      "imobiliaria": "Singular Imóveis",
      "status": "sucesso",
      "total_imoveis": 15,
      "imoveis_encontrados": [...]
    }
  ]
}
```

## ⚙️ Configurações

Para ativar/desativar imobiliárias, edite o arquivo `imoveis_links.py`:

```python
"SINGULAR_IMOVEIS": {
    "nome": "Singular Imóveis",
    "url": "...",
    "ativa": True  # Mude para False para desativar
}
```

## 📝 Notas Importantes

- **Web Scraping**: Cada site tem estrutura HTML diferente. O sistema usa seletores genéricos.
- **Limitações**: Alguns sites podem usar JavaScript para carregar conteúdo dinamicamente.
- **Ética**: O sistema respeita intervalos entre requisições (2 segundos).

## 📜 Como Obter Documentos Oficiais do Imóvel

### 1️⃣ Cartório de Registro de Imóveis (Escritura e Proprietário)

**1º Ofício de Registro de Imóveis:**
- 📞 Telefone/WhatsApp: **(33) 3271-2282**
- 📍 Rua Arthur Bernardes, 684 - Centro - GV/MG
- 🌐 https://1rigv.com.br/
- 💰 Custo: R$ 50-100 | Prazo: 24-48h
- 📄 **Solicitar**: "Certidão de Matrícula Atualizada do imóvel na Rua Rainier Barbosa, 338"

**O que você recebe:**
- ✅ Nome completo do proprietário
- ✅ CPF/CNPJ do proprietário
- ✅ Histórico de proprietários anteriores
- ✅ Hipotecas, penhoras ou ônus

### 2️⃣ Prefeitura (IPTU e Dados Cadastrais)

- 🌐 Portal: http://intranet.valadares.mg.gov.br:8080/
- 📍 Rua Marechal Floriano, 905 – 4º andar
- 📄 Consultar número de inscrição do imóvel e débitos

### 3️⃣ Processos Judiciais

- 🏛️ TJMG: https://www4.tjmg.jus.br/juridico/sf/index.jsp
- 📋 Buscar por endereço ou parte envolvida

---

## 🔄 Próximas Melhorias

- [ ] Filtros personalizados (preço, quartos, etc.)
- [ ] Suporte a Selenium para sites dinâmicos
- [ ] Exportação para CSV/Excel
- [ ] Notificações por email/SMS quando imóvel for encontrado
- [ ] Interface web
- [ ] Integração com API do WhatsApp para alertas

## 📞 Suporte

Este sistema foi desenvolvido para uso pessoal na busca de imóveis em Governador Valadares.

---

**Desenvolvido com ❤️ para facilitar a busca de imóveis em GV**
