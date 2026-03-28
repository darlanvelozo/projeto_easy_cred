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
- **Rotas** — Lista de rotas com metricas, detalhe de cada rota
- **Clientes** — Lista, cadastro, edicao, detalhe e mapa de clientes
- **Emprestimos** — Lista, novo emprestimo, detalhe com parcelas
- **Caixa** — Saldo por rota e historico de movimentacoes
- **Relatorios** — Inadimplencia, recebimentos do mes, carteira por rota, top inadimplentes
- **Configuracoes** — Editar dados da empresa, configurar rotas (taxa, periodicidade, parcelas, limite)

### Configuracoes

Na pagina de configuracoes o admin pode:

1. **Editar dados da empresa** — nome, CNPJ, e-mail, telefone
2. **Configurar cada rota** — taxa de juros padrao, periodicidade, numero de parcelas e limite maximo de emprestimo
3. **Visualizar equipe** — lista de gerentes e vendedores ativos

As configuracoes de rota sao aplicadas automaticamente ao criar novos emprestimos:
- Campos pre-preenchidos ao selecionar a rota
- Limite maximo validado no formulario e no servidor
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
- Registrar pagamentos
- Ver saldo do caixa por rota e historico de movimentacoes
- Acessar relatorios

### O que o gerente NAO pode fazer
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
- **Ver detalhe** do emprestimo com lista de parcelas

#### Pagamentos
- **Registrar pagamento** de parcelas pendentes ou atrasadas

### O que o vendedor NAO pode fazer
- Ver rotas (pagina de gestao de rotas)
- Acessar caixa, relatorios ou configuracoes
- Ver dados de outros vendedores ou de rotas que nao sao dele

---

## Funcionalidades do Sistema

### Mapa de Clientes (`/clientes/mapa/`)
- Visualizacao dos clientes com localizacao no mapa (OpenStreetMap)
- Filtro por rota
- Popup com nome, rota, telefone e link para detalhe
- Vendedor ve apenas clientes das suas rotas
- Botao de acesso na lista de clientes

### Cadastro de Cliente com GPS
- No formulario de cliente, botao **"Usar GPS"** captura a localizacao do celular
- Latitude e longitude sao preenchidas automaticamente
- Cliente aparece no mapa apos salvar
- Link **"Abrir no Maps"** no detalhe do cliente

### Criacao de Emprestimo
1. Selecionar rota → campos pre-preenchidos pela configuracao (taxa, periodicidade, parcelas)
2. Selecionar cliente e informar valor principal
3. Sistema calcula e exibe previa: valor total com juros e valor da parcela
4. Se valor exceder limite da rota, alerta visual + bloqueio no servidor
5. Ao salvar, o sistema automaticamente:
   - Calcula valor total e valor da parcela
   - Gera todas as parcelas com vencimentos
   - Registra saida no caixa da rota

### Registro de Pagamento
1. No detalhe do emprestimo, clicar **"Pagar"** na parcela
2. Valor pre-preenchido, escolher forma (dinheiro/pix/transferencia)
3. Ao salvar, o sistema automaticamente:
   - Registra entrada no caixa da rota
   - Marca parcela como paga
   - Se era a ultima parcela, marca emprestimo como quitado

---

## Fluxo Diario de Uso

### Vendedor (campo)
1. Fazer login no celular
2. Consultar **Cobrancas de hoje** no dashboard
3. Abrir **Mapa** para planejar a rota de visitas
4. Em cada cliente:
   - Registrar pagamento das parcelas do dia
   - Se novo cliente, cadastrar com GPS
   - Se necessario, criar novo emprestimo
5. Acompanhar **Recebido Hoje** para controle

### Gerente (supervisao)
1. Verificar **desempenho dos vendedores** no dashboard
2. Conferir **parcelas dos proximos 7 dias** para planejar a semana
3. Monitorar **rotas** e identificar problemas (inadimplencia alta, caixa baixo)
4. Acessar **relatorios** para visao mensal

### Admin (gestao)
1. Analisar **indicadores financeiros** no dashboard
2. Verificar **recebimentos do dia**
3. Acompanhar **inadimplentes** e tomar decisoes
4. Ajustar **configuracoes** das rotas conforme necessidade
5. Consultar **relatorios** para decisoes estrategicas

---

## Isolamento de Dados (Multi-tenant)

O sistema garante que cada empresa ve **apenas seus proprios dados**:
- Usuarios so acessam dados da sua empresa
- Vendedores so veem dados das rotas onde estao vinculados
- Rotas, emprestimos, pagamentos e movimentacoes sao isolados por empresa

---

## Regras de Negocio

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
| **Vencimento automatico (vendedor)** | Vendedor nao escolhe data — 1o vencimento e sempre amanha |
| **Config pre-preenche formulario** | Ao selecionar rota, taxa/parcelas/periodicidade sao preenchidos da configuracao |
