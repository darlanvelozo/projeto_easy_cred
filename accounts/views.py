from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.ativo:
                messages.error(request, 'Sua conta está desativada. Contate o administrador.')
                return render(request, 'accounts/login.html')
            login(request, user)
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser:
        return redirect('/admin/')
    if user.perfil == 'admin':
        return redirect('accounts:dashboard_admin')
    if user.perfil == 'gerente':
        return redirect('accounts:dashboard_gerente')
    return redirect('accounts:dashboard_vendedor')


@login_required
def dashboard_admin(request):
    return render(request, 'accounts/dashboard_admin.html')


@login_required
def dashboard_gerente(request):
    return render(request, 'accounts/dashboard_gerente.html')


@login_required
def dashboard_vendedor(request):
    return render(request, 'accounts/dashboard_vendedor.html')
