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


class MovimentacaoCaixaForm(forms.Form):
    valor = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0.01,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': '0,00'}),
    )
    descricao = forms.CharField(
        max_length=300,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Descricao da movimentacao'}),
    )
