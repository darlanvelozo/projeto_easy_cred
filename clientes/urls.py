from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.cliente_lista, name='lista'),
    path('novo/', views.cliente_criar, name='criar'),
    path('<int:pk>/editar/', views.cliente_editar, name='editar'),
]
