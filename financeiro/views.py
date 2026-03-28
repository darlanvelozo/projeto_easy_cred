from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from django.utils import timezone

from accounts.decorators import requer_perfil
from rotas.models import Rota, CaixaRota
from emprestimos.models import Parcela
from .models import MovimentacaoFinanceira, Pagamento
from .forms import PagamentoForm, MovimentacaoCaixaForm


@login_required
@requer_perfil('admin', 'gerente', 'vendedor')
def registrar_pagamento(request, parcela_id):
    empresa = request.user.empresa
    parcela = get_object_or_404(
        Parcela.objects.select_related('emprestimo__cliente', 'emprestimo__rota'),
        pk=parcela_id,
        emprestimo__rota__empresa=empresa,
    )

    if parcela.status in ('paga', 'cancelada'):
        messages.error(request, 'Esta parcela nao pode receber pagamentos.')
        return redirect('emprestimos:detalhe', pk=parcela.emprestimo.pk)

    # Calcular valor ja pago e restante
    total_pago = (
        Pagamento.objects.filter(parcela=parcela)
        .aggregate(t=Sum('valor'))['t'] or Decimal('0')
    )
    valor_restante = parcela.valor - total_pago

    # Calcular multa e juros de mora se atrasada
    multa_valor = Decimal('0')
    juros_valor = Decimal('0')
    config = getattr(parcela.emprestimo.rota, 'configuracao', None)
    hoje = timezone.localdate()
    dias_atraso = max(0, (hoje - parcela.vencimento).days) if parcela.vencimento < hoje else 0

    if dias_atraso > 0 and config:
        if config.multa_atraso:
            multa_valor = valor_restante * config.multa_atraso / 100
        if config.juros_mora_dia:
            juros_valor = valor_restante * config.juros_mora_dia / 100 * dias_atraso

    valor_com_acrescimo = valor_restante + multa_valor + juros_valor

    # Historico de pagamentos desta parcela
    pagamentos_anteriores = Pagamento.objects.filter(parcela=parcela).order_by('-data_pagamento')

    if request.method == 'POST':
        form = PagamentoForm(request.POST)
        if form.is_valid():
            valor_recebido = form.cleaned_data['valor']

            if valor_recebido <= 0:
                messages.error(request, 'Valor deve ser maior que zero.')
            else:
                pgto = form.save(commit=False)
                pgto.parcela = parcela
                pgto.recebido_por = request.user
                pgto.save()  # signal registra entrada no caixa

                # Verificar se parcela foi totalmente paga
                novo_total_pago = total_pago + valor_recebido
                if novo_total_pago >= parcela.valor:
                    parcela.status = 'paga'
                    parcela.pago_em = timezone.now()
                    parcela.save(update_fields=['status', 'pago_em'])

                    # Verificar se emprestimo foi quitado
                    emp = parcela.emprestimo
                    pendentes = emp.parcelas.exclude(status__in=['paga', 'cancelada']).count()
                    if pendentes == 0:
                        emp.status = 'quitado'
                        emp.save(update_fields=['status'])
                        messages.success(request, f'Emprestimo #{emp.pk} quitado!')
                    else:
                        messages.success(
                            request,
                            f'Parcela {parcela.numero}/{emp.num_parcelas} paga integralmente.'
                        )
                else:
                    messages.success(
                        request,
                        f'Pagamento parcial registrado. '
                        f'Restante: R$ {(parcela.valor - novo_total_pago):.2f}'
                    )

                return redirect('emprestimos:detalhe', pk=parcela.emprestimo.pk)
    else:
        form = PagamentoForm(initial={'valor': valor_com_acrescimo})

    return render(request, 'financeiro/pagamento_form.html', {
        'form': form,
        'parcela': parcela,
        'total_pago': total_pago,
        'valor_restante': valor_restante,
        'multa_valor': multa_valor,
        'juros_valor': juros_valor,
        'valor_com_acrescimo': valor_com_acrescimo,
        'dias_atraso': dias_atraso,
        'pagamentos_anteriores': pagamentos_anteriores,
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


@login_required
@requer_perfil('admin', 'gerente')
def caixa_aporte(request, rota_id):
    empresa = request.user.empresa
    rota = get_object_or_404(Rota, pk=rota_id, empresa=empresa)
    caixa, _ = CaixaRota.objects.get_or_create(rota=rota)

    if request.method == 'POST':
        form = MovimentacaoCaixaForm(request.POST)
        if form.is_valid():
            valor = form.cleaned_data['valor']
            descricao = form.cleaned_data['descricao']

            saldo_anterior = caixa.saldo
            saldo_posterior = saldo_anterior + valor

            MovimentacaoFinanceira.objects.create(
                caixa=caixa,
                tipo='entrada',
                origem='aporte',
                valor=valor,
                saldo_anterior=saldo_anterior,
                saldo_posterior=saldo_posterior,
                registrado_por=request.user,
                descricao=descricao,
            )
            CaixaRota.objects.filter(pk=caixa.pk).update(saldo=saldo_posterior)

            messages.success(request, f'Aporte de R$ {valor:.2f} realizado na rota "{rota.nome}".')
            return redirect('financeiro:caixa_movimentacoes', rota_id=rota.pk)
    else:
        form = MovimentacaoCaixaForm()

    return render(request, 'financeiro/caixa_movimentacao.html', {
        'form': form,
        'rota': rota,
        'caixa': caixa,
        'tipo': 'aporte',
        'titulo': f'Aporte — {rota.nome}',
    })


@login_required
@requer_perfil('admin')
def caixa_retirada(request, rota_id):
    empresa = request.user.empresa
    rota = get_object_or_404(Rota, pk=rota_id, empresa=empresa)
    caixa, _ = CaixaRota.objects.get_or_create(rota=rota)

    if request.method == 'POST':
        form = MovimentacaoCaixaForm(request.POST)
        if form.is_valid():
            valor = form.cleaned_data['valor']
            descricao = form.cleaned_data['descricao']

            saldo_anterior = caixa.saldo
            saldo_posterior = saldo_anterior - valor

            MovimentacaoFinanceira.objects.create(
                caixa=caixa,
                tipo='saida',
                origem='retirada',
                valor=valor,
                saldo_anterior=saldo_anterior,
                saldo_posterior=saldo_posterior,
                registrado_por=request.user,
                descricao=descricao,
            )
            CaixaRota.objects.filter(pk=caixa.pk).update(saldo=saldo_posterior)

            messages.success(request, f'Retirada de R$ {valor:.2f} da rota "{rota.nome}".')
            return redirect('financeiro:caixa_movimentacoes', rota_id=rota.pk)
    else:
        form = MovimentacaoCaixaForm()

    return render(request, 'financeiro/caixa_movimentacao.html', {
        'form': form,
        'rota': rota,
        'caixa': caixa,
        'tipo': 'retirada',
        'titulo': f'Retirada — {rota.nome}',
    })
