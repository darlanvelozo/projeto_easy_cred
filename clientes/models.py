from django.db import models
from accounts.models import Empresa
from rotas.models import Rota


class Cliente(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='clientes')
    rota = models.ForeignKey(Rota, on_delete=models.PROTECT, related_name='clientes', null=True, blank=True)
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.CharField(max_length=300, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nome


class ClienteDocumento(models.Model):
    TIPO_CHOICES = [
        ('rg', 'RG'),
        ('cpf', 'CPF'),
        ('comprovante_residencia', 'Comprovante de Residência'),
        ('foto', 'Foto'),
        ('outro', 'Outro'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='documentos')
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    arquivo = models.FileField(upload_to='clientes/documentos/')
    descricao = models.CharField(max_length=200, blank=True)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento do Cliente'
        verbose_name_plural = 'Documentos dos Clientes'

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.cliente.nome}'
