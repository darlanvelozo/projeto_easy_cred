# SystemPay.tec — Guia de Utilização

> Guia prático do sistema organizado por perfil de usuário.

---

## Credenciais de Acesso (ambiente de demonstração)

| Usuário | Perfil | Senha | Empresa |
|---|---|---|---|
| `admin_cf` | Admin SaaS | `admin123` | Crédito Fácil Ltda |
| `gerente_cf` | Gerente | `gerente123` | Crédito Fácil Ltda |
| `vendedor_cf1` | Vendedor | `vend123` | Crédito Fácil Ltda |
| `vendedor_cf2` | Vendedor | `vend123` | Crédito Fácil Ltda |
| `admin_fc` | Admin SaaS | `admin123` | FinCred Soluções ME |
| `gerente_fc` | Gerente | `gerente123` | FinCred Soluções ME |
| `vendedor_fc1` | Vendedor | `vend123` | FinCred Soluções ME |
| `vendedor_fc2` | Vendedor | `vend123` | FinCred Soluções ME |

Para popular o banco com dados de demonstração:

```bash
source myenv/bin/activate
python manage.py popular_banco --limpar
```

---

## 1. Visão Admin SaaS

**Acesso:** Login com perfil `admin` (ex: `admin_cf` / `admin123`)

O Admin SaaS é o dono ou gestor principal da empresa que contratou o sistema. Ele tem visão completa de toda a operação.

### Dashboard (`/dashboard/admin/`)

Ao fazer login, o admin é redirecionado automaticamente para seu dashboard, que apresenta:

#### Métricas principais (topo)
- **Carteira Ativa** — Valor total contratado (com juros) de todos os empréstimos ativos da empresa
- **A Receber** — Soma das parcelas pendentes e atrasadas ainda não pagas
- **Saldo em Caixa** — Saldo consolidado de todos os caixas das rotas
- **Inadimplência** — Valor total das parcelas em atraso
- **Recebido Hoje** — Total de pagamentos registrados no dia

#### Contadores
- Clientes ativos, Empréstimos ativos, Clientes inadimplentes, Parcelas que vencem hoje

#### Rotas da empresa
Cards com resumo de cada rota: clientes, empréstimos ativos, inadimplentes, saldo do caixa, configuração (periodicidade, taxa de juros, número de vendedores).

#### Últimos empréstimos
Tabela com os 8 empréstimos mais recentes: cliente, vendedor, rota, valor principal, total com juros, parcelas, periodicidade, data e status.

#### Inadimplentes
Lista dos clientes em atraso: nome, rota, telefone, valor atrasado, quantidade de parcelas e dias de atraso.

#### Recebimentos hoje
Pagamentos registrados no dia corrente com detalhes de cliente, rota, parcela e valor.

### Navegação lateral (sidebar)
O admin tem acesso a todos os itens do menu:
- **Dashboard** — Painel principal
- **Rotas** — Gestão de rotas (em desenvolvimento)
- **Clientes** — Gestão de clientes (em desenvolvimento)
- **Empréstimos** — Gestão de empréstimos (em desenvolvimento)
- **Caixa** — Gestão financeira (em desenvolvimento)
- **Relatórios** — Relatórios gerenciais (em desenvolvimento)
- **Configurações** — Configurações do sistema (em desenvolvimento)

---

## 2. Visão Gerente

**Acesso:** Login com perfil `gerente` (ex: `gerente_cf` / `gerente123`)

O Gerente é responsável por supervisionar as rotas, os vendedores e a operação do dia a dia.

### Dashboard (`/dashboard/gerente/`)

#### Métricas principais
- **Rotas Ativas** — Quantidade de rotas operando na empresa
- **Vendedores** — Quantidade de vendedores ativos
- **Clientes Ativos** — Total de clientes com cadastro ativo
- **Inadimplentes** — Clientes com parcelas em atraso

#### Rotas
Cards com resumo de cada rota: clientes, empréstimos ativos, inadimplentes, configuração (periodicidade, taxa de juros) e saldo do caixa.

#### Vendedores — Desempenho de hoje
Tabela com cada vendedor: nome, rotas vinculadas, empréstimos ativos e valor coletado hoje. Permite ao gerente acompanhar a produtividade da equipe em tempo real.

#### Parcelas nos próximos 7 dias
Tabela com as parcelas pendentes para os próximos 7 dias: cliente, rota, vencimento, valor e status. Ajuda no planejamento das cobranças da semana.

### Navegação lateral
O gerente vê:
- **Dashboard**, **Rotas**, **Clientes**, **Empréstimos**, **Caixa**, **Relatórios**

Não tem acesso a: Configurações.

### Permissões
- O gerente **não** pode acessar o dashboard do admin (`/dashboard/admin/`). Se tentar, será redirecionado de volta ao seu painel.

---

## 3. Visão Vendedor

**Acesso:** Login com perfil `vendedor` (ex: `vendedor_cf1` / `vend123`)

O Vendedor é o trabalhador de campo que percorre as rotas, concede empréstimos e coleta pagamentos.

### Dashboard (`/dashboard/vendedor/`)

#### Métricas principais
- **Minha Carteira** — Valor total dos empréstimos ativos atribuídos ao vendedor, com quantidade de empréstimos
- **Parcelas Hoje** — Quantidade de parcelas com vencimento hoje e valor total a cobrar
- **Recebido Hoje** — Valor total que o vendedor já coletou no dia
- **Inadimplentes** — Quantidade de clientes em atraso nas rotas do vendedor

#### Cobranças de hoje
Lista das parcelas com vencimento no dia de hoje: nome do cliente, rota, número da parcela e valor. Cada item tem um botão **"Registrar Pagamento"** (funcionalidade em desenvolvimento).

#### Clientes inadimplentes
Lista dos clientes em atraso nas rotas do vendedor: nome, rota, telefone, valor total atrasado, quantidade de parcelas atrasadas e dias de atraso. Permite ao vendedor priorizar cobranças.

#### Minha carteira ativa
Tabela completa com todos os empréstimos ativos do vendedor: cliente, rota, valor da parcela, parcelas restantes (ex: 7/10) e data do próximo vencimento.

### Navegação lateral
O vendedor vê apenas:
- **Dashboard**, **Clientes**, **Empréstimos**

Não tem acesso a: Rotas, Caixa, Relatórios, Configurações.

### Permissões
- O vendedor **não** pode acessar o dashboard do admin nem do gerente. Se tentar, será redirecionado para seu próprio painel.
- O vendedor **só vê dados das suas próprias rotas** — não tem acesso a dados de outros vendedores ou de outras empresas.

---

## Fluxo Geral de Uso

### 1. Login
- Acesse a página inicial do sistema (`/`)
- Informe usuário e senha
- O sistema redireciona automaticamente para o dashboard correspondente ao seu perfil

### 2. Operação diária (Vendedor)
1. Ao iniciar o dia, consulte as **Cobranças de hoje** para saber quais clientes visitar
2. Verifique os **Clientes inadimplentes** para priorizar cobranças em atraso
3. Registre pagamentos conforme recebidos (funcionalidade em desenvolvimento)
4. Acompanhe o **Recebido Hoje** para controlar o total coletado

### 3. Supervisão (Gerente)
1. Acompanhe o **desempenho dos vendedores** pela tabela de coletado hoje
2. Verifique as **parcelas dos próximos 7 dias** para planejar a semana
3. Monitore as **rotas** para identificar desequilíbrios (inadimplência alta, caixa baixo)

### 4. Gestão (Admin)
1. Analise os **indicadores financeiros** (carteira, saldo, inadimplência)
2. Acompanhe os **recebimentos do dia** para validar a operação
3. Monitore os **últimos empréstimos** concedidos
4. Identifique e acompanhe **clientes inadimplentes**

---

## Isolamento de Dados (Multi-tenant)

O sistema garante que cada empresa vê **apenas seus próprios dados**:
- Um vendedor da "Crédito Fácil" não vê clientes da "FinCred"
- Rotas, empréstimos, pagamentos e movimentações são isolados por empresa
- Não há possibilidade de cruzamento de dados entre empresas

---

## Regras de Negócio Importantes

| Regra | Descrição |
|---|---|
| **Juros simples** | `valor_total = principal × (1 + taxa/100)` |
| **Taxa gravada no contrato** | Alterações na configuração da rota não afetam empréstimos já criados |
| **Caixa via movimentações** | O saldo do caixa nunca é alterado diretamente — toda alteração passa por uma movimentação financeira |
| **Parcelas automáticas** | Ao criar um empréstimo, as parcelas são geradas automaticamente pelo sistema |
| **Saída automática no caixa** | Ao criar um empréstimo, o valor principal é debitado do caixa da rota |
| **Entrada automática no caixa** | Ao registrar um pagamento, o valor é creditado no caixa da rota |
