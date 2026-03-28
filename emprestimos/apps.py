from django.apps import AppConfig

class EmprestimosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'emprestimos'
    verbose_name = 'Empréstimos'

    def ready(self):
        import emprestimos.signals  # noqa: F401
