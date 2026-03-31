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
| **Admin** | Tudo: configuracoes, relatorios, CRUD completo, gestao de equipe, cancelamentos, retiradas |
| **Gerente** | Gerencia rotas, clientes, emprestimos, caixa (aportes) e relatorios |
| **Vendedor** | Opera na rota: cria emprestimos, registra pagamentos, ve seus proprios dados |

### Rota
- Territorio/carteira de clientes.
- Possui uma **ConfiguracaoRota** (taxa de juros, periodicidade, num. parcelas, limite maximo, multa, juros de mora).
- Possui um **CaixaRota** (saldo consolidado da rota).
- Vendedores sao vinculados a rotas via **VendedorRota**.

### Cliente
- Pertence a uma empresa e pode estar vinculado a uma rota.
- Pode ter multiplos emprestimos.
- Possui campos opcionais de `latitude` e `longitude` para visualizacao em mapa.
- Possui campo opcional `limite_credito` para controle individual de credito.
- A localizacao pode ser capturada pelo GPS do celular do vendedor no momento do cadastro.

### Emprestimo
- Contrato entre o sistema e um cliente, operado por um vendedor em uma rota.
- Grava a taxa de juros **no momento da criacao** (imutavel — mudancas futuras na config da rota nao afetam contratos existentes).
- Status: `ativo`, `quitado`, `inadimplente`, `cancelado`.

### Parcela
- Divisao do emprestimo em pagamentos periodicos.
- Status: `pendente`, `paga`, `atrasada`, `cancelada`.
- Pode receber multiplos pagamentos parciais — so vira "paga" quando a soma dos pagamentos >= valor.

### Pagamento
- Registro de um valor recebido referente a uma parcela.
- Uma parcela pode ter multiplos pagamentos (pagamentos parciais).

### MovimentacaoFinanceira
- Registro de toda entrada ou saida no caixa da rota.
- **Unica porta de alteracao do saldo** — o saldo nunca e alterado diretamente.
- Origens: `pagamento`, `emprestimo`, `aporte`, `retirada`, `ajuste`.

---

## 2. Fluxos Automaticos (O que leva ao que)

### 2.1 Criar Emprestimo

```
Usuario preenche formulario
        |
        v
[Validacao do Formulario]
   - Valor principal <= limite maximo da rota? (se configurado)
   - Saldo do caixa >= valor principal? (se nao, bloqueia)
   - Limite de credito do cliente nao ultrapassado?
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

**Validacoes que impedem a criacao:**
- Caixa insuficiente: "Caixa da rota insuficiente. Saldo: R$ X"
- Limite da rota excedido: "Valor excede o limite da rota: maximo R$ X"
- Limite de credito do cliente excedido: "Limite de credito do cliente excedido. Ativos: R$ X / Limite: R$ Y"

---

### 2.2 Registrar Pagamento (com suporte a pagamento parcial)

```
Usuario clica "Pagar" em uma parcela
        |
        v
[Calculo de valores]
   - Soma pagamentos anteriores desta parcela (total_pago)
   - Calcula valor_restante = valor - total_pago
   - Se parcela esta atrasada:
     - Calcula multa: valor_restante * multa_atraso / 100
     - Calcula juros mora: valor_restante * juros_mora_dia / 100 * dias_atraso
     - Sugere valor com acrescimos
        |
        v
[Validacao]
   - Parcela ja esta paga ou cancelada? Se sim, bloqueia.
   - Valor recebido > 0?
        |
        v
[Pagamento.save()] — Grava valor, forma, quem recebeu
        |
        v
[Signal post_save: registrar_entrada_caixa]
   - Registra MovimentacaoFinanceira tipo "entrada", origem "pagamento"
   - Atualiza saldo do CaixaRota (saldo += valor do pagamento)
        |
        v
[View: verifica se parcela foi totalmente paga]
   - novo_total_pago = total_pago + valor_recebido
   - Se novo_total_pago >= valor da parcela:
       Marca parcela como "paga" + registra pago_em
   - Se nao: parcela continua "pendente" ou "atrasada"
        |
        v
[View: verifica quitacao do emprestimo]
   - Conta parcelas restantes (nao pagas e nao canceladas)
   - Se ZERO parcelas pendentes:
       emprestimo.status = "quitado"
```

**Resultado:** 1 pagamento + 1 movimentacao de entrada no caixa + (possivelmente) parcela paga + (possivelmente) emprestimo quitado.

---

### 2.3 Pagamento Parcial

```
Exemplo: Parcela de R$ 100,00

Pagamento 1: R$ 40,00
   -> total_pago = 40, valor_restante = 60
   -> parcela continua "pendente" (ou "atrasada")
   -> entrada de R$ 40 no caixa

Pagamento 2: R$ 35,00
   -> total_pago = 75, valor_restante = 25
   -> parcela continua "pendente"
   -> entrada de R$ 35 no caixa

Pagamento 3: R$ 25,00
   -> total_pago = 100, valor_restante = 0
   -> parcela marcada como "paga"
   -> entrada de R$ 25 no caixa
```

- Historico de todos os pagamentos parciais e visivel no formulario de pagamento e no detalhe do emprestimo.
- A coluna "Pago" na tabela de parcelas mostra o total ja recebido e o valor restante.

---

### 2.4 Multa e Juros de Mora

```
Parcela atrasada (vencimento < hoje)
        |
        v
[Calculo automatico no formulario de pagamento]
   - dias_atraso = hoje - vencimento
   - multa = valor_restante * multa_atraso% (configurado na rota)
   - juros = valor_restante * juros_mora_dia% * dias_atraso
   - valor_sugerido = valor_restante + multa + juros
        |
        v
[Exibicao no formulario]
   - Mostra bloco amarelo com detalhamento:
     - Valor original restante
     - + Multa (X%)
     - + Juros de mora (Y% x Z dias)
     - = Total com acrescimos
   - Campo "valor" pre-preenchido com total + acrescimos
```

**Configuracao:** campos `multa_atraso` e `juros_mora_dia` na ConfiguracaoRota, editaveis na pagina de Configuracoes pelo admin.

**Importante:** os acrescimos sao **sugestivos** — o valor pre-preenche o campo, mas o usuario pode alterar. O valor efetivamente recebido e o que o usuario digitar.

---

### 2.5 Cancelamento de Emprestimo

```
Admin clica "Cancelar Emprestimo" no detalhe
        |
        v
[Tela de confirmacao]
   - Exibe resumo do emprestimo
   - Campo obrigatorio: motivo do cancelamento
   - Aviso: "Esta acao nao pode ser desfeita"
        |
        v
[Calculo do estorno]
   - total_pago = soma de todos os pagamentos do emprestimo
   - valor_estorno = valor_principal - total_pago
   - Se total_pago > valor_principal: estorno = 0
        |
        v
[Estorno no caixa] (se valor_estorno > 0)
   - Registra MovimentacaoFinanceira tipo "entrada", origem "ajuste"
   - Descricao: "Cancelamento emprestimo #X — motivo"
   - Atualiza saldo do CaixaRota
        |
        v
[Cancelar parcelas]
   - Todas as parcelas com status "pendente" ou "atrasada"
     sao marcadas como "cancelada"
   - Parcelas ja pagas permanecem como "paga"
        |
        v
[Marcar emprestimo]
   - emprestimo.status = "cancelado"
   - Motivo adicionado ao campo observacao
```

**Resultado:** emprestimo cancelado + parcelas pendentes canceladas + estorno parcial no caixa.

**Permissao:** somente Admin pode cancelar emprestimos.

---

### 2.6 Aporte de Capital no Caixa

```
Admin ou Gerente acessa Caixa > Aporte
        |
        v
[Formulario]
   - Valor do aporte (obrigatorio, > 0)
   - Descricao (obrigatorio)
        |
        v
[Registrar movimentacao]
   - MovimentacaoFinanceira tipo "entrada", origem "aporte"
   - saldo_posterior = saldo_anterior + valor
   - Atualiza CaixaRota.saldo
```

**Resultado:** saldo do caixa aumenta + movimentacao registrada.

---

### 2.7 Retirada de Capital do Caixa

```
Admin acessa Caixa > Retirada
        |
        v
[Formulario]
   - Valor da retirada (obrigatorio, > 0)
   - Descricao (obrigatorio)
        |
        v
[Registrar movimentacao]
   - MovimentacaoFinanceira tipo "saida", origem "retirada"
   - saldo_posterior = saldo_anterior - valor
   - Atualiza CaixaRota.saldo
```

**Resultado:** saldo do caixa diminui + movimentacao registrada.

**Permissao:** somente Admin pode fazer retiradas.

---

### 2.8 Marcacao Automatica de Inadimplencia

```
Management command: python manage.py atualizar_parcelas
        |
        v
[Etapa 1: Parcelas atrasadas]
   - Busca todas as parcelas com status="pendente"
     e vencimento < hoje
   - Marca como status="atrasada"
        |
        v
[Etapa 2: Emprestimos inadimplentes]
   - Busca emprestimos com status="ativo"
     que possuem parcelas com status="atrasada"
   - Marca como status="inadimplente"
```

**Execucao:** deve ser rodado diariamente (via cron job ou task scheduler).

Exemplo de cron para rodar todo dia as 6h:
```
0 6 * * * cd /caminho/systempaytec && /caminho/myenv/bin/python manage.py atualizar_parcelas
```

---

### 2.9 Selecionar Rota no Formulario de Emprestimo

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

### 2.10 Vendedor Cria Emprestimo (formulario simplificado)

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
   - Inclui validacao de saldo e limite de credito
```

**Resultado:** vendedor tem interface simplificada, sem precisar definir datas.

---

### 2.11 Mapa de Clientes

```
Usuario acessa /clientes/mapa/
        |
        v
[Filtro por rota]
   - Admin/Gerente: veem todas as rotas
   - Vendedor: veem apenas suas rotas
        |
        v
[Busca clientes com lat/lng + dados financeiros]
   - Filtra: ativo=True, latitude e longitude preenchidos
   - Pre-computa via annotate (sem N+1):
     - emprestimos_ativos e valor_carteira por cliente
     - parcelas_atrasadas e valor_atrasado por cliente
     - parcelas_hoje e valor_hoje por cliente
   - Serializa em JSON para o frontend
        |
        v
[Leaflet (OpenStreetMap) — mapa interativo]
   - Markers coloridos por status:
     - Verde: em dia | Amarelo: cobranca hoje
     - Vermelho: inadimplente | Azul: sem emprestimo
   - Busca flutuante: filtra markers em tempo real
   - Filtros rapidos: chips "Todos", "Cobranca hoje", "Inadimplentes"
   - Bottom sheet ao clicar: metricas, dados, acoes (perfil, ligar, navegar)
   - GPS: botao "Minha localizacao" para vendedor se localizar
   - Swipe-to-dismiss no bottom sheet
```

---

### 2.12 Captura de GPS no Cadastro de Cliente

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

---

### 2.13 Salvar Configuracao da Rota

```
Admin edita campos na pagina de Configuracoes
        |
        v
[POST: salvar_config_{rota_id}]
   - Cria ou atualiza a ConfiguracaoRota da rota
   - Valores salvos: taxa_juros_padrao, periodicidade_padrao,
     num_parcelas_padrao, limite_emprestimo_max,
     multa_atraso, juros_mora_dia
        |
        v
[Efeito no sistema]
   - Proximos emprestimos criados nessa rota usarao esses valores como padrao
   - Limite maximo sera validado na criacao de novos emprestimos
   - Multa e juros serao aplicados em pagamentos de parcelas atrasadas
   - Emprestimos existentes NAO sao afetados
```

---

### 2.14 CRUD de Rotas

```
Admin acessa Rotas > Nova Rota
        |
        v
[Formulario]
   - Nome (obrigatorio)
   - Descricao (opcional)
   - Ativa (checkbox)
        |
        v
[Salvar]
   - Cria a Rota vinculada a empresa do admin
   - Redireciona para detalhe da rota
   - A ConfiguracaoRota pode ser definida na pagina de Configuracoes
```

Admin tambem pode editar rotas existentes (nome, descricao, ativar/desativar).

---

### 2.15 Login e Redirecionamento

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
   - vendedor   -> Dashboard Vendedor (minha carteira, cobrancas do dia)
```

---

## 3. Regras de Permissao (Quem pode o que)

O sistema usa o decorator `@requer_perfil()` em cada view. Superusers sempre passam.

| Funcionalidade | Admin | Gerente | Vendedor |
|---|:---:|:---:|:---:|
| Dashboard proprio | Sim | Sim | Sim |
| Listar rotas | Sim | Sim | - |
| Criar/editar rota | Sim | - | - |
| Detalhe da rota | Sim | Sim | - |
| Listar clientes | Sim | Sim | Sim* |
| Criar/editar cliente | Sim | Sim | Sim* |
| Detalhe do cliente | Sim | Sim | Sim* |
| Mapa de clientes | Sim | Sim | Sim* |
| Listar emprestimos | Sim | Sim | Sim* |
| Criar emprestimo | Sim | Sim | Sim** |
| Detalhe emprestimo | Sim | Sim | Sim* |
| Cancelar emprestimo | Sim | - | - |
| Registrar pagamento | Sim | Sim | Sim |
| Caixa (saldos) | Sim | Sim | - |
| Movimentacoes do caixa | Sim | Sim | - |
| Aporte no caixa | Sim | Sim | - |
| Retirada do caixa | Sim | - | - |
| Relatorios | Sim | Sim | - |
| Configuracoes (editar) | Sim | - | - |

**\* Vendedor so ve/edita dados das rotas onde esta vinculado e emprestimos que ele proprio criou.**

**\*\* Vendedor cria emprestimo com restricoes: nao escolhe data de vencimento (auto-calcula para amanha), so ve clientes e rotas dele.**

### Isolamento do Vendedor
- **Clientes:** ve e edita apenas clientes das rotas onde esta vinculado.
- **Emprestimos:** ve apenas emprestimos onde ele e o vendedor.
- **Rotas:** no formulario de emprestimo e cliente, so aparecem as rotas dele.
- **Mapa:** ve apenas clientes das suas rotas com localizacao cadastrada.
- **Dashboard:** metricas pessoais (minha carteira, cobrancas do dia, meus inadimplentes).
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

### Multa e Juros de Mora
Aplicados automaticamente ao pagar parcela atrasada:
```
dias_atraso = hoje - data_vencimento
multa = valor_restante * (multa_atraso / 100)
juros = valor_restante * (juros_mora_dia / 100) * dias_atraso
total_com_acrescimos = valor_restante + multa + juros
```

- `multa_atraso`: percentual fixo sobre o valor restante (ex: 2%)
- `juros_mora_dia`: percentual diario sobre o valor restante (ex: 0.033%)
- Configurados por rota na pagina de Configuracoes
- O valor sugerido e pre-preenchido no formulario, mas o usuario pode alterar

### Limite de Emprestimo
Validado em 3 niveis ao criar emprestimo:
1. **Limite da rota** (`limite_emprestimo_max`): valor principal nao pode ultrapassar
2. **Limite de credito do cliente** (`limite_credito`): soma de emprestimos ativos + novo <= limite
3. **Saldo do caixa**: caixa deve ter saldo >= valor principal

Ordem de prioridade para limite de credito:
- Se o cliente tem `limite_credito` definido, usa esse
- Se nao, usa o `limite_emprestimo_max` da rota
- Se nenhum esta definido, nao ha limite

### Validacao de Saldo no Caixa
Ao criar emprestimo:
```
Se caixa.saldo < valor_principal:
   BLOQUEIA — "Caixa da rota insuficiente. Saldo: R$ X"

Se a rota nao tem caixa:
   BLOQUEIA — "Esta rota ainda nao possui caixa. Realize um aporte primeiro."
```

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
| Entrada | `aporte` | Ao realizar aporte de capital na rota |
| Saida | `retirada` | Ao realizar retirada de dinheiro do caixa |
| Entrada | `ajuste` | Ao cancelar emprestimo (estorno) |
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
                         /         \
                        /           \
              Todas parcelas    Admin cancela
              restantes pagas   com motivo
                    |                |
                    v                v
               [QUITADO]       [CANCELADO]
                              (estorno no caixa)
```

| Transicao | Gatilho |
|---|---|
| Ativo -> Quitado | Automatico: ao pagar a ultima parcela, a view verifica se restam pendentes. Se zero, marca como quitado. |
| Ativo -> Inadimplente | Automatico: command `atualizar_parcelas` marca parcelas vencidas como atrasadas e emprestimos com atraso como inadimplentes. |
| Inadimplente -> Quitado | Automatico: se todas as parcelas restantes forem pagas (via pagamentos posteriores). |
| Ativo/Inadimplente -> Cancelado | Manual: admin cancela com motivo obrigatorio. Estorno proporcional no caixa. |

---

## 7. Ciclo de Vida da Parcela

```
    [PENDENTE]
     /   |    \
    /    |     \
  Pago   |   Vencimento
  total  |   passa sem pgto
   |     |        |
   v     |        v
 [PAGA]  |   [ATRASADA]
         |    /      \
    Pago |   /      Pago
  parcial|  Pago     total
         |  parcial    |
         v    |        v
   (continua  |     [PAGA]
   pendente/  |
   atrasada)  v
         (continua
          atrasada)

   [CANCELADA] <-- emprestimo cancelado
```

| Transicao | Gatilho |
|---|---|
| Pendente -> Paga | Soma dos pagamentos >= valor da parcela |
| Pendente -> Atrasada | Command `atualizar_parcelas` (vencimento < hoje) |
| Atrasada -> Paga | Soma dos pagamentos >= valor da parcela |
| Pendente/Atrasada -> Cancelada | Emprestimo cancelado pelo admin |

**Pagamento parcial:** a parcela so muda de status quando a soma de todos os pagamentos cobre o valor integral. Ate la, continua com seu status atual.

---

## 8. Resumo: O Que e Automatico vs Manual

### Automatico (o sistema faz sozinho)
| Acao | Gatilho |
|---|---|
| Calcular valor_total e valor_parcela | Ao salvar o emprestimo (`Model.save()`) |
| Gerar todas as parcelas | Ao criar emprestimo (signal `gerar_parcelas`) |
| Registrar saida no caixa | Ao criar emprestimo (signal `registrar_saida_caixa`) |
| Registrar entrada no caixa | Ao registrar pagamento (signal `registrar_entrada_caixa`) |
| Marcar parcela como paga | Quando soma de pagamentos >= valor (view `registrar_pagamento`) |
| Marcar emprestimo como quitado | Quando todas as parcelas estao pagas ou canceladas (view `registrar_pagamento`) |
| Calcular multa e juros de mora | Ao abrir formulario de pagamento de parcela atrasada |
| Validar saldo do caixa | Ao criar emprestimo (form `clean()`) |
| Validar limite de credito do cliente | Ao criar emprestimo (form `clean()`) |
| Estorno no caixa ao cancelar | Ao cancelar emprestimo (view `emprestimo_cancelar`) |
| Cancelar parcelas pendentes | Ao cancelar emprestimo (view `emprestimo_cancelar`) |
| Marcar parcelas vencidas como atrasadas | Command `atualizar_parcelas` (roda diariamente) |
| Marcar emprestimos com atraso como inadimplentes | Command `atualizar_parcelas` (roda diariamente) |
| Pre-preencher formulario com config da rota | Ao selecionar rota (AJAX no frontend) |
| Validar limite maximo da rota | Ao submeter formulario (backend + frontend) |
| Redirecionar para dashboard correto | Ao fazer login (view `dashboard_redirect`) |
| Bloquear acesso por perfil | Em toda requisicao (decorator `@requer_perfil`) |
| Filtrar dados por empresa | Em toda view (queryset filtrado por `empresa`) |
| Filtrar dados do vendedor | Nas views de emprestimo e cliente (ve so os seus) |
| Calcular data 1o vencimento (vendedor) | Ao submeter formulario como vendedor (= amanha) |
| Captura GPS do cliente | Ao clicar "Usar GPS" (navigator.geolocation) |

### Manual (usuario precisa fazer)
| Acao | Quem faz |
|---|---|
| Cadastrar empresa | Admin |
| Criar e editar rotas | Admin |
| Cadastrar clientes | Admin, Gerente ou Vendedor |
| Definir configuracao da rota (taxa, parcelas, limite, multa, juros) | Admin (Configuracoes) |
| Vincular vendedores a rotas | Admin (via Django Admin) |
| Criar emprestimos | Admin, Gerente ou Vendedor |
| Registrar pagamentos | Admin, Gerente ou Vendedor |
| Cancelar emprestimo (com motivo) | Admin |
| Realizar aporte no caixa | Admin ou Gerente |
| Realizar retirada do caixa | Admin |
| Rodar atualizacao de inadimplencia | Cron job ou manual (`python manage.py atualizar_parcelas`) |
