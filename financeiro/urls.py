from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('pagamento/<int:parcela_id>/', views.registrar_pagamento, name='registrar_pagamento'),
    path('caixa/', views.caixa_lista, name='caixa_lista'),
    path('caixa/<int:rota_id>/', views.caixa_movimentacoes, name='caixa_movimentacoes'),
]
