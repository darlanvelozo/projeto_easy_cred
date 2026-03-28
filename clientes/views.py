from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from accounts.decorators import requer_perfil
from rotas.models import Rota, VendedorRota
from emprestimos.models import Emprestimo
from .models import Cliente
from .forms import ClienteForm


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def cliente_lista(request):
    empresa = request.user.empresa
    qs = Cliente.objects.filter(empresa=empresa).select_related('rota').order_by('nome')

    # Vendedor só vê clientes das suas rotas
    if request.user.perfil == 'vendedor':
        rotas_ids = VendedorRota.objects.filter(
            vendedor=request.user, ativo=True
        ).values_list('rota_id', flat=True)
        qs = qs.filter(rota_id__in=rotas_ids)

    # Busca
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(nome__icontains=q)

    # Filtro por rota
    rota_id = request.GET.get('rota', '')
    if rota_id:
        qs = qs.filter(rota_id=rota_id)

    # Filtro por status
    status = request.GET.get('status', '')
    if status == 'ativo':
        qs = qs.filter(ativo=True)
    elif status == 'inativo':
        qs = qs.filter(ativo=False)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    rotas = Rota.objects.filter(empresa=empresa, ativa=True).order_by('nome')

    return render(request, 'clientes/lista.html', {
        'page': page,
        'q': q,
        'rota_filtro': rota_id,
        'status_filtro': status,
        'rotas': rotas,
        'total': paginator.count,
    })


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def cliente_detalhe(request, pk):
    empresa = request.user.empresa
    cliente = get_object_or_404(Cliente, pk=pk, empresa=empresa)

    # Vendedor só vê clientes das suas rotas
    if request.user.perfil == 'vendedor':
        rotas_ids = VendedorRota.objects.filter(
            vendedor=request.user, ativo=True
        ).values_list('rota_id', flat=True)
        if cliente.rota_id not in rotas_ids:
            messages.error(request, 'Você não tem permissão para ver este cliente.')
            return redirect('clientes:lista')

    emprestimos = (
        Emprestimo.objects.filter(cliente=cliente)
        .select_related('rota', 'vendedor')
        .order_by('-criado_em')
    )

    return render(request, 'clientes/detalhe.html', {
        'cliente': cliente,
        'emprestimos': emprestimos,
    })


@login_required
@requer_perfil('admin', 'gerente')
def cliente_criar(request):
    empresa = request.user.empresa
    if request.method == 'POST':
        form = ClienteForm(request.POST, empresa=empresa)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.empresa = empresa
            cliente.save()
            messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso.')
            return redirect('clientes:lista')
    else:
        form = ClienteForm(empresa=empresa)

    return render(request, 'clientes/form.html', {
        'form': form,
        'titulo': 'Novo Cliente',
    })


@login_required
@requer_perfil('admin', 'gerente')
def cliente_editar(request, pk):
    empresa = request.user.empresa
    cliente = get_object_or_404(Cliente, pk=pk, empresa=empresa)

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente, empresa=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cliente "{cliente.nome}" atualizado.')
            return redirect('clientes:lista')
    else:
        form = ClienteForm(instance=cliente, empresa=empresa)

    return render(request, 'clientes/form.html', {
        'form': form,
        'titulo': 'Editar Cliente',
        'cliente': cliente,
    })
