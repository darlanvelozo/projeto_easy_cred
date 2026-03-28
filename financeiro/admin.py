from django.contrib import admin
from .models import Pagamento, MovimentacaoFinanceira


class MovimentacaoInline(admin.TabularInline):
    model = MovimentacaoFinanceira
    extra = 0
    readonly_fields = ('tipo', 'origem', 'valor', 'saldo_anterior', 'saldo_posterior', 'registrado_por', 'criado_em')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'parcela', 'valor', 'forma', 'recebido_por', 'data_pagamento')
    list_filter = ('forma', 'parcela__emprestimo__rota__empresa')
    search_fields = ('parcela__emprestimo__cliente__nome', 'recebido_por__username')
    ordering = ('-data_pagamento',)
    readonly_fields = ('data_pagamento',)


@admin.register(MovimentacaoFinanceira)
class MovimentacaoFinanceiraAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'caixa', 'tipo', 'origem', 'valor',
        'saldo_anterior', 'saldo_posterior', 'registrado_por', 'criado_em',
    )
    list_filter = ('tipo', 'origem', 'caixa__rota__empresa')
    search_fields = ('caixa__rota__nome', 'registrado_por__username')
    ordering = ('-criado_em',)
    readonly_fields = ('saldo_anterior', 'saldo_posterior', 'criado_em')
