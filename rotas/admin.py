from django.contrib import admin
from .models import Rota, ConfiguracaoRota, VendedorRota, CaixaRota


class ConfiguracaoRotaInline(admin.StackedInline):
    model = ConfiguracaoRota
    extra = 1
    can_delete = False


class CaixaRotaInline(admin.StackedInline):
    model = CaixaRota
    extra = 0
    readonly_fields = ('saldo', 'atualizado_em')
    can_delete = False


class VendedorRotaInline(admin.TabularInline):
    model = VendedorRota
    extra = 1
    autocomplete_fields = ('vendedor',)


@admin.register(Rota)
class RotaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'ativa', 'criado_em')
    list_filter = ('ativa', 'empresa')
    search_fields = ('nome', 'empresa__nome')
    ordering = ('empresa', 'nome')
    inlines = [ConfiguracaoRotaInline, CaixaRotaInline, VendedorRotaInline]


@admin.register(VendedorRota)
class VendedorRotaAdmin(admin.ModelAdmin):
    list_display = ('vendedor', 'rota', 'ativo', 'vinculado_em')
    list_filter = ('ativo', 'rota__empresa')
    search_fields = ('vendedor__username', 'vendedor__first_name', 'rota__nome')


@admin.register(CaixaRota)
class CaixaRotaAdmin(admin.ModelAdmin):
    list_display = ('rota', 'saldo', 'atualizado_em')
    readonly_fields = ('saldo', 'atualizado_em')
    search_fields = ('rota__nome',)
