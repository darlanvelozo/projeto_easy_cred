from django import forms
from .models import Cliente
from rotas.models import Rota


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'cpf', 'telefone', 'rota', 'endereco', 'bairro', 'cidade', 'uf', 'ativo']
        widgets = {
            'nome':     forms.TextInput(attrs={'placeholder': 'Nome completo'}),
            'cpf':      forms.TextInput(attrs={'placeholder': '000.000.000-00'}),
            'telefone': forms.TextInput(attrs={'placeholder': '(00) 00000-0000'}),
            'endereco': forms.TextInput(attrs={'placeholder': 'Rua, número'}),
            'bairro':   forms.TextInput(attrs={'placeholder': 'Bairro'}),
            'cidade':   forms.TextInput(attrs={'placeholder': 'Cidade'}),
            'uf':       forms.TextInput(attrs={'placeholder': 'UF', 'maxlength': '2'}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['rota'].queryset = Rota.objects.filter(empresa=empresa, ativa=True)
        self.fields['rota'].empty_label = 'Selecione a rota'
        self.fields['ativo'].widget = forms.CheckboxInput()
