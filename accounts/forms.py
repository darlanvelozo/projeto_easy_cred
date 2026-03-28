from django import forms
from .models import Empresa
from rotas.models import ConfiguracaoRota


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nome', 'cnpj', 'email', 'telefone']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Nome da empresa'}),
            'cnpj': forms.TextInput(attrs={'placeholder': '00.000.000/0000-00'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@empresa.com'}),
            'telefone': forms.TextInput(attrs={'placeholder': '(00) 00000-0000'}),
        }


class ConfiguracaoRotaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoRota
        fields = [
            'taxa_juros_padrao', 'periodicidade_padrao',
            'num_parcelas_padrao', 'limite_emprestimo_max',
            'multa_atraso', 'juros_mora_dia',
        ]
        widgets = {
            'taxa_juros_padrao': forms.NumberInput(attrs={
                'step': '0.01', 'min': '0', 'placeholder': '0,00',
            }),
            'num_parcelas_padrao': forms.NumberInput(attrs={
                'min': '1', 'max': '120',
            }),
            'limite_emprestimo_max': forms.NumberInput(attrs={
                'step': '0.01', 'min': '0', 'placeholder': 'Sem limite',
            }),
            'multa_atraso': forms.NumberInput(attrs={
                'step': '0.01', 'min': '0', 'placeholder': '0,00',
            }),
            'juros_mora_dia': forms.NumberInput(attrs={
                'step': '0.0001', 'min': '0', 'placeholder': '0,0000',
            }),
        }
        labels = {
            'taxa_juros_padrao': 'Taxa de Juros (%)',
            'periodicidade_padrao': 'Periodicidade',
            'num_parcelas_padrao': 'Nº Parcelas',
            'limite_emprestimo_max': 'Limite Máx. (R$)',
            'multa_atraso': 'Multa Atraso (%)',
            'juros_mora_dia': 'Juros Mora/Dia (%)',
        }
