from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def controle_estoque(request):
    context = {
        'title': 'Controle de Estoque - TI'
    }
    return render(request, 'apps/ti/controle_estoque.html', context)

@login_required
def admin(request):
    context = {
        'title': 'Admin - TI'
    }
    return render(request, 'apps/ti/admin.html', context)

@login_required
def controle_salas(request):
    context = {
        'title': 'Controle de Salas - TI'
    }
    return render(request, 'apps/ti/controle_salas.html', context)
