from django import forms
from .models import Emprestimo
from clientes.models import Cliente
from rotas.models import Rota
from accounts.models import Usuario


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
            'observacao': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Observações (opcional)'}),
        }

    def __init__(self, *args, empresa=None, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        if empresa:
            self.fields['cliente'].queryset = Cliente.objects.filter(empresa=empresa, ativo=True).order_by('nome')
            self.fields['rota'].queryset = Rota.objects.filter(empresa=empresa, ativa=True)
            self.fields['vendedor'].queryset = Usuario.objects.filter(empresa=empresa, perfil='vendedor', ativo=True)

        self.fields['cliente'].empty_label = 'Selecione o cliente'
        self.fields['rota'].empty_label = 'Selecione a rota'
        self.fields['vendedor'].empty_label = 'Selecione o vendedor'

        # Vendedor preenche automaticamente
        if usuario and usuario.perfil == 'vendedor':
            self.fields['vendedor'].initial = usuario
            self.fields['vendedor'].widget = forms.HiddenInput()

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
                        f'máximo R$ {config.limite_emprestimo_max:.2f}'
                    )
        return cleaned
