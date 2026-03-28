from django.core.management.base import BaseCommand
from django.utils import timezone

from emprestimos.models import Emprestimo, Parcela


class Command(BaseCommand):
    help = 'Marca parcelas vencidas como atrasadas e emprestimos com atraso como inadimplentes.'

    def handle(self, *args, **options):
        hoje = timezone.localdate()

        # 1. Marcar parcelas pendentes vencidas como atrasadas
        parcelas_atualizadas = Parcela.objects.filter(
            status='pendente',
            vencimento__lt=hoje,
        ).update(status='atrasada')

        self.stdout.write(f'{parcelas_atualizadas} parcela(s) marcada(s) como atrasada(s).')

        # 2. Marcar emprestimos ativos com parcelas atrasadas como inadimplentes
        emprestimos_inadimplentes = (
            Emprestimo.objects
            .filter(status='ativo', parcelas__status='atrasada')
            .distinct()
        )
        total_inadimplentes = emprestimos_inadimplentes.update(status='inadimplente')

        self.stdout.write(f'{total_inadimplentes} emprestimo(s) marcado(s) como inadimplente(s).')
        self.stdout.write(self.style.SUCCESS('Atualizacao concluida.'))
