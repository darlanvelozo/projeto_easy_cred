from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone

from .decorators import requer_perfil
from .models import Usuario
from rotas.models import Rota, CaixaRota, VendedorRota, ConfiguracaoRota
from clientes.models import Cliente
from emprestimos.models import Emprestimo, Parcela
from financeiro.models import Pagamento, MovimentacaoFinanceira


# ── Autenticação ──────────────────────────────────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rota_resumo(rota):
    """Monta dict resumo de uma rota para uso nos dashboards."""
    emp_ativos = Emprestimo.objects.filter(rota=rota, status='ativo').count()
    emp_inadimp = Emprestimo.objects.filter(rota=rota, status='inadimplente').count()
    carteira_rota = (
        Emprestimo.objects.filter(rota=rota, status='ativo')
        .aggregate(t=Sum('valor_total'))['t'] or Decimal('0')
    )
    clientes_rota = Cliente.objects.filter(rota=rota, ativo=True).count()
    vendedores_rota = rota.vendedores.filter(ativo=True).count()
    caixa = getattr(rota, 'caixa', None)
    config = getattr(rota, 'configuracao', None)

    return {
        'rota':          rota,
        'config':        config,
        'ativos':        emp_ativos,
        'inadimplentes': emp_inadimp,
        'carteira':      carteira_rota,
        'clientes':      clientes_rota,
        'num_vendedores': vendedores_rota,
        'saldo':         caixa.saldo if caixa else Decimal('0'),
        'atualizado_em': caixa.atualizado_em if caixa else None,
    }


def _clientes_inadimplentes(empresa, hoje, limite=6):
    """Retorna lista de dicts pré-computados de clientes inadimplentes."""
    clientes_base = (
        Cliente.objects
        .filter(empresa=empresa, emprestimos__status='inadimplente')
        .distinct()
        .select_related('rota')[:limite]
    )

    resultado = []
    for cliente in clientes_base:
        parcelas_atrasadas = Parcela.objects.filter(
            emprestimo__cliente=cliente,
            status='atrasada',
        )
        valor_atrasado = parcelas_atrasadas.aggregate(t=Sum('valor'))['t'] or Decimal('0')
        qtd_atrasadas = parcelas_atrasadas.count()
        mais_antiga = parcelas_atrasadas.order_by('vencimento').first()
        dias_atraso = (hoje - mais_antiga.vencimento).days if mais_antiga else 0

        resultado.append({
            'nome':          cliente.nome,
            'rota':          cliente.rota.nome if cliente.rota else '—',
            'telefone':      cliente.telefone,
            'valor_atrasado': valor_atrasado,
            'qtd_atrasadas': qtd_atrasadas,
            'dias_atraso':   dias_atraso,
        })
    return resultado


# ── Dashboard Admin SaaS ──────────────────────────────────────────────────────

@login_required
@requer_perfil('admin')
def dashboard_admin(request):
    empresa = request.user.empresa
    hoje = timezone.localdate()

    carteira_ativa = (
        Emprestimo.objects
        .filter(rota__empresa=empresa, status='ativo')
        .aggregate(total=Sum('valor_total'))['total'] or Decimal('0')
    )

    saldo_devedor = (
        Parcela.objects
        .filter(
            emprestimo__rota__empresa=empresa,
            emprestimo__status='ativo',
            status__in=['pendente', 'atrasada'],
        )
        .aggregate(total=Sum('valor'))['total'] or Decimal('0')
    )

    total_inadimplente = (
        Parcela.objects
        .filter(emprestimo__rota__empresa=empresa, status='atrasada')
        .aggregate(total=Sum('valor'))['total'] or Decimal('0')
    )

    recebido_hoje = (
        Pagamento.objects
        .filter(parcela__emprestimo__rota__empresa=empresa, data_pagamento__date=hoje)
        .aggregate(total=Sum('valor'))['total'] or Decimal('0')
    )

    saldo_caixas = (
        CaixaRota.objects
        .filter(rota__empresa=empresa)
        .aggregate(total=Sum('saldo'))['total'] or Decimal('0')
    )

    total_clientes = Cliente.objects.filter(empresa=empresa, ativo=True).count()
    total_emprestimos_ativos = Emprestimo.objects.filter(rota__empresa=empresa, status='ativo').count()
    total_inadimplentes_clientes = (
        Cliente.objects
        .filter(empresa=empresa, emprestimos__status='inadimplente')
        .distinct().count()
    )
    total_parcelas_vencendo_hoje = Parcela.objects.filter(
        emprestimo__rota__empresa=empresa, vencimento=hoje, status='pendente',
    ).count()

    rotas = (
        Rota.objects.filter(empresa=empresa, ativa=True)
        .select_related('configuracao', 'caixa')
    )
    rotas_resumo = [_rota_resumo(r) for r in rotas]

    ultimos_emprestimos = (
        Emprestimo.objects
        .filter(rota__empresa=empresa)
        .select_related('cliente', 'rota', 'vendedor')
        .order_by('-criado_em')[:8]
    )

    clientes_inadimplentes = _clientes_inadimplentes(empresa, hoje)

    pagamentos_hoje = (
        Pagamento.objects
        .filter(parcela__emprestimo__rota__empresa=empresa, data_pagamento__date=hoje)
        .select_related('parcela__emprestimo__cliente', 'parcela__emprestimo__rota', 'recebido_por')
        .order_by('-data_pagamento')[:5]
    )

    return render(request, 'accounts/dashboard_admin.html', {
        'hoje': hoje,
        'carteira_ativa': carteira_ativa,
        'saldo_devedor': saldo_devedor,
        'total_inadimplente': total_inadimplente,
        'recebido_hoje': recebido_hoje,
        'saldo_caixas': saldo_caixas,
        'total_clientes': total_clientes,
        'total_emprestimos_ativos': total_emprestimos_ativos,
        'total_inadimplentes_clientes': total_inadimplentes_clientes,
        'total_parcelas_vencendo_hoje': total_parcelas_vencendo_hoje,
        'rotas_resumo': rotas_resumo,
        'ultimos_emprestimos': ultimos_emprestimos,
        'clientes_inadimplentes': clientes_inadimplentes,
        'pagamentos_hoje': pagamentos_hoje,
    })


# ── Dashboard Gerente ─────────────────────────────────────────────────────────

@login_required
@requer_perfil('admin', 'gerente')
def dashboard_gerente(request):
    empresa = request.user.empresa
    hoje = timezone.localdate()
    semana = hoje + timedelta(days=7)

    rotas = (
        Rota.objects.filter(empresa=empresa, ativa=True)
        .select_related('configuracao', 'caixa')
    )
    rotas_resumo = [_rota_resumo(r) for r in rotas]

    vendedores = (
        Usuario.objects
        .filter(empresa=empresa, perfil='vendedor', ativo=True)
        .prefetch_related('rotas_vinculadas__rota')
    )

    vendedores_resumo = []
    for v in vendedores:
        rotas_nomes = ', '.join(
            vr.rota.nome for vr in v.rotas_vinculadas.filter(ativo=True)
        )
        emp_ativos = Emprestimo.objects.filter(vendedor=v, status='ativo').count()
        coletado_hoje = (
            Pagamento.objects.filter(recebido_por=v, data_pagamento__date=hoje)
            .aggregate(t=Sum('valor'))['t'] or Decimal('0')
        )
        vendedores_resumo.append({
            'vendedor':     v,
            'rotas':        rotas_nomes or '—',
            'emp_ativos':   emp_ativos,
            'coletado_hoje': coletado_hoje,
        })

    total_clientes = Cliente.objects.filter(empresa=empresa, ativo=True).count()
    total_emprestimos_ativos = Emprestimo.objects.filter(rota__empresa=empresa, status='ativo').count()
    total_inadimplentes_clientes = (
        Cliente.objects
        .filter(empresa=empresa, emprestimos__status='inadimplente')
        .distinct().count()
    )

    proximas_parcelas = (
        Parcela.objects
        .filter(
            emprestimo__rota__empresa=empresa,
            status='pendente',
            vencimento__range=(hoje, semana),
        )
        .select_related('emprestimo__cliente', 'emprestimo__rota', 'emprestimo__vendedor')
        .order_by('vencimento')[:10]
    )

    return render(request, 'accounts/dashboard_gerente.html', {
        'hoje': hoje,
        'rotas_resumo': rotas_resumo,
        'vendedores_resumo': vendedores_resumo,
        'total_clientes': total_clientes,
        'total_emprestimos_ativos': total_emprestimos_ativos,
        'total_inadimplentes_clientes': total_inadimplentes_clientes,
        'total_rotas_ativas': len(rotas_resumo),
        'total_vendedores': len(vendedores_resumo),
        'proximas_parcelas': proximas_parcelas,
    })


# ── Dashboard Vendedor ────────────────────────────────────────────────────────

@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def dashboard_vendedor(request):
    user = request.user
    empresa = user.empresa
    hoje = timezone.localdate()

    rotas_ids = VendedorRota.objects.filter(
        vendedor=user, ativo=True
    ).values_list('rota_id', flat=True)

    minha_carteira = (
        Emprestimo.objects
        .filter(vendedor=user, status='ativo')
        .select_related('cliente', 'rota')
        .order_by('cliente__nome')
    )

    valor_carteira = minha_carteira.aggregate(t=Sum('valor_total'))['t'] or Decimal('0')

    parcelas_hoje = (
        Parcela.objects
        .filter(
            emprestimo__vendedor=user,
            emprestimo__status__in=['ativo', 'inadimplente'],
            vencimento=hoje,
            status__in=['pendente', 'atrasada'],
        )
        .select_related('emprestimo__cliente', 'emprestimo__rota')
        .order_by('emprestimo__cliente__nome')
    )
    valor_parcelas_hoje = parcelas_hoje.aggregate(t=Sum('valor'))['t'] or Decimal('0')

    recebido_hoje = (
        Pagamento.objects
        .filter(recebido_por=user, data_pagamento__date=hoje)
        .aggregate(t=Sum('valor'))['t'] or Decimal('0')
    )

    inadimplentes = (
        Cliente.objects
        .filter(rota_id__in=rotas_ids, emprestimos__status='inadimplente')
        .distinct()
        .select_related('rota')[:8]
    )

    inadimplentes_resumo = []
    for cliente in inadimplentes:
        parcelas_atr = Parcela.objects.filter(
            emprestimo__cliente=cliente, status='atrasada',
        )
        valor_atr = parcelas_atr.aggregate(t=Sum('valor'))['t'] or Decimal('0')
        qtd_atr = parcelas_atr.count()
        mais_antiga = parcelas_atr.order_by('vencimento').first()
        dias = (hoje - mais_antiga.vencimento).days if mais_antiga else 0

        inadimplentes_resumo.append({
            'nome': cliente.nome,
            'rota': cliente.rota.nome if cliente.rota else '—',
            'telefone': cliente.telefone,
            'valor_atrasado': valor_atr,
            'qtd_atrasadas': qtd_atr,
            'dias_atraso': dias,
        })

    # Parcelas restantes por empréstimo ativo (para resumo da carteira)
    carteira_resumo = []
    for emp in minha_carteira[:15]:
        restantes = emp.parcelas.filter(status__in=['pendente', 'atrasada']).count()
        prox = emp.parcelas.filter(status='pendente').order_by('vencimento').first()
        carteira_resumo.append({
            'emprestimo': emp,
            'restantes': restantes,
            'proximo_vencimento': prox.vencimento if prox else None,
            'valor_parcela': emp.valor_parcela,
        })

    return render(request, 'accounts/dashboard_vendedor.html', {
        'hoje': hoje,
        'minha_carteira': carteira_resumo,
        'valor_carteira': valor_carteira,
        'parcelas_hoje': parcelas_hoje,
        'valor_parcelas_hoje': valor_parcelas_hoje,
        'recebido_hoje': recebido_hoje,
        'inadimplentes_resumo': inadimplentes_resumo,
        'total_emprestimos_ativos': minha_carteira.count(),
        'total_parcelas_hoje': parcelas_hoje.count(),
        'total_inadimplentes': len(inadimplentes_resumo),
    })


# ── Relatórios ───────────────────────────────────────────────────────────────

@login_required
@requer_perfil('admin', 'gerente')
def relatorios(request):
    empresa = request.user.empresa
    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)

    # Inadimplência
    clientes_inadimp = (
        Cliente.objects.filter(empresa=empresa, emprestimos__status='inadimplente')
        .distinct().count()
    )
    valor_inadimp = (
        Parcela.objects.filter(emprestimo__rota__empresa=empresa, status='atrasada')
        .aggregate(t=Sum('valor'))['t'] or Decimal('0')
    )
    parcelas_atrasadas = Parcela.objects.filter(
        emprestimo__rota__empresa=empresa, status='atrasada'
    ).count()

    # Recebimentos do mês
    recebido_mes = (
        Pagamento.objects.filter(
            parcela__emprestimo__rota__empresa=empresa,
            data_pagamento__date__gte=inicio_mes,
        ).aggregate(t=Sum('valor'))['t'] or Decimal('0')
    )
    pagamentos_mes = Pagamento.objects.filter(
        parcela__emprestimo__rota__empresa=empresa,
        data_pagamento__date__gte=inicio_mes,
    ).count()

    # Empréstimos concedidos no mês
    emprestimos_mes = Emprestimo.objects.filter(
        rota__empresa=empresa, criado_em__date__gte=inicio_mes,
    ).count()
    valor_concedido_mes = (
        Emprestimo.objects.filter(rota__empresa=empresa, criado_em__date__gte=inicio_mes)
        .aggregate(t=Sum('valor_principal'))['t'] or Decimal('0')
    )

    # Carteira por rota
    rotas = Rota.objects.filter(empresa=empresa, ativa=True).select_related('caixa')
    carteira_rotas = []
    for rota in rotas:
        ativos = Emprestimo.objects.filter(rota=rota, status='ativo').count()
        carteira = (
            Emprestimo.objects.filter(rota=rota, status='ativo')
            .aggregate(t=Sum('valor_total'))['t'] or Decimal('0')
        )
        inadimp = Emprestimo.objects.filter(rota=rota, status='inadimplente').count()
        recebido_rota = (
            Pagamento.objects.filter(
                parcela__emprestimo__rota=rota,
                data_pagamento__date__gte=inicio_mes,
            ).aggregate(t=Sum('valor'))['t'] or Decimal('0')
        )
        saldo = rota.caixa.saldo if hasattr(rota, 'caixa') else Decimal('0')
        carteira_rotas.append({
            'rota': rota,
            'ativos': ativos,
            'carteira': carteira,
            'inadimplentes': inadimp,
            'recebido_mes': recebido_rota,
            'saldo': saldo,
        })

    # Top inadimplentes
    inadimplentes = _clientes_inadimplentes(empresa, hoje, limite=10)

    return render(request, 'accounts/relatorios.html', {
        'hoje': hoje,
        'inicio_mes': inicio_mes,
        'clientes_inadimp': clientes_inadimp,
        'valor_inadimp': valor_inadimp,
        'parcelas_atrasadas': parcelas_atrasadas,
        'recebido_mes': recebido_mes,
        'pagamentos_mes': pagamentos_mes,
        'emprestimos_mes': emprestimos_mes,
        'valor_concedido_mes': valor_concedido_mes,
        'carteira_rotas': carteira_rotas,
        'inadimplentes': inadimplentes,
    })


# ── Configurações ────────────────────────────────────────────────────────────

@login_required
@requer_perfil('admin')
def configuracoes(request):
    empresa = request.user.empresa
    rotas = Rota.objects.filter(empresa=empresa).select_related('configuracao').order_by('nome')
    vendedores = Usuario.objects.filter(empresa=empresa, perfil='vendedor').order_by('first_name')
    gerentes = Usuario.objects.filter(empresa=empresa, perfil='gerente').order_by('first_name')

    return render(request, 'accounts/configuracoes.html', {
        'empresa': empresa,
        'rotas': rotas,
        'vendedores': vendedores,
        'gerentes': gerentes,
    })
