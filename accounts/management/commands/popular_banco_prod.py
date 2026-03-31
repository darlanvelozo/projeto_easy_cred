"""
Management command: popular_banco_prod
Popula o banco apenas se estiver vazio (para deploy em producao).
Roda automaticamente no Procfile sem resetar dados existentes.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from accounts.models import Usuario


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstracao se estiver vazio'

    def handle(self, *args, **options):
        if Usuario.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Banco ja possui dados — pulando popular_banco_prod.'
            ))
            return

        self.stdout.write(self.style.NOTICE('Banco vazio — populando dados de demonstracao...'))
        call_command('popular_banco')
        call_command('atualizar_parcelas')
        self.stdout.write(self.style.SUCCESS('Banco populado com sucesso!'))
