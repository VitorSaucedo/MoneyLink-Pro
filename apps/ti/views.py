from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch, Subquery, OuterRef
from .utils import (atribuir_item_pa, desatribuir_item_pa, verificar_disponibilidade_periferico, 
                    verificar_disponibilidade_computador, gerar_resposta_api, listar_itens_atribuidos_pa)
from .pagination_utils import paginate_queryset, get_pagination_data
from .models import (
    TipoPeriferico, 
    Periferico, 
    PosicaoAtendimento, 
    AtribuicaoFuncionarioPA, 
    AtribuicaoPerifericoPA,
    Sala,
    Ilha,
    Computador,
    AtribuicaoComputadorPA
)
from .forms import (
    TipoPerifericoForm,
    PerifericoForm,
    PosicaoAtendimentoForm,
    AtribuicaoFuncionarioPAForm,
    AtribuicaoPerifericoPAForm,
    SalaForm,
    IlhaForm,
    ComputadorForm,
    AtribuicaoComputadorPAForm
)
from apps.funcionarios.models import Funcionario
import json
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest

# Create your views here.

@login_required
def controle_estoque(request):
    """
    View para exibir o controle de estoque de periféricos por sala e ilha.
    Mostra uma tabela com a contagem de periféricos de cada tipo em cada sala/ilha.
    """
    # Obter todas as salas com ilhas pré-carregadas
    salas = Sala.objects.all().prefetch_related(
        Prefetch('ilhas', queryset=Ilha.objects.all().order_by('nome'))
    )
    
    # Obter todos os tipos de periféricos
    tipos_perifericos = TipoPeriferico.objects.all().order_by('nome')
    
    # Inicializar dicionário para contagem de periféricos por sala/ilha/tipo
    perifericos_por_sala_ilha = {}
    total_geral_perifericos = 0
    
    # Popular o dicionário com os dados
    for sala in salas:
        perifericos_por_sala_ilha[sala.id] = {}
        
        for ilha in sala.ilhas.all():
            perifericos_por_sala_ilha[sala.id][ilha.id] = {}
            
            # Inicializar contador para cada tipo de periférico nesta ilha
            for tipo in tipos_perifericos:
                perifericos_por_sala_ilha[sala.id][ilha.id][tipo.id] = 0
            
            # Obter todas as PAs desta ilha
            posicoes_atendimento_ilha = PosicaoAtendimento.objects.filter(ilha=ilha)
            
            # Para cada PA, buscar e contar os periféricos atribuídos
            for pa in posicoes_atendimento_ilha:
                # Buscar atribuições ativas de periféricos para esta PA usando select_related
                atribuicoes_ativas = AtribuicaoPerifericoPA.objects.filter(
                    posicao_atendimento=pa,
                    ativo=True
                ).select_related('periferico__tipo')
                
                # Contar periféricos por tipo
                for atribuicao in atribuicoes_ativas:
                    tipo_id = atribuicao.periferico.tipo.id
                    if tipo_id in perifericos_por_sala_ilha[sala.id][ilha.id]:
                        perifericos_por_sala_ilha[sala.id][ilha.id][tipo_id] += 1
                        total_geral_perifericos += 1
    
    # Obter contagem de computadores cadastrados de forma otimizada
    computadores_cadastrados_total = Computador.objects.count()

    # Contagem de computadores em uso por sala/ilha - abordagem mais eficiente
    computadores_em_uso_por_sala_ilha = {}
    computadores_em_uso_total_geral = 0
    
    # Pré-calcular contagens de computadores por ilha usando agregação
    contagens_computadores_por_ilha = (
        AtribuicaoComputadorPA.objects
        .filter(ativo=True)
        .values('posicao_atendimento__ilha')
        .annotate(count=Count('computador', distinct=True))
    )
    
    # Criar dicionário de contagens para acesso rápido
    contagens_dict = {item['posicao_atendimento__ilha']: item['count'] 
                     for item in contagens_computadores_por_ilha if item['posicao_atendimento__ilha'] is not None}
    
    # Preencher o dicionário de contagens por sala/ilha
    for sala in salas:
        computadores_em_uso_por_sala_ilha[sala.id] = {}
        for ilha in sala.ilhas.all():
            # Obter a contagem do dicionário pré-calculado ou usar 0
            contagem_ilha_atual = contagens_dict.get(ilha.id, 0)
            computadores_em_uso_por_sala_ilha[sala.id][ilha.id] = contagem_ilha_atual
            computadores_em_uso_total_geral += contagem_ilha_atual

    # Computadores em uso - Query mais eficiente
    ids_computadores_em_uso = AtribuicaoComputadorPA.objects.filter(ativo=True)\
        .values_list('computador_id', flat=True)\
        .distinct()
    
    # Computadores disponíveis - Query mais eficiente
    computadores_disponiveis_total = Computador.objects.filter(status='disponivel')\
        .exclude(id__in=Subquery(ids_computadores_em_uso))\
        .count()

    # Calcular computadores disponíveis POR MARCA (incluindo marcas com 0 disponíveis)
    # ids_computadores_em_uso já foi definido acima
    
    # 1. Obter todas as marcas distintas cadastradas de computadores (para garantir que todas apareçam na lista)
    todas_as_marcas_cadastradas = Computador.objects.values_list('marca', flat=True).distinct().order_by('marca')
    
    # 2. Obter a contagem de computadores REALMENTE disponíveis por marca
    #    (status='disponivel' E não estão em uso)
    contagem_disponiveis_raw = Computador.objects.filter(
        status='disponivel'
    ).exclude(
        id__in=ids_computadores_em_uso
    ).values('marca').annotate(
        quantidade_disponivel=Count('id') # Assumindo que cada registro de Computador é uma unidade
    ).order_by('marca')
    
    # 3. Criar um dicionário com as contagens de disponíveis para consulta rápida
    disponiveis_dict = {item['marca']: item['quantidade_disponivel'] for item in contagem_disponiveis_raw}
    
    # 4. Montar a lista final, garantindo todas as marcas com suas respectivas quantidades (ou 0)
    computadores_disponiveis_por_marca_list = []
    for marca_nome in todas_as_marcas_cadastradas:
        computadores_disponiveis_por_marca_list.append({
            'marca': marca_nome,
            'quantidade_disponivel': disponiveis_dict.get(marca_nome, 0) # Usa 0 se a marca não estiver no dict de disponíveis
        })

    # --- Construção do Histórico de Movimentações de forma otimizada --- 
    
    # Define a quantidade máxima de registros a serem retornados de cada tabela
    limite_registros = 500  # Limite para melhorar a performance
    itens_por_pagina = 20   # Aumentamos a quantidade para mostrar mais histórico por página
    
    # 1. Buscar histórico de movimentações de PERIFÉRICOS com limite para melhorar performance
    perifericos_query = AtribuicaoPerifericoPA.objects\
        .select_related('periferico', 'periferico__tipo', 'posicao_atendimento__ilha', 'posicao_atendimento__sala')\
        .order_by('-data_atribuicao')[:limite_registros]
    
    historico_movimentacoes = []
    
    # Processar atribuições de periféricos
    for atribuicao in perifericos_query:
        pa = atribuicao.posicao_atendimento
        periferico = atribuicao.periferico
        
        # Construir local e descrição do item uma única vez por atribuição
        sala_nome = pa.sala.nome if pa.sala else 'S/Sala'
        ilha_nome = pa.ilha.nome if pa.ilha else 'S/Ilha'
        local = f"{sala_nome}, {ilha_nome} - PA {pa.numero}"
        item_descricao = f"Periférico: {periferico.tipo.nome} {periferico.marca} {periferico.modelo or ''}"
        
        # Evento de adição
        if atribuicao.data_atribuicao:
            historico_movimentacoes.append({
                'data_evento': atribuicao.data_atribuicao,
                'tipo_evento': 'Adicionado em',
                'item_movimentado': item_descricao,
                'local': local,
                'tipo_item': 'periferico'
            })
        
        # Evento de remoção
        if atribuicao.data_remocao:
            historico_movimentacoes.append({
                'data_evento': atribuicao.data_remocao,
                'tipo_evento': 'Removido de',
                'item_movimentado': item_descricao,
                'local': local,
                'tipo_item': 'periferico'
            })

    # 2. Buscar histórico de movimentações de COMPUTADORES com limite para melhorar performance
    computadores_query = AtribuicaoComputadorPA.objects\
        .select_related('computador', 'posicao_atendimento__ilha', 'posicao_atendimento__sala')\
        .order_by('-data_atribuicao')[:limite_registros]
    
    # Processar atribuições de computadores
    for atribuicao in computadores_query:
        pa = atribuicao.posicao_atendimento
        computador = atribuicao.computador
        
        # Construir local e descrição do item uma única vez por atribuição
        sala_nome = pa.sala.nome if pa.sala else 'S/Sala'
        ilha_nome = pa.ilha.nome if pa.ilha else 'S/Ilha'
        local = f"{sala_nome}, {ilha_nome} - PA {pa.numero}"
        item_descricao = f"Computador: {computador.marca}"
        
        # Evento de adição
        if atribuicao.data_atribuicao:
            historico_movimentacoes.append({
                'data_evento': atribuicao.data_atribuicao,
                'tipo_evento': 'Adicionado em',
                'item_movimentado': item_descricao,
                'local': local,
                'tipo_item': 'computador'
            })
        
        # Evento de remoção
        if atribuicao.data_remocao:
            historico_movimentacoes.append({
                'data_evento': atribuicao.data_remocao,
                'tipo_evento': 'Removido de',
                'item_movimentado': item_descricao,
                'local': local,
                'tipo_item': 'computador'
            })
    
    # Ordenar o histórico combinado por data_evento, mais recentes primeiro
    historico_movimentacoes = [item for item in historico_movimentacoes if item.get('data_evento')]
    historico_movimentacoes.sort(key=lambda x: x['data_evento'], reverse=True)
    
    # Obter a data da última atualização para o contexto
    data_ultima_atualizacao_real = None
    if historico_movimentacoes:
        data_ultima_atualizacao_real = historico_movimentacoes[0]['data_evento']
    
    # Usar a função auxiliar de paginação
    page_obj = paginate_queryset(request, historico_movimentacoes, itens_por_pagina)
    # Obter metadados de paginação para o template
    pagination_data = get_pagination_data(page_obj)

    # Contexto para o template
    context = {
        'salas': salas,
        'tipos_perifericos': tipos_perifericos,
        'perifericos_por_sala_ilha': perifericos_por_sala_ilha,
        'total_geral_perifericos': total_geral_perifericos,
        'historico_page_obj': page_obj, # Passa o objeto da página para o template
        'pagination_data': pagination_data, # Adiciona metadados de paginação
        'data_ultima_atualizacao_real': data_ultima_atualizacao_real, # Adiciona a data ao contexto
        'computadores_cadastrados_total': computadores_cadastrados_total,
        'computadores_em_uso_por_sala_ilha': computadores_em_uso_por_sala_ilha,
        'computadores_em_uso_total_geral': computadores_em_uso_total_geral,
        'computadores_disponiveis_total': computadores_disponiveis_total,
        'computadores_disponiveis_por_marca_list': computadores_disponiveis_por_marca_list,
        'itens_por_pagina': itens_por_pagina,
    }
    
    return render(request, 'apps/ti/controle_estoque.html', context)

@login_required
def controle_manutencao(request):
    # Utilizar as ferramentas de otimização de consulta
    # 1. Carregar periféricos em manutenção com seus tipos
    perifericos_manutencao_qs = Periferico.objects.filter(status='manutencao').select_related('tipo')
    
    # 2. Carregar computadores em manutenção
    computadores_manutencao_qs = Computador.objects.filter(status='manutencao')
    
    # 3. Pré-carregar as últimas atribuições dos periféricos em manutenção
    # Utilizar um dicionário para mapear periféricos para suas últimas atribuições
    perifericos_ids = list(perifericos_manutencao_qs.values_list('id', flat=True))
    ultima_atribuicao_periferico = {}
    
    if perifericos_ids:
        # Usando Subquery para obter apenas a última atribuição de cada periférico
        ultimas_atribuicoes_perifericos = AtribuicaoPerifericoPA.objects\
            .filter(periferico_id__in=perifericos_ids)\
            .order_by('periferico_id', '-data_atribuicao')\
            .distinct('periferico_id')\
            .select_related('posicao_atendimento__sala', 'posicao_atendimento__ilha')

        # Em bancos que não suportam distinct com campos específicos (como SQLite),
        # podemos usar esta abordagem alternativa:
        perifericos_atribuicoes = {}
        for atr in AtribuicaoPerifericoPA.objects.filter(periferico_id__in=perifericos_ids)\
                                   .order_by('-data_atribuicao')\
                                   .select_related('posicao_atendimento__sala', 'posicao_atendimento__ilha'):            
            if atr.periferico_id not in perifericos_atribuicoes:
                perifericos_atribuicoes[atr.periferico_id] = atr
        
        ultima_atribuicao_periferico = perifericos_atribuicoes
    
    # 4. Pré-carregar as últimas atribuições dos computadores em manutenção
    # Utilizar um dicionário para mapear computadores para suas últimas atribuições
    computadores_ids = list(computadores_manutencao_qs.values_list('id', flat=True))
    ultima_atribuicao_computador = {}
    
    if computadores_ids:
        # Abordagem similar para computadores
        computadores_atribuicoes = {}
        for atr in AtribuicaoComputadorPA.objects.filter(computador_id__in=computadores_ids)\
                                   .order_by('-data_atribuicao')\
                                   .select_related('posicao_atendimento__sala', 'posicao_atendimento__ilha'):
            if atr.computador_id not in computadores_atribuicoes:
                computadores_atribuicoes[atr.computador_id] = atr
        
        ultima_atribuicao_computador = computadores_atribuicoes
    
    # Inicializar contadores
    itens_manutencao_lista = []
    contagem_por_tipo = {
        'Mouse': 0,
        'Mousepad': 0,
        'Teclado': 0,
        'Monitor': 0,
        'Fone': 0,
        'Computador': 0,
        'Outros Periféricos': 0
    }
    total_itens_manutencao = 0
    
    # Processar periféricos em manutenção
    for p in perifericos_manutencao_qs:
        # Obter a última atribuição do dicionário pré-carregado
        ultima_atribuicao = ultima_atribuicao_periferico.get(p.id)
        ultima_pa_obj = ultima_atribuicao.posicao_atendimento if ultima_atribuicao else None
        
        # Adicionar informações do periférico à lista
        itens_manutencao_lista.append({
            'id_item': p.id,
            'tipo_item_obj': p,
            'nome_item': p.tipo.nome,
            'marca_modelo': f"{p.marca} {p.modelo}",
            'ultima_pa': ultima_pa_obj,
            'observacoes': p.observacoes,
            'tipo_item_slug': 'periferico'
        })
        
        # Atualizar contagem por tipo
        nome_tipo = p.tipo.nome.capitalize()
        if nome_tipo in contagem_por_tipo:
            contagem_por_tipo[nome_tipo] += 1
        else:
            # Mapear para categorias conhecidas
            if 'mouse' in nome_tipo.lower() and nome_tipo != 'Mousepad':
                contagem_por_tipo['Mouse'] += 1
            elif 'mousepad' in nome_tipo.lower():
                contagem_por_tipo['Mousepad'] += 1
            elif 'teclado' in nome_tipo.lower():
                contagem_por_tipo['Teclado'] += 1
            elif 'monitor' in nome_tipo.lower():
                contagem_por_tipo['Monitor'] += 1
            elif 'fone' in nome_tipo.lower() or 'headset' in nome_tipo.lower():
                contagem_por_tipo['Fone'] += 1
            else:
                contagem_por_tipo['Outros Periféricos'] += 1
        
        total_itens_manutencao += 1
    
    # Processar computadores em manutenção
    for c in computadores_manutencao_qs:
        # Obter a última atribuição do dicionário pré-carregado
        ultima_atribuicao = ultima_atribuicao_computador.get(c.id)
        ultima_pa_obj = ultima_atribuicao.posicao_atendimento if ultima_atribuicao else None
        
        # Adicionar informações do computador à lista
        itens_manutencao_lista.append({
            'id_item': c.id,
            'tipo_item_obj': c,
            'nome_item': 'Computador',
            'marca_modelo': c.marca,
            'ultima_pa': ultima_pa_obj,
            'observacoes': c.observacoes,
            'tipo_item_slug': 'computador'
        })
        
        contagem_por_tipo['Computador'] += 1
        total_itens_manutencao += 1
    
    # Ordenar itens por tipo para melhor visualização
    itens_manutencao_lista.sort(key=lambda x: (x['tipo_item_slug'], x['nome_item']))
    
    # Implementar paginação
    itens_por_pagina = 15
    page_obj = paginate_queryset(request, itens_manutencao_lista, itens_por_pagina)
    pagination_data = get_pagination_data(page_obj)
    
    # Preparar contexto para o template
    context = {
        'itens_manutencao': page_obj,
        'pagination_data': pagination_data,
        'contagem_por_tipo': contagem_por_tipo,
        'total_itens_manutencao': total_itens_manutencao,
        'header_title': 'Controle de Manutenção de Periféricos e Computadores',
        'title': 'Controle de Manutenção',
        'itens_por_pagina': itens_por_pagina,
    }
    
    return render(request, 'apps/ti/controle_manutencao.html', context)

@login_required
@require_POST
def marcar_consertado(request, item_id, tipo_item_slug):
    try:
        if tipo_item_slug == 'periferico':
            item = get_object_or_404(Periferico, id=item_id)
            item.status = 'disponivel' # Ou 'livre' dependendo da sua nomenclatura para disponível
            item.save()
            messages.success(request, f"Periférico '{item}' marcado como consertado e disponível.")
        elif tipo_item_slug == 'computador':
            item = get_object_or_404(Computador, id=item_id)
            item.status = 'disponivel'
            item.save()
            messages.success(request, f"Computador '{item}' marcado como consertado e disponível.")
        else:
            messages.error(request, "Tipo de item desconhecido.")
            
    except Exception as e:
        messages.error(request, f"Erro ao marcar item como consertado: {e}")
        
    return redirect('ti:controle_manutencao')

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
        'computadores_list': Computador.objects.filter(status='disponivel'),
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
    
    # Obter todos os tipos de periféricos
    tipos_perifericos = TipoPeriferico.objects.all()
    # Lista de tipos comuns/esperados para cada PA (usado para verificar o que está faltando)
    tipos_perifericos_comuns = TipoPeriferico.objects.filter(nome__in=[
        'Mouse', 'Teclado', 'Monitor', 'Fone', 'Mousepad'
    ])
    
    # Carrega os periféricos atribuídos a cada PA
    perifericos_por_pa = {}
    perifericos_faltando_por_pa = {} # Para rastrear tipos de periféricos faltantes em cada PA
    
    atribuicoes = AtribuicaoPerifericoPA.objects.filter(ativo=True).select_related('periferico', 'periferico__tipo', 'posicao_atendimento')
    
    # Inicializar o dicionário para rastrear periféricos faltantes para todas as PAs
    for pa in posicoes:
        perifericos_faltando_por_pa[pa.id] = {
            'tipos': [t for t in tipos_perifericos_comuns],  # Lista de objetos TipoPeriferico
            'nomes': [t.nome for t in tipos_perifericos_comuns]  # Lista de nomes para facilitar verificação
        }
    
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
        
        # Remover da lista de tipos faltantes
        tipo_atual = atribuicao.periferico.tipo
        if pa_id in perifericos_faltando_por_pa and tipo_atual.nome in perifericos_faltando_por_pa[pa_id]['nomes']:
            # Remover o tipo da lista de faltantes
            tipo_index = perifericos_faltando_por_pa[pa_id]['nomes'].index(tipo_atual.nome)
            perifericos_faltando_por_pa[pa_id]['nomes'].pop(tipo_index)
            perifericos_faltando_por_pa[pa_id]['tipos'].pop(tipo_index)
    
    # Carregar periféricos disponíveis por tipo
    perifericos_disponiveis_por_tipo = {}
    for tipo in tipos_perifericos_comuns:
        perifericos_disponiveis_por_tipo[tipo.id] = Periferico.objects.filter(
            tipo=tipo, 
            status='disponivel'
        ).values('id', 'marca', 'modelo')
    
    # Carrega os computadores atribuídos a cada PA
    computadores_por_pa = {}
    atribuicoes_computador = AtribuicaoComputadorPA.objects.filter(ativo=True).select_related('computador', 'posicao_atendimento')
    
    for atribuicao in atribuicoes_computador:
        pa_id = atribuicao.posicao_atendimento.id
        if pa_id not in computadores_por_pa:
            computadores_por_pa[pa_id] = []
        computadores_por_pa[pa_id].append({
            'marca': atribuicao.computador.marca,
            'id': atribuicao.computador.id
        })
    
    context = {
        'title': 'Controle de Salas - TI',
        'salas': salas,
        'ilhas': ilhas,
        'posicoes': posicoes,
        'perifericos_por_pa': perifericos_por_pa,
        'computadores_por_pa': computadores_por_pa,
        'perifericos_faltando_por_pa': perifericos_faltando_por_pa,
        'perifericos_disponiveis_por_tipo': perifericos_disponiveis_por_tipo,
        'tipos_perifericos_comuns': tipos_perifericos_comuns
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
    # Otimizar consulta com select_related para carregar tipos junto com periféricos
    perifericos_queryset = Periferico.objects.all()\
        .select_related('tipo')\
        .order_by('tipo__nome', 'marca', 'modelo')
    
    # Implementar filtros dinâmicos
    status_filter = request.GET.get('status')
    tipo_filter = request.GET.get('tipo_id')
    search_query = request.GET.get('query')
    
    # Aplicar filtros se fornecidos
    if status_filter and status_filter != 'todos':
        perifericos_queryset = perifericos_queryset.filter(status=status_filter)
    
    if tipo_filter:
        perifericos_queryset = perifericos_queryset.filter(tipo_id=tipo_filter)
    
    if search_query:
        perifericos_queryset = perifericos_queryset.filter(
            Q(marca__icontains=search_query) | 
            Q(modelo__icontains=search_query) |
            Q(numero_serie__icontains=search_query) |
            Q(tipo__nome__icontains=search_query)
        )
    
    # Implementar paginação
    itens_por_pagina = 20
    perifericos_paginados = paginate_queryset(request, perifericos_queryset, itens_por_pagina)
    pagination_data = get_pagination_data(perifericos_paginados)
    
    # Carregar tipos para filtro
    tipos_perifericos = TipoPeriferico.objects.all().order_by('nome')
    
    # Preparar opções para filtro de status
    opcoes_status = [
        {'value': 'todos', 'display': 'Todos'},
        {'value': 'disponivel', 'display': 'Disponível'},
        {'value': 'em_uso', 'display': 'Em Uso'},
        {'value': 'manutencao', 'display': 'Em Manutenção'},
        {'value': 'inativo', 'display': 'Inativo'}
    ]
    
    context = {
        'title': 'Periféricos',
        'perifericos': perifericos_paginados,
        'pagination_data': pagination_data,
        'itens_por_pagina': itens_por_pagina,
        'tipos_perifericos': tipos_perifericos,
        'opcoes_status': opcoes_status,
        'status_filter': status_filter,
        'tipo_filter': tipo_filter,
        'search_query': search_query,
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
    # Otimizar consulta com select_related para reduzir queries ao banco
    atribuicoes_queryset = AtribuicaoFuncionarioPA.objects.all()\
        .select_related('funcionario', 'posicao_atendimento__ilha', 'posicao_atendimento__sala')\
        .order_by('-ativo', '-data_inicio')
    
    # Implementar paginação
    itens_por_pagina = 20
    atribuicoes_paginadas = paginate_queryset(request, atribuicoes_queryset, itens_por_pagina)
    pagination_data = get_pagination_data(atribuicoes_paginadas)
    
    context = {
        'title': 'Atribuições de Funcionários a PAs',
        'atribuicoes': atribuicoes_paginadas,
        'pagination_data': pagination_data,
        'itens_por_pagina': itens_por_pagina,
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
            atribuicao = form.save()
            
            # Atualizar status do periférico para 'em_uso'
            periferico = atribuicao.periferico
            periferico.status = 'em_uso'
            periferico.save()
            
            messages.success(request, 'Atribuição de periférico a PA cadastrada com sucesso!')
            
            # Se a requisição veio via AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': 'Periférico atribuído com sucesso!',
                    'periferico': {
                        'id': periferico.id,
                        'tipo': periferico.tipo.nome,
                        'marca': periferico.marca,
                        'modelo': periferico.modelo
                    }
                })
                
            # Caso contrário, redirecionar normalmente
            return redirect('ti:atribuicao_periferico') 
        else:
            # Tratamento de erro
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
                
            # Se a requisição veio via AJAX, retornar JSON com erros
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
                
            # Caso contrário, renderizar template com erros
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
        return gerar_resposta_api(False, error='Requisição inválida.', status=400)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            periferico_id = data.get('periferico_id')
            pa_id = data.get('pa_id')
        else:
            return gerar_resposta_api(False, error='Requisição inválida. Esperado JSON.', status=400)

        if not periferico_id or not pa_id:
            return gerar_resposta_api(False, error='IDs do periférico e da PA são obrigatórios.', status=400)

        # Encontrar a atribuição ATIVA do periférico para esta PA
        atribuicao = get_object_or_404(
            AtribuicaoPerifericoPA,
            periferico_id=periferico_id,
            posicao_atendimento_id=pa_id,
            ativo=True # Garante que estamos removendo a atribuição ativa
        )

        # Usar a função auxiliar para desatribuir o periférico
        desatribuir_item_pa(atribuicao)

        return gerar_resposta_api(True, message='Periférico removido da PA com sucesso.')

    except AtribuicaoPerifericoPA.DoesNotExist:
        return gerar_resposta_api(False, error='Atribuição ativa não encontrada para este periférico e PA.', status=404)
    except json.JSONDecodeError:
        return gerar_resposta_api(False, error='Corpo da requisição JSON inválido.', status=400)
    except Exception as e:
        # Logar o erro em um ambiente de produção
        # logger.error(f"Erro ao remover periférico da PA: {e}")
        return gerar_resposta_api(False, error=f'Erro interno do servidor: {str(e)}', status=500)

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

@login_required
@require_POST
def ramal_update(request):
    """
    View para atualizar o ramal de um funcionário.
    """
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario_id')
        ramal = request.POST.get('ramal')
        
        # Log para debug
        print(f"Solicitação de atualização de ramal - Funcionário ID: {funcionario_id}, Ramal: {ramal}")
        
        if not funcionario_id or not ramal:
            messages.error(request, 'Funcionário e ramal são obrigatórios.')
            return redirect('ti:admin')
        
        # Verificar se o ramal já existe
        funcionario_com_ramal = Funcionario.objects.filter(ramal=ramal).exclude(id=funcionario_id).first()
        if funcionario_com_ramal:
            messages.error(request, f'O ramal {ramal} já está atribuído ao funcionário {funcionario_com_ramal.nome_completo}.')
            return redirect('ti:admin')
        
        try:
            funcionario = Funcionario.objects.get(id=funcionario_id)
            # Verificar se o ramal já está atribuído a este funcionário
            if funcionario.ramal == ramal:
                messages.info(request, f'O funcionário {funcionario.nome_completo} já possui o ramal {ramal}.')
            else:
                # Atualizar o ramal
                ramal_antigo = funcionario.ramal
                funcionario.ramal = ramal
                funcionario.save()
                
                # Log para debug
                print(f"Ramal atualizado - Funcionário: {funcionario.nome_completo}, Ramal antigo: {ramal_antigo}, Novo ramal: {ramal}")
                
                messages.success(request, f'Ramal {ramal} atribuído com sucesso ao funcionário {funcionario.nome_completo}.')
        except Funcionario.DoesNotExist:
            messages.error(request, 'Funcionário não encontrado.')
        
        return redirect('ti:admin')

@login_required
@require_POST
def api_verificar_ramal(request):
    """
    API para verificar se um ramal já existe.
    Recebe um JSON com ramal e funcionario_id.
    Retorna um JSON com existe=True/False e funcionario_nome se existir.
    """
    try:
        data = json.loads(request.body)
        ramal = data.get('ramal')
        funcionario_id = data.get('funcionario_id')
        
        # Log para debug
        print(f"API Verificar Ramal - Ramal: {ramal}, Funcionário ID: {funcionario_id}")
        
        if not ramal:
            return JsonResponse({'error': 'Ramal não fornecido.'}, status=400)
        
        # Verificar se o ramal já existe para outro funcionário
        query = Funcionario.objects.filter(ramal=ramal)
        
        # Log para debug
        print(f"Total de funcionários com ramal {ramal}: {query.count()}")
        for f in query:
            print(f"  - ID: {f.id}, Nome: {f.nome_completo}")
        
        # Excluir o próprio funcionário da verificação (se um ID foi fornecido)
        if funcionario_id and funcionario_id.isdigit() and int(funcionario_id) > 0:
            query = query.exclude(id=funcionario_id)
            # Log para debug
            print(f"Após excluir o funcionário {funcionario_id}, restaram: {query.count()}")
        
        # Buscar o primeiro resultado (se houver)
        funcionario_com_ramal = query.first()
        
        if funcionario_com_ramal:
            # Log para debug
            print(f"Ramal {ramal} já utilizado por: {funcionario_com_ramal.nome_completo} (ID: {funcionario_com_ramal.id})")
            
            return JsonResponse({
                'existe': True,
                'funcionario_nome': funcionario_com_ramal.nome_completo,
                'funcionario_id': funcionario_com_ramal.id
            })
        else:
            # Log para debug
            print(f"Ramal {ramal} está disponível")
            
            return JsonResponse({'existe': False})
            
    except json.JSONDecodeError as e:
        print(f"Erro de decodificação JSON: {e}")
        return JsonResponse({'error': 'Dados JSON inválidos.'}, status=400)
    except Exception as e:
        print(f"Erro ao verificar ramal: {e}")
        return JsonResponse({'error': str(e)}, status=500)

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
        'title': 'Cadastrar Computador',
        'form': form,
    }
    return render(request, 'apps/ti/computador_form.html', context)

@login_required
def atribuicao_computador_pa_create(request):
    if request.method == 'POST':
        form = AtribuicaoComputadorPAForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de computador cadastrada com sucesso!')
            return redirect('ti:admin')
    else:
        form = AtribuicaoComputadorPAForm()
    
    context = {
        'title': 'Cadastrar Atribuição de Computador',
        'form': form,
    }
    return render(request, 'apps/ti/atribuicao_computador_pa_form.html', context)

@require_GET
@login_required
def api_listar_computadores_disponiveis(request):
    """
    Retorna uma lista de computadores com status 'disponivel' 
    ou que não estão em nenhuma atribuição ativa.
    """
    try:
        # Computadores explicitamente marcados como 'disponivel'
        computadores_status_disponivel = Computador.objects.filter(status='disponivel')

        # IDs dos computadores que já estão em uma atribuição ATIVA
        ids_computadores_atribuidos = AtribuicaoComputadorPA.objects.filter(ativo=True).values_list('computador_id', flat=True).distinct()

        # Computadores que não estão na lista de IDs atribuídos ativamente
        computadores_nao_em_atribuicao_ativa = Computador.objects.exclude(id__in=ids_computadores_atribuidos)
        
        # Combinar os dois querysets e remover duplicatas
        # Usar um set de IDs para garantir unicidade e depois buscar os objetos
        ids_disponiveis = set(computadores_status_disponivel.values_list('id', flat=True)) \
                          .union(set(computadores_nao_em_atribuicao_ativa.values_list('id', flat=True)))
        
        computadores_disponiveis = Computador.objects.filter(id__in=list(ids_disponiveis)).order_by('marca')

        lista_para_json = [
            {
                "id": comp.id,
                "marca": comp.marca,
            }
            for comp in computadores_disponiveis
        ]
        return JsonResponse({"computadores": lista_para_json})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_POST
@login_required
def api_adicionar_computador_pa(request, pa_id):
    try:
        data = json.loads(request.body)
        computador_id = data.get('computador_id')

        if not computador_id:
            return gerar_resposta_api(False, error='ID do Computador não fornecido.', status=400)

        pa_alvo = get_object_or_404(PosicaoAtendimento, pk=pa_id)
        computador = get_object_or_404(Computador, pk=computador_id)

        # Verificar disponibilidade do computador
        disponivel, mensagem = verificar_disponibilidade_computador(computador_id, pa_id=pa_id)
        if not disponivel:
            return gerar_resposta_api(False, error=mensagem, status=400)
        
        # Usar a função auxiliar para atribuir o computador à PA
        atribuir_item_pa(computador, pa_alvo, AtribuicaoComputadorPA)
        
        # Listar computadores atribuídos à PA para a resposta
        lista_computadores_pa = listar_itens_atribuidos_pa(pa_alvo, 'computador')

        return gerar_resposta_api(
            True, 
            message='Computador adicionado à PA com sucesso!',
            data={'lista_computadores_pa': lista_computadores_pa}
        )

    except PosicaoAtendimento.DoesNotExist:
        return gerar_resposta_api(False, error='PA não encontrada.', status=404)
    except Computador.DoesNotExist:
        return gerar_resposta_api(False, error='Computador não encontrado.', status=404)
    except json.JSONDecodeError:
        return gerar_resposta_api(False, error='Dados JSON inválidos.', status=400)
    except Exception as e:
        return gerar_resposta_api(False, error=str(e), status=500)

@require_POST
@login_required
def api_remover_computador_pa(request, pa_id):
    try:
        data = json.loads(request.body)
        computador_id = data.get('computador_id')

        if not computador_id:
            return gerar_resposta_api(False, error='ID do Computador não fornecido.', status=400)

        pa_alvo = get_object_or_404(PosicaoAtendimento, pk=pa_id)
        computador = get_object_or_404(Computador, pk=computador_id)

        atribuicao_ativa = AtribuicaoComputadorPA.objects.filter(
            posicao_atendimento=pa_alvo, 
            computador=computador, 
            ativo=True
        ).first()

        if not atribuicao_ativa:
            return gerar_resposta_api(False, error='Computador não está ativamente atribuído a esta PA.', status=400)

        # Usar a função auxiliar para desatribuir o computador
        desatribuir_item_pa(atribuicao_ativa)
        
        # Listar computadores atribuídos à PA para a resposta
        lista_computadores_pa = listar_itens_atribuidos_pa(pa_alvo, 'computador')

        return gerar_resposta_api(
            True,
            message='Computador removido da PA com sucesso!',
            data={'lista_computadores_pa': lista_computadores_pa}
        )

    except PosicaoAtendimento.DoesNotExist:
        return gerar_resposta_api(False, error='PA não encontrada.', status=404)
    except Computador.DoesNotExist:
        return gerar_resposta_api(False, error='Computador não encontrado.', status=404)
    except json.JSONDecodeError:
        return gerar_resposta_api(False, error='Dados JSON inválidos.', status=400)
    except Exception as e:
        return gerar_resposta_api(False, error=str(e), status=500)

@require_POST
@login_required
def api_atualizar_status_periferico(request, periferico_id):
    try:
        data = json.loads(request.body)
        novo_status = data.get('status')
        pa_id = data.get('pa_id') # PA da qual o periférico está sendo gerenciado no frontend
        observacoes = data.get('observacoes') # Adicionado

        if not novo_status or novo_status not in [s[0] for s in Periferico.status_choices]:
            return JsonResponse({'success': False, 'error': 'Status inválido fornecido.'}, status=400)

        periferico = get_object_or_404(Periferico, pk=periferico_id)
        
        # Salvar o status antigo para referência, se necessário
        # status_antigo = periferico.status

        periferico.status = novo_status
        if novo_status == 'manutencao' and observacoes:
            periferico.observacoes = observacoes
        elif novo_status == 'disponivel': # Limpar observações ao voltar de manutenção para disponível
            if periferico.observacoes and periferico.observacoes.startswith("MANUTENÇÃO:"):
                 periferico.observacoes = None # Ou um valor padrão, se preferir
            elif not periferico.observacoes: # Se já estava None, mantém None
                pass
        periferico.save()
        
        mensagem = f'Status do periférico {periferico.tipo.nome} {periferico.marca} atualizado para {periferico.get_status_display()}.';
        periferico_removido_da_pa_especifica = False

        # Lógica adicional baseada no novo status e na PA de origem
        if novo_status == 'disponivel' and pa_id:
            # Se o periférico foi marcado como 'disponível' e estava associado a uma PA específica (via frontend context),
            # devemos desassociá-lo dessa PA.
            atribuicao_especifica = AtribuicaoPerifericoPA.objects.filter(
                periferico=periferico,
                posicao_atendimento_id=pa_id,
                ativo=True
            ).first()
            
            if atribuicao_especifica:
                atribuicao_especifica.ativo = False
                atribuicao_especifica.data_remocao = timezone.now()
                atribuicao_especifica.save()
                periferico_removido_da_pa_especifica = True
                mensagem += f' Ele foi desatribuído da PA {atribuicao_especifica.posicao_atendimento.numero}.'
        
        elif novo_status == 'manutencao' and pa_id:
            # Se o periférico foi marcado como 'Em Manutenção' e estava associado a uma PA específica,
            # também devemos desassociá-lo dessa PA.
            atribuicao_especifica = AtribuicaoPerifericoPA.objects.filter(
                periferico=periferico,
                posicao_atendimento_id=pa_id,
                ativo=True
            ).first()
            
            if atribuicao_especifica:
                atribuicao_especifica.ativo = False
                atribuicao_especifica.data_remocao = timezone.now()
                atribuicao_especifica.save()
                periferico_removido_da_pa_especifica = True
                mensagem += f' Ele foi desatribuído da PA {atribuicao_especifica.posicao_atendimento.numero} para manutenção.'
        
        elif novo_status == 'em_uso' and pa_id:
            # Se marcado como 'Em Uso' e uma pa_id foi fornecida, garantir que ele esteja ativo nessa PA.
            # Se não houver atribuição ativa para esta PA, pode ser necessário criar ou reativar uma.
            # Esta lógica pode ser complexa se um periférico puder estar em várias PAs (o que não é o caso atualmente para "em_uso")
            # Por ora, vamos assumir que se está em uso, já está corretamente atribuído pela interface principal.
            # Apenas garantimos que não haja atribuições ativas conflitantes se este periférico só pode estar em uma PA por vez.
            pass # A atribuição é gerenciada separadamente; aqui apenas atualizamos o status do objeto Periférico.

        return JsonResponse({
            'success': True, 
            'message': mensagem,
            'novo_status_display': periferico.get_status_display(),
            'periferico_removido_da_pa': periferico_removido_da_pa_especifica
        })

    except Periferico.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Periférico não encontrado.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos.'}, status=400)
    except Exception as e:
        # Logar o erro em um ambiente de produção
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.error(f"Erro em api_atualizar_status_periferico: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
@login_required
def api_atualizar_status_computador(request, computador_id):
    try:
        data = json.loads(request.body)
        novo_status = data.get('status')
        pa_id = data.get('pa_id') # PA da qual o computador está sendo gerenciado no frontend
        observacoes = data.get('observacoes') # Adicionado

        if not novo_status or novo_status not in [s[0] for s in Computador.status_choices]:
            return JsonResponse({'success': False, 'error': 'Status inválido fornecido.'}, status=400)

        computador = get_object_or_404(Computador, pk=computador_id)

        computador.status = novo_status
        if novo_status == 'manutencao' and observacoes:
            computador.observacoes = observacoes
        elif novo_status == 'disponivel': # Limpar observações ao voltar de manutenção para disponível
            if computador.observacoes and computador.observacoes.startswith("MANUTENÇÃO:"):
                computador.observacoes = None
            elif not computador.observacoes:
                pass

        computador.save()
        
        partes_mensagem = [
            f'Status do computador {computador.marca} atualizado para {computador.get_status_display()}.'
        ]
        computador_removido_da_pa_especifica = False
        lista_computadores_pa_atualizada = []

        if (novo_status == 'disponivel' or novo_status == 'manutencao') and pa_id:
            atribuicao_especifica = AtribuicaoComputadorPA.objects.filter(
                computador=computador,
                posicao_atendimento_id=pa_id,
                ativo=True
            ).first()
            
            if atribuicao_especifica:
                atribuicao_especifica.ativo = False
                atribuicao_especifica.data_remocao = timezone.now()
                atribuicao_especifica.save()
                computador_removido_da_pa_especifica = True
                acao = "para manutenção" if novo_status == 'manutencao' else "pois está livre"
                partes_mensagem.append(f'Ele foi desatribuído da PA {atribuicao_especifica.posicao_atendimento.numero} {acao}.')
                
                pa_alvo = get_object_or_404(PosicaoAtendimento, pk=pa_id)
                atribuicoes_pa_atual = AtribuicaoComputadorPA.objects.filter(
                    posicao_atendimento=pa_alvo, 
                    ativo=True
                ).select_related('computador')
                for atr in atribuicoes_pa_atual:
                    lista_computadores_pa_atualizada.append({
                        'id': atr.computador.id,
                        'marca': atr.computador.marca,
                    })
        
        mensagem_final = " ".join(partes_mensagem)

        return JsonResponse({
            'success': True, 
            'message': mensagem_final,
            'novo_status_display': computador.get_status_display(),
            'computador_removido_da_pa': computador_removido_da_pa_especifica,
            'lista_computadores_pa': lista_computadores_pa_atualizada
        })

    except Computador.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Computador não encontrado.'}, status=404)
    except PosicaoAtendimento.DoesNotExist: # Caso pa_id seja inválido ao buscar lista atualizada
        return JsonResponse({'success': False, 'error': 'PA não encontrada ao tentar atualizar lista de computadores.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos.'}, status=400)
    except Exception as e:
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.error(f"Erro em api_atualizar_status_computador: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_GET
@login_required
def api_listar_perifericos_disponiveis_por_tipo(request, tipo_id):
    """
    Retorna uma lista de periféricos disponíveis de um determinado tipo.
    """
    try:
        # Verificar se o tipo existe
        tipo = get_object_or_404(TipoPeriferico, pk=tipo_id)
        
        # Buscar periféricos disponíveis deste tipo
        perifericos = Periferico.objects.filter(
            tipo=tipo, 
            status='disponivel'
        ).order_by('marca', 'modelo')
        
        # Formatar para JSON
        perifericos_list = [
            {
                'id': p.id,
                'marca': p.marca,
                'modelo': p.modelo,
                'tipo_nome': tipo.nome
            } for p in perifericos
        ]
        
        return JsonResponse({
            'success': True,
            'tipo': {
                'id': tipo.id,
                'nome': tipo.nome
            },
            'perifericos': perifericos_list
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Função para Auto Atribuição de PA pelo próprio funcionário
@login_required
def auto_atribuicao_pa(request):
    """
    View para permitir que o funcionário selecione a própria PA.
    Detecta o usuário logado e atribui a PA a ele automaticamente.
    """
    # Verificar se o usuário está associado a um funcionário
    try:
        funcionario = Funcionario.objects.get(usuario=request.user)
    except Funcionario.DoesNotExist:
        funcionario = None
        messages.error(request, 'Seu usuário não está vinculado a nenhum funcionário no sistema.')
    
    context = {
        'funcionario': funcionario
    }
    
    # Se o funcionário existe, buscar a PA atual e PAs disponíveis
    if funcionario:
        # Verificar se o funcionário está atribuído a uma PA ativa através da tabela de atribuições
        atribuicao_atual = AtribuicaoFuncionarioPA.objects.filter(
            funcionario=funcionario,
            ativo=True
        ).select_related('posicao_atendimento', 'posicao_atendimento__sala', 'posicao_atendimento__ilha').first()
        
        pa_atual = None
        if atribuicao_atual:
            pa_atual = atribuicao_atual.posicao_atendimento
        else:
            # Verificar também diretamente na tabela de PAs como fallback
            pa_atual = PosicaoAtendimento.objects.filter(funcionario=funcionario).first()
            
        context['pa_atual'] = pa_atual
        
        # Buscar PAs livres ou ocupadas (para permitir troca)
        pas_disponiveis = PosicaoAtendimento.objects.filter(
            Q(status='livre') | Q(status='ocupada')
        ).select_related('sala', 'ilha', 'funcionario')
        
        # Se o funcionário já tem uma PA, exclua ela da lista
        if pa_atual:
            pas_disponiveis = pas_disponiveis.exclude(id=pa_atual.id)
        
        context['pas_disponiveis'] = pas_disponiveis
    
    # Processo de atribuição (via POST)
    if request.method == 'POST' and funcionario:
        pa_id = request.POST.get('posicao_atendimento')
        
        if not pa_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Selecione uma PA válida.'
                })
            messages.error(request, 'Selecione uma PA válida.')
            return redirect('ti:auto_atribuicao_pa')
        
        try:
            pa = PosicaoAtendimento.objects.get(id=pa_id)
            
            # Verificar se a PA está em estado válido para atribuição (livre, ocupada ou manutenção)
            if pa.status not in ['livre', 'ocupada', 'manutencao']:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'PA {pa.numero} não está disponível. Status atual: {pa.get_status_display()}.'
                    })
                messages.error(request, f'PA {pa.numero} não está disponível. Status atual: {pa.get_status_display()}.')
                return redirect('ti:auto_atribuicao_pa')
            
            # Se o funcionário já tem uma PA, desatribuir
            if pa_atual:
                pa_atual.funcionario = None
                pa_atual.status = 'livre'
                pa_atual.save()
                
                # Finalizar a atribuição anterior no histórico
                atribuicoes_antigas = AtribuicaoFuncionarioPA.objects.filter(
                    funcionario=funcionario,
                    posicao_atendimento=pa_atual,
                    ativo=True
                )
                for atribuicao in atribuicoes_antigas:
                    atribuicao.ativo = False
                    atribuicao.data_fim = timezone.now().date()
                    atribuicao.save()
                    
            # Se a PA selecionada já está ocupada por outro funcionário, desatribuir
            if pa.status == 'ocupada' and pa.funcionario and pa.funcionario != funcionario:
                funcionario_anterior = pa.funcionario
                
                # Finalizar a atribuição do funcionário anterior no histórico
                atribuicoes_antigas = AtribuicaoFuncionarioPA.objects.filter(
                    funcionario=funcionario_anterior,
                    posicao_atendimento=pa,
                    ativo=True
                )
                for atribuicao in atribuicoes_antigas:
                    atribuicao.ativo = False
                    atribuicao.data_fim = timezone.now().date()
                    atribuicao.save()
                    
                # Registrar esta troca para fins de auditoria
                from django.contrib.admin.models import LogEntry, CHANGE
                from django.contrib.contenttypes.models import ContentType
                
                try:
                    # Tentando criar um log de auditoria
                    LogEntry.objects.create(
                        user_id=request.user.id,
                        content_type_id=ContentType.objects.get_for_model(PosicaoAtendimento).id,
                        object_id=pa.id,
                        object_repr=str(pa),
                        action_flag=CHANGE,
                        change_message=f'PA ocupada por {funcionario_anterior} foi transferida para {funcionario}'
                    )
                except Exception:
                    # Silenciosamente ignorar erros no log (não é crítico)
                    pass
            
            # Atribuir funcionário à nova PA
            pa.funcionario = funcionario
            pa.status = 'ocupada'
            pa.save()
            
            # Registrar no histórico
            AtribuicaoFuncionarioPA.objects.create(
                funcionario=funcionario,
                posicao_atendimento=pa,
                data_inicio=timezone.now().date(),
                ativo=True
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Você foi atribuído com sucesso à PA {pa.numero} - {pa.ilha.nome} ({pa.sala.nome})'
                })
            
            messages.success(request, f'Você foi atribuído com sucesso à PA {pa.numero} - {pa.ilha.nome} ({pa.sala.nome})')
            return redirect('ti:auto_atribuicao_pa')
            
        except PosicaoAtendimento.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'PA não encontrada.'
                })
            messages.error(request, 'PA não encontrada.')
            return redirect('ti:auto_atribuicao_pa')
    
    return render(request, 'apps/ti/auto_atribuicao_pa.html', context)

