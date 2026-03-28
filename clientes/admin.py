from django.contrib import admin
from .models import Cliente, ClienteDocumento


class ClienteDocumentoInline(admin.TabularInline):
    model = ClienteDocumento
    extra = 1
    readonly_fields = ('enviado_em',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'telefone', 'rota', 'empresa', 'ativo', 'criado_em')
    list_filter = ('ativo', 'empresa', 'rota')
    search_fields = ('nome', 'cpf', 'telefone')
    ordering = ('nome',)
    inlines = [ClienteDocumentoInline]
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('nome', 'cpf', 'telefone'),
        }),
        ('Endereço', {
            'fields': ('endereco', 'bairro', 'cidade', 'uf'),
        }),
        ('Vinculação', {
            'fields': ('empresa', 'rota', 'ativo'),
        }),
    )
