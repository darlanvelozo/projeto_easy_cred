from django import forms
from .models import Rota


class RotaForm(forms.ModelForm):
    class Meta:
        model = Rota
        fields = ['nome', 'descricao', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Nome da rota'}),
            'descricao': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Descricao (opcional)'}),
        }
