from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum

from accounts.decorators import requer_perfil
from clientes.models import Cliente
from emprestimos.models import Emprestimo, Parcela
from .models import Rota, VendedorRota, CaixaRota


@login_required
@requer_perfil('admin', 'gerente')
def rota_lista(request):
    empresa = request.user.empresa
    rotas = (
        Rota.objects.filter(empresa=empresa)
        .select_related('configuracao', 'caixa')
        .annotate(
            total_clientes=Count('clientes', filter=Q(clientes__ativo=True)),
            total_emprestimos=Count('emprestimos', filter=Q(emprestimos__status='ativo')),
            total_vendedores=Count('vendedores', filter=Q(vendedores__ativo=True)),
        )
        .order_by('nome')
    )

    return render(request, 'rotas/lista.html', {'rotas': rotas})


@login_required
@requer_perfil('admin', 'gerente')
def rota_detalhe(request, pk):
    empresa = request.user.empresa
    rota = get_object_or_404(
        Rota.objects.select_related('configuracao', 'caixa'),
        pk=pk, empresa=empresa,
    )

    clientes = Cliente.objects.filter(rota=rota, ativo=True).order_by('nome')
    emprestimos_ativos = (
        Emprestimo.objects.filter(rota=rota, status='ativo')
        .select_related('cliente', 'vendedor')
        .order_by('-criado_em')
    )
    vendedores = (
        VendedorRota.objects.filter(rota=rota, ativo=True)
        .select_related('vendedor')
    )

    carteira = emprestimos_ativos.aggregate(t=Sum('valor_total'))['t'] or Decimal('0')
    total_inadimplentes = Emprestimo.objects.filter(rota=rota, status='inadimplente').count()
    parcelas_atrasadas = Parcela.objects.filter(
        emprestimo__rota=rota, status='atrasada'
    ).aggregate(t=Sum('valor'))['t'] or Decimal('0')

    caixa, _ = CaixaRota.objects.get_or_create(rota=rota)

    return render(request, 'rotas/detalhe.html', {
        'rota': rota,
        'clientes': clientes,
        'emprestimos_ativos': emprestimos_ativos,
        'vendedores': vendedores,
        'carteira': carteira,
        'total_inadimplentes': total_inadimplentes,
        'parcelas_atrasadas': parcelas_atrasadas,
        'caixa': caixa,
    })
