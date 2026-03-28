# EasyCred — Contexto do Projeto

> Arquivo de referência contínua. Atualizado a cada nova implementação ou decisão de negócio.

---

## Visão Geral

### As 3 Visões do Sistema
| Visão | Quem | Acesso |
|---|---|---|
| **Admin Geral** | Dono/operador do SystemPay | Django `/admin/` — gestão de todas as empresas |
| **Admin SaaS** | Empresa cliente que contratou | Dashboard próprio: rotas, vendedores, relatórios |
| **Vendedor** | Trabalhador de campo | Dashboard simplificado: rota, clientes, empréstimos, cobranças |

Sistema SaaS de gestão de crédito rotativo (agiotagem formalizada / crédito popular) operado por empresas que possuem **rotas de cobrança**. Vendedores percorrem rotas, concedem empréstimos a clientes e coletam parcelas.

---

## Regras de Negócio

### Empresa (Tenant)
- Cada empresa é um tenant isolado no sistema.
- Todos os dados (rotas, clientes, empréstimos) pertencem a uma empresa.
- Usuários são vinculados a uma empresa e só enxergam dados dela.

### Usuários e Perfis
| Perfil | Acesso |
|---|---|
| `admin` | Acesso total à empresa: configurações, relatórios, todos os dados |
| `gerente` | Gerencia rotas, vendedores, clientes e relatórios |
| `vendedor` | Opera na rota: concede empréstimos, registra pagamentos |

### Rotas
- Rota = território/carteira de clientes atribuída a um ou mais vendedores.
- Cada rota tem uma `ConfiguracaoRota` com taxa padrão, periodicidade e número de parcelas padrão.
- Cada rota tem um `CaixaRota` com saldo consolidado.
- Um vendedor pode estar vinculado a múltiplas rotas (`VendedorRota`).

### Empréstimos
- Juros simples: `valor_total = principal * (1 + taxa/100)`.
- A taxa é **gravada no contrato** no momento da criação — mudanças futuras na configuração da rota não afetam contratos existentes.
- Parcelas são geradas automaticamente com base em `num_parcelas`, `periodicidade` e `data_primeiro_vencimento`.
- Periodicidades suportadas: diário, semanal, quinzenal, mensal.
- Status do empréstimo: `ativo`, `quitado`, `inadimplente`, `cancelado`.

### Parcelas
- Geradas automaticamente via signal `post_save` no `Emprestimo` (`emprestimos/signals.py`).
- Status: `pendente`, `paga`, `atrasada`.
- Uma parcela pode ter múltiplos pagamentos (pagamentos parciais).

### Caixa e Movimentações
- **Regra crítica:** o saldo do `CaixaRota` nunca é alterado diretamente — toda alteração passa obrigatoriamente por uma `MovimentacaoFinanceira`.
- Isso garante rastreabilidade total e permite reconstruir histórico.
- Origens de movimentação: `pagamento`, `emprestimo` (saída ao conceder), `aporte`, `retirada`, `ajuste`.
- Ao registrar um pagamento → cria `Pagamento` → cria `MovimentacaoFinanceira` (entrada) → atualiza saldo do `CaixaRota`.
- Ao conceder empréstimo → cria `Emprestimo` → cria `MovimentacaoFinanceira` (saída) → atualiza saldo.

---

## Arquitetura de Apps

```
systempaytec/
├── accounts/       # Empresa + Usuario (AbstractUser)
├── rotas/          # Rota, ConfiguracaoRota, VendedorRota, CaixaRota
├── clientes/       # Cliente, ClienteDocumento
├── emprestimos/    # Emprestimo, Parcela
└── financeiro/     # Pagamento, MovimentacaoFinanceira
```

---

## Estado Atual da Implementação

### Concluído
- [x] Estrutura de todos os apps criada
- [x] `models.py` de todos os apps implementados
- [x] `AUTH_USER_MODEL = 'accounts.Usuario'` configurado
- [x] Migrations geradas e aplicadas (banco limpo)
- [x] Settings: `pt-br`, `America/Sao_Paulo`

### Pendente / Próximos Passos
- [x] `admin.py` — registrar todos os models no painel Django Admin
- [x] Signal `post_save` no `Emprestimo` para gerar parcelas automaticamente (`emprestimos/signals.py`)
- [x] Signal `post_save` no `Emprestimo` para registrar saída no caixa (`emprestimos/signals.py`)
- [x] Signal `post_save` no `Pagamento` para registrar entrada no caixa (`financeiro/signals.py`)
- [x] Autenticação: login e logout implementados
- [x] Página de login SystemPay (layout split, toggle senha, mensagens de erro)
- [x] Redirecionamento por perfil após login (superuser→/admin/, admin/gerente/vendedor→dashboard próprio)
- [x] Base layout (base.html): sidebar escura, topbar, cards, badges, tabelas — reutilizável em todas as telas
- [x] Dashboard Admin SaaS: 5 métricas + 4 contadores, rotas, últimos empréstimos, inadimplentes, pagamentos hoje
- [x] Dashboard Gerente: rotas, vendedores, parcelas próximos 7 dias, métricas
- [x] Dashboard Vendedor: carteira ativa, cobranças hoje, inadimplentes, métricas pessoais
- [x] Controle de permissões por perfil (`accounts/decorators.py` — `requer_perfil`)
- [x] `MovimentacaoInline` no admin do Pagamento
- [x] Guard `ConfiguracaoRota` com `getattr` + `{% if r.config %}` nos templates
- [x] `popular_banco` atualizado para funcionar com signals (sem duplicações)
- [ ] Recuperação de senha
- [ ] Relatórios: inadimplência, fluxo de caixa, carteira por rota

---

## Decisões Técnicas

| Decisão | Motivo |
|---|---|
| `AbstractUser` customizado desde o início | Evita migração problemática posterior |
| Taxa gravada no contrato | Imutabilidade histórica dos contratos |
| `MovimentacaoFinanceira` como única porta de entrada no caixa | Rastreabilidade total |
| SQLite em desenvolvimento | Simplicidade; migrar para PostgreSQL em produção |
| `python-dateutil` instalado | Necessário para cálculo de vencimentos com `relativedelta` |

---

## Stack

- Python 3.12
- Django 6.0.3
- SQLite (dev) → PostgreSQL (prod)
- Ambiente virtual: `/home/darlan/systempay/myenv/`
- Repositório: https://github.com/darlanvelozo/projeto_easy_cred (branch `master`)
