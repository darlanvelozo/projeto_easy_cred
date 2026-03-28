from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum

from accounts.decorators import requer_perfil
from rotas.models import Rota, CaixaRota, VendedorRota
from financeiro.models import MovimentacaoFinanceira
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

    # Calcular totais para pagamento parcial
    from financeiro.models import Pagamento
    for p in parcelas:
        p.total_pago = (
            Pagamento.objects.filter(parcela=p).aggregate(t=Sum('valor'))['t']
            or Decimal('0')
        )
        p.valor_restante = p.valor - p.total_pago

    return render(request, 'emprestimos/detalhe.html', {
        'emp': emp,
        'parcelas': parcelas,
    })


@login_required
@requer_perfil('admin')
def emprestimo_cancelar(request, pk):
    empresa = request.user.empresa
    emp = get_object_or_404(
        Emprestimo.objects.select_related('rota'),
        pk=pk, rota__empresa=empresa,
    )

    if emp.status == 'cancelado':
        messages.error(request, 'Este emprestimo ja esta cancelado.')
        return redirect('emprestimos:detalhe', pk=pk)

    if emp.status == 'quitado':
        messages.error(request, 'Nao e possivel cancelar um emprestimo quitado.')
        return redirect('emprestimos:detalhe', pk=pk)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, 'Informe o motivo do cancelamento.')
            return render(request, 'emprestimos/cancelar.html', {'emp': emp})

        # Calcular valor a estornar (valor principal - parcelas ja pagas)
        from financeiro.models import Pagamento
        total_pago = (
            Pagamento.objects.filter(parcela__emprestimo=emp)
            .aggregate(t=Sum('valor'))['t'] or Decimal('0')
        )
        valor_estorno = emp.valor_principal - total_pago
        if valor_estorno < 0:
            valor_estorno = Decimal('0')

        # Estornar no caixa
        if valor_estorno > 0:
            caixa, _ = CaixaRota.objects.get_or_create(rota=emp.rota)
            saldo_anterior = caixa.saldo
            saldo_posterior = saldo_anterior + valor_estorno

            MovimentacaoFinanceira.objects.create(
                caixa=caixa,
                tipo='entrada',
                origem='ajuste',
                valor=valor_estorno,
                saldo_anterior=saldo_anterior,
                saldo_posterior=saldo_posterior,
                registrado_por=request.user,
                descricao=f'Cancelamento emprestimo #{emp.pk} — {motivo}',
            )
            CaixaRota.objects.filter(pk=caixa.pk).update(saldo=saldo_posterior)

        # Cancelar parcelas pendentes/atrasadas
        emp.parcelas.filter(status__in=['pendente', 'atrasada']).update(status='cancelada')

        # Marcar emprestimo como cancelado
        emp.status = 'cancelado'
        emp.observacao = f'{emp.observacao}\n[CANCELADO] {motivo}'.strip()
        emp.save(update_fields=['status', 'observacao'])

        messages.success(
            request,
            f'Emprestimo #{emp.pk} cancelado. '
            f'Estorno de R$ {valor_estorno:.2f} no caixa.'
        )
        return redirect('emprestimos:detalhe', pk=pk)

    return render(request, 'emprestimos/cancelar.html', {'emp': emp})
