from django import forms
from .models import Cliente
from rotas.models import Rota


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nome', 'cpf', 'telefone', 'rota', 'endereco', 'bairro',
            'cidade', 'uf', 'latitude', 'longitude', 'ativo',
        ]
        widgets = {
            'nome':      forms.TextInput(attrs={'placeholder': 'Nome completo'}),
            'cpf':       forms.TextInput(attrs={'placeholder': '000.000.000-00'}),
            'telefone':  forms.TextInput(attrs={'placeholder': '(00) 00000-0000'}),
            'endereco':  forms.TextInput(attrs={'placeholder': 'Rua, numero'}),
            'bairro':    forms.TextInput(attrs={'placeholder': 'Bairro'}),
            'cidade':    forms.TextInput(attrs={'placeholder': 'Cidade'}),
            'uf':        forms.TextInput(attrs={'placeholder': 'UF', 'maxlength': '2'}),
            'latitude':  forms.NumberInput(attrs={'placeholder': '-00.0000000', 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'placeholder': '-00.0000000', 'step': '0.0000001'}),
        }

    def __init__(self, *args, empresa=None, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['rota'].queryset = Rota.objects.filter(empresa=empresa, ativa=True)

        # Vendedor so ve suas rotas
        if usuario and usuario.perfil == 'vendedor':
            rotas_ids = usuario.rotas_vinculadas.filter(ativo=True).values_list('rota_id', flat=True)
            self.fields['rota'].queryset = Rota.objects.filter(pk__in=rotas_ids, ativa=True)

        self.fields['rota'].empty_label = 'Selecione a rota'
        self.fields['ativo'].widget = forms.CheckboxInput()
