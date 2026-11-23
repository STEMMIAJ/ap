# PLANO DE FIXAÇÃO DO FLUXO PERICIAL

Objetivo: fechar os gargalos do fluxo de complexidade e honorários usando as
correções que o Dr. Jésus **já criou** e que estão enterradas em bancos que
nenhuma skill lê. Nada é apagado sem o sim dele.

---

## PRINCÍPIO ÚNICO

> **A correção já existe. Procure antes de propor.**

Isto não é preferência, é a trava 3 do `erros-recorrentes`: procurar em
`00-MESTRE.md`, `TASKS.md`, memória e nos arquivos do projeto **antes** de
perguntar. O que o plano faz é mecanizar essa busca, porque ela está falhando
em silêncio: a correção foi escrita, salva, e o fluxo nunca a lê.

Toda proposta tem que carregar o campo `fonte` apontando para onde ele já
decidiu aquilo. **Proposta sem fonte é invenção e é rejeitada na validação.**

---

## ONDE ISTO RODA

| | |
|---|---|
| Roda | **No Mac dele**, em sessão do Claude Code no Terminal |
| Não roda | Nesta sessão de nuvem |
| Por quê | `list_computer_folders` devolve lista vazia: nenhuma pasta do Mac está compartilhada. E não existe ferramenta de GPT/Codex nesta sessão. Sessão-filha herda o ambiente da mãe, então filha na nuvem tem o mesmo bloqueio |

Para destravar: no Mac, **app do Claude → Ajustes → Claude Code → Remote
Control**, liberando a pasta `STEMMIA`. Ou simplesmente rodar o plano no
Terminal do Mac, que é o caminho mais curto.

---

## ARQUITETURA — 3 agentes e 1 portão

```
                 ┌──────────────────────────────┐
                 │  SESSÃO-MÃE (Claude, no Mac) │
                 │  dona da fila                │
                 │  NUNCA escreve nos bancos    │
                 └───────┬──────────────┬───────┘
                         │              │
            um gargalo   │              │  proposta validada
            por vez      ▼              ▼
          ┌──────────────────────┐   ┌─────────────────────┐
          │ FILHA "ARQUEÓLOGA"   │   │ PORTÃO DE ANUÊNCIA  │
          │ (sessão-filha)       │   │ fase3_portao...py   │
          │ SÓ LÊ                │   │ pergunta item a item│
          │ acha a correção que  │   │ ÚNICO que escreve   │
          │ ele já escreveu      │   └─────────┬───────────┘
          └──────────┬───────────┘             │
                     │ prova literal            │ sim / não / adiar
                     ▼                          ▼
          ┌──────────────────────┐        Dr. Jésus
          │ CODEX (CLI no Mac)   │
          │ redige o patch       │
          │ 2º modelo = 2º olhar │
          └──────────────────────┘
```

### Por que cada um existe

**Sessão-mãe** — mantém a fila e valida. Não escreve nos bancos: quem escreve
é só o portão. Separar quem decide de quem executa é o que impede uma rodada
ruim de corromper o acervo.

**Sessão-filha arqueóloga** — contexto separado, só leitura. Varrer 214 casos e
dezenas de bancos estoura o contexto da mãe; por isso vai para a filha, que
devolve só o achado com a prova. Ela **não propõe nada**: entrega o trecho
literal com arquivo e linha.

**Codex** — segundo modelo, cegueira diferente da minha. Recebe o gargalo + a
correção enterrada + as regras canônicas, e redige o patch. Dois modelos têm
que concordar antes de a proposta chegar nele. É revisão cruzada, não enfeite.

**Portão** — único ponto de escrita. Três garantias já testadas:
nada é apagado (vai para quarentena), tudo é reversível (`REVERSAO.sh`), e
proposta contra arquivo que mudou é recusada (confere sha256).

---

## O CICLO — um gargalo por volta

| Passo | Quem | O que faz | Sai com |
|---|---|---|---|
| 1 | mãe | tira o gargalo do topo da fila | enunciado + sintoma medido |
| 2 | **filha** | varre os bancos procurando onde ele já corrigiu isso | trecho literal + arquivo:linha, ou `NÃO ENCONTRADO` |
| 3 | mãe | se `NÃO ENCONTRADO`, **para e pergunta a ele**. Não inventa regra | decisão dele, registrada |
| 4 | **codex** | redige o patch a partir da correção achada | `PROPOSTAS.json` |
| 5 | mãe | valida contra as 4 travas anti-inflação e as 8 travas | aprovado ou devolvido ao passo 4 |
| 6 | **portão** | mostra a ele, item a item | sim / não / adiar, registrado |
| 7 | mãe | roda a FASE 1 de novo e confirma que o gargalo fechou | gargalo sai da fila, ou volta com o motivo |

**A volta só fecha quando a FASE 1 provar que fechou.** Sem medição depois,
não há fixação — só impressão de fixação.

### Validação do passo 5 — o que a mãe recusa

- proposta sem `fonte` apontando para decisão dele que exista
- proposta que cria índice multiplicador (trava 4: dupla incidência)
- proposta que soma a mesma unidade de trabalho duas vezes (trava 3)
- proposta que introduz fator sem gatilho comprovado nos autos (trava 1)
- proposta que mexe em valor sem a marca `A_CONFIRMAR_PELO_PERITO`
- proposta que propõe valor em AJG

---

## AS TRÊS FASES, E O QUE JÁ ESTÁ CONSTRUÍDO

| Fase | Arquivo | Estado |
|---|---|---|
| 1. Arqueologia | `fase1_inventariar_regras.py` | **pronto e testado** |
| 2. Proposta | o Codex redige; formato definido abaixo | formato pronto, conteúdo depende da FASE 1 |
| 3. Portão | `fase3_portao_anuencia.py` | **pronto e testado** |

### FASE 1 — descobre o que ninguém lê

```bash
python3 fase1_inventariar_regras.py --json ~/Desktop/INVENTARIO-REGRAS.json
```

Varre as skills, STEMMIA, ACERVO-LAUDO-IDEAL e as pastas antigas. Para cada
arquivo de regra: impressão digital, data, e **quem o lê**. Relata:

| Seção | O que acusa |
|---|---|
| **ÓRFÃOS** | regra existe, nenhuma skill cita. **É aqui que estão as correções perdidas** |
| DIVERGÊNCIAS | mesma skill ou mesmo arquivo, conteúdo diferente em dois lugares |
| CÓPIAS | conteúdo idêntico duplicado |
| CONFLITOS | mesma chave (`valor_hora`, `f1_base`, `teto`…) com valor diferente entre arquivos |

Nada é alterado. Sai com código 1 se achar problema.

### FASE 2 — formato da proposta

```json
{"propostas": [
  {"id": "P-001",
   "tipo": "ALTERAR_CHAVE",
   "arquivo": "/Users/jesus/Desktop/STEMMIA/.../CATALOGO-125-FATORES.json",
   "sha_esperado": "<da FASE 1, obrigatório>",
   "alvo": "valor_hora",
   "antes": 292, "depois": 350,
   "motivo": "fixação judicial real do caso Isaque + 20%",
   "fonte": "00-SUMARIO-DE-TUDO.md:L142",
   "risco": "MEDIO"}
]}
```

Tipos: `ALTERAR_CHAVE` · `REMOVER_CHAVE` · `ALTERAR_LINHA` · `REMOVER_LINHA` ·
`ADICIONAR_LINHA` · `APOSENTAR_ARQUIVO`.

`sha_esperado` e `fonte` são obrigatórios. Sem eles o portão recusa o lote
inteiro antes de tocar em nada.

### FASE 3 — o portão

```bash
python3 fase3_portao_anuencia.py PROPOSTAS.json --revisar        # só mostra
python3 fase3_portao_anuencia.py PROPOSTAS.json --so-risco ALTO  # as graves primeiro
python3 fase3_portao_anuencia.py PROPOSTAS.json                  # pergunta e aplica
```

Para cada proposta: arquivo, alvo, antes, depois, motivo, fonte, risco.
Resposta `s` / `n` / `a` / `q`.

**Garantias verificadas em teste:**

| Garantia | Como foi provado |
|---|---|
| Recusar não toca no arquivo | sha256 idêntico antes e depois; quarentena nem é criada |
| Remoção não apaga | chave removida reaparece em `<arquivo>.removidos.json` com data, proposta, motivo e fonte |
| Reversão restaura o original | `REVERSAO.sh` devolveu `valor_hora: 292` **e** o multiplicador removido |
| Arquivo mudado por fora é recusado | proposta com sha falso não foi aplicada; `f1_base` permaneceu 3.0 |
| Duas propostas no mesmo arquivo | backup feito uma só vez, no primeiro toque, para a reversão não restaurar estado intermediário |

Registro append-only em `DECISOES-REGISTRADAS.jsonl`: cada veredicto com data,
rodada e detalhe. Serve de prova do que ele autorizou.

---

## FILA DE GARGALOS — o alvo, em ordem

Ordenado por dinheiro errado e casos atingidos. Os seis primeiros são defeitos
documentados no próprio fluxo; os quatro seguintes são achados da auditoria de
27/08 registrada em `ACHADOS-2026-08-27.md`.

| # | Gargalo | Dano medido | Origem |
|---|---|---|---|
| 1 | Rodapé do PJe ausente → páginas contam 1 → F1 = 0,01 h | **104 de 214 casos** com honorários zerados | bug 3 |
| 2 | Dois layouts de pasta: `00-FLUXO/` × `01-ANALISE/` | **171 casos invisíveis** ao gerador de petição | documentado |
| 3 | Três motores de cálculo divergentes | **R$ 5.075** de diferença na mesma entrada | bug 7 |
| 4 | `modalidade_exame` inalcançável pela CLI | perícia indireta cobra F3 inexistente: **+R$ 2.275** | bug 5 |
| 5 | 30 arquivos com CNJ interno divergente | laudo pode sair com dado de outro processo | bug 2a |
| 6 | Fatores securitários nunca confirmam | apólice nos autos e o fator volta indeterminado | bug 2b |
| 7 | Raiz morta `STEMMIA Dexter` na skill de honorários | os 9 caminhos executáveis não resolvem | achado 27/08 |
| 8 | 11 rotas de skill apontam para nome inexistente | `calculo-honorarios`, `gestao-prazos`, `gerar-laudo`… a etapa morre em silêncio | achado 27/08 |
| 9 | 15 skills `custom` no manifest sem pasta em disco | provavelmente onde as rotas quebradas moram | achado 27/08 |
| 10 | 18 decisões pendentes sem veredicto | critério re-derivado a cada rodada | `DECISOES-PENDENTES-DR-JESUS.md` |
| 11 | `calibracao-log.json` vazio, n = 1 | R$ 350 é âncora sobre um caso, não mediana | documentado |
| 12 | `cli_proposta.py:415` não checa `returncode` | petição pode sair com valor de rodada anterior | bug 6 |

Os gargalos 7, 8 e 9 vêm primeiro na prática: **sem eles resolvidos, nada mais
executa.** Caminho morto não roda.

---

## O QUE FICA SÓ PARA ELE

O plano decide tudo o que é mecânico. Sobra o irredutível:

1. **Valor final.** `A_CONFIRMAR_PELO_PERITO` até declaração expressa. Só
   `LIBERADO_PELO_PERITO` libera protocolo.
2. **Apagar regra.** Nenhuma sai de nenhum banco sem o `s` no portão.
3. **Conclusão clínica e jurídica.**
4. **As 18 decisões pendentes** e as duas que a auditoria levantou:
   degrau do arredondamento, e o que `×1,5` multiplica na F6.
5. **Login e 2FA** dos portais.

---

## COMANDOS, NO MAC

```bash
P=~/Desktop/STEMMIA/_PLANO-FIXACAO     # onde este plano e os scripts ficam

# FASE 1 — descobrir
python3 "$P/fase1_inventariar_regras.py" --json ~/Desktop/INVENTARIO-REGRAS.json

# conferir a raiz e as rotas (auditoria de agosto)
python3 "$P/auditar_caminhos_skills.py" --csv ~/Desktop/auditoria-skills.csv

# FASE 3 — revisar antes de qualquer escrita
python3 "$P/fase3_portao_anuencia.py" PROPOSTAS.json --revisar
```

**Confirmar antes de começar:** `codex` está instalado e autenticado no Mac?
`<pendente>CONFIRMAR `which codex``</pendente>. Sem ele, o passo 4 roda com um
segundo agente Claude em vez do Codex — a revisão cruzada continua, com um
olhar menos independente.

---

## O QUE ESTE PLANO NÃO FAZ

- Não reimplementa a calculadora. A seção 1 do fluxo canônico proíbe variante
  paralela, e já existem três motores divergentes — um quarto pioraria.
- Não decide valor.
- Não apaga nada.
- Não inventa regra quando a arqueologia volta vazia: para e pergunta.
