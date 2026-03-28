from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Emprestimo, Parcela
from rotas.models import CaixaRota
from financeiro.models import MovimentacaoFinanceira


def _delta(periodicidade, n):
    if periodicidade == 'diario':
        return timedelta(days=n)
    if periodicidade == 'semanal':
        return timedelta(weeks=n)
    if periodicidade == 'quinzenal':
        return timedelta(days=15 * n)
    return relativedelta(months=n)


@receiver(post_save, sender=Emprestimo)
def gerar_parcelas(sender, instance, created, **kwargs):
    if not created:
        return

    parcelas = []
    for i in range(1, instance.num_parcelas + 1):
        vencimento = instance.data_primeiro_vencimento + _delta(instance.periodicidade, i - 1)
        parcelas.append(Parcela(
            emprestimo=instance,
            numero=i,
            valor=instance.valor_parcela,
            vencimento=vencimento,
            status='pendente',
        ))
    Parcela.objects.bulk_create(parcelas)


@receiver(post_save, sender=Emprestimo)
def registrar_saida_caixa(sender, instance, created, **kwargs):
    if not created:
        return

    caixa, _ = CaixaRota.objects.get_or_create(rota=instance.rota)
    saldo_anterior = caixa.saldo
    saldo_posterior = saldo_anterior - instance.valor_principal

    MovimentacaoFinanceira.objects.create(
        caixa=caixa,
        tipo='saida',
        origem='emprestimo',
        valor=instance.valor_principal,
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior,
        registrado_por=instance.vendedor,
        descricao=f'Empréstimo #{instance.pk} — {instance.cliente.nome}',
    )

    CaixaRota.objects.filter(pk=caixa.pk).update(saldo=saldo_posterior)
