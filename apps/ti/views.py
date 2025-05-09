from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import (
    TipoPeriferico, 
    Periferico, 
    PosicaoAtendimento, 
    AtribuicaoFuncionarioPA, 
    AtribuicaoPerifericoPA,
    Sala,
    Ilha
)
from .forms import (
    TipoPerifericoForm,
    PerifericoForm,
    PosicaoAtendimentoForm,
    AtribuicaoFuncionarioPAForm,
    AtribuicaoPerifericoPAForm,
    SalaForm,
    IlhaForm
)
from apps.funcionarios.models import Funcionario

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
        'title': 'Admin - TI',
        'tipos_perifericos': TipoPeriferico.objects.all().count(),
        'perifericos': Periferico.objects.all().count(),
        'salas': Sala.objects.all().count(),
        'ilhas': Ilha.objects.all().count(),
        'posicoes_atendimento': PosicaoAtendimento.objects.all().count(),
        'atribuicoes_funcionarios': AtribuicaoFuncionarioPA.objects.filter(ativo=True).count(),
        'atribuicoes_perifericos': AtribuicaoPerifericoPA.objects.filter(ativo=True).count(),
        'tipos_perifericos_list': TipoPeriferico.objects.all(),
        'salas_list': Sala.objects.all(),
        'funcionarios_list': Funcionario.objects.all(),
        'perifericos_list': Periferico.objects.filter(status='disponivel'),
        'posicoes_atendimento_list': PosicaoAtendimento.objects.all(),
    }
    
    if request.method == 'POST':
        if 'funcionario' in request.POST and 'posicao_atendimento' in request.POST and 'data_inicio' in request.POST:
            # Processamento do formulário de atribuição de funcionário
            form = AtribuicaoFuncionarioPAForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Atribuição de funcionário cadastrada com sucesso!')
                return redirect('ti:admin')
        
        if 'periferico' in request.POST and 'posicao_atendimento' in request.POST and 'data_atribuicao' in request.POST:
            # Processamento do formulário de atribuição de periférico
            form = AtribuicaoPerifericoPAForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Atribuição de periférico cadastrada com sucesso!')
                return redirect('ti:admin')
    
    return render(request, 'apps/ti/admin.html', context)

@login_required
def controle_salas(request):
    salas = Sala.objects.all()
    ilhas = Ilha.objects.all()
    
    # Carrega todas as posições de atendimento com seus relacionamentos
    posicoes = PosicaoAtendimento.objects.all().select_related('funcionario', 'ilha', 'sala')
    
    # Carrega os periféricos atribuídos a cada PA
    perifericos_por_pa = {}
    atribuicoes = AtribuicaoPerifericoPA.objects.filter(ativo=True).select_related('periferico', 'periferico__tipo', 'posicao_atendimento')
    
    for atribuicao in atribuicoes:
        pa_id = atribuicao.posicao_atendimento.id
        if pa_id not in perifericos_por_pa:
            perifericos_por_pa[pa_id] = []
        perifericos_por_pa[pa_id].append({
            'tipo': atribuicao.periferico.tipo.nome,
            'marca': atribuicao.periferico.marca,
            'modelo': atribuicao.periferico.modelo,
            'id': atribuicao.periferico.id
        })
    
    context = {
        'title': 'Controle de Salas - TI',
        'salas': salas,
        'ilhas': ilhas,
        'posicoes': posicoes,
        'perifericos_por_pa': perifericos_por_pa
    }
    return render(request, 'apps/ti/controle_salas.html', context)

# Views para Tipos de Periféricos
@login_required
def tipo_periferico_list(request):
    tipos = TipoPeriferico.objects.all()
    context = {
        'title': 'Tipos de Periféricos',
        'tipos': tipos,
    }
    return render(request, 'apps/ti/tipo_periferico_list.html', context)

@login_required
def tipo_periferico_create(request):
    if request.method == 'POST':
        form = TipoPerifericoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de periférico cadastrado com sucesso!')
            return redirect('ti:tipo_periferico_list')
    else:
        form = TipoPerifericoForm()
    
    context = {
        'title': 'Cadastrar Tipo de Periférico',
        'form': form,
    }
    return render(request, 'apps/ti/tipo_periferico_form.html', context)

@login_required
def tipo_periferico_update(request, pk):
    tipo = get_object_or_404(TipoPeriferico, pk=pk)
    if request.method == 'POST':
        form = TipoPerifericoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de periférico atualizado com sucesso!')
            return redirect('ti:tipo_periferico_list')
    else:
        form = TipoPerifericoForm(instance=tipo)
    
    context = {
        'title': 'Editar Tipo de Periférico',
        'form': form,
        'tipo': tipo,
    }
    return render(request, 'apps/ti/tipo_periferico_form.html', context)

@login_required
def tipo_periferico_delete(request, pk):
    tipo = get_object_or_404(TipoPeriferico, pk=pk)
    if request.method == 'POST':
        tipo.delete()
        messages.success(request, 'Tipo de periférico excluído com sucesso!')
        return redirect('ti:tipo_periferico_list')
    
    context = {
        'title': 'Confirmar Exclusão',
        'objeto': tipo,
    }
    return render(request, 'apps/ti/confirm_delete.html', context)

# Views para Periféricos
@login_required
def periferico_list(request):
    perifericos = Periferico.objects.all()
    context = {
        'title': 'Periféricos',
        'perifericos': perifericos,
    }
    return render(request, 'apps/ti/periferico_list.html', context)

@login_required
def periferico_create(request):
    if request.method == 'POST':
        form = PerifericoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Periférico cadastrado com sucesso!')
            return redirect('ti:periferico_list')
    else:
        form = PerifericoForm()
    
    context = {
        'title': 'Cadastrar Periférico',
        'form': form,
    }
    return render(request, 'apps/ti/periferico_form.html', context)

@login_required
def periferico_update(request, pk):
    periferico = get_object_or_404(Periferico, pk=pk)
    if request.method == 'POST':
        form = PerifericoForm(request.POST, instance=periferico)
        if form.is_valid():
            form.save()
            messages.success(request, 'Periférico atualizado com sucesso!')
            return redirect('ti:periferico_list')
    else:
        form = PerifericoForm(instance=periferico)
    
    context = {
        'title': 'Editar Periférico',
        'form': form,
        'periferico': periferico,
    }
    return render(request, 'apps/ti/periferico_form.html', context)

@login_required
def periferico_delete(request, pk):
    periferico = get_object_or_404(Periferico, pk=pk)
    if request.method == 'POST':
        periferico.delete()
        messages.success(request, 'Periférico excluído com sucesso!')
        return redirect('ti:periferico_list')
    
    context = {
        'title': 'Confirmar Exclusão',
        'objeto': periferico,
    }
    return render(request, 'apps/ti/confirm_delete.html', context)

# Views para Posições de Atendimento (PAs)
@login_required
def posicao_atendimento_list(request):
    posicoes = PosicaoAtendimento.objects.all()
    context = {
        'title': 'Posições de Atendimento',
        'posicoes': posicoes,
    }
    return render(request, 'apps/ti/posicao_atendimento_list.html', context)

@login_required
def posicao_atendimento_create(request):
    if request.method == 'POST':
        form = PosicaoAtendimentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Posição de atendimento cadastrada com sucesso!')
            return redirect('ti:posicao_atendimento_list')
    else:
        form = PosicaoAtendimentoForm()
    
    context = {
        'title': 'Cadastrar Posição de Atendimento',
        'form': form,
    }
    return render(request, 'apps/ti/posicao_atendimento_form.html', context)

@login_required
def posicao_atendimento_update(request, pk):
    posicao = get_object_or_404(PosicaoAtendimento, pk=pk)
    if request.method == 'POST':
        form = PosicaoAtendimentoForm(request.POST, instance=posicao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Posição de atendimento atualizada com sucesso!')
            return redirect('ti:posicao_atendimento_list')
    else:
        form = PosicaoAtendimentoForm(instance=posicao)
    
    context = {
        'title': 'Editar Posição de Atendimento',
        'form': form,
        'posicao': posicao,
    }
    return render(request, 'apps/ti/posicao_atendimento_form.html', context)

@login_required
def posicao_atendimento_delete(request, pk):
    posicao = get_object_or_404(PosicaoAtendimento, pk=pk)
    if request.method == 'POST':
        posicao.delete()
        messages.success(request, 'Posição de atendimento excluída com sucesso!')
        return redirect('ti:posicao_atendimento_list')
    
    context = {
        'title': 'Confirmar Exclusão',
        'objeto': posicao,
    }
    return render(request, 'apps/ti/confirm_delete.html', context)

# Views para Atribuição de Funcionários a PAs
@login_required
def atribuicao_funcionario_pa_list(request):
    atribuicoes = AtribuicaoFuncionarioPA.objects.all()
    context = {
        'title': 'Atribuições de Funcionários a PAs',
        'atribuicoes': atribuicoes,
    }
    return render(request, 'apps/ti/atribuicao_funcionario_pa_list.html', context)

@login_required
def atribuicao_funcionario_pa_create(request):
    if request.method == 'POST':
        form = AtribuicaoFuncionarioPAForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de funcionário a PA cadastrada com sucesso!')
            return redirect('ti:atribuicao_funcionario_pa_list')
    else:
        form = AtribuicaoFuncionarioPAForm()
    
    context = {
        'title': 'Atribuir Funcionário a PA',
        'form': form,
    }
    return render(request, 'apps/ti/atribuicao_funcionario_pa_form.html', context)

@login_required
def atribuicao_funcionario_pa_update(request, pk):
    atribuicao = get_object_or_404(AtribuicaoFuncionarioPA, pk=pk)
    if request.method == 'POST':
        form = AtribuicaoFuncionarioPAForm(request.POST, instance=atribuicao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de funcionário a PA atualizada com sucesso!')
            return redirect('ti:atribuicao_funcionario_pa_list')
    else:
        form = AtribuicaoFuncionarioPAForm(instance=atribuicao)
    
    context = {
        'title': 'Editar Atribuição de Funcionário a PA',
        'form': form,
        'atribuicao': atribuicao,
    }
    return render(request, 'apps/ti/atribuicao_funcionario_pa_form.html', context)

@login_required
def atribuicao_funcionario_pa_delete(request, pk):
    atribuicao = get_object_or_404(AtribuicaoFuncionarioPA, pk=pk)
    if request.method == 'POST':
        atribuicao.delete()
        messages.success(request, 'Atribuição de funcionário a PA excluída com sucesso!')
        return redirect('ti:atribuicao_funcionario_pa_list')
    
    context = {
        'title': 'Confirmar Exclusão',
        'objeto': atribuicao,
    }
    return render(request, 'apps/ti/confirm_delete.html', context)

# Views para Atribuição de Periféricos a PAs
@login_required
def atribuicao_periferico_pa_list(request):
    atribuicoes = AtribuicaoPerifericoPA.objects.all()
    context = {
        'title': 'Atribuições de Periféricos a PAs',
        'atribuicoes': atribuicoes,
    }
    return render(request, 'apps/ti/atribuicao_periferico_pa_list.html', context)

@login_required
def atribuicao_periferico_pa_create(request):
    if request.method == 'POST':
        form = AtribuicaoPerifericoPAForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de periférico a PA cadastrada com sucesso!')
            return redirect('ti:atribuicao_periferico_pa_list')
    else:
        form = AtribuicaoPerifericoPAForm()
    
    context = {
        'title': 'Atribuir Periférico a PA',
        'form': form,
    }
    return render(request, 'apps/ti/atribuicao_periferico_pa_form.html', context)

@login_required
def atribuicao_periferico_pa_update(request, pk):
    atribuicao = get_object_or_404(AtribuicaoPerifericoPA, pk=pk)
    if request.method == 'POST':
        form = AtribuicaoPerifericoPAForm(request.POST, instance=atribuicao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de periférico a PA atualizada com sucesso!')
            return redirect('ti:atribuicao_periferico_pa_list')
    else:
        form = AtribuicaoPerifericoPAForm(instance=atribuicao)
    
    context = {
        'title': 'Editar Atribuição de Periférico a PA',
        'form': form,
        'atribuicao': atribuicao,
    }
    return render(request, 'apps/ti/atribuicao_periferico_pa_form.html', context)

@login_required
def atribuicao_periferico_pa_delete(request, pk):
    atribuicao = get_object_or_404(AtribuicaoPerifericoPA, pk=pk)
    if request.method == 'POST':
        atribuicao.delete()
        messages.success(request, 'Atribuição de periférico a PA excluída com sucesso!')
        return redirect('ti:atribuicao_periferico_pa_list')
    
    context = {
        'title': 'Confirmar Exclusão',
        'objeto': atribuicao,
    }
    return render(request, 'apps/ti/confirm_delete.html', context)

# Views para Sala
@login_required
def sala_list(request):
    salas = Sala.objects.all()
    context = {
        'title': 'Salas',
        'salas': salas,
    }
    return render(request, 'apps/ti/sala_list.html', context)

@login_required
def sala_create(request):
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sala cadastrada com sucesso!')
            return redirect('ti:sala_list')
    else:
        form = SalaForm()
    
    context = {
        'title': 'Cadastrar Sala',
        'form': form,
    }
    return render(request, 'apps/ti/sala_form.html', context)

@login_required
def sala_update(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    if request.method == 'POST':
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sala atualizada com sucesso!')
            return redirect('ti:sala_list')
    else:
        form = SalaForm(instance=sala)
    
    context = {
        'title': 'Editar Sala',
        'form': form,
        'sala': sala,
    }
    return render(request, 'apps/ti/sala_form.html', context)

@login_required
def sala_delete(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    if request.method == 'POST':
        sala.delete()
        messages.success(request, 'Sala excluída com sucesso!')
        return redirect('ti:sala_list')
    
    context = {
        'title': 'Confirmar Exclusão',
        'objeto': sala,
    }
    return render(request, 'apps/ti/confirm_delete.html', context)

# Views para Ilha
@login_required
def ilha_list(request):
    ilhas = Ilha.objects.all()
    context = {
        'title': 'Ilhas',
        'ilhas': ilhas,
    }
    return render(request, 'apps/ti/ilha_list.html', context)

@login_required
def ilha_create(request):
    if request.method == 'POST':
        form = IlhaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ilha cadastrada com sucesso!')
            return redirect('ti:ilha_list')
    else:
        form = IlhaForm()
    
    context = {
        'title': 'Cadastrar Ilha',
        'form': form,
    }
    return render(request, 'apps/ti/ilha_form.html', context)

@login_required
def ilha_update(request, pk):
    ilha = get_object_or_404(Ilha, pk=pk)
    if request.method == 'POST':
        form = IlhaForm(request.POST, instance=ilha)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ilha atualizada com sucesso!')
            return redirect('ti:ilha_list')
    else:
        form = IlhaForm(instance=ilha)
    
    context = {
        'title': 'Editar Ilha',
        'form': form,
        'ilha': ilha,
    }
    return render(request, 'apps/ti/ilha_form.html', context)

@login_required
def ilha_delete(request, pk):
    ilha = get_object_or_404(Ilha, pk=pk)
    if request.method == 'POST':
        ilha.delete()
        messages.success(request, 'Ilha excluída com sucesso!')
        return redirect('ti:ilha_list')
    
    context = {
        'title': 'Confirmar Exclusão',
        'objeto': ilha,
    }
    return render(request, 'apps/ti/confirm_delete.html', context)

# View API para obter ilhas de uma sala específica
@login_required
def api_ilhas_por_sala(request, sala_id):
    ilhas = Ilha.objects.filter(sala_id=sala_id).values('id', 'nome')
    return JsonResponse(list(ilhas), safe=False)
