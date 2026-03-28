from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Empresa, Usuario


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'email', 'telefone', 'ativo', 'criado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'cnpj', 'email')
    ordering = ('nome',)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'empresa', 'perfil', 'email', 'ativo', 'is_staff')
    list_filter = ('perfil', 'ativo', 'empresa')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Dados do Sistema', {
            'fields': ('empresa', 'perfil', 'telefone', 'ativo'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados do Sistema', {
            'fields': ('empresa', 'perfil', 'telefone'),
        }),
    )
