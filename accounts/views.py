from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone

from rotas.models import Rota, CaixaRota
from clientes.models import Cliente
from emprestimos.models import Emprestimo, Parcela
from financeiro.models import Pagamento


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.ativo:
                messages.error(request, 'Sua conta está desativada. Contate o administrador.')
                return render(request, 'accounts/login.html')
            login(request, user)
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser:
        return redirect('/admin/')
    if user.perfil == 'admin':
        return redirect('accounts:dashboard_admin')
    if user.perfil == 'gerente':
        return redirect('accounts:dashboard_gerente')
    return redirect('accounts:dashboard_vendedor')


@login_required
def dashboard_admin(request):
    empresa = request.user.empresa
    hoje = timezone.localdate()

    # ── Métricas financeiras ─────────────────────────────────────────────────
    # Carteira ativa: valor total contratado dos empréstimos em andamento
    carteira_ativa = (
        Emprestimo.objects
        .filter(rota__empresa=empresa, status='ativo')
        .aggregate(total=Sum('valor_total'))['total'] or Decimal('0')
    )

    # Saldo devedor: parcelas ainda não pagas de empréstimos ativos (o que será recebido)
    saldo_devedor = (
        Parcela.objects
        .filter(
            emprestimo__rota__empresa=empresa,
            emprestimo__status='ativo',
            status__in=['pendente', 'atrasada'],
        )
        .aggregate(total=Sum('valor'))['total'] or Decimal('0')
    )

    # Inadimplência: soma das parcelas com status atrasada
    total_inadimplente = (
        Parcela.objects
        .filter(emprestimo__rota__empresa=empresa, status='atrasada')
        .aggregate(total=Sum('valor'))['total'] or Decimal('0')
    )

    # Recebido hoje: soma dos pagamentos registrados na data de hoje
    recebido_hoje = (
        Pagamento.objects
        .filter(
            parcela__emprestimo__rota__empresa=empresa,
            data_pagamento__date=hoje,
        )
        .aggregate(total=Sum('valor'))['total'] or Decimal('0')
    )

    # Saldo dos caixas: soma do saldo atual de todos os CaixaRota da empresa
    saldo_caixas = (
        CaixaRota.objects
        .filter(rota__empresa=empresa)
        .aggregate(total=Sum('saldo'))['total'] or Decimal('0')
    )

    # ── Contadores ───────────────────────────────────────────────────────────
    total_clientes = Cliente.objects.filter(empresa=empresa, ativo=True).count()

    total_emprestimos_ativos = Emprestimo.objects.filter(
        rota__empresa=empresa, status='ativo'
    ).count()

    total_inadimplentes_clientes = (
        Cliente.objects
        .filter(empresa=empresa, emprestimos__status='inadimplente')
        .distinct().count()
    )

    total_parcelas_vencendo_hoje = Parcela.objects.filter(
        emprestimo__rota__empresa=empresa,
        vencimento=hoje,
        status='pendente',
    ).count()

    # ── Rotas com resumo ─────────────────────────────────────────────────────
    rotas = (
        Rota.objects
        .filter(empresa=empresa, ativa=True)
        .select_related('configuracao', 'caixa')
    )

    rotas_resumo = []
    for rota in rotas:
        emp_ativos      = Emprestimo.objects.filter(rota=rota, status='ativo').count()
        emp_inadimp     = Emprestimo.objects.filter(rota=rota, status='inadimplente').count()
        carteira_rota   = (
            Emprestimo.objects.filter(rota=rota, status='ativo')
            .aggregate(t=Sum('valor_total'))['t'] or Decimal('0')
        )
        clientes_rota   = Cliente.objects.filter(rota=rota, ativo=True).count()
        vendedores_rota = rota.vendedores.filter(ativo=True).count()
        caixa           = getattr(rota, 'caixa', None)

        rotas_resumo.append({
            'rota':          rota,
            'ativos':        emp_ativos,
            'inadimplentes': emp_inadimp,
            'carteira':      carteira_rota,
            'clientes':      clientes_rota,
            'num_vendedores': vendedores_rota,
            'saldo':         caixa.saldo if caixa else Decimal('0'),
            'atualizado_em': caixa.atualizado_em if caixa else None,
        })

    # ── Últimos empréstimos ───────────────────────────────────────────────────
    ultimos_emprestimos = (
        Emprestimo.objects
        .filter(rota__empresa=empresa)
        .select_related('cliente', 'rota', 'vendedor')
        .order_by('-criado_em')[:8]
    )

    # ── Clientes inadimplentes — dados pré-computados ─────────────────────────
    clientes_base = (
        Cliente.objects
        .filter(empresa=empresa, emprestimos__status='inadimplente')
        .distinct()
        .select_related('rota')[:6]
    )

    clientes_inadimplentes = []
    for cliente in clientes_base:
        parcelas_atrasadas = Parcela.objects.filter(
            emprestimo__cliente=cliente,
            status='atrasada',
        )
        valor_atrasado  = parcelas_atrasadas.aggregate(t=Sum('valor'))['t'] or Decimal('0')
        qtd_atrasadas   = parcelas_atrasadas.count()

        # dia do vencimento mais antigo em atraso
        mais_antiga = parcelas_atrasadas.order_by('vencimento').first()
        dias_atraso = (hoje - mais_antiga.vencimento).days if mais_antiga else 0

        clientes_inadimplentes.append({
            'nome':          cliente.nome,
            'rota':          cliente.rota.nome if cliente.rota else '—',
            'telefone':      cliente.telefone,
            'valor_atrasado': valor_atrasado,
            'qtd_atrasadas': qtd_atrasadas,
            'dias_atraso':   dias_atraso,
        })

    # ── Últimos pagamentos do dia ─────────────────────────────────────────────
    pagamentos_hoje = (
        Pagamento.objects
        .filter(
            parcela__emprestimo__rota__empresa=empresa,
            data_pagamento__date=hoje,
        )
        .select_related(
            'parcela__emprestimo__cliente',
            'parcela__emprestimo__rota',
            'recebido_por',
        )
        .order_by('-data_pagamento')[:5]
    )

    ctx = {
        'hoje':                       hoje,
        'carteira_ativa':             carteira_ativa,
        'saldo_devedor':              saldo_devedor,
        'total_inadimplente':         total_inadimplente,
        'recebido_hoje':              recebido_hoje,
        'saldo_caixas':               saldo_caixas,
        'total_clientes':             total_clientes,
        'total_emprestimos_ativos':   total_emprestimos_ativos,
        'total_inadimplentes_clientes': total_inadimplentes_clientes,
        'total_parcelas_vencendo_hoje': total_parcelas_vencendo_hoje,
        'rotas_resumo':               rotas_resumo,
        'ultimos_emprestimos':        ultimos_emprestimos,
        'clientes_inadimplentes':     clientes_inadimplentes,
        'pagamentos_hoje':            pagamentos_hoje,
    }
    return render(request, 'accounts/dashboard_admin.html', ctx)


@login_required
def dashboard_gerente(request):
    return render(request, 'accounts/dashboard_gerente.html')


@login_required
def dashboard_vendedor(request):
    return render(request, 'accounts/dashboard_vendedor.html')
