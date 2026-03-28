from django.db import models
from accounts.models import Usuario
from rotas.models import Rota, CaixaRota
from emprestimos.models import Parcela


class Pagamento(models.Model):
    FORMA_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'Pix'),
        ('transferencia', 'Transferência'),
    ]

    parcela = models.ForeignKey(Parcela, on_delete=models.PROTECT, related_name='pagamentos')
    recebido_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='pagamentos_recebidos')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    forma = models.CharField(max_length=20, choices=FORMA_CHOICES, default='dinheiro')
    data_pagamento = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'

    def __str__(self):
        return f'Pgto R$ {self.valor} — {self.parcela}'


class MovimentacaoFinanceira(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]

    ORIGEM_CHOICES = [
        ('pagamento', 'Pagamento de Parcela'),
        ('emprestimo', 'Concessão de Empréstimo'),
        ('aporte', 'Aporte de Capital'),
        ('retirada', 'Retirada'),
        ('ajuste', 'Ajuste Manual'),
    ]

    caixa = models.ForeignKey(CaixaRota, on_delete=models.PROTECT, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=2)
    referencia_pagamento = models.ForeignKey(
        Pagamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimentacoes'
    )
    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='movimentacoes')
    criado_em = models.DateTimeField(auto_now_add=True)
    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Movimentação Financeira'
        verbose_name_plural = 'Movimentações Financeiras'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.get_tipo_display()} R$ {self.valor} — {self.caixa.rota.nome}'
