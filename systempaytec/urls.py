"""
URL configuration for systempaytec project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf import settings
import os

def service_worker(request):
    """Serve service-worker.js from root scope with correct content type."""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'service-worker.js')
    from django.http import FileResponse
    return FileResponse(
        open(sw_path, 'rb'),
        content_type='application/javascript',
        headers={'Service-Worker-Allowed': '/'},
    )

urlpatterns = [
    path('service-worker.js', service_worker, name='service_worker'),
    path('admin/', admin.site.urls),
    path('rotas/', include('rotas.urls')),
    path('clientes/', include('clientes.urls')),
    path('emprestimos/', include('emprestimos.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('', include('accounts.urls')),
]
