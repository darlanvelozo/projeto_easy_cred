from django.urls import path
from . import views

app_name = 'rotas'

urlpatterns = [
    path('', views.rota_lista, name='lista'),
    path('nova/', views.rota_criar, name='criar'),
    path('<int:pk>/', views.rota_detalhe, name='detalhe'),
    path('<int:pk>/editar/', views.rota_editar, name='editar'),
]
