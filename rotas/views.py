from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from accounts.decorators import requer_perfil
from .models import Rota


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
