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

    # ── Métricas principais ──────────────────────────────────────────────────
    carteira_ativa = (
        Emprestimo.objects
        .filter(rota__empresa=empresa, status='ativo')
        .aggregate(total=Sum('valor_principal'))['total'] or Decimal('0')
    )

    total_inadimplente = (
        Parcela.objects
        .filter(emprestimo__rota__empresa=empresa, status='atrasada')
        .aggregate(total=Sum('valor'))['total'] or Decimal('0')
    )

    recebido_hoje = (
        Pagamento.objects
        .filter(
            parcela__emprestimo__rota__empresa=empresa,
            data_pagamento__date=hoje,
        )
        .aggregate(total=Sum('valor'))['total'] or Decimal('0')
    )

    saldo_caixas = (
        CaixaRota.objects
        .filter(rota__empresa=empresa)
        .aggregate(total=Sum('saldo'))['total'] or Decimal('0')
    )

    # ── Contadores ───────────────────────────────────────────────────────────
    total_clientes   = Cliente.objects.filter(empresa=empresa, ativo=True).count()
    total_emprestimos_ativos = Emprestimo.objects.filter(rota__empresa=empresa, status='ativo').count()
    total_inadimplentes_clientes = (
        Cliente.objects
        .filter(empresa=empresa, emprestimos__status='inadimplente')
        .distinct().count()
    )

    # ── Rotas com resumo ─────────────────────────────────────────────────────
    rotas = (
        Rota.objects
        .filter(empresa=empresa, ativa=True)
        .select_related('configuracao', 'caixa')
        .prefetch_related('vendedores')
    )

    rotas_resumo = []
    for rota in rotas:
        ativos = Emprestimo.objects.filter(rota=rota, status='ativo').count()
        inadimplentes = Emprestimo.objects.filter(rota=rota, status='inadimplente').count()
        saldo = getattr(rota, 'caixa', None)
        rotas_resumo.append({
            'rota': rota,
            'ativos': ativos,
            'inadimplentes': inadimplentes,
            'saldo': saldo.saldo if saldo else Decimal('0'),
            'num_vendedores': rota.vendedores.filter(ativo=True).count(),
        })

    # ── Últimos empréstimos ───────────────────────────────────────────────────
    ultimos_emprestimos = (
        Emprestimo.objects
        .filter(rota__empresa=empresa)
        .select_related('cliente', 'rota', 'vendedor')
        .order_by('-criado_em')[:8]
    )

    # ── Clientes inadimplentes ────────────────────────────────────────────────
    clientes_inadimplentes = (
        Cliente.objects
        .filter(empresa=empresa, emprestimos__status='inadimplente')
        .distinct()
        .prefetch_related('emprestimos')[:6]
    )

    ctx = {
        'hoje': hoje,
        'carteira_ativa': carteira_ativa,
        'total_inadimplente': total_inadimplente,
        'recebido_hoje': recebido_hoje,
        'saldo_caixas': saldo_caixas,
        'total_clientes': total_clientes,
        'total_emprestimos_ativos': total_emprestimos_ativos,
        'total_inadimplentes_clientes': total_inadimplentes_clientes,
        'rotas_resumo': rotas_resumo,
        'ultimos_emprestimos': ultimos_emprestimos,
        'clientes_inadimplentes': clientes_inadimplentes,
    }
    return render(request, 'accounts/dashboard_admin.html', ctx)


@login_required
def dashboard_gerente(request):
    return render(request, 'accounts/dashboard_gerente.html')


@login_required
def dashboard_vendedor(request):
    return render(request, 'accounts/dashboard_vendedor.html')
