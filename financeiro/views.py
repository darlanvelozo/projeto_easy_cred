from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

from accounts.decorators import requer_perfil
from rotas.models import Rota, CaixaRota
from emprestimos.models import Parcela
from .models import MovimentacaoFinanceira
from .forms import PagamentoForm


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def registrar_pagamento(request, parcela_id):
    empresa = request.user.empresa
    parcela = get_object_or_404(
        Parcela.objects.select_related('emprestimo__cliente', 'emprestimo__rota'),
        pk=parcela_id,
        emprestimo__rota__empresa=empresa,
    )

    if parcela.status == 'paga':
        messages.error(request, 'Esta parcela já foi paga.')
        return redirect('emprestimos:detalhe', pk=parcela.emprestimo.pk)

    if request.method == 'POST':
        form = PagamentoForm(request.POST)
        if form.is_valid():
            pgto = form.save(commit=False)
            pgto.parcela = parcela
            pgto.recebido_por = request.user
            pgto.save()  # signal registra entrada no caixa

            # Marcar parcela como paga
            parcela.status = 'paga'
            parcela.pago_em = timezone.now()
            parcela.save(update_fields=['status', 'pago_em'])

            # Verificar se empréstimo foi quitado
            emp = parcela.emprestimo
            pendentes = emp.parcelas.exclude(status='paga').count()
            if pendentes == 0:
                emp.status = 'quitado'
                emp.save(update_fields=['status'])
                messages.success(request, f'Empréstimo #{emp.pk} quitado!')
            else:
                messages.success(request, f'Pagamento da parcela {parcela.numero}/{emp.num_parcelas} registrado.')

            return redirect('emprestimos:detalhe', pk=emp.pk)
    else:
        form = PagamentoForm(initial={'valor': parcela.valor})

    return render(request, 'financeiro/pagamento_form.html', {
        'form': form,
        'parcela': parcela,
    })


@login_required
@requer_perfil('admin', 'gerente')
def caixa_lista(request):
    empresa = request.user.empresa
    rotas = (
        Rota.objects.filter(empresa=empresa)
        .select_related('caixa')
        .order_by('nome')
    )

    return render(request, 'financeiro/caixa_lista.html', {'rotas': rotas})


@login_required
@requer_perfil('admin', 'gerente')
def caixa_movimentacoes(request, rota_id):
    empresa = request.user.empresa
    rota = get_object_or_404(Rota, pk=rota_id, empresa=empresa)
    caixa, _ = CaixaRota.objects.get_or_create(rota=rota)

    qs = MovimentacaoFinanceira.objects.filter(caixa=caixa).select_related('registrado_por').order_by('-criado_em')

    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'financeiro/caixa_movimentacoes.html', {
        'rota': rota,
        'caixa': caixa,
        'page': page,
    })
