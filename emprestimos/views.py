from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from accounts.decorators import requer_perfil
from rotas.models import Rota, VendedorRota
from .models import Emprestimo
from .forms import EmprestimoForm


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def emprestimo_lista(request):
    empresa = request.user.empresa
    qs = (
        Emprestimo.objects.filter(rota__empresa=empresa)
        .select_related('cliente', 'rota', 'vendedor')
        .order_by('-criado_em')
    )

    # Vendedor só vê os seus
    if request.user.perfil == 'vendedor':
        qs = qs.filter(vendedor=request.user)

    # Filtros
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(cliente__nome__icontains=q)

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    rota_id = request.GET.get('rota', '')
    if rota_id:
        qs = qs.filter(rota_id=rota_id)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    rotas = Rota.objects.filter(empresa=empresa, ativa=True).order_by('nome')

    return render(request, 'emprestimos/lista.html', {
        'page': page,
        'q': q,
        'status_filtro': status,
        'rota_filtro': rota_id,
        'rotas': rotas,
        'total': paginator.count,
    })


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def emprestimo_criar(request):
    empresa = request.user.empresa
    usuario = request.user

    if request.method == 'POST':
        form = EmprestimoForm(request.POST, empresa=empresa, usuario=usuario)
        if form.is_valid():
            emp = form.save()  # save() calcula totais, signal gera parcelas + saída caixa
            messages.success(request, f'Empréstimo #{emp.pk} criado para {emp.cliente.nome}.')
            return redirect('emprestimos:detalhe', pk=emp.pk)
    else:
        form = EmprestimoForm(empresa=empresa, usuario=usuario)

    return render(request, 'emprestimos/form.html', {
        'form': form,
        'titulo': 'Novo Empréstimo',
    })


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def emprestimo_detalhe(request, pk):
    empresa = request.user.empresa
    emp = get_object_or_404(
        Emprestimo.objects.select_related('cliente', 'rota', 'vendedor'),
        pk=pk, rota__empresa=empresa,
    )

    # Vendedor só vê os próprios
    if request.user.perfil == 'vendedor' and emp.vendedor != request.user:
        messages.error(request, 'Você não tem permissão para ver este empréstimo.')
        return redirect('emprestimos:lista')

    parcelas = emp.parcelas.order_by('numero')

    return render(request, 'emprestimos/detalhe.html', {
        'emp': emp,
        'parcelas': parcelas,
    })
