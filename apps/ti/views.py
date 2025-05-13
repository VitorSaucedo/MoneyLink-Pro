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
import json
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator

# Create your views here.

@login_required
def controle_estoque(request):
    """
    View para exibir o controle de estoque de periféricos por sala e ilha.
    Mostra uma tabela com a contagem de periféricos de cada tipo em cada sala/ilha.
    """
    # Obter todas as salas
    salas = Sala.objects.all().prefetch_related('ilhas')
    
    # Obter todos os tipos de periféricos
    tipos_perifericos = TipoPeriferico.objects.all()
    
    # Inicializar dicionário para contagem de periféricos por sala/ilha/tipo
    perifericos_por_sala_ilha = {}
    total_geral = 0
    
    # Popular o dicionário com os dados
    for sala in salas:
        perifericos_por_sala_ilha[sala.id] = {}
        
        for ilha in sala.ilhas.all():
            perifericos_por_sala_ilha[sala.id][ilha.id] = {}
            
            # Inicializar contador para cada tipo de periférico nesta ilha
            for tipo in tipos_perifericos:
                perifericos_por_sala_ilha[sala.id][ilha.id][tipo.id] = 0
            
            # Obter todas as PAs desta ilha
            posicoes_atendimento_ilha = PosicaoAtendimento.objects.filter(ilha=ilha) # Renomeada para evitar conflito
            
            # Para cada PA, contar os periféricos por tipo
            for pa in posicoes_atendimento_ilha: # Uso da variável renomeada
                # Obter os periféricos atribuídos a esta PA
                atribuicoes_pa_ativa = AtribuicaoPerifericoPA.objects.filter( # Renomeada para evitar conflito
                    posicao_atendimento=pa,
                    data_remocao__isnull=True  # Somente atribuições ativas
                ).select_related('periferico__tipo')
                
                for atribuicao in atribuicoes_pa_ativa: # Uso da variável renomeada
                    tipo_id = atribuicao.periferico.tipo.id
                    perifericos_por_sala_ilha[sala.id][ilha.id][tipo_id] += 1
                    total_geral += 1

    # Buscar histórico de movimentações
    historico_movimentacoes = []
    atribuicoes_todas = AtribuicaoPerifericoPA.objects.select_related(
        'periferico__tipo', 
        'posicao_atendimento__ilha__sala' # Inclui ilha e sala para evitar N+1 queries
    ).order_by('-data_atribuicao') # Ordena por data de atribuição inicialmente

    for atribuicao in atribuicoes_todas:
        local = f"{atribuicao.posicao_atendimento.sala.nome if atribuicao.posicao_atendimento.sala else 'N/A'}, {atribuicao.posicao_atendimento.ilha.nome if atribuicao.posicao_atendimento.ilha else 'N/A'} - PA {atribuicao.posicao_atendimento.numero}"
        
        # Evento de Adição
        if atribuicao.data_atribuicao: # Garante que a data existe
            historico_movimentacoes.append({
                'data': atribuicao.data_atribuicao, # Mantém a data original para exibição, se necessário
                'tipo_evento': 'Adicionado em',
                'periferico': f"{atribuicao.periferico.tipo.nome} {atribuicao.periferico.marca} {atribuicao.periferico.modelo}",
                'local': local,
                'timestamp': atribuicao.data_atribuicao # Usa diretamente o DateTimeField
            })
        
        # Evento de Remoção, se aplicável
        if atribuicao.data_remocao:
            historico_movimentacoes.append({
                'data': atribuicao.data_remocao, # Mantém a data original para exibição, se necessário
                'tipo_evento': 'Removido de',
                'periferico': f"{atribuicao.periferico.tipo.nome} {atribuicao.periferico.marca} {atribuicao.periferico.modelo}",
                'local': local,
                'timestamp': atribuicao.data_remocao # Usa diretamente o DateTimeField
            })

    # Ordenar o histórico combinado por data (timestamp), mais recentes primeiro
    # Filtrar itens sem timestamp (caso data_atribuicao ou data_remocao seja None, o que não deveria acontecer para datas obrigatórias)
    historico_movimentacoes = [item for item in historico_movimentacoes if item['timestamp']]
    historico_movimentacoes.sort(key=lambda x: x['timestamp'], reverse=True)

    # Obter a data da última atualização real
    data_ultima_atualizacao_real = None
    if historico_movimentacoes:
        data_ultima_atualizacao_real = historico_movimentacoes[0]['timestamp']

    # Configurar paginação para o histórico
    paginator = Paginator(historico_movimentacoes, 10) # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Contexto para o template
    context = {
        'salas': salas,
        'tipos_perifericos': tipos_perifericos,
        'perifericos_por_sala_ilha': perifericos_por_sala_ilha,
        'total_geral': total_geral,
        'historico_page_obj': page_obj, # Passa o objeto da página para o template
        'data_ultima_atualizacao_real': data_ultima_atualizacao_real, # Adiciona a data ao contexto
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
        # O processamento do formulário de atribuição de funcionário foi REMOVIDO daqui.
        # Essa lógica agora é centralizada na API chamada pelo Controle de Salas.
        
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

@login_required
def atualizar_status_pa(request):
    """
    View para processar as requisições AJAX para atualizar o status das PAs
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        pa_id = request.POST.get('pa_id')
        novo_status = request.POST.get('status')
        
        # Validar o novo status
        status_validos = ['livre', 'ocupada', 'manutencao', 'inativa']
        if novo_status not in status_validos:
            return JsonResponse({'success': False, 'error': 'Status inválido'})
        
        try:
            # Buscar a PA
            pa = PosicaoAtendimento.objects.get(pk=pa_id)
            
            # Atualizar o status
            pa.status = novo_status
            pa.save()
            
            return JsonResponse({'success': True})
        except PosicaoAtendimento.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'PA não encontrada'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método inválido'})

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
def atribuicao_periferico(request):
    # Instancia o formulário para cadastrar novo periférico (sempre, para GET)
    form_periferico = PerifericoForm()
    
    if request.method == 'POST':
        # Checa qual formulário foi submetido usando o nome do botão
        if 'submit_periferico' in request.POST:
            # Esta parte é para o form_periferico, não nos preocupamos com o form_atribuicao_pa aqui
            # A lógica de processamento do form_periferico já deve existir ou ser tratada por periferico_create
            pass # Assumindo que o POST de form_periferico é tratado em periferico_create ou aqui
        
        elif 'submit_atribuicao_pa' in request.POST:
            form_atribuicao_pa = AtribuicaoPerifericoPAForm(request.POST)
            if form_atribuicao_pa.is_valid():
                form_atribuicao_pa.save()
                messages.success(request, 'Atribuição de periférico a PA cadastrada com sucesso!')
                return redirect('ti:atribuicao_periferico') 
            # Se o form_atribuicao_pa não for válido, ele será passado para o contexto com erros
            # e seu campo 'periferico' será filtrado abaixo.
    else:
        # Para requisições GET, instancia um formulário de atribuição vazio
        form_atribuicao_pa = AtribuicaoPerifericoPAForm()
    
    # Modificar o queryset para o campo 'periferico' do formulário de atribuição PA
    # Isso se aplica tanto para GET (novo formulário) quanto para POST inválido do form_atribuicao_pa
    # (quando ele é re-renderizado com erros)
    # Se o form_atribuicao_pa não foi definido no POST (ou seja, era o form_periferico que foi submetido),
    # precisamos instanciá-lo aqui para o contexto.
    if 'form_atribuicao_pa' not in locals():
        form_atribuicao_pa = AtribuicaoPerifericoPAForm()

    form_atribuicao_pa.fields['periferico'].queryset = Periferico.objects.filter(status='disponivel').order_by('tipo__nome', 'marca', 'modelo')
    
    # Contexto para os selects dos formulários (manter os existentes se ainda forem usados)
    tipos_perifericos = TipoPeriferico.objects.all()
    # perifericos_disponiveis é agora tratado pelo queryset do form
    posicoes_atendimento = PosicaoAtendimento.objects.all() # Por enquanto, todas as PAs
    
    context = {
        'title': 'Gestão de Periféricos e Atribuições',
        'form_periferico': form_periferico, 
        'form_atribuicao_pa': form_atribuicao_pa,
        'tipos_perifericos_list': tipos_perifericos,
        # 'perifericos_list': perifericos_disponiveis, # Não é mais necessário passar separado se o form usa o queryset
        'posicoes_atendimento_list': posicoes_atendimento # Será modificado por JS
    }
    return render(request, 'apps/ti/atribuicao_periferico.html', context)

@login_required
def atribuicao_periferico_pa_create(request):
    # Esta view pode não ser mais necessária para o POST do formulário de atribuição,
    # mas pode ser mantida se houver outros usos ou para GET (embora o form agora esteja na 'list' view).
    # Por ora, vamos manter a lógica original, mas o POST dela não será mais atingido pelo form principal.
    if request.method == 'POST':
        form = AtribuicaoPerifericoPAForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de periférico a PA cadastrada com sucesso!')
            # Idealmente, redirecionaria para a nova página unificada
            return redirect('ti:atribuicao_periferico') 
        else:
            # Tratamento de erro se este POST for atingido e inválido (improvável com a nova estrutura)
            # Re-renderizar a página principal com o formulário inválido
            # Precisamos reconstruir o contexto da página principal aqui
            form_periferico = PerifericoForm()
            tipos_perifericos = TipoPeriferico.objects.all()
            perifericos_disponiveis = Periferico.objects.filter(status='disponivel')
            posicoes_atendimento = PosicaoAtendimento.objects.all()
            context = {
                'title': 'Gestão de Periféricos e Atribuições',
                'form_periferico': form_periferico,
                'form_atribuicao_pa': form, # form é o AtribuicaoPerifericoPAForm com erros
                'tipos_perifericos_list': tipos_perifericos,
                'perifericos_list': perifericos_disponiveis,
                'posicoes_atendimento_list': posicoes_atendimento
            }
            messages.error(request, 'Erro ao tentar atribuir periférico. Verifique os campos.')
            return render(request, 'apps/ti/atribuicao_periferico.html', context)
    else:
        # Se for GET, apenas redireciona para a página principal onde o formulário agora reside
        return redirect('ti:atribuicao_periferico')

@login_required
def atribuicao_periferico_pa_update(request, pk):
    atribuicao = get_object_or_404(AtribuicaoPerifericoPA, pk=pk)
    if request.method == 'POST':
        form = AtribuicaoPerifericoPAForm(request.POST, instance=atribuicao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de periférico a PA atualizada com sucesso!')
            return redirect('ti:atribuicao_periferico')
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
        return redirect('ti:atribuicao_periferico')
    
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

@login_required
@require_POST # Garante que a view só aceite POST
def remover_periferico_pa(request):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Requisição inválida.'}, status=400)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            periferico_id = data.get('periferico_id')
            pa_id = data.get('pa_id')
        else:
            return JsonResponse({'success': False, 'error': 'Requisição inválida. Esperado JSON.'}, status=400)

        if not periferico_id or not pa_id:
            return JsonResponse({'success': False, 'error': 'IDs do periférico e da PA são obrigatórios.'}, status=400)

        # Encontrar a atribuição ATIVA do periférico para esta PA
        atribuicao = get_object_or_404(
            AtribuicaoPerifericoPA,
            periferico_id=periferico_id,
            posicao_atendimento_id=pa_id,
            ativo=True # Garante que estamos removendo a atribuição ativa
        )

        # Marcar a atribuição como inativa em vez de deletar
        atribuicao.ativo = False
        atribuicao.data_remocao = timezone.now()
        atribuicao.save()
        
        # Atualizar o status do periférico para disponível
        periferico = atribuicao.periferico
        # Verificar se o periférico não está ativo em nenhuma outra PA antes de mudar status para 'disponivel'
        outras_atribuicoes_ativas = AtribuicaoPerifericoPA.objects.filter(
            periferico=periferico,
            ativo=True
        ).exclude(pk=atribuicao.pk).exists()
        
        if not outras_atribuicoes_ativas:
            periferico.status = 'disponivel'
            periferico.save()

        return JsonResponse({'success': True, 'message': 'Periférico removido da PA com sucesso.'})

    except AtribuicaoPerifericoPA.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Atribuição ativa não encontrada para este periférico e PA.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Corpo da requisição JSON inválido.'}, status=400)
    except Exception as e:
        # Logar o erro em um ambiente de produção
        # logger.error(f"Erro ao remover periférico da PA: {e}")
        return JsonResponse({'success': False, 'error': f'Erro interno do servidor: {str(e)}'}, status=500)

@login_required
def render_controlesalas(request):
    return render(request, 'apps/ti/controle_salas.html')

@login_required
@require_GET # Adicionado para aceitar apenas GET
def api_controle_salas(request):
    """
    API para fornecer dados do controle de salas de forma otimizada.
    """
    try:
        # Otimização das queries
        salas = Sala.objects.prefetch_related(
            'ilha_set', # Ilhas da sala
            'ilha_set__posicaoatendimento_set', # PAs da ilha
            'ilha_set__posicaoatendimento_set__atribuicaofuncionariopa_set', # Atribuição Func a PA
            'ilha_set__posicaoatendimento_set__atribuicaofuncionariopa_set__funcionario', # Funcionário da Atribuição
            'ilha_set__posicaoatendimento_set__atribuicaoperifericopa_set', # Atribuição Perif a PA
            'ilha_set__posicaoatendimento_set__atribuicaoperifericopa_set__periferico', # Periférico da Atribuição
            'ilha_set__posicaoatendimento_set__atribuicaoperifericopa_set__periferico__tipo' # Tipo do Periférico
        ).all()

        salas_data = []
        for sala in salas:
            ilhas_data = []
            for ilha in sala.ilha_set.all():
                pas_data = []
                for pa in ilha.posicaoatendimento_set.all():
                    # Encontrar funcionário ativo (se houver)
                    funcionario_ativo = None
                    # Itera sobre as atribuições pré-carregadas
                    for atr_func in pa.atribuicaofuncionariopa_set.all():
                        if atr_func.ativo: # Considera apenas a ativa
                            funcionario_ativo = {
                                'id': atr_func.funcionario.id,
                                'nome_completo': atr_func.funcionario.nome_completo,
                                'ramal': atr_func.funcionario.ramal
                            }
                            break # Assume apenas um funcionário ativo por PA
                    
                    # Encontrar periféricos ativos
                    perifericos_ativos = []
                    # Itera sobre as atribuições pré-carregadas
                    for atr_perif in pa.atribuicaoperifericopa_set.all():
                        if atr_perif.ativo: # Considera apenas as ativas
                            perifericos_ativos.append({
                                'id': atr_perif.periferico.id,
                                'tipo': atr_perif.periferico.tipo.nome,
                                'marca': atr_perif.periferico.marca,
                                'modelo': atr_perif.periferico.modelo
                            })

                    pas_data.append({
                        'id': pa.id,
                        'numero': pa.numero,
                        'status': pa.status,
                        'funcionario': funcionario_ativo, # Pode ser None
                        'perifericos': perifericos_ativos
                    })
                
                ilhas_data.append({
                    'id': ilha.id,
                    'nome': ilha.nome,
                    'posicoes_atendimento': pas_data
                })
            
            salas_data.append({
                'id': sala.id,
                'nome': sala.nome,
                'ilhas': ilhas_data
            })
        
        return JsonResponse({
            'success': True,
            'salas': salas_data
        })
    except Exception as e:
        # Considerar loggar o erro: import logging; logger = logging.getLogger(__name__); logger.error(...) 
        return JsonResponse({
            'success': False,
            'error': f'Erro ao carregar dados das salas: {str(e)}'
        }, status=500)

@require_GET
@login_required # Opcional, mas recomendado
def get_funcionarios_json(request):
    """
    Retorna uma lista de funcionários ativos em formato JSON
    para popular o dropdown.
    """
    try:
        # Filtrar funcionários ativos e ordenar por nome
        funcionarios = Funcionario.objects.filter(status=True).order_by('nome_completo')
        
        # Preparar dados para JSON
        funcionarios_data = [
            {
                'id': f.id,
                'nome': f.nome_completo,
                'ramal': f.ramal or '' # Tratar ramal nulo
            }
            for f in funcionarios
        ]
        
        return JsonResponse({'funcionarios': funcionarios_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
@login_required # Opcional, mas recomendado
def atribuir_funcionario_pa(request):
    """
    Atribui um funcionário a uma PA ou desatribui (se funcionario_id for None/0).
    Espera um JSON no corpo da requisição com pa_id e funcionario_id.
    
    Funcionalidades:
    1. Remove o funcionário atual da PA e substitui pelo novo (em PosicaoAtendimento.funcionario)
    2. Se o novo funcionário já estiver em outra PA, ele é removido de lá (em PosicaoAtendimento.funcionario)
    3. Gerencia o histórico em AtribuicaoFuncionarioPA:
        a. Finaliza atribuições antigas para a PA alvo.
        b. Finaliza atribuições antigas para o funcionário em outras PAs.
        c. Cria uma nova atribuição ativa para o funcionário na PA alvo.
    4. Retorna todos os dados do funcionário relacionados
    """
    try:
        data = json.loads(request.body)
        pa_id = data.get('pa_id')
        funcionario_id = data.get('funcionario_id') # Pode ser None ou 0 para desatribuir

        if not pa_id:
            return JsonResponse({'error': 'ID da PA não fornecido.'}, status=400)

        pa_alvo = get_object_or_404(PosicaoAtendimento, pk=pa_id)
        novo_funcionario = None
        novo_status_pa = 'livre' # Status padrão se desatribuir
        pas_afetadas_info = [] # Lista de PAs afetadas para retornar ao frontend
        hoje = timezone.now() # Definir uma vez para consistência

        # 1. Lidar com o NOVO FUNCIONÁRIO (se um está sendo atribuído)
        if funcionario_id and int(funcionario_id) != 0:
            novo_funcionario = get_object_or_404(Funcionario, pk=funcionario_id)
            novo_status_pa = 'ocupada'

            # 1a. Verificar se este NOVO FUNCIONÁRIO já está atribuído a OUTRA PA
            # e desvinculá-lo de lá (tanto de PosicaoAtendimento quanto de AtribuicaoFuncionarioPA)
            outras_pas_do_novo_funcionario = PosicaoAtendimento.objects.filter(
                funcionario=novo_funcionario
            ).exclude(id=pa_alvo.id).select_related('ilha', 'sala')

            for pa_anterior_do_novo_func in outras_pas_do_novo_funcionario:
                pas_afetadas_info.append({
                    'id': pa_anterior_do_novo_func.id,
                    'numero': pa_anterior_do_novo_func.numero,
                    'status': 'livre',
                    'ilha': pa_anterior_do_novo_func.ilha.nome if pa_anterior_do_novo_func.ilha else 'N/A',
                    'sala': pa_anterior_do_novo_func.sala.nome if pa_anterior_do_novo_func.sala else 'N/A'
                })
                
                # Finalizar AtribuicaoFuncionarioPA na PA anterior do NOVO funcionário
                AtribuicaoFuncionarioPA.objects.filter(
                    posicao_atendimento=pa_anterior_do_novo_func,
                    funcionario=novo_funcionario,
                    ativo=True
                ).update(ativo=False, data_fim=hoje)
                
                # Atualizar PosicaoAtendimento da PA anterior
                pa_anterior_do_novo_func.funcionario = None
                pa_anterior_do_novo_func.status = 'livre'
                pa_anterior_do_novo_func.save()
        else: # Caso de desatribuição (funcionario_id é None ou 0)
            funcionario_id = None # Garantir que seja None para a resposta JSON e lógica subsequente

        # 2. Lidar com o FUNCIONÁRIO ANTIGO da PA ALVO (se havia um)
        funcionario_antigo_da_pa_alvo_info = None
        if pa_alvo.funcionario: # Se a PA alvo tinha um funcionário ANTES da mudança
            funcionario_antigo_da_pa_alvo_info = {
                'id': pa_alvo.funcionario.id,
                'nome': pa_alvo.funcionario.nome_completo,
                'ramal': pa_alvo.funcionario.ramal
            }
            # Finalizar AtribuicaoFuncionarioPA do FUNCIONÁRIO ANTIGO na PA ALVO
            # Isso acontece mesmo que o novo funcionário seja o mesmo (reafirmação da atribuição) ou se for desatribuição
            AtribuicaoFuncionarioPA.objects.filter(
                posicao_atendimento=pa_alvo,
                funcionario=pa_alvo.funcionario,
                ativo=True
            ).update(ativo=False, data_fim=hoje)

        # 3. Atualizar a PA ALVO (PosicaoAtendimento)
        pa_alvo.funcionario = novo_funcionario # Pode ser None
        pa_alvo.status = novo_status_pa
        pa_alvo.save()

        # 4. Criar NOVA AtribuicaoFuncionarioPA para o NOVO FUNCIONÁRIO na PA ALVO (se houver novo funcionário)
        if novo_funcionario:
            AtribuicaoFuncionarioPA.objects.create(
                funcionario=novo_funcionario,
                posicao_atendimento=pa_alvo,
                data_inicio=hoje,
                ativo=True
            )
        
        # 5. Preparar os dados do funcionário para a resposta
        novo_funcionario_info = None
        if novo_funcionario:
            novo_funcionario_info = {
                'id': novo_funcionario.id,
                'nome': novo_funcionario.nome_completo,
                'ramal': novo_funcionario.ramal,
                'cargo': novo_funcionario.cargo.nome if novo_funcionario.cargo else None,
                'departamento': novo_funcionario.departamento.nome if novo_funcionario.departamento else None,
                'empresa': novo_funcionario.empresa.nome if novo_funcionario.empresa else None,
                'loja': novo_funcionario.loja.nome if novo_funcionario.loja else None
            }
        
        # 6. Preparar dados de resposta
        response_data = {
            'success': True,
            'message': 'PA atualizada e histórico de atribuição gerenciado com sucesso.',
            'pa_id': pa_alvo.id,
            'pa_numero': pa_alvo.numero,
            'novo_status': pa_alvo.status, # Status atualizado da PA alvo
            'funcionario': novo_funcionario_info, # Dados do novo funcionário atribuído
            'funcionario_antigo': funcionario_antigo_da_pa_alvo_info, # Dados do funcionário que saiu da PA alvo
            'pas_afetadas': pas_afetadas_info # Lista de outras PAs que foram atualizadas
        }
        return JsonResponse(response_data)

    except PosicaoAtendimento.DoesNotExist:
        return JsonResponse({'error': 'PA não encontrada.'}, status=404)
    except Funcionario.DoesNotExist:
        return JsonResponse({'error': 'Funcionário não encontrado.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados JSON inválidos.'}, status=400)
    except Exception as e:
        # Logar o erro real no servidor seria ideal aqui
        return JsonResponse({'error': f'Erro interno do servidor: {str(e)}'}, status=500)

@require_GET
@login_required
def api_pas_para_atribuicao_periferico(request, periferico_id):
    """
    Retorna uma lista de PAs que NÂO possuem um periférico do MESMO TIPO 
    que o periférico_id fornecido já atribuído ativamente.
    """
    try:
        periferico_selecionado = get_object_or_404(Periferico, pk=periferico_id)
        tipo_do_periferico_selecionado_id = periferico_selecionado.tipo.id

        # IDs das PAs que JÁ TÊM um periférico deste tipo atribuído ativamente
        pas_com_este_tipo_ids = AtribuicaoPerifericoPA.objects.filter(
            periferico__tipo_id=tipo_do_periferico_selecionado_id,
            ativo=True
        ).values_list('posicao_atendimento_id', flat=True).distinct()

        # Buscar todas as PAs que NÃO ESTÃO na lista acima
        # Ordenar por sala, ilha e número para consistência
        pas_disponiveis = PosicaoAtendimento.objects.exclude(
            id__in=list(pas_com_este_tipo_ids)
        ).select_related('ilha', 'sala').order_by('sala__nome', 'ilha__nome', 'numero')

        pas_data = [
            {
                'id': pa.id,
                # Para o texto da opção, podemos usar o __str__ do modelo ou montar um customizado
                'nome': f"{pa.sala.nome if pa.sala else 'S/ Sala'} - {pa.ilha.nome if pa.ilha else 'S/ Ilha'} - PA {pa.numero}"
            }
            for pa in pas_disponiveis
        ]
        
        return JsonResponse({'posicoes_atendimento': pas_data})
    except Periferico.DoesNotExist:
        return JsonResponse({'error': 'Periférico não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


