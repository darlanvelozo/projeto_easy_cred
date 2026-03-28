from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from accounts.models import Usuario
from rotas.models import Rota
from clientes.models import Cliente


class Emprestimo(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('quitado', 'Quitado'),
        ('inadimplente', 'Inadimplente'),
        ('cancelado', 'Cancelado'),
    ]

    PERIODICIDADE_CHOICES = [
        ('diario', 'Diário'),
        ('semanal', 'Semanal'),
        ('quinzenal', 'Quinzenal'),
        ('mensal', 'Mensal'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='emprestimos')
    rota = models.ForeignKey(Rota, on_delete=models.PROTECT, related_name='emprestimos')
    vendedor = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='emprestimos')
    valor_principal = models.DecimalField(max_digits=10, decimal_places=2)
    taxa_juros = models.DecimalField(max_digits=5, decimal_places=2, help_text='Taxa em % aplicada no momento da criação')
    num_parcelas = models.PositiveSmallIntegerField()
    periodicidade = models.CharField(max_length=20, choices=PERIODICIDADE_CHOICES, default='semanal')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    data_primeiro_vencimento = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    criado_em = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'

    def save(self, *args, **kwargs):
        # Juros simples: total = principal * (1 + taxa/100)
        taxa_decimal = self.taxa_juros / 100
        self.valor_total = self.valor_principal * (1 + taxa_decimal)
        self.valor_parcela = self.valor_total / self.num_parcelas
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Empréstimo #{self.pk} — {self.cliente.nome} R$ {self.valor_principal}'


class Parcela(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('paga', 'Paga'),
        ('atrasada', 'Atrasada'),
        ('cancelada', 'Cancelada'),
    ]

    emprestimo = models.ForeignKey(Emprestimo, on_delete=models.PROTECT, related_name='parcelas')
    numero = models.PositiveSmallIntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    pago_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Parcela'
        verbose_name_plural = 'Parcelas'
        ordering = ['emprestimo', 'numero']
        unique_together = ('emprestimo', 'numero')

    def __str__(self):
        return f'Parcela {self.numero}/{self.emprestimo.num_parcelas} — {self.emprestimo.cliente.nome}'
