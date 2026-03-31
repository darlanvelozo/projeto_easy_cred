# EasyCred — Guia de Utilizacao

> Guia pratico do sistema organizado por perfil de usuario.

---

## Credenciais de Acesso (ambiente de demonstracao)

| Usuario | Perfil | Senha | Rota |
|---|---|---|---|
| `darlan` | Admin SaaS | `darlan123` | — |
| `marcos` | Gerente | `marcos123` | — |
| `raimundo` | Vendedor | `raimundo123` | Teresina |
| `chico` | Vendedor | `chico123` | Picos |

Para popular o banco com dados de demonstracao:

```bash
source myenv/bin/activate
python manage.py popular_banco --limpar
```

Para atualizar parcelas vencidas e marcar inadimplencia:

```bash
python manage.py atualizar_parcelas
```

---

## 1. Visao Admin SaaS

**Acesso:** Login com `darlan` / `darlan123`

O Admin e o dono ou gestor principal da empresa. Tem visao completa de toda a operacao.

### Dashboard (`/dashboard/admin/`)

Ao fazer login, o admin e redirecionado automaticamente para seu dashboard.

#### Metricas principais (topo)
- **Carteira Ativa** — Valor total contratado (com juros) de todos os emprestimos ativos
- **A Receber** — Soma das parcelas pendentes e atrasadas
- **Saldo em Caixa** — Saldo consolidado de todos os caixas das rotas
- **Inadimplencia** — Valor total das parcelas em atraso
- **Recebido Hoje** — Total de pagamentos registrados no dia

#### Contadores
- Clientes ativos, Emprestimos ativos, Clientes inadimplentes, Parcelas que vencem hoje

#### Rotas da empresa
Cards com resumo de cada rota: clientes, emprestimos ativos, inadimplentes, saldo do caixa, configuracao.

#### Ultimos emprestimos
Tabela com os 8 emprestimos mais recentes: cliente, vendedor, rota, valor, parcelas, data e status.

#### Inadimplentes
Clientes em atraso: nome, rota, telefone, valor atrasado, parcelas e dias de atraso.

#### Recebimentos hoje
Pagamentos do dia com detalhes de cliente, rota, parcela e valor.

### Navegacao lateral (sidebar)
O admin tem acesso a todos os itens:
- **Dashboard** — Painel principal
- **Rotas** — Lista de rotas com metricas, criar/editar rotas, detalhe de cada rota
- **Clientes** — Lista, cadastro, edicao, detalhe e mapa de clientes
- **Emprestimos** — Lista, novo emprestimo, detalhe com parcelas, cancelamento
- **Caixa** — Saldo por rota, historico de movimentacoes, aportes e retiradas
- **Relatorios** — Inadimplencia, recebimentos do mes, carteira por rota, top inadimplentes
- **Configuracoes** — Editar dados da empresa, configurar rotas (taxa, periodicidade, parcelas, limite, multa, juros)

### Configuracoes

Na pagina de configuracoes o admin pode:

1. **Editar dados da empresa** — nome, CNPJ, e-mail, telefone
2. **Configurar cada rota:**
   - Taxa de juros padrao (%)
   - Periodicidade padrao (diario/semanal/quinzenal/mensal)
   - Numero de parcelas padrao
   - Limite maximo de emprestimo (R$)
   - Multa por atraso (%) — percentual fixo sobre valor da parcela
   - Juros de mora diario (%) — percentual diario sobre valor da parcela
3. **Visualizar equipe** — lista de gerentes e vendedores ativos

As configuracoes de rota sao aplicadas automaticamente ao criar novos emprestimos:
- Campos pre-preenchidos ao selecionar a rota
- Limite maximo validado no formulario e no servidor
- Multa e juros aplicados automaticamente em pagamentos de parcelas atrasadas
- Emprestimos existentes nao sao afetados por mudancas

---

## 2. Visao Gerente

**Acesso:** Login com `marcos` / `marcos123`

O Gerente supervisiona rotas, vendedores e a operacao do dia a dia.

### Dashboard (`/dashboard/gerente/`)

#### Metricas principais
- **Rotas Ativas** — Quantidade de rotas operando
- **Vendedores** — Quantidade de vendedores ativos
- **Clientes Ativos** — Total de clientes com cadastro ativo
- **Inadimplentes** — Clientes com parcelas em atraso

#### Rotas
Cards com resumo de cada rota: clientes, emprestimos ativos, inadimplentes, configuracao e saldo do caixa.

#### Vendedores — Desempenho de hoje
Tabela com cada vendedor: nome, rotas vinculadas, emprestimos ativos e valor coletado hoje.

#### Parcelas nos proximos 7 dias
Parcelas pendentes para os proximos 7 dias: cliente, rota, vencimento, valor e status.

### O que o gerente pode fazer
- Listar, ver detalhe de rotas
- Listar, cadastrar, editar e ver detalhe de clientes
- Ver mapa de clientes
- Listar, criar emprestimos e ver detalhe com parcelas
- Registrar pagamentos (incluindo pagamentos parciais)
- Ver saldo do caixa por rota e historico de movimentacoes
- Realizar aportes no caixa das rotas
- Acessar relatorios

### O que o gerente NAO pode fazer
- Criar ou editar rotas
- Cancelar emprestimos
- Realizar retiradas do caixa
- Acessar configuracoes (exclusivo do admin)

---

## 3. Visao Vendedor

**Acesso:** Login com `raimundo` / `raimundo123` (Teresina) ou `chico` / `chico123` (Picos)

O Vendedor e o trabalhador de campo que percorre as rotas, cadastra clientes, concede emprestimos e coleta pagamentos.

### Dashboard (`/dashboard/vendedor/`)

#### Metricas principais
- **Minha Carteira** — Valor total dos emprestimos ativos do vendedor
- **Parcelas Hoje** — Quantidade e valor das parcelas com vencimento hoje
- **Recebido Hoje** — Valor total coletado no dia
- **Inadimplentes** — Clientes em atraso nas rotas do vendedor

#### Cobrancas de hoje
Parcelas com vencimento hoje: cliente, rota, numero da parcela e valor. Botao **"Registrar Pagamento"** para cada parcela.

#### Clientes inadimplentes
Clientes em atraso: nome, rota, telefone, valor atrasado, parcelas atrasadas e dias de atraso.

#### Minha carteira ativa
Todos os emprestimos ativos do vendedor: cliente, rota, valor da parcela, parcelas restantes e proximo vencimento.

### O que o vendedor pode fazer

#### Clientes
- **Listar** clientes das suas rotas
- **Cadastrar** novos clientes com captura de GPS pelo celular
- **Editar** clientes das suas rotas
- **Ver detalhe** do cliente com historico de emprestimos
- **Ver mapa** dos clientes com localizacao cadastrada

#### Emprestimos
- **Listar** seus emprestimos
- **Criar** emprestimo com formulario simplificado:
  - So ve clientes e rotas vinculadas a ele
  - Taxa, parcelas e periodicidade pre-preenchidos pela configuracao da rota
  - Data do 1o vencimento calculada automaticamente (amanha)
  - Limite maximo da rota validado
  - Saldo do caixa validado
  - Limite de credito do cliente validado
- **Ver detalhe** do emprestimo com lista de parcelas (incluindo valor pago e restante)

#### Pagamentos
- **Registrar pagamento** de parcelas pendentes ou atrasadas
- **Pagamento parcial** — pode pagar valor menor que a parcela
- Ver multa e juros de mora calculados automaticamente para parcelas atrasadas

### O que o vendedor NAO pode fazer
- Ver rotas (pagina de gestao de rotas)
- Cancelar emprestimos
- Acessar caixa, relatorios ou configuracoes
- Ver dados de outros vendedores ou de rotas que nao sao dele
- Definir limite de credito de clientes (campo oculto para vendedor)

---

## Funcionalidades do Sistema

### Mapa de Clientes (`/clientes/mapa/`)
- Visualizacao dos clientes com localizacao no mapa (OpenStreetMap)
- **Markers coloridos por status:**
  - Verde: em dia (emprestimos ativos sem atraso)
  - Amarelo: cobranca hoje (parcelas vencem hoje)
  - Vermelho: inadimplente (parcelas atrasadas)
  - Azul: sem emprestimo ativo
- **Busca flutuante:** filtra clientes em tempo real por nome, telefone, rota ou endereco
- **Filtros rapidos:** chips "Todos", "Cobranca hoje", "Inadimplentes" na base do mapa
- **Filtro por rota:** dropdown com selecao visual
- **Bottom sheet de detalhes:** ao clicar no marker, painel deslizante com:
  - Metricas: emprestimos ativos, valor carteira, parcelas atrasadas
  - Dados: telefone, CPF, endereco completo, valor em atraso
  - Acoes: Perfil, Ligar (link tel:), Navegar (Google Maps com rota)
  - Swipe para baixo para fechar
- **Minha localizacao:** botao GPS mostra posicao do vendedor no mapa
- Vendedor ve apenas clientes das suas rotas

### Cadastro de Cliente com GPS
- No formulario de cliente, botao **"Usar GPS"** captura a localizacao do celular
- Latitude e longitude sao preenchidas automaticamente
- Cliente aparece no mapa apos salvar
- Link **"Abrir no Maps"** no detalhe do cliente

### Limite de Credito por Cliente
- Campo opcional no cadastro do cliente (visivel apenas para admin/gerente)
- Se definido, o sistema valida ao criar emprestimo: soma dos emprestimos ativos + novo <= limite
- Se nao definido, o sistema usa o limite maximo da rota como referencia
- Mensagem clara: "Limite de credito do cliente excedido. Ativos: R$ X / Limite: R$ Y"

### Criacao de Emprestimo
1. Selecionar rota → campos pre-preenchidos pela configuracao (taxa, periodicidade, parcelas)
2. Selecionar cliente e informar valor principal
3. Sistema calcula e exibe previa: valor total com juros e valor da parcela
4. Validacoes automaticas:
   - Valor excede limite da rota? → alerta visual + bloqueio no servidor
   - Saldo do caixa insuficiente? → bloqueio com mensagem de saldo atual
   - Limite de credito do cliente excedido? → bloqueio com detalhamento
5. Ao salvar, o sistema automaticamente:
   - Calcula valor total e valor da parcela
   - Gera todas as parcelas com vencimentos
   - Registra saida no caixa da rota

### Registro de Pagamento
1. No detalhe do emprestimo, clicar **"Pagar"** na parcela
2. Sistema exibe:
   - Resumo da parcela (cliente, valor, vencimento, rota, status)
   - Se ja houve pagamentos parciais: valor ja pago e valor restante
   - Se parcela atrasada: calculo de multa e juros de mora (bloco amarelo)
   - Historico de pagamentos anteriores desta parcela
3. Valor pre-preenchido (com acrescimos se atrasada)
4. Pode informar valor parcial — a parcela so sera marcada como paga quando o total cobrir o valor integral
5. Ao salvar, o sistema automaticamente:
   - Registra entrada no caixa da rota
   - Se total pago >= valor: marca parcela como paga
   - Se era a ultima parcela: marca emprestimo como quitado

### Pagamento Parcial
- Ao registrar pagamento, pode informar qualquer valor > 0
- O sistema rastreia todos os pagamentos de cada parcela
- Na tabela de parcelas do emprestimo, mostra:
  - **Pago**: valor total ja recebido (em verde)
  - **Resta**: valor restante (em amarelo)
- A parcela so vira "paga" quando soma dos pagamentos >= valor da parcela
- Dica no formulario explica o funcionamento

### Multa e Juros de Mora
- Configurados por rota na pagina de Configuracoes:
  - **Multa Atraso (%)**: percentual fixo sobre o valor restante
  - **Juros Mora/Dia (%)**: percentual diario sobre o valor restante
- Ao abrir o formulario de pagamento de parcela atrasada:
  - Calcula automaticamente multa + juros baseado nos dias de atraso
  - Exibe bloco detalhado: valor original, + multa, + juros, = total
  - Pre-preenche o campo valor com o total com acrescimos
- O usuario pode alterar o valor antes de confirmar

### Cancelamento de Emprestimo
1. No detalhe do emprestimo, admin clica **"Cancelar Emprestimo"** (botao vermelho)
2. Tela de confirmacao exibe:
   - Resumo do emprestimo (valor, parcelas, status)
   - Aviso: "Esta acao nao pode ser desfeita"
3. Admin informa motivo obrigatorio
4. Ao confirmar, o sistema:
   - Calcula estorno: valor_principal - total ja pago
   - Registra entrada no caixa (movimentacao tipo "ajuste")
   - Cancela todas as parcelas pendentes/atrasadas
   - Parcelas ja pagas permanecem como "paga"
   - Marca emprestimo como "cancelado"
   - Registra motivo no campo observacao

### Aporte de Capital no Caixa
1. Na pagina de Caixa, clicar **"Aporte"** na rota desejada
2. Informar valor e descricao
3. Ao confirmar:
   - Registra movimentacao de entrada (origem "aporte")
   - Saldo do caixa aumenta
- Disponivel para Admin e Gerente

### Retirada de Capital do Caixa
1. Na pagina de Caixa, clicar **"Retirada"** na rota desejada
2. Informar valor e descricao
3. Ao confirmar:
   - Registra movimentacao de saida (origem "retirada")
   - Saldo do caixa diminui
- Disponivel apenas para Admin

### Gestao de Rotas
- **Criar rota:** Admin acessa Rotas > "Nova Rota", informa nome, descricao e se esta ativa
- **Editar rota:** Na lista de rotas, clicar "Editar" para alterar nome, descricao ou ativar/desativar
- **Configurar rota:** Na pagina de Configuracoes, definir taxa, periodicidade, parcelas, limite, multa e juros
- Disponivel apenas para Admin

### Marcacao Automatica de Inadimplencia
- O command `atualizar_parcelas` deve ser rodado diariamente
- Marca parcelas pendentes com vencimento passado como "atrasada"
- Marca emprestimos ativos com parcelas atrasadas como "inadimplente"
- Pode ser automatizado via cron job:
  ```
  0 6 * * * cd /caminho/systempaytec && /caminho/myenv/bin/python manage.py atualizar_parcelas
  ```

---

## Fluxo Diario de Uso

### Vendedor (campo)
1. **Instalar o app:** abrir o sistema no celular e aceitar "Adicionar a tela inicial" (PWA)
2. Fazer login no celular — navegacao via **bottom tabs** (Painel, Clientes, Emprestimos, Mapa)
3. Consultar **Cobrancas de hoje** no dashboard — usar **Quick Actions** para acoes rapidas
4. Abrir **Mapa** para planejar a rota de visitas:
   - Filtrar por "Cobranca hoje" para ver apenas clientes do dia
   - Tocar no marker para ver detalhes e ligar direto
   - Usar "Navegar" para abrir rota no Google Maps
   - Ativar GPS para se localizar no mapa
5. Em cada cliente:
   - Registrar pagamento das parcelas do dia (total ou parcial)
   - Se novo cliente, cadastrar com GPS (botao **+** flutuante)
   - Se necessario, criar novo emprestimo (botao **+** flutuante)
6. Acompanhar **Recebido Hoje** para controle
7. O app funciona offline para paginas ja visitadas

### Gerente (supervisao)
1. Verificar **desempenho dos vendedores** no dashboard
2. Conferir **parcelas dos proximos 7 dias** para planejar a semana
3. Monitorar **rotas** e identificar problemas (inadimplencia alta, caixa baixo)
4. Realizar **aportes** nas rotas que precisam de capital
5. Acessar **relatorios** para visao mensal

### Admin (gestao)
1. Analisar **indicadores financeiros** no dashboard
2. Verificar **recebimentos do dia**
3. Acompanhar **inadimplentes** e tomar decisoes
4. **Cancelar** emprestimos problematicos quando necessario
5. Realizar **aportes e retiradas** nas rotas
6. Ajustar **configuracoes** das rotas (taxa, limite, multa, juros)
7. **Criar novas rotas** conforme expansao do negocio
8. Consultar **relatorios** para decisoes estrategicas

---

## Isolamento de Dados (Multi-tenant)

O sistema garante que cada empresa ve **apenas seus proprios dados**:
- Usuarios so acessam dados da sua empresa
- Vendedores so veem dados das rotas onde estao vinculados
- Rotas, emprestimos, pagamentos e movimentacoes sao isolados por empresa

---

## Regras de Negocio — Resumo

| Regra | Descricao |
|---|---|
| **Juros simples** | `valor_total = principal x (1 + taxa/100)` |
| **Taxa gravada no contrato** | Mudancas na configuracao da rota nao afetam emprestimos existentes |
| **Caixa via movimentacoes** | Saldo nunca e alterado diretamente — toda alteracao passa por movimentacao financeira |
| **Parcelas automaticas** | Ao criar emprestimo, parcelas sao geradas automaticamente com vencimentos calculados |
| **Saida automatica no caixa** | Ao criar emprestimo, valor principal e debitado do caixa da rota |
| **Entrada automatica no caixa** | Ao registrar pagamento, valor e creditado no caixa da rota |
| **Quitacao automatica** | Ao pagar ultima parcela, emprestimo e marcado como quitado |
| **Limite por rota** | Valor principal nao pode exceder o limite maximo configurado na rota |
| **Limite por cliente** | Soma de emprestimos ativos nao pode exceder limite de credito do cliente |
| **Validacao de saldo** | Caixa da rota deve ter saldo suficiente para conceder emprestimo |
| **Vencimento automatico (vendedor)** | Vendedor nao escolhe data — 1o vencimento e sempre amanha |
| **Config pre-preenche formulario** | Ao selecionar rota, taxa/parcelas/periodicidade sao preenchidos da configuracao |
| **Pagamento parcial** | Aceita valor menor que a parcela; quitacao so quando soma >= valor |
| **Multa e juros automaticos** | Calculados e sugeridos ao pagar parcela atrasada |
| **Cancelamento com estorno** | Admin cancela com motivo; estorno proporcional no caixa |
| **Inadimplencia automatica** | Command diario marca parcelas vencidas e emprestimos com atraso |
| **Aporte e retirada** | Movimentacoes manuais no caixa com rastreabilidade total |
