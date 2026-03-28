from django.urls import path
from . import views

app_name = 'rotas'

urlpatterns = [
    path('', views.rota_lista, name='lista'),
    path('<int:pk>/', views.rota_detalhe, name='detalhe'),
]
