from django.urls import path
from . import views

app_name = 'emprestimos'

urlpatterns = [
    path('', views.emprestimo_lista, name='lista'),
    path('novo/', views.emprestimo_criar, name='criar'),
    path('<int:pk>/', views.emprestimo_detalhe, name='detalhe'),
    path('<int:pk>/cancelar/', views.emprestimo_cancelar, name='cancelar'),
]
