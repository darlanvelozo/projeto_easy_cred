from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Pagamento, MovimentacaoFinanceira
from rotas.models import CaixaRota


@receiver(post_save, sender=Pagamento)
def registrar_entrada_caixa(sender, instance, created, **kwargs):
    if not created:
        return

    rota = instance.parcela.emprestimo.rota
    caixa, _ = CaixaRota.objects.get_or_create(rota=rota)
    saldo_anterior = caixa.saldo
    saldo_posterior = saldo_anterior + instance.valor

    MovimentacaoFinanceira.objects.create(
        caixa=caixa,
        tipo='entrada',
        origem='pagamento',
        valor=instance.valor,
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior,
        referencia_pagamento=instance,
        registrado_por=instance.recebido_por,
        descricao=f'Parcela {instance.parcela.numero}/{instance.parcela.emprestimo.num_parcelas} — {instance.parcela.emprestimo.cliente.nome}',
    )

    CaixaRota.objects.filter(pk=caixa.pk).update(saldo=saldo_posterior)
