from django.db import models
from accounts.models import Empresa, Usuario


class Rota(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='rotas')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rota'
        verbose_name_plural = 'Rotas'

    def __str__(self):
        return f'{self.nome} — {self.empresa.nome}'


class ConfiguracaoRota(models.Model):
    PERIODICIDADE_CHOICES = [
        ('diario', 'Diário'),
        ('semanal', 'Semanal'),
        ('quinzenal', 'Quinzenal'),
        ('mensal', 'Mensal'),
    ]

    rota = models.OneToOneField(Rota, on_delete=models.CASCADE, related_name='configuracao')
    taxa_juros_padrao = models.DecimalField(max_digits=5, decimal_places=2, help_text='Taxa em % por período')
    periodicidade_padrao = models.CharField(max_length=20, choices=PERIODICIDADE_CHOICES, default='semanal')
    num_parcelas_padrao = models.PositiveSmallIntegerField(default=10)
    limite_emprestimo_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    multa_atraso = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Multa por atraso em % sobre o valor da parcela',
    )
    juros_mora_dia = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True,
        help_text='Juros de mora diario em % sobre o valor da parcela',
    )

    class Meta:
        verbose_name = 'Configuração de Rota'
        verbose_name_plural = 'Configurações de Rotas'

    def __str__(self):
        return f'Config — {self.rota.nome}'


class VendedorRota(models.Model):
    vendedor = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='rotas_vinculadas')
    rota = models.ForeignKey(Rota, on_delete=models.PROTECT, related_name='vendedores')
    ativo = models.BooleanField(default=True)
    vinculado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vendedor na Rota'
        verbose_name_plural = 'Vendedores nas Rotas'
        unique_together = ('vendedor', 'rota')

    def __str__(self):
        return f'{self.vendedor} → {self.rota.nome}'


class CaixaRota(models.Model):
    rota = models.OneToOneField(Rota, on_delete=models.PROTECT, related_name='caixa')
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Caixa da Rota'
        verbose_name_plural = 'Caixas das Rotas'

    def __str__(self):
        return f'Caixa {self.rota.nome} — R$ {self.saldo}'
