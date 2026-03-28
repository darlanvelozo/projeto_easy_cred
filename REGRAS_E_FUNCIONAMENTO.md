# EasyCred — Regras de Negocio e Funcionamento do Sistema

> Documento tecnico que explica **o que acontece por tras** de cada acao no sistema: fluxos automaticos, validacoes, permissoes e a cadeia de causa-e-efeito entre as entidades.

---

## 1. Estrutura de Dados (Quem e o que)

### Empresa (Tenant)
- Toda informacao no sistema pertence a uma **Empresa**.
- Usuarios so enxergam dados da propria empresa — isolamento total.

### Usuarios e Perfis
| Perfil | O que pode fazer |
|---|---|
| **Admin** | Tudo: configuracoes, relatorios, CRUD completo, gestao de equipe |
| **Gerente** | Gerencia rotas, clientes, emprestimos, caixa e relatorios |
| **Vendedor** | Opera na rota: cria emprestimos, registra pagamentos, ve seus proprios dados |

### Rota
- Territorio/carteira de clientes.
- Possui uma **ConfiguracaoRota** (taxa de juros, periodicidade, num. parcelas, limite maximo).
- Possui um **CaixaRota** (saldo consolidado da rota).
- Vendedores sao vinculados a rotas via **VendedorRota**.

### Cliente
- Pertence a uma empresa e pode estar vinculado a uma rota.
- Pode ter multiplos emprestimos.
- Possui campos opcionais de `latitude` e `longitude` para visualizacao em mapa.
- A localizacao pode ser capturada pelo GPS do celular do vendedor no momento do cadastro.

### Emprestimo
- Contrato entre o sistema e um cliente, operado por um vendedor em uma rota.
- Grava a taxa de juros **no momento da criacao** (imutavel — mudancas futuras na config da rota nao afetam contratos existentes).
- Status: `ativo`, `quitado`, `inadimplente`, `cancelado`.

### Parcela
- Divisao do emprestimo em pagamentos periodicos.
- Status: `pendente`, `paga`, `atrasada`.

### Pagamento
- Registro de um valor recebido referente a uma parcela.

### MovimentacaoFinanceira
- Registro de toda entrada ou saida no caixa da rota.
- **Unica porta de alteracao do saldo** — o saldo nunca e alterado diretamente.

---

## 2. Fluxos Automaticos (O que leva ao que)

### 2.1 Criar Emprestimo

```
Usuario preenche formulario
        |
        v
[Validacao do Formulario]
   - Valor principal <= limite maximo da rota? (se configurado)
   - Todos os campos obrigatorios preenchidos?
        |
        v
[Model.save()] — Calculo automatico:
   valor_total = valor_principal * (1 + taxa_juros / 100)
   valor_parcela = valor_total / num_parcelas
        |
        v
[Signal post_save: gerar_parcelas]
   - Cria N parcelas automaticamente
   - Cada parcela com vencimento calculado pela periodicidade:
     - diario: +1 dia por parcela
     - semanal: +7 dias por parcela
     - quinzenal: +15 dias por parcela
     - mensal: +1 mes por parcela
   - Todas comecam com status "pendente"
        |
        v
[Signal post_save: registrar_saida_caixa]
   - Busca (ou cria) o CaixaRota da rota
   - Registra MovimentacaoFinanceira tipo "saida", origem "emprestimo"
   - Grava saldo_anterior e saldo_posterior
   - Atualiza o saldo do CaixaRota (saldo -= valor_principal)
```

**Resultado:** 1 emprestimo + N parcelas + 1 movimentacao de saida no caixa.

---

### 2.2 Registrar Pagamento

```
Usuario clica "Pagar" em uma parcela
        |
        v
[Validacao]
   - Parcela ja esta paga? Se sim, bloqueia.
        |
        v
[Pagamento.save()] — Grava valor, forma, quem recebeu
        |
        v
[Signal post_save: registrar_entrada_caixa]
   - Busca o CaixaRota da rota (via parcela -> emprestimo -> rota)
   - Registra MovimentacaoFinanceira tipo "entrada", origem "pagamento"
   - Grava saldo_anterior e saldo_posterior
   - Atualiza saldo do CaixaRota (saldo += valor do pagamento)
        |
        v
[View: atualiza parcela]
   - Marca parcela como "paga"
   - Registra data/hora do pagamento (pago_em)
        |
        v
[View: verifica quitacao]
   - Conta parcelas restantes (nao pagas) do emprestimo
   - Se ZERO parcelas pendentes:
       emprestimo.status = "quitado"
```

**Resultado:** 1 pagamento + 1 movimentacao de entrada no caixa + parcela paga + (possivelmente) emprestimo quitado.

---

### 2.3 Selecionar Rota no Formulario de Emprestimo

```
Usuario seleciona uma rota no dropdown
        |
        v
[JavaScript: requisicao AJAX]
   - Busca GET /api/config-rota/{id}/
   - Servidor retorna JSON com a ConfiguracaoRota da rota
        |
        v
[Preenchimento automatico dos campos]
   - Taxa de Juros <- taxa_juros_padrao
   - Periodicidade <- periodicidade_padrao
   - Num. Parcelas <- num_parcelas_padrao
   - Exibe badge com info da config e limite maximo
        |
        v
[Validacao em tempo real]
   - Se valor_principal > limite_max: exibe alerta visual
   - No envio do formulario: validacao server-side bloqueia a criacao
```

**Resultado:** campos pre-preenchidos + alerta visual de limite + validacao no servidor.

---

### 2.4 Vendedor Cria Emprestimo (formulario simplificado)

```
Vendedor preenche formulario
        |
        v
[Campos automaticos]
   - Vendedor: preenchido automaticamente (campo oculto)
   - Rotas: filtradas — so aparecem as rotas do vendedor
   - Clientes: filtrados — so clientes das rotas do vendedor
   - Data 1o vencimento: calculada automaticamente = amanha
        |
        v
[Vendedor escolhe apenas]
   - Cliente, Rota, Valor, Periodicidade
   - Taxa e parcelas vem pre-preenchidas da config da rota
        |
        v
[Validacao + criacao]
   - Mesma cadeia do fluxo 2.1 (calculo, parcelas, caixa)
```

**Resultado:** vendedor tem interface simplificada, sem precisar definir datas.

---

### 2.5 Mapa de Clientes

```
Usuario acessa /clientes/mapa/
        |
        v
[Filtro por rota]
   - Admin/Gerente: veem todas as rotas
   - Vendedor: veem apenas suas rotas
        |
        v
[Busca clientes com lat/lng]
   - Filtra: ativo=True, latitude e longitude preenchidos
   - Serializa em JSON para o frontend
        |
        v
[Leaflet (OpenStreetMap)]
   - Renderiza mapa com marcadores para cada cliente
   - Popup: nome, rota, telefone, endereco, link para detalhe
   - Mapa centralizado e com zoom ajustado aos marcadores
```

**Resultado:** visualizacao geografica dos clientes da rota.

---

### 2.6 Captura de GPS no Cadastro de Cliente

```
Vendedor clica "Usar GPS" no formulario de cliente
        |
        v
[navigator.geolocation.getCurrentPosition]
   - Solicita permissao do navegador
   - Usa alta precisao (enableHighAccuracy: true)
        |
        v
[Preenche campos]
   - latitude <- coords.latitude (7 casas decimais)
   - longitude <- coords.longitude (7 casas decimais)
        |
        v
[Salvo com o cliente]
   - Os campos lat/lng sao persistidos no banco
   - Cliente aparece no mapa automaticamente
```

**Resultado:** localizacao do cliente capturada no campo pelo vendedor.

---

### 2.7 Salvar Configuracao da Rota

```
Admin edita campos na pagina de Configuracoes
        |
        v
[POST: salvar_config_{rota_id}]
   - Cria ou atualiza a ConfiguracaoRota da rota
   - Valores salvos: taxa_juros_padrao, periodicidade_padrao,
     num_parcelas_padrao, limite_emprestimo_max
        |
        v
[Efeito no sistema]
   - Proximos emprestimos criados nessa rota usarao esses valores como padrao
   - Limite maximo sera validado na criacao de novos emprestimos
   - Emprestimos existentes NAO sao afetados
```

---

### 2.8 Login e Redirecionamento

```
Usuario faz login
        |
        v
[Verificacao]
   - Usuario ativo? Se nao, bloqueia com mensagem
   - Credenciais validas? Se nao, mensagem de erro
        |
        v
[Redirecionamento por perfil]
   - superuser  -> /admin/ (Django Admin)
   - admin      -> Dashboard Admin (visao completa da empresa)
   - gerente    -> Dashboard Gerente (rotas, vendedores, parcelas proximas)
   - vendedor   -> Dashboard Vendedor (minha carteira, cobranças do dia)
```

---

## 3. Regras de Permissao (Quem pode o que)

O sistema usa o decorator `@requer_perfil()` em cada view. Superusers sempre passam.

| Funcionalidade | Admin | Gerente | Vendedor |
|---|:---:|:---:|:---:|
| Dashboard proprio | Sim | Sim | Sim |
| Listar rotas | Sim | Sim | - |
| Detalhe da rota | Sim | Sim | - |
| Listar clientes | Sim | Sim | Sim* |
| Criar/editar cliente | Sim | Sim | Sim* |
| Detalhe do cliente | Sim | Sim | Sim* |
| Mapa de clientes | Sim | Sim | Sim* |
| Listar emprestimos | Sim | Sim | Sim* |
| Criar emprestimo | Sim | Sim | Sim** |
| Detalhe emprestimo | Sim | Sim | Sim* |
| Registrar pagamento | Sim | Sim | Sim |
| Caixa (saldos) | Sim | Sim | - |
| Movimentacoes do caixa | Sim | Sim | - |
| Relatorios | Sim | Sim | - |
| Configuracoes (editar) | Sim | - | - |

**\* Vendedor so ve/edita dados das rotas onde esta vinculado e emprestimos que ele proprio criou.**

**\*\* Vendedor cria emprestimo com restricoes: nao escolhe data de vencimento (auto-calcula para amanha), so ve clientes e rotas dele.**

### Isolamento do Vendedor
- **Clientes:** ve e edita apenas clientes das rotas onde esta vinculado.
- **Emprestimos:** ve apenas emprestimos onde ele e o vendedor.
- **Rotas:** no formulario de emprestimo e cliente, so aparecem as rotas dele.
- **Mapa:** ve apenas clientes das suas rotas com localizacao cadastrada.
- **Dashboard:** metricas pessoais (minha carteira, cobranças do dia, meus inadimplentes).
- **Formulario de emprestimo:** data do 1o vencimento e calculada automaticamente (amanha).

---

## 4. Regras de Calculo

### Juros Simples
```
valor_total = valor_principal * (1 + taxa_juros / 100)
valor_parcela = valor_total / num_parcelas
```

A taxa e **gravada no contrato** — se a configuracao da rota mudar depois, contratos existentes mantem o valor original.

### Vencimentos das Parcelas
A partir da `data_primeiro_vencimento`, cada parcela seguinte e calculada:

| Periodicidade | Incremento |
|---|---|
| Diario | +1 dia |
| Semanal | +7 dias |
| Quinzenal | +15 dias |
| Mensal | +1 mes (usa `relativedelta`) |

Exemplo: emprestimo de 4 parcelas semanais com 1o vencimento em 01/04:
- Parcela 1: 01/04
- Parcela 2: 08/04
- Parcela 3: 15/04
- Parcela 4: 22/04

### Limite de Emprestimo
- Configuravel por rota no campo `limite_emprestimo_max`.
- Se definido, o `valor_principal` nao pode ultrapassar esse valor.
- Validado no frontend (alerta visual) e no backend (rejeita o formulario).
- Se nao definido, nao ha limite.

---

## 5. Rastreabilidade Financeira

### Principio
> O saldo do `CaixaRota` **nunca e alterado diretamente**. Toda alteracao passa por uma `MovimentacaoFinanceira`.

Isso garante:
- **Historico completo**: toda entrada e saida tem registro com data, valor, responsavel e contexto.
- **Reconstrucao**: e possivel recalcular o saldo somando todas as movimentacoes.
- **Auditoria**: cada movimentacao grava `saldo_anterior` e `saldo_posterior`.

### Tipos de Movimentacao
| Tipo | Origem | Quando acontece |
|---|---|---|
| Saida | `emprestimo` | Ao criar um emprestimo (valor_principal sai do caixa) |
| Entrada | `pagamento` | Ao registrar pagamento de parcela (valor entra no caixa) |
| Entrada | `aporte` | Aporte de capital inicial na rota |
| Saida | `retirada` | Retirada de dinheiro do caixa |
| Entrada/Saida | `ajuste` | Ajuste manual pelo admin |

### Cadeia de Rastreio
```
Pagamento
   |-- referencia_pagamento --> MovimentacaoFinanceira
   |-- parcela --> Parcela
                      |-- emprestimo --> Emprestimo
                                            |-- cliente --> Cliente
                                            |-- rota --> Rota --> CaixaRota
                                            |-- vendedor --> Usuario
```

Ou seja: dado qualquer movimentacao, e possivel rastrear ate o cliente, vendedor e rota de origem.

---

## 6. Ciclo de Vida do Emprestimo

```
                    [ATIVO]
                   /       \
                  /         \
    Todas parcelas      Parcelas vencem
    pagas               sem pagamento
         |                    |
         v                    v
     [QUITADO]         [INADIMPLENTE]
                              |
                              v
                       [CANCELADO]
                    (acao manual do admin)
```

| Transicao | Gatilho |
|---|---|
| Ativo -> Quitado | Automatico: ao pagar a ultima parcela, a view verifica se restam pendentes. Se zero, marca como quitado. |
| Ativo -> Inadimplente | Manual/batch: quando parcelas vencem sem pagamento (parcela.status muda para "atrasada"). |
| Qualquer -> Cancelado | Acao manual do admin. |

---

## 7. Ciclo de Vida da Parcela

```
    [PENDENTE]
     /      \
    /        \
  Pagamento   Vencimento passa
  registrado   sem pagamento
     |              |
     v              v
   [PAGA]      [ATRASADA]
                    |
                  Pagamento
                  registrado
                    |
                    v
                  [PAGA]
```

| Transicao | Gatilho |
|---|---|
| Pendente -> Paga | Pagamento registrado na view `registrar_pagamento` |
| Pendente -> Atrasada | Data de vencimento ultrapassada (processo batch ou verificacao manual) |
| Atrasada -> Paga | Pagamento registrado mesmo apos vencimento |

---

## 8. Resumo: O Que e Automatico vs Manual

### Automatico (o sistema faz sozinho)
| Acao | Gatilho |
|---|---|
| Calcular valor_total e valor_parcela | Ao salvar o emprestimo (`Model.save()`) |
| Gerar todas as parcelas | Ao criar emprestimo (signal `gerar_parcelas`) |
| Registrar saida no caixa | Ao criar emprestimo (signal `registrar_saida_caixa`) |
| Registrar entrada no caixa | Ao registrar pagamento (signal `registrar_entrada_caixa`) |
| Marcar parcela como paga | Ao registrar pagamento (view `registrar_pagamento`) |
| Marcar emprestimo como quitado | Ao pagar ultima parcela (view `registrar_pagamento`) |
| Pre-preencher formulario com config da rota | Ao selecionar rota (AJAX no frontend) |
| Validar limite maximo da rota | Ao submeter formulario (backend + frontend) |
| Redirecionar para dashboard correto | Ao fazer login (view `dashboard_redirect`) |
| Bloquear acesso por perfil | Em toda requisicao (decorator `@requer_perfil`) |
| Filtrar dados por empresa | Em toda view (queryset filtrado por `empresa`) |
| Filtrar dados do vendedor | Nas views de emprestimo e cliente (ve so os seus) |
| Calcular data 1o vencimento (vendedor) | Ao submeter formulario de emprestimo como vendedor (= amanha) |
| Captura GPS do cliente | Ao clicar "Usar GPS" no formulario (navigator.geolocation) |

### Manual (usuario precisa fazer)
| Acao | Quem faz |
|---|---|
| Cadastrar empresa e rotas | Admin |
| Cadastrar clientes | Admin, Gerente ou Vendedor |
| Definir configuracao da rota | Admin (pagina de Configuracoes) |
| Vincular vendedores a rotas | Admin (via Django Admin) |
| Criar emprestimos | Admin, Gerente ou Vendedor |
| Registrar pagamentos | Admin, Gerente ou Vendedor |
| Marcar emprestimo como inadimplente | Admin ou Gerente |
| Cancelar emprestimo | Admin |
| Aportar capital no caixa | Admin (via Django Admin) |
