from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.cliente_lista, name='lista'),
    path('mapa/', views.cliente_mapa, name='mapa'),
    path('novo/', views.cliente_criar, name='criar'),
    path('<int:pk>/', views.cliente_detalhe, name='detalhe'),
    path('<int:pk>/editar/', views.cliente_editar, name='editar'),
]
