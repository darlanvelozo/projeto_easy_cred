# EasyCred — Roadmap de Melhorias

> Etapas organizadas por prioridade. Cada etapa contem funcionalidades que dependem uma da outra e devem ser implementadas juntas.

---

## ETAPA 1 — Seguranca e Infraestrutura Basica
> **Prioridade: CRITICA** — Sem isso, o sistema nao pode ir para producao.

### 1.1 Separar settings dev/prod
- [ ] Criar `settings/base.py`, `settings/dev.py`, `settings/prod.py`
- [ ] Mover SECRET_KEY para variavel de ambiente
- [ ] DEBUG=False em producao
- [ ] ALLOWED_HOSTS configuravel por ambiente

### 1.2 Banco de dados PostgreSQL
- [ ] Configurar PostgreSQL no settings de producao
- [ ] Testar todas as migrations no PostgreSQL
- [ ] Adicionar `db_index=True` nos campos mais consultados (status, vencimento, empresa, rota)

### 1.3 Seguranca Django
- [ ] SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE
- [ ] X_FRAME_OPTIONS = 'DENY'
- [ ] SECURE_HSTS_SECONDS
- [ ] Protecao contra brute force no login (django-axes ou django-ratelimit)

### 1.4 Static/Media files
- [ ] Configurar STATIC_ROOT + whitenoise para servir arquivos estaticos
- [ ] Configurar MEDIA_ROOT e MEDIA_URL para uploads (ClienteDocumento)
- [ ] Validar tipo e tamanho de arquivos no upload

### 1.5 Docker e deploy
- [ ] Dockerfile multi-stage (Python + gunicorn)
- [ ] docker-compose.yml (app + postgres + redis)
- [ ] Procfile para Railway/Render
- [ ] requirements.txt atualizado com gunicorn, whitenoise, psycopg2-binary

---

## ETAPA 2 — Gestao de Usuarios e Autenticacao
> **Prioridade: ALTA** — O admin precisa gerenciar sua equipe sem o Django Admin.

### 2.1 Recuperacao de senha
- [ ] View de "Esqueci minha senha" com envio de e-mail
- [ ] Configurar EMAIL_BACKEND (SendGrid, AWS SES ou Gmail)
- [ ] Templates de e-mail para reset de senha
- [ ] Link na pagina de login

### 2.2 Troca de senha
- [ ] View para o usuario trocar a propria senha (logado)
- [ ] Validacao de senha atual antes de alterar

### 2.3 Gestao de equipe pelo Admin SaaS
- [ ] Tela para listar usuarios da empresa (na pagina de Configuracoes)
- [ ] Formulario para criar novo usuario (gerente ou vendedor)
- [ ] Ativar/desativar usuario
- [ ] Resetar senha de um usuario da equipe
- [ ] Vincular/desvincular vendedor de rotas (sem precisar do Django Admin)

### 2.4 Perfil do usuario
- [ ] Pagina de "Meu Perfil" para cada usuario
- [ ] Editar nome, telefone, foto (opcional)

---

## ETAPA 3 — Logica de Negocio Completa ✅
> **Prioridade: ALTA** — Implementado em 2026-03-28.

### 3.1 Validacao de saldo no caixa
- [x] Ao criar emprestimo, verificar se o caixa da rota tem saldo suficiente
- [x] Bloquear criacao se saldo < valor_principal
- [x] Mensagem clara: "Caixa da rota insuficiente. Saldo: R$ X"

### 3.2 Marcacao automatica de inadimplencia
- [x] Management command `atualizar_parcelas` que roda diariamente
- [x] Marca parcelas vencidas como "atrasada"
- [x] Marca emprestimos com parcelas atrasadas como "inadimplente"
- [ ] Configurar via cron/celery para rodar todo dia as 6h

### 3.3 Cancelamento de emprestimo
- [x] View para admin cancelar emprestimo
- [x] Logica: estorna valor no caixa (movimentacao de entrada tipo "ajuste")
- [x] Marca todas as parcelas pendentes como canceladas
- [x] Exige motivo obrigatorio (campo observacao)
- [x] Emprestimos com parcelas ja pagas: estorno parcial

### 3.4 Aporte e retirada de caixa
- [x] View para admin/gerente fazer aporte no caixa da rota
- [x] View para admin fazer retirada do caixa
- [x] Formulario com valor, descricao, tipo
- [x] Movimentacao registrada automaticamente

### 3.5 Pagamento parcial
- [x] Permitir pagar valor menor que a parcela
- [x] Valor restante calculado via sum de pagamentos
- [x] Parcela so vira "paga" quando soma dos pagamentos >= valor
- [x] Historico de pagamentos parciais visivel no detalhe

### 3.6 Multa e juros de mora
- [x] Campos `multa_atraso` e `juros_mora_dia` na ConfiguracaoRota
- [x] Ao registrar pagamento de parcela atrasada, calcular acrescimo
- [x] Exibir valor original vs valor com multa no formulario de pagamento

### 3.7 Limite de credito por cliente
- [x] Campo `limite_credito` no model Cliente (opcional)
- [x] Ao criar emprestimo, verificar: soma de emprestimos ativos do cliente + novo <= limite
- [x] Se nao definido, usa o limite da rota

### 3.8 CRUD de Rotas completo
- [x] View para admin criar nova rota
- [x] Editar rota existente (nome, descricao, ativa)
- [x] A ConfiguracaoRota ja e editavel (pagina de Configuracoes)

---

## ETAPA 4 — Notificacoes e Comunicacao
> **Prioridade: MEDIA** — Melhora a operacao e reduz inadimplencia.

### 4.1 Notificacoes no sistema
- [ ] Model `Notificacao` (usuario, titulo, mensagem, lida, criado_em)
- [ ] Icone de sino no topbar com contador de nao lidas
- [ ] Dropdown com ultimas notificacoes
- [ ] Pagina de todas as notificacoes

### 4.2 Notificacoes automaticas
- [ ] Parcela vencendo hoje → notifica vendedor
- [ ] Parcela atrasada ha X dias → notifica gerente
- [ ] Emprestimo quitado → notifica admin
- [ ] Novo emprestimo criado → notifica gerente
- [ ] Caixa abaixo de limite minimo → notifica admin

### 4.3 Integracao WhatsApp (API)
- [ ] Enviar lembrete de cobranca para cliente via WhatsApp
- [ ] Template de mensagem configuravel pelo admin
- [ ] Registro de mensagens enviadas
- [ ] Integracao com API oficial (Meta Business) ou Evolution API

---

## ETAPA 5 — Relatorios e Visualizacoes
> **Prioridade: MEDIA** — Essencial para tomada de decisao.

### 5.1 Graficos nos relatorios
- [ ] Integrar Chart.js ou ApexCharts
- [ ] Grafico de recebimentos diarios (ultimos 30 dias)
- [ ] Grafico de emprestimos concedidos vs quitados por mes
- [ ] Grafico de inadimplencia por rota (pizza/donut)
- [ ] Grafico de evolucao do saldo do caixa

### 5.2 Relatorio de desempenho por vendedor
- [ ] Total concedido, total recebido, taxa de inadimplencia
- [ ] Comparativo entre vendedores
- [ ] Filtro por periodo

### 5.3 Relatorio de fluxo de caixa
- [ ] Entradas vs saidas por periodo
- [ ] Projecao de recebimentos futuros (parcelas pendentes)
- [ ] Exportar para PDF

### 5.4 Exportacao de dados
- [ ] Exportar lista de clientes para Excel/CSV
- [ ] Exportar movimentacoes do caixa para Excel/CSV
- [ ] Exportar relatorio de inadimplentes para PDF
- [ ] Gerar comprovante/recibo de pagamento (PDF)

### 5.5 Contrato de emprestimo (PDF)
- [ ] Template de contrato com dados do emprestimo
- [ ] Gerar PDF ao criar emprestimo
- [ ] Botao "Imprimir Contrato" no detalhe do emprestimo
- [ ] Campos configuráveis pelo admin (texto do contrato, logo)

---

## ETAPA 6 — Experiencia do Vendedor (Mobile) (parcialmente concluida)
> **Prioridade: MEDIA** — O vendedor e o principal usuario do sistema no dia a dia.

### 6.1 PWA (Progressive Web App) ✅
- [x] manifest.json com nome, icones, shortcuts, display standalone
- [x] Service worker com cache-first para assets, network-first para paginas, offline fallback
- [x] Icones SVG (192px e 512px, normal + maskable)
- [x] Meta tags Apple/Android (apple-mobile-web-app-capable, theme-color, viewport-fit)
- [x] Banner de instalacao com prompt nativo
- [x] Funcionar offline basico (cache de paginas ja visitadas)

### 6.2 UX Mobile-First ✅
- [x] Bottom navigation bar por perfil (vendedor, gerente, admin)
- [x] Floating Action Button (FAB) nas paginas de lista
- [x] Quick Actions no dashboard do vendedor (Novo Emprestimo, Novo Cliente, Mapa, Clientes)
- [x] Card views no mobile (tabelas convertidas em listas de cards)
- [x] Touch targets minimos de 44px em todos os botoes/links
- [x] Formularios responsivos (2 colunas desktop, 1 coluna mobile)
- [x] Safe area support para notch (iPhone X+)
- [x] Haptic feedback ao tocar botoes
- [x] Body scroll lock quando sidebar aberta
- [x] Animacoes suaves (fade-in, transitions)

### 6.3 Mapa Interativo Avancado ✅
- [x] Markers coloridos por status (em dia, cobranca hoje, inadimplente, sem emprestimo)
- [x] Busca flutuante sobre o mapa com filtro em tempo real
- [x] Filtros rapidos por chips (Todos, Cobranca hoje, Inadimplentes)
- [x] Bottom sheet com detalhes do cliente (metricas, dados, acoes)
- [x] Botao "Ligar" (tel: link direto) e "Navegar" (Google Maps)
- [x] GPS "Minha localizacao" para vendedor se localizar
- [x] Swipe-to-dismiss no bottom sheet
- [x] Dados enriquecidos via backend (emprestimos, parcelas, atrasos)

### 6.4 Ainda pendente
- [ ] Ordenar clientes por proximidade geografica no mapa
- [ ] Marcar clientes ja visitados no mapa
- [ ] Formulario simplificado de cadastro rapido (nome, telefone, GPS)
- [ ] Foto do documento via camera do celular
- [ ] Cadastro + emprestimo em sequencia

---

## ETAPA 7 — Gestao Avancada
> **Prioridade: BAIXA** — Funcionalidades para escalar o negocio.

### 7.1 Renegociacao de emprestimo
- [ ] View para renegociar emprestimo inadimplente
- [ ] Opções: estender prazo, reduzir parcela, novo acordo
- [ ] Registrar emprestimo original como "renegociado"
- [ ] Criar novo emprestimo com vinculo ao original

### 7.2 Importacao em lote
- [ ] Upload de CSV com clientes (nome, cpf, telefone, endereco, rota)
- [ ] Validacao linha a linha com relatorio de erros
- [ ] Preview antes de confirmar importacao

### 7.3 Multi-empresa (SaaS completo)
- [ ] Tela de cadastro de nova empresa (self-service)
- [ ] Planos e limites (num. de rotas, vendedores, emprestimos)
- [ ] Painel do superadmin para gerenciar todas as empresas
- [ ] Cobranca/assinatura (Stripe, PagSeguro, ou Asaas)

### 7.4 API REST
- [ ] Instalar Django REST Framework
- [ ] Endpoints para clientes, emprestimos, parcelas, pagamentos
- [ ] Autenticacao por token (JWT)
- [ ] Documentacao Swagger/OpenAPI
- [ ] Preparar para app mobile nativo futuro

### 7.5 Audit log
- [ ] Registrar quem alterou o que e quando
- [ ] Historico de alteracoes em clientes, emprestimos, configuracoes
- [ ] Visivel para o admin na interface

### 7.6 Backup automatico
- [ ] Backup diario do banco PostgreSQL
- [ ] Envio para storage externo (S3, Google Drive)
- [ ] Alerta se backup falhar

---

## Resumo por Prioridade

| Etapa | Prioridade | Foco |
|---|---|---|
| 1. Seguranca e Infraestrutura | CRITICA | Deploy seguro |
| 2. Usuarios e Autenticacao | ALTA | Gestao da equipe |
| 3. Logica de Negocio | ALTA | Operacao real completa |
| 4. Notificacoes | MEDIA | Comunicacao e alertas |
| 5. Relatorios e Visualizacoes | MEDIA | Tomada de decisao |
| 6. Experiencia Mobile | MEDIA | Produtividade do vendedor |
| 7. Gestao Avancada | BAIXA | Escala e SaaS completo |
