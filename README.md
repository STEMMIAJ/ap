# 🏠 Sistema de Busca de Imóveis - Governador Valadares

Sistema automatizado para pesquisar imóveis para aluguel nos bairros **Lagoa Santa** e **Santo Agostinho** em Governador Valadares/MG.

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

### 1️⃣ Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2️⃣ Executar a Busca

```bash
python pesquisar_imoveis.py
```

### 3️⃣ Ver os Resultados

Após a execução, será criado o arquivo `resultados_imoveis.json` com todos os dados coletados.

## 📁 Estrutura dos Arquivos

```
ap/
├── imoveis_links.py          # Configuração de URLs das imobiliárias
├── pesquisar_imoveis.py      # Script principal de busca
├── requirements.txt          # Dependências Python
├── resultados_imoveis.json   # Resultados da busca (gerado automaticamente)
└── README.md                 # Este arquivo
```

## 🔧 Funcionalidades

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

## 🔄 Próximas Melhorias

- [ ] Filtros personalizados (preço, quartos, etc.)
- [ ] Suporte a Selenium para sites dinâmicos
- [ ] Exportação para CSV/Excel
- [ ] Notificações de novos imóveis
- [ ] Interface web

## 📞 Suporte

Este sistema foi desenvolvido para uso pessoal na busca de imóveis em Governador Valadares.

---

**Desenvolvido com ❤️ para facilitar a busca de imóveis em GV**
