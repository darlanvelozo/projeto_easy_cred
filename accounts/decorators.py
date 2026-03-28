from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def requer_perfil(*perfis):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.perfil not in perfis:
                messages.error(request, 'Você não tem permissão para acessar esta página.')
                return redirect('accounts:dashboard_redirect')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
