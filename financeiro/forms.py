from django import forms
from .models import Pagamento


class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ['valor', 'forma', 'observacao']
        widgets = {
            'valor': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'observacao': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Observações (opcional)'}),
        }
