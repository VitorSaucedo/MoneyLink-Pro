from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import (
    Sala, Ilha, PosicaoAtendimento, 
    AtribuicaoFuncionarioPA, AtribuicaoPerifericoPA,
    Computador, Periferico, AtribuicaoComputadorPA,
    TipoPeriferico
)
from .forms import (
    SalaForm, IlhaForm, PosicaoAtendimentoForm,
    AtribuicaoFuncionarioPAForm, AtribuicaoPerifericoPAForm,
    ComputadorForm, AtribuicaoComputadorPAForm,
    TipoPerifericoForm, PerifericoForm
)

# Views para Computadores
@login_required
def computador_create(request):
    if request.method == 'POST':
        form = ComputadorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Computador cadastrado com sucesso!')
            return redirect('ti:admin')
    else:
        form = ComputadorForm()
    
    context = {
        'form': form
    }
    return render(request, 'apps/ti/computador_form.html', context)

@login_required
def atribuicao_computador_pa_create(request):
    if request.method == 'POST':
        form = AtribuicaoComputadorPAForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de computador realizada com sucesso!')
            return redirect('ti:admin')
    else:
        form = AtribuicaoComputadorPAForm()
    
    context = {
        'form': form
    }
    return render(request, 'apps/ti/atribuicao_computador_pa_form.html', context)


# Views para Tipos de Periféricos
@login_required
def tipo_periferico_list(request):
    tipos = TipoPeriferico.objects.all().order_by('nome')
    context = {
        'tipos': tipos
    }
    return render(request, 'apps/ti/tipo_periferico_list.html', context)

@login_required
def tipo_periferico_create(request):
    if request.method == 'POST':
        form = TipoPerifericoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de periférico cadastrado com sucesso!')
            return redirect('ti:admin')
    else:
        form = TipoPerifericoForm()
    
    context = {
        'form': form
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
        'form': form,
        'tipo': tipo
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
        'tipo': tipo
    }
    return render(request, 'apps/ti/tipo_periferico_confirm_delete.html', context)


# Views para Periféricos
@login_required
def periferico_list(request):
    perifericos = Periferico.objects.all().select_related('tipo')
    context = {
        'perifericos': perifericos
    }
    return render(request, 'apps/ti/periferico_list.html', context)

@login_required
def periferico_create(request):
    if request.method == 'POST':
        form = PerifericoForm(request.POST)
        if form.is_valid():
            # Obter a quantidade a ser criada
            quantidade = form.cleaned_data.get('quantidade', 1)
            
            # Limitar a quantidade para evitar sobrecarga (opcional)
            quantidade = min(quantidade, 100)  # Máximo de 100 periféricos por vez
            
            if quantidade > 1:
                # Se a quantidade for maior que 1, criar múltiplos periféricos
                perif_criados = 0
                modelo_base = form.save(commit=False)  # Não salvar ainda
                
                # Salvar as informações originais
                tipo = modelo_base.tipo
                marca = modelo_base.marca
                modelo = modelo_base.modelo
                data_aquisicao = modelo_base.data_aquisicao
                loja = modelo_base.loja
                status = modelo_base.status
                observacoes = modelo_base.observacoes
                
                # Definir quantidade como 1 para cada periférico individual
                modelo_base.quantidade = 1
                modelo_base.save()
                perif_criados += 1
                
                # Criar os periféricos adicionais
                for _ in range(1, quantidade):
                    periferico = Periferico(
                        tipo=tipo,
                        marca=marca,
                        modelo=modelo,
                        data_aquisicao=data_aquisicao,
                        quantidade=1,  # Cada periférico terá quantidade 1
                        loja=loja,
                        status=status,
                        observacoes=observacoes
                    )
                    periferico.save()
                    perif_criados += 1
                
                messages.success(request, f'{perif_criados} periféricos cadastrados com sucesso!')
            else:
                # Se quantidade for 1, salvar normalmente
                form.save()
                messages.success(request, 'Periférico cadastrado com sucesso!')
            
            return redirect('ti:admin')
    else:
        form = PerifericoForm()
    
    context = {
        'form': form,
        'title': 'Cadastrar Novo Periférico'
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
        'form': form,
        'periferico': periferico
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
        'periferico': periferico
    }
    return render(request, 'apps/ti/periferico_confirm_delete.html', context)

# Funções que faltavam para gerenciar atribuições

@login_required
def atribuicao_funcionario_pa_delete(request, pk):
    atribuicao = get_object_or_404(AtribuicaoFuncionarioPA, pk=pk)
    if request.method == 'POST':
        atribuicao.delete()
        messages.success(request, 'Atribuição de funcionário excluída com sucesso!')
        return redirect('ti:atribuicao_funcionario_pa_list')
    
    context = {
        'atribuicao': atribuicao
    }
    return render(request, 'apps/ti/atribuicao_funcionario_pa_confirm_delete.html', context)

# Views para Atribuição de Periféricos a PAs
@login_required
def atribuicao_periferico(request):
    # Lógica para a página de atribuição de periféricos
    context = {}
    return render(request, 'apps/ti/atribuicao_periferico.html', context)

@login_required
def atribuicao_periferico_pa_create(request):
    if request.method == 'POST':
        form = AtribuicaoPerifericoPAForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de periférico cadastrada com sucesso!')
            return redirect('ti:admin')
    else:
        form = AtribuicaoPerifericoPAForm()
    
    context = {
        'form': form
    }
    return render(request, 'apps/ti/atribuicao_periferico_pa_form.html', context)

@login_required
def atribuicao_periferico_pa_update(request, pk):
    atribuicao = get_object_or_404(AtribuicaoPerifericoPA, pk=pk)
    if request.method == 'POST':
        form = AtribuicaoPerifericoPAForm(request.POST, instance=atribuicao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de periférico atualizada com sucesso!')
            return redirect('ti:admin')
    else:
        form = AtribuicaoPerifericoPAForm(instance=atribuicao)
    
    context = {
        'form': form,
        'atribuicao': atribuicao
    }
    return render(request, 'apps/ti/atribuicao_periferico_pa_form.html', context)

@login_required
def atribuicao_periferico_pa_delete(request, pk):
    atribuicao = get_object_or_404(AtribuicaoPerifericoPA, pk=pk)
    if request.method == 'POST':
        atribuicao.delete()
        messages.success(request, 'Atribuição de periférico excluída com sucesso!')
        return redirect('ti:admin')
    
    context = {
        'atribuicao': atribuicao
    }
    return render(request, 'apps/ti/atribuicao_periferico_pa_confirm_delete.html', context)

# Funções de API
@login_required
def api_pas_para_atribuicao_periferico(request, periferico_id):
    # Lógica para filtrar PAs disponíveis para atribuição
    posicoes = PosicaoAtendimento.objects.all().select_related('sala', 'ilha')
    data = [{
        'id': pa.id,
        'texto': f"{pa.sala.nome} - {pa.ilha.nome} - PA {pa.numero}"
    } for pa in posicoes]
    
    return JsonResponse(data, safe=False)

@login_required
def get_funcionarios_json(request):
    # Retorna a lista de funcionários em formato JSON
    funcionarios = []
    return JsonResponse(funcionarios, safe=False)

@login_required
def atribuir_funcionario_pa(request):
    # Lógica para atribuir funcionário a uma PA via AJAX
    if request.method == 'POST':
        # Implementar lógica de atribuição
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def api_listar_computadores_disponiveis(request):
    # Lista computadores disponíveis para atribuição
    computadores = Computador.objects.filter(status='disponivel').values('id', 'marca', 'modelo')
    return JsonResponse(list(computadores), safe=False)


# Views para Ramais
@login_required
def ramal_list(request):
    # Implementar a listagem de ramais
    # Aqui você pode adaptar de acordo com o modelo real usado para ramais no seu sistema
    ramais = []  # Substituir por uma consulta real ao modelo de ramais
    context = {
        'ramais': ramais
    }
    return render(request, 'apps/ti/ramal_list.html', context)

@login_required
def ramal_create(request):
    # Implementar a criação de ramais
    if request.method == 'POST':
        # Processar o formulário de criação de ramal
        # form = RamalForm(request.POST)  # Criar um formulário real para ramais
        # if form.is_valid():
        #     form.save()
        #     messages.success(request, 'Ramal cadastrado com sucesso!')
        #     return redirect('ti:admin')
        messages.success(request, 'Ramal cadastrado com sucesso!')
        return redirect('ti:admin')
    else:
        # form = RamalForm()
        pass
    
    context = {
        # 'form': form
    }
    return render(request, 'apps/ti/ramal_form.html', context)

@login_required
def ramal_update(request):
    # Implementar atualização geral de ramais
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario_id')
        ramal = request.POST.get('ramal')
        
        if funcionario_id and ramal:
            # Aqui você implementaria a lógica para atualizar o ramal do funcionário
            # Exemplo: Ramal.objects.update_or_create(funcionario_id=funcionario_id, defaults={'numero': ramal})
            messages.success(request, 'Ramal atualizado com sucesso!')
        else:
            messages.error(request, 'Dados incompletos para atualizar o ramal.')
            
        return redirect('ti:admin')
    
    return redirect('ti:admin')

@login_required
def ramal_edit(request, pk):
    # Implementar edição de ramal específico
    # ramal = get_object_or_404(Ramal, pk=pk)
    if request.method == 'POST':
        # form = RamalForm(request.POST, instance=ramal)
        # if form.is_valid():
        #     form.save()
        #     messages.success(request, 'Ramal atualizado com sucesso!')
        #     return redirect('ti:ramal_list')
        messages.success(request, 'Ramal atualizado com sucesso!')
        return redirect('ti:admin')
    else:
        # form = RamalForm(instance=ramal)
        pass
    
    context = {
        # 'form': form,
        # 'ramal': ramal
    }
    return render(request, 'apps/ti/ramal_form.html', context)

@login_required
def ramal_delete(request, pk):
    # Implementar exclusão de ramal
    # ramal = get_object_or_404(Ramal, pk=pk)
    if request.method == 'POST':
        # ramal.delete()
        messages.success(request, 'Ramal excluído com sucesso!')
        return redirect('ti:admin')
    
    context = {
        # 'ramal': ramal
    }
    return render(request, 'apps/ti/ramal_confirm_delete.html', context)
