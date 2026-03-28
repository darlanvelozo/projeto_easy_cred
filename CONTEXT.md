# EasyCred — Contexto do Projeto

> Arquivo de referencia continua. Atualizado a cada nova implementacao ou decisao de negocio.

---

## Visao Geral

Sistema SaaS de gestao de credito popular operado por empresas que possuem **rotas de cobranca**. Vendedores percorrem rotas, cadastram clientes, concedem emprestimos e coletam parcelas diariamente.

### As 3 Visoes do Sistema
| Visao | Quem | Acesso |
|---|---|---|
| **Admin SaaS** | Dono da empresa | Dashboard completo, configuracoes, relatorios, gestao total |
| **Gerente** | Supervisor de campo | Rotas, vendedores, clientes, emprestimos, caixa, relatorios |
| **Vendedor** | Trabalhador de campo | Seus clientes, seus emprestimos, cobranças do dia, mapa, GPS |

### Dados de Demonstracao
| Usuario | Perfil | Senha | Rota |
|---|---|---|---|
| `darlan` | Admin SaaS | `darlan123` | — |
| `marcos` | Gerente | `marcos123` | — |
| `raimundo` | Vendedor | `raimundo123` | Teresina |
| `chico` | Vendedor | `chico123` | Picos |

---

## Regras de Negocio

### Empresa (Tenant)
- Cada empresa e um tenant isolado no sistema.
- Todos os dados pertencem a uma empresa. Usuarios so enxergam dados dela.

### Usuarios e Perfis
| Perfil | Acesso |
|---|---|
| `admin` | Acesso total: configuracoes, relatorios, todos os dados |
| `gerente` | Rotas, clientes, emprestimos, caixa, relatorios |
| `vendedor` | Clientes e emprestimos das suas rotas, cadastro, pagamentos, mapa |

### Rotas
- Territorio/carteira de clientes atribuida a vendedores.
- `ConfiguracaoRota`: taxa padrao, periodicidade, parcelas, limite maximo.
- `CaixaRota`: saldo consolidado (alterado apenas via MovimentacaoFinanceira).
- Vendedores vinculados via `VendedorRota` (M2M).

### Emprestimos
- Juros simples: `valor_total = principal * (1 + taxa/100)`.
- Taxa **gravada no contrato** — imutavel apos criacao.
- Parcelas geradas automaticamente (signal post_save).
- Periodicidades: diario (mais comum), semanal, quinzenal, mensal.
- Status: `ativo`, `quitado`, `inadimplente`, `cancelado`.
- Vendedor nao escolhe data de vencimento — auto-calcula (amanha).

### Parcelas
- Geradas automaticamente via signal.
- Status: `pendente`, `paga`, `atrasada`.

### Caixa e Movimentacoes
- **Regra critica:** saldo do CaixaRota NUNCA e alterado diretamente.
- Toda alteracao passa por MovimentacaoFinanceira (rastreabilidade total).
- Origens: `pagamento`, `emprestimo`, `aporte`, `retirada`, `ajuste`.

### Clientes
- Possuem latitude/longitude para visualizacao em mapa.
- GPS capturado pelo celular do vendedor no cadastro.
- Vendedor cadastra e edita clientes das suas rotas.

---

## Arquitetura de Apps

```
systempaytec/
├── accounts/       # Empresa, Usuario (AbstractUser), dashboards, config, relatorios
├── rotas/          # Rota, ConfiguracaoRota, VendedorRota, CaixaRota
├── clientes/       # Cliente, ClienteDocumento
├── emprestimos/    # Emprestimo, Parcela + signals (parcelas + saida caixa)
└── financeiro/     # Pagamento, MovimentacaoFinanceira + signal (entrada caixa)
```

---

## Estado Atual da Implementacao

### Concluido
- [x] Models de todos os apps + migrations
- [x] AUTH_USER_MODEL customizado (AbstractUser)
- [x] admin.py completo com inlines e filtros
- [x] Signals: gerar parcelas, saida caixa (emprestimo), entrada caixa (pagamento)
- [x] Login/logout com redirecionamento por perfil
- [x] Base layout responsivo: sidebar, topbar, hamburger mobile
- [x] 3 dashboards (admin, gerente, vendedor) com metricas em tempo real
- [x] Decorator @requer_perfil para controle de acesso
- [x] CRUD Clientes: lista, criar, editar, detalhe, mapa (Leaflet/OpenStreetMap)
- [x] Cadastro de cliente com captura GPS (navigator.geolocation)
- [x] CRUD Emprestimos: lista, criar (AJAX config rota), detalhe com parcelas
- [x] Formulario simplificado do vendedor (auto-vencimento, filtro rotas/clientes)
- [x] Validacao de limite maximo por rota (frontend + backend)
- [x] Registro de pagamento com quitacao automatica
- [x] Caixa: saldo por rota + historico de movimentacoes paginado
- [x] Relatorios: inadimplencia, recebimentos mes, carteira por rota, top inadimplentes
- [x] Configuracoes editaveis: empresa + config por rota
- [x] API AJAX para config da rota (pre-preenchimento de formulario)
- [x] popular_banco com dados realistas do Piaui (Teresina + Picos)
- [x] 19 templates, 27 clientes, 32 emprestimos de demonstracao
- [x] Documentacao: CONTEXT.md, REGRAS_E_FUNCIONAMENTO.md, GUIA_USUARIO.md

---

## Decisoes Tecnicas

| Decisao | Motivo |
|---|---|
| AbstractUser customizado | Evita migracao problematica posterior |
| Taxa gravada no contrato | Imutabilidade historica |
| MovimentacaoFinanceira como unica porta | Rastreabilidade total do caixa |
| Signals para automacao | Desacoplamento entre apps |
| Leaflet/OpenStreetMap para mapa | Gratuito, sem API key |
| SQLite em dev | Simplicidade; PostgreSQL em producao |
| python-dateutil | Calculo de vencimentos com relativedelta |

---

## Stack

- Python 3.12 / Django 6.0.3
- SQLite (dev) → PostgreSQL (prod)
- Leaflet + OpenStreetMap (mapa)
- Ambiente virtual: `/home/darlan/systempay/myenv/`
- Repositorio: https://github.com/darlanvelozo/projeto_easy_cred (branch `master`)
