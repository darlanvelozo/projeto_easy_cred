from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django import forms
from django.utils import timezone
from .models import Emprestimo
from clientes.models import Cliente
from rotas.models import Rota
from accounts.models import Usuario


def _proximo_vencimento(periodicidade):
    """Calcula o primeiro vencimento a partir de amanha, baseado na periodicidade."""
    amanha = timezone.localdate() + timedelta(days=1)
    return amanha


class EmprestimoForm(forms.ModelForm):
    class Meta:
        model = Emprestimo
        fields = [
            'cliente', 'rota', 'vendedor', 'valor_principal',
            'taxa_juros', 'num_parcelas', 'periodicidade',
            'data_primeiro_vencimento', 'observacao',
        ]
        widgets = {
            'valor_principal': forms.NumberInput(attrs={'placeholder': '0,00', 'step': '0.01', 'min': '1'}),
            'taxa_juros':      forms.NumberInput(attrs={'placeholder': '0,00', 'step': '0.01', 'min': '0'}),
            'num_parcelas':    forms.NumberInput(attrs={'min': '1', 'max': '120'}),
            'data_primeiro_vencimento': forms.DateInput(attrs={'type': 'date'}),
            'observacao': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Observacoes (opcional)'}),
        }

    def __init__(self, *args, empresa=None, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        self.usuario = usuario

        if empresa:
            self.fields['cliente'].queryset = Cliente.objects.filter(empresa=empresa, ativo=True).order_by('nome')
            self.fields['rota'].queryset = Rota.objects.filter(empresa=empresa, ativa=True)
            self.fields['vendedor'].queryset = Usuario.objects.filter(empresa=empresa, perfil='vendedor', ativo=True)

        self.fields['cliente'].empty_label = 'Selecione o cliente'
        self.fields['rota'].empty_label = 'Selecione a rota'
        self.fields['vendedor'].empty_label = 'Selecione o vendedor'

        if usuario and usuario.perfil == 'vendedor':
            # Vendedor e preenchido automaticamente
            self.fields['vendedor'].initial = usuario
            self.fields['vendedor'].widget = forms.HiddenInput()

            # Vendedor so ve suas rotas
            rotas_ids = usuario.rotas_vinculadas.filter(ativo=True).values_list('rota_id', flat=True)
            self.fields['rota'].queryset = Rota.objects.filter(pk__in=rotas_ids, ativa=True)
            self.fields['cliente'].queryset = Cliente.objects.filter(
                empresa=empresa, ativo=True, rota_id__in=rotas_ids,
            ).order_by('nome')

            # Vendedor nao escolhe data de vencimento — auto-calcula
            self.fields['data_primeiro_vencimento'].widget = forms.HiddenInput()
            self.fields['data_primeiro_vencimento'].required = False
            self.fields['data_primeiro_vencimento'].initial = _proximo_vencimento('semanal')

    def clean(self):
        cleaned = super().clean()
        rota = cleaned.get('rota')
        valor_principal = cleaned.get('valor_principal')

        if rota and valor_principal:
            config = getattr(rota, 'configuracao', None)
            if config and config.limite_emprestimo_max:
                if valor_principal > config.limite_emprestimo_max:
                    self.add_error(
                        'valor_principal',
                        f'Valor excede o limite da rota "{rota.nome}": '
                        f'maximo R$ {config.limite_emprestimo_max:.2f}'
                    )

        # Se vendedor, auto-preenche data_primeiro_vencimento = amanha
        if self.usuario and self.usuario.perfil == 'vendedor':
            cleaned['data_primeiro_vencimento'] = _proximo_vencimento(
                cleaned.get('periodicidade', 'semanal')
            )

        return cleaned
