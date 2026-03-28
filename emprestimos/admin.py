from django.contrib import admin
from .models import Emprestimo, Parcela


class ParcelaInline(admin.TabularInline):
    model = Parcela
    extra = 0
    readonly_fields = ('numero', 'valor', 'vencimento', 'status', 'pago_em')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'cliente', 'rota', 'vendedor',
        'valor_principal', 'valor_total', 'num_parcelas',
        'periodicidade', 'status', 'criado_em',
    )
    list_filter = ('status', 'periodicidade', 'rota', 'rota__empresa')
    search_fields = ('cliente__nome', 'vendedor__username')
    ordering = ('-criado_em',)
    readonly_fields = ('valor_total', 'valor_parcela', 'criado_em')
    inlines = [ParcelaInline]
    fieldsets = (
        ('Contrato', {
            'fields': ('cliente', 'rota', 'vendedor', 'status', 'observacao'),
        }),
        ('Financeiro', {
            'fields': (
                'valor_principal', 'taxa_juros', 'valor_total',
                'num_parcelas', 'valor_parcela', 'periodicidade',
                'data_primeiro_vencimento',
            ),
        }),
        ('Auditoria', {
            'fields': ('criado_em',),
        }),
    )


@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = ('emprestimo', 'numero', 'valor', 'vencimento', 'status', 'pago_em')
    list_filter = ('status', 'emprestimo__rota__empresa')
    search_fields = ('emprestimo__cliente__nome',)
    ordering = ('emprestimo', 'numero')
    readonly_fields = ('pago_em',)
