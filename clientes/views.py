import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from accounts.decorators import requer_perfil
from rotas.models import Rota, VendedorRota
from emprestimos.models import Emprestimo, Parcela
from .models import Cliente
from .forms import ClienteForm


def _rotas_do_vendedor(user):
    return VendedorRota.objects.filter(
        vendedor=user, ativo=True,
    ).values_list('rota_id', flat=True)


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def cliente_lista(request):
    empresa = request.user.empresa
    qs = Cliente.objects.filter(empresa=empresa).select_related('rota').order_by('nome')

    # Vendedor so ve clientes das suas rotas
    if request.user.perfil == 'vendedor':
        qs = qs.filter(rota_id__in=_rotas_do_vendedor(request.user))

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

    # Vendedor so ve clientes das suas rotas
    if request.user.perfil == 'vendedor':
        if cliente.rota_id not in list(_rotas_do_vendedor(request.user)):
            messages.error(request, 'Voce nao tem permissao para ver este cliente.')
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
@requer_perfil('admin', 'gerente', 'vendedor')
def cliente_criar(request):
    empresa = request.user.empresa
    usuario = request.user

    if request.method == 'POST':
        form = ClienteForm(request.POST, empresa=empresa, usuario=usuario)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.empresa = empresa
            cliente.save()
            messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso.')
            return redirect('clientes:detalhe', pk=cliente.pk)
    else:
        form = ClienteForm(empresa=empresa, usuario=usuario)

    return render(request, 'clientes/form.html', {
        'form': form,
        'titulo': 'Novo Cliente',
    })


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def cliente_editar(request, pk):
    empresa = request.user.empresa
    usuario = request.user
    cliente = get_object_or_404(Cliente, pk=pk, empresa=empresa)

    # Vendedor so edita clientes das suas rotas
    if usuario.perfil == 'vendedor':
        if cliente.rota_id not in list(_rotas_do_vendedor(usuario)):
            messages.error(request, 'Voce nao tem permissao para editar este cliente.')
            return redirect('clientes:lista')

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente, empresa=empresa, usuario=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cliente "{cliente.nome}" atualizado.')
            return redirect('clientes:detalhe', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente, empresa=empresa, usuario=usuario)

    return render(request, 'clientes/form.html', {
        'form': form,
        'titulo': 'Editar Cliente',
        'cliente': cliente,
    })


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def cliente_mapa(request):
    empresa = request.user.empresa

    # Filtro por rota
    rota_id = request.GET.get('rota', '')

    qs = Cliente.objects.filter(
        empresa=empresa, ativo=True,
        latitude__isnull=False, longitude__isnull=False,
    ).select_related('rota')

    if request.user.perfil == 'vendedor':
        qs = qs.filter(rota_id__in=_rotas_do_vendedor(request.user))

    if rota_id:
        qs = qs.filter(rota_id=rota_id)

    # Pre-compute loan stats per client
    from django.db.models import Count, Sum, Q
    from datetime import date

    clientes_list = list(qs)
    cliente_ids = [c.pk for c in clientes_list]

    # Active loans per client
    emp_stats = {}
    if cliente_ids:
        for row in Emprestimo.objects.filter(
            cliente_id__in=cliente_ids, status='ativo',
        ).values('cliente_id').annotate(
            total_ativos=Count('id'),
            valor_carteira=Sum('valor_total'),
        ):
            emp_stats[row['cliente_id']] = (row['total_ativos'], row['valor_carteira'])

    # Overdue installments per client
    parcelas_atrasadas = {}
    if cliente_ids:
        for row in Parcela.objects.filter(
            emprestimo__cliente_id__in=cliente_ids,
            status='atrasada',
        ).values('emprestimo__cliente_id').annotate(
            qtd=Count('id'),
            valor=Sum('valor'),
        ):
            parcelas_atrasadas[row['emprestimo__cliente_id']] = (row['qtd'], row['valor'])

    # Today's installments per client
    hoje = date.today()
    parcelas_hoje = {}
    if cliente_ids:
        for row in Parcela.objects.filter(
            emprestimo__cliente_id__in=cliente_ids,
            vencimento=hoje,
            status='pendente',
        ).values('emprestimo__cliente_id').annotate(
            qtd=Count('id'),
            valor=Sum('valor'),
        ):
            parcelas_hoje[row['emprestimo__cliente_id']] = (row['qtd'], row['valor'])

    clientes_data = []
    for c in clientes_list:
        emp_info = emp_stats.get(c.pk)
        atraso_info = parcelas_atrasadas.get(c.pk)
        hoje_info = parcelas_hoje.get(c.pk)

        clientes_data.append({
            'id': c.pk,
            'nome': c.nome,
            'telefone': c.telefone or '',
            'cpf': c.cpf or '',
            'rota': c.rota.nome if c.rota else '',
            'endereco': c.endereco or '',
            'bairro': c.bairro or '',
            'cidade': (c.cidade + '/' + c.uf) if c.cidade else '',
            'lat': float(c.latitude),
            'lng': float(c.longitude),
            'emprestimos_ativos': emp_info[0] if emp_info else 0,
            'valor_carteira': float(emp_info[1] or 0) if emp_info else 0,
            'parcelas_atrasadas': atraso_info[0] if atraso_info else 0,
            'valor_atrasado': float(atraso_info[1] or 0) if atraso_info else 0,
            'parcelas_hoje': hoje_info[0] if hoje_info else 0,
            'valor_hoje': float(hoje_info[1] or 0) if hoje_info else 0,
        })

    clientes_json = json.dumps(clientes_data)

    rotas = Rota.objects.filter(empresa=empresa, ativa=True).order_by('nome')
    if request.user.perfil == 'vendedor':
        rotas = rotas.filter(pk__in=_rotas_do_vendedor(request.user))

    return render(request, 'clientes/mapa.html', {
        'clientes_json': clientes_json,
        'total': qs.count(),
        'rotas': rotas,
        'rota_filtro': rota_id,
    })
