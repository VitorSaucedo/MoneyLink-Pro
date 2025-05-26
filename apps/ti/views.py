from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch, Subquery, OuterRef, Sum
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
    AtribuicaoComputadorPA,
    Loja
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
from apps.funcionarios.models import Funcionario, Empresa
import json
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest

# Create your views here.

# View principal para Admin
@login_required
def admin(request):
    # Inicializar os formulários
    form_periferico = PerifericoForm()
    form_atribuicao_pa = AtribuicaoPerifericoPAForm()
    
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
        'lojas_list': Loja.objects.filter(status=True).order_by('nome'),
        'empresas_list': Empresa.objects.filter(status=True),
        # Adicionar os formulários no contexto
        'form_periferico': form_periferico,
        'form_atribuicao_pa': form_atribuicao_pa,
    }
    
    if request.method == 'POST':
        # Verificar qual formulário foi enviado
        if 'submit_periferico' in request.POST:
            # Processamento do formulário de cadastro de periférico
            form_periferico = PerifericoForm(request.POST)
            if form_periferico.is_valid():
                form_periferico.save()
                messages.success(request, 'Periférico cadastrado com sucesso!')
                return redirect('ti:admin')
            else:
                # Se o formulário não for válido, repassar o formulário com erros
                context['form_periferico'] = form_periferico
        
        elif 'submit_atribuicao_pa' in request.POST:
            # Processamento do formulário de atribuição de periférico a PA
            form_atribuicao_pa = AtribuicaoPerifericoPAForm(request.POST)
            if form_atribuicao_pa.is_valid():
                form_atribuicao_pa.save()
                messages.success(request, 'Atribuição de periférico cadastrada com sucesso!')
                return redirect('ti:admin')
            else:
                # Se o formulário não for válido, repassar o formulário com erros
                context['form_atribuicao_pa'] = form_atribuicao_pa
                
        elif 'periferico' in request.POST and 'posicao_atendimento' in request.POST and 'data_atribuicao' in request.POST:
            # Processamento do formulário de atribuição de periférico (formato antigo)
            form = AtribuicaoPerifericoPAForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Atribuição de periférico cadastrada com sucesso!')
                return redirect('ti:admin')
    
    return render(request, 'apps/ti/admin.html', context)
# Views para Loja removidas - funcionalidade já existe em outro módulo

@login_required
def loja_list(request):
    lojas = Loja.objects.all()
    context = {
        'title': 'Lojas',
        'lojas': lojas,
    }
    return render(request, 'apps/ti/loja_list.html', context)

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

@login_required
def controle_estoque(request):
    """
    View para exibir o controle de estoque de periféricos por sala e ilha.
    Mostra uma tabela com a contagem de periféricos de cada tipo em cada sala/ilha.
    Permite filtrar por loja selecionada.
    """
    
    # Obter a loja selecionada, se houver
    loja_id = request.GET.get('loja')
    loja_selecionada = None
    loja_atual = None
    
    # Obter todas as lojas ativas para o seletor
    lojas = Loja.objects.filter(status=True).order_by('nome')
    
    # Filtrar por loja, se for selecionada
    if loja_id:
        try:
            loja_selecionada = int(loja_id)
            loja_atual = get_object_or_404(Loja, id=loja_selecionada)
        except (ValueError, TypeError):
            loja_selecionada = None
    
    # Obter todas as salas com ilhas pré-carregadas
    salas = Sala.objects.all().prefetch_related(
        Prefetch('ilhas', queryset=Ilha.objects.all().order_by('nome'))
    )
    
    # Obter todos os tipos de periféricos
    tipos_perifericos = TipoPeriferico.objects.all().order_by('nome')
    
    # Calcular o total de periféricos por tipo (independentemente de atribuição)
    perifericos_totais_por_tipo = {}
    filtro_loja = {'loja_id': loja_selecionada} if loja_selecionada else {}
    
    for tipo in tipos_perifericos:
        # Contar todos os periféricos deste tipo, independente de estarem atribuídos a PAs
        # Usando Sum('quantidade') em vez de count() para obter o número real de unidades
        total_tipo = Periferico.objects.filter(
            tipo=tipo, 
            status='disponivel',  # Apenas periféricos disponíveis
            **filtro_loja
        ).exclude(
            id__in=AtribuicaoPerifericoPA.objects.filter(ativo=True).values_list('periferico_id', flat=True)
        ).aggregate(total=Sum('quantidade'))['total'] or 0
        
        perifericos_totais_por_tipo[tipo.id] = total_tipo
    
    # Inicializar dicionário para contagem de periféricos por sala/ilha/tipo
    perifericos_por_sala_ilha = {}
    total_geral_perifericos = 0
    
    # Usar Sum com annotate para calcular de forma mais eficiente a quantidade de periféricos em uso
    # Agrupar por sala, ilha e tipo de periférico
    perifericos_em_uso = AtribuicaoPerifericoPA.objects.filter(
        ativo=True
    ).select_related(
        'posicao_atendimento', 'posicao_atendimento__sala', 'posicao_atendimento__ilha', 'periferico', 'periferico__tipo'
    )
    
    if loja_selecionada:
        perifericos_em_uso = perifericos_em_uso.filter(periferico__loja_id=loja_selecionada)
    
    # Calcular o total geral de periféricos em uso para a coluna Total
    total_geral_perifericos = perifericos_em_uso.aggregate(
        total=Sum('periferico__quantidade')
    )['total'] or 0
    
    # Inicializar estrutura para todas as salas e ilhas
    for sala in salas:
        perifericos_por_sala_ilha[sala.id] = {}
        for ilha in sala.ilhas.all():
            perifericos_por_sala_ilha[sala.id][ilha.id] = {}
            # Inicializar contador para cada tipo de periférico nesta ilha
            for tipo in tipos_perifericos:
                perifericos_por_sala_ilha[sala.id][ilha.id][tipo.id] = 0
    
    # Processar cada periférico em uso
    for atribuicao in perifericos_em_uso:
        pa = atribuicao.posicao_atendimento
        if not pa.sala_id or not pa.ilha_id:
            continue  # Pular se não tiver sala ou ilha atribuída
            
        periferico = atribuicao.periferico
        tipo_id = periferico.tipo_id
        quantidade = periferico.quantidade if hasattr(periferico, 'quantidade') else 1
        
        # Se a estrutura existir, incrementar a contagem
        if (pa.sala_id in perifericos_por_sala_ilha and 
            pa.ilha_id in perifericos_por_sala_ilha[pa.sala_id] and
            tipo_id in perifericos_por_sala_ilha[pa.sala_id][pa.ilha_id]):
            
            perifericos_por_sala_ilha[pa.sala_id][pa.ilha_id][tipo_id] += quantidade
    
    # Calcular o total de periféricos em uso por tipo
    total_por_tipo_periferico = {}
    for tipo in tipos_perifericos:
        # Inicializar contagem para cada tipo
        total_por_tipo_periferico[tipo.id] = 0
        
        # Somar para cada sala e ilha
        for sala_id in perifericos_por_sala_ilha:
            for ilha_id in perifericos_por_sala_ilha[sala_id]:
                if tipo.id in perifericos_por_sala_ilha[sala_id][ilha_id]:
                    total_por_tipo_periferico[tipo.id] += perifericos_por_sala_ilha[sala_id][ilha_id][tipo.id]
    
    # Obter contagem de computadores cadastrados de forma otimizada
    computadores_cadastrados_total = Computador.objects.all().count()

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
    ids_computadores_em_uso = AtribuicaoComputadorPA.objects.filter(
        ativo=True
    ).values_list('computador_id', flat=True)\
        .distinct()
    
    # Computadores disponíveis - Cálculo será feito abaixo após a contagem por marca
    # Aplicar filtro de loja se necessário
    computadores_query = Computador.objects.filter(status='disponivel')
    if loja_selecionada:
        computadores_query = computadores_query.filter(loja_id=loja_selecionada)
    
    # Total de computadores cadastrados na loja selecionada
    if loja_selecionada:
        computadores_cadastrados_total = Computador.objects.filter(loja_id=loja_selecionada).count()
    else:
        computadores_cadastrados_total = Computador.objects.all().count()

    # Calcular computadores disponíveis POR MARCA (incluindo marcas com 0 disponíveis)
    # ids_computadores_em_uso já foi definido acima
    
    # 1. Obter todas as marcas distintas cadastradas de computadores (para garantir que todas apareçam na lista)
    todas_as_marcas_cadastradas = Computador.objects.all()
    
    # Aplicar filtro de loja se necessário
    if loja_selecionada:
        todas_as_marcas_cadastradas = todas_as_marcas_cadastradas.filter(loja_id=loja_selecionada)
    
    todas_as_marcas_cadastradas = todas_as_marcas_cadastradas.values_list('marca', flat=True).distinct().order_by('marca')
    
    # 2. Obter a contagem de computadores REALMENTE disponíveis por marca
    #    (status='disponivel' E não estão em uso)
    contagem_disponiveis_raw = Computador.objects.filter(
        status='disponivel'
    ).exclude(
        id__in=ids_computadores_em_uso
    )
    
    # Aplicar filtro de loja para computadores disponíveis
    if loja_selecionada:
        contagem_disponiveis_raw = contagem_disponiveis_raw.filter(loja_id=loja_selecionada)
    
    contagem_disponiveis_raw = contagem_disponiveis_raw.values('marca').annotate(
        quantidade_disponivel=Sum('quantidade') # Somar o campo quantidade para obter o total real
    ).order_by('marca')
    
    # 3. Criar um dicionário com as contagens de disponíveis para consulta rápida
    disponiveis_dict = {item['marca']: item['quantidade_disponivel'] for item in contagem_disponiveis_raw}
    
    # 4. Montar a lista final, garantindo todas as marcas com suas respectivas quantidades (ou 0)
    computadores_disponiveis_por_marca_list = []
    total_soma_marcas = 0  # Inicializar contador para soma total
    
    for marca_nome in todas_as_marcas_cadastradas:
        quantidade_marca = disponiveis_dict.get(marca_nome, 0)
        total_soma_marcas += quantidade_marca  # Adicionar ao total
        computadores_disponiveis_por_marca_list.append({
            'marca': marca_nome,
            'quantidade_disponivel': quantidade_marca # Usa 0 se a marca não estiver no dict de disponíveis
        })
    
    # Usar a soma calculada acima para garantir consistência
    computadores_disponiveis_total = total_soma_marcas

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

    # Dados adicionais de computadores que estavam faltando
    computadores_manutencao = Computador.objects.filter(status='manutencao').count()
    
    # Computadores em uso que não estão atribuídos a uma PA
    computadores_em_uso = Computador.objects.filter(status='em_uso').count()
    computadores_em_uso_sem_pa = computadores_em_uso - computadores_em_uso_total_geral
    if computadores_em_uso_sem_pa < 0:
        computadores_em_uso_sem_pa = 0
        
    # Contexto para o template
    context = {
        'salas': salas,
        'tipos_perifericos': tipos_perifericos,
        'perifericos_por_sala_ilha': perifericos_por_sala_ilha,
        'total_geral_perifericos': total_geral_perifericos,
        'perifericos_totais_por_tipo': perifericos_totais_por_tipo,
        'total_por_tipo_periferico': total_por_tipo_periferico,
        'historico_page_obj': page_obj, # Passa o objeto da página para o template
        'pagination_data': pagination_data, # Adiciona metadados de paginação
        'data_ultima_atualizacao_real': data_ultima_atualizacao_real, # Adiciona a data ao contexto
        'computadores_cadastrados_total': computadores_cadastrados_total,
        'computadores_em_uso_por_sala_ilha': computadores_em_uso_por_sala_ilha,
        'computadores_em_uso_total_geral': computadores_em_uso_total_geral,
        'computadores_disponiveis_total': computadores_disponiveis_total,
        'computadores_disponiveis_por_marca_list': computadores_disponiveis_por_marca_list,
        'computadores_manutencao': computadores_manutencao,
        'computadores_em_uso_sem_pa': computadores_em_uso_sem_pa,
        'lojas': lojas,
        'loja_selecionada': loja_selecionada,
        'loja_atual': loja_atual,
    }
    
    return render(request, 'apps/ti/controle_estoque.html', context)

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


# Views para Controle de Manutenção
@login_required
def controle_manutencao(request):
    # Obter periféricos em manutenção
    perifericos_em_manutencao = Periferico.objects.filter(status='manutencao')
    
    # Obter computadores em manutenção
    computadores_em_manutencao = Computador.objects.filter(status='manutencao')
    
    context = {
        'title': 'Controle de Manutenção - TI',
        'perifericos_em_manutencao': perifericos_em_manutencao,
        'computadores_em_manutencao': computadores_em_manutencao,
    }
    
    return render(request, 'apps/ti/controle_manutencao.html', context)

@login_required
def marcar_consertado(request, item_id, tipo_item_slug):
    # Verificar qual tipo de item (periférico ou computador)
    if tipo_item_slug == 'periferico':
        item = get_object_or_404(Periferico, id=item_id)
        item.status = 'disponivel'
        item.save()
        messages.success(request, f'Periférico {item.marca} {item.modelo} marcado como consertado.')
        
    elif tipo_item_slug == 'computador':
        item = get_object_or_404(Computador, id=item_id)
        item.status = 'disponivel'
        item.save()
        messages.success(request, f'Computador {item.marca} marcado como consertado.')
    
    else:
        messages.error(request, 'Tipo de item inválido.')
    
    return redirect('ti:controle_manutencao')


# Views para API
@login_required
def api_ilhas_por_sala(request, sala_id):
    ilhas = list(Ilha.objects.filter(sala_id=sala_id).values('id', 'nome', 'quantidade_pas'))
    return JsonResponse({'ilhas': ilhas})

@login_required
def api_ilha_info(request, ilha_id):
    try:
        # Obter a ilha
        ilha = get_object_or_404(Ilha, id=ilha_id)
        
        # Contar quantas PAs já existem para esta ilha
        pas_existentes = PosicaoAtendimento.objects.filter(ilha=ilha).count()
        
        # Calcular quantas PAs ainda podem ser criadas
        pas_disponiveis = max(0, ilha.quantidade_pas - pas_existentes)
        
        return JsonResponse({
            'success': True,
            'ilha': {
                'id': ilha.id,
                'nome': ilha.nome,
                'quantidade_pas': ilha.quantidade_pas,
                'pas_existentes': pas_existentes,
                'pas_disponiveis': pas_disponiveis
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def atualizar_status_pa(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pa_id = data.get('pa_id')
            novo_status = data.get('status')
            
            pa = PosicaoAtendimento.objects.get(id=pa_id)
            pa.status = novo_status
            pa.save()
            
            return JsonResponse({'success': True, 'message': f'Status da PA atualizado para {novo_status}'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)

@login_required
def remover_periferico_pa(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            periferico_id = data.get('periferico_id')
            pa_id = data.get('pa_id')
            
            # Encontrar a atribuição ativa
            atribuicao = AtribuicaoPerifericoPA.objects.get(
                periferico_id=periferico_id,
                posicao_atendimento_id=pa_id,
                ativo=True
            )
            
            # Desativar a atribuição
            atribuicao.ativo = False
            atribuicao.data_remocao = timezone.now()
            atribuicao.save()
            
            # Atualizar status do periférico
            periferico = Periferico.objects.get(id=periferico_id)
            periferico.status = 'disponivel'
            periferico.save()
            
            return JsonResponse({'success': True, 'message': 'Periférico removido com sucesso'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)

@login_required
def api_controle_salas(request):
    # Implementação básica - retorna dados necessários para a página de controle de salas
    salas = list(Sala.objects.values('id', 'nome'))
    ilhas = list(Ilha.objects.values('id', 'nome', 'sala_id'))
    posicoes = list(PosicaoAtendimento.objects.values('id', 'numero', 'ilha_id', 'status'))
    
    return JsonResponse({
        'salas': salas,
        'ilhas': ilhas,
        'posicoes': posicoes
    })


# Views para Salas
@login_required
def sala_list(request):
    salas = Sala.objects.all()
    context = {
        'salas': salas
    }
    return render(request, 'apps/ti/sala_list.html', context)

@login_required
def sala_create(request):
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sala cadastrada com sucesso!')
            return redirect('ti:admin')
    else:
        form = SalaForm()
    
    context = {
        'form': form
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
        'form': form,
        'sala': sala
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
        'sala': sala
    }
    return render(request, 'apps/ti/sala_confirm_delete.html', context)


# Views para Ilhas
@login_required
def ilha_list(request):
    ilhas = Ilha.objects.all().select_related('sala')
    context = {
        'ilhas': ilhas
    }
    return render(request, 'apps/ti/ilha_list.html', context)

@login_required
def ilha_create(request):
    if request.method == 'POST':
        form = IlhaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ilha cadastrada com sucesso!')
            return redirect('ti:admin')
    else:
        form = IlhaForm()
    
    context = {
        'form': form
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
        'form': form,
        'ilha': ilha
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
        'ilha': ilha
    }
    return render(request, 'apps/ti/ilha_confirm_delete.html', context)


# Views para Posições de Atendimento
@login_required
def posicao_atendimento_list(request):
    posicoes = PosicaoAtendimento.objects.all().select_related('sala', 'ilha')
    context = {
        'posicoes': posicoes
    }
    return render(request, 'apps/ti/posicao_atendimento_list.html', context)

@login_required
def posicao_atendimento_create(request):
    if request.method == 'POST':
        # Obter número de PAs a serem criadas
        quantidade_pas = int(request.POST.get('quantidade_pas', 1))
        
        # Limitar a quantidade para evitar sobrecarga
        quantidade_pas = min(quantidade_pas, 20)  # Máximo de 20 PAs por vez
        
        # Verificar se ilha foi selecionada
        ilha_id = request.POST.get('ilha')
        if ilha_id:
            try:
                ilha = Ilha.objects.get(id=ilha_id)
                
                # Contar PAs existentes para esta ilha
                pas_existentes = PosicaoAtendimento.objects.filter(ilha=ilha).count()
                
                # Verificar quantas PAs ainda podem ser criadas
                pas_disponiveis = max(0, ilha.quantidade_pas - pas_existentes)
                
                # Limitar a quantidade ao disponível
                quantidade_pas = min(quantidade_pas, pas_disponiveis)
                
                # Se não for possível criar nenhuma PA, mostrar erro
                if quantidade_pas <= 0:
                    messages.error(request, f'Não há mais espaço para criar PAs na ilha {ilha.nome}. Capacidade máxima atingida.')
                    return redirect('ti:admin')
                
                # Preparar dados base para todas as PAs
                pa_data = request.POST.copy()
                
                # Processar cada PA
                pas_criadas = 0
                for _ in range(quantidade_pas):
                    # Se o usuário forneceu um número específico e a quantidade > 1, não usar esse número
                    if quantidade_pas > 1 and pa_data.get('numero'):
                        pa_data['numero'] = ''  # Permitir geração automática de números sequenciais
                    
                    form = PosicaoAtendimentoForm(pa_data)
                    if form.is_valid():
                        form.save()
                        pas_criadas += 1
                
                if pas_criadas > 0:
                    if pas_criadas == 1:
                        messages.success(request, 'Posição de atendimento cadastrada com sucesso!')
                    else:
                        messages.success(request, f'{pas_criadas} posições de atendimento cadastradas com sucesso!')
                    return redirect('ti:admin')
                else:
                    messages.error(request, 'Não foi possível criar as posições de atendimento.')
            except Exception as e:
                messages.error(request, f'Erro ao criar posições de atendimento: {str(e)}')
        else:
            # Processar normalmente se não houver ilha selecionada
            form = PosicaoAtendimentoForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Posição de atendimento cadastrada com sucesso!')
                return redirect('ti:admin')
    else:
        form = PosicaoAtendimentoForm()
    
    context = {
        'form': form
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
        'form': form,
        'posicao': posicao
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
        'posicao': posicao
    }
    return render(request, 'apps/ti/posicao_atendimento_confirm_delete.html', context)


# Views para Atribuição de Funcionários a PAs
@login_required
def atribuicao_funcionario_pa_list(request):
    atribuicoes = AtribuicaoFuncionarioPA.objects.all().select_related('funcionario', 'posicao_atendimento', 'posicao_atendimento__sala', 'posicao_atendimento__ilha')
    context = {
        'atribuicoes': atribuicoes
    }
    return render(request, 'apps/ti/atribuicao_funcionario_pa_list.html', context)

@login_required
def atribuicao_funcionario_pa_create(request):
    if request.method == 'POST':
        form = AtribuicaoFuncionarioPAForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de funcionário cadastrada com sucesso!')
            return redirect('ti:admin')
    else:
        form = AtribuicaoFuncionarioPAForm()
    
    context = {
        'form': form
    }
    return render(request, 'apps/ti/atribuicao_funcionario_pa_form.html', context)

@login_required
def atribuicao_funcionario_pa_update(request, pk):
    atribuicao = get_object_or_404(AtribuicaoFuncionarioPA, pk=pk)
    if request.method == 'POST':
        form = AtribuicaoFuncionarioPAForm(request.POST, instance=atribuicao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atribuição de funcionário atualizada com sucesso!')
            return redirect('ti:atribuicao_funcionario_pa_list')
    else:
        form = AtribuicaoFuncionarioPAForm(instance=atribuicao)
    
    context = {
        'form': form,
        'atribuicao': atribuicao
    }
    return render(request, 'apps/ti/atribuicao_funcionario_pa_form.html', context)


# Views para Periféricos
@login_required
def periferico_list(request):
    perifericos = Periferico.objects.all()
    context = {
        'perifericos': perifericos
    }
    return render(request, 'apps/ti/periferico_list.html', context)

@login_required
def periferico_create(request):
    if request.method == 'POST':
        # Verificar se é um envio em lote
        if 'perifericos_lote' in request.POST:
            try:
                perifericos_lote = json.loads(request.POST.get('perifericos_lote', '[]'))
                if not perifericos_lote:
                    messages.warning(request, 'Nenhum periférico para cadastrar.')
                    return redirect('ti:admin')
                
                # Contadores para feedback
                total_cadastrados = 0
                erros = []
                
                # Processar cada periférico do lote
                for item in perifericos_lote:
                    try:
                        # Criar cada periférico com base nos dados do lote
                        tipo_id = item.get('tipo_id')
                        marca = item.get('marca', '').strip()
                        modelo = item.get('modelo', '').strip()
                        data_aquisicao = item.get('data_aquisicao')
                        loja_id = item.get('loja_id')
                        quantidade = item.get('quantidade', 1)
                        
                        # Validar dados obrigatórios
                        if not (tipo_id and marca and modelo and loja_id):
                            erros.append(f"Dados incompletos para periférico: {marca} {modelo}")
                            continue
                        
                        # Converter data se necessário
                        if data_aquisicao:
                            try:
                                data_aquisicao = timezone.datetime.strptime(data_aquisicao, '%Y-%m-%d').date()
                            except (ValueError, TypeError):
                                data_aquisicao = None
                        
                        # Criar periférico
                        periferico = Periferico(
                            tipo_id=tipo_id,
                            marca=marca,
                            modelo=modelo,
                            data_aquisicao=data_aquisicao,
                            loja_id=loja_id,
                            quantidade=quantidade,
                            status='disponivel'
                        )
                        periferico.save()
                        total_cadastrados += 1
                    except Exception as e:
                        erros.append(f"Erro ao cadastrar {marca} {modelo}: {str(e)}")
                
                # Feedback para o usuário
                if total_cadastrados > 0:
                    if total_cadastrados == 1:
                        messages.success(request, f'1 periférico cadastrado com sucesso!')
                    else:
                        messages.success(request, f'{total_cadastrados} periféricos cadastrados com sucesso!')
                
                if erros:
                    for erro in erros[:5]:  # Limitar a quantidade de erros exibidos
                        messages.error(request, erro)
                    
                    if len(erros) > 5:
                        messages.error(request, f'...e mais {len(erros) - 5} erros.')
                
                return redirect('ti:admin')
            
            except json.JSONDecodeError:
                messages.error(request, 'Formato de dados inválido para cadastro em lote.')
                return redirect('ti:admin')
            
        # Processo normal (formulário individual)
        form = PerifericoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Periférico cadastrado com sucesso!')
            return redirect('ti:admin')
    else:
        form = PerifericoForm()
    
    context = {
        'form': form
    }
    return render(request, 'apps/ti/periferico_form.html', context)


# Importar funções extras do arquivo views_extras.py
from .views_extras import (
    # Funções de tipos de periféricos
    tipo_periferico_list, tipo_periferico_create,
    tipo_periferico_update, tipo_periferico_delete,
    # Funções de periféricos
    periferico_list, periferico_create, 
    periferico_update, periferico_delete,
    # Funções de ramais
    ramal_list, ramal_create, ramal_update, ramal_edit, ramal_delete,
    # Funções de computadores
    computador_create, atribuicao_computador_pa_create,
    # Funções de atribuições de funcionários
    atribuicao_funcionario_pa_delete,
    # Funções de atribuições de periféricos
    atribuicao_periferico, atribuicao_periferico_pa_create,
    atribuicao_periferico_pa_update, atribuicao_periferico_pa_delete,
    # Funções de API
    api_pas_para_atribuicao_periferico, get_funcionarios_json,
    atribuir_funcionario_pa, api_listar_computadores_disponiveis
)

@require_POST
@login_required
def cadastrar_atribuicoes_perifericos_lote(request):
    """
    View para cadastrar várias atribuições de periféricos de uma só vez.
    Recebe um JSON com um array de atribuições.
    """
    try:
        # Obter dados do corpo da requisição (JSON)
        data = json.loads(request.body)
        atribuicoes = data.get('atribuicoes', [])
        
        if not atribuicoes:
            return JsonResponse({'success': False, 'error': 'Nenhuma atribuição fornecida'})
        
        resultados = []
        
        # Processar cada atribuição
        for item in atribuicoes:
            try:
                periferico_id = item.get('periferico')
                pa_id = item.get('posicao_atendimento')
                data_str = item.get('data_atribuicao')
                
                # Validar dados básicos
                if not all([periferico_id, pa_id]):
                    resultados.append({
                        'success': False, 
                        'error': 'Dados incompletos',
                        'periferico': periferico_id,
                        'pa': pa_id
                    })
                    continue
                
                # Verificar se o periférico existe
                try:
                    periferico = Periferico.objects.get(id=periferico_id)
                except Periferico.DoesNotExist:
                    resultados.append({
                        'success': False, 
                        'error': 'Periférico não encontrado',
                        'periferico': periferico_id,
                        'pa': pa_id
                    })
                    continue
                
                # Verificar se a PA existe
                try:
                    pa = PosicaoAtendimento.objects.get(id=pa_id)
                except PosicaoAtendimento.DoesNotExist:
                    resultados.append({
                        'success': False, 
                        'error': 'PA não encontrada',
                        'periferico': periferico_id,
                        'pa': pa_id
                    })
                    continue
                
                # Criar atribuição
                data_atribuicao = timezone.now()
                if data_str:
                    try:
                        data_atribuicao = timezone.datetime.fromisoformat(data_str)
                    except (ValueError, TypeError):
                        # Se a data for inválida, usa a hora atual
                        pass
                
                # Verificar se já existe uma atribuição ativa deste periférico
                atribuicao_existente = AtribuicaoPerifericoPA.objects.filter(
                    periferico=periferico,
                    ativo=True
                ).first()
                
                if atribuicao_existente:
                    # Desativar atribuição existente
                    atribuicao_existente.ativo = False
                    atribuicao_existente.data_remocao = timezone.now()
                    atribuicao_existente.save()
                
                # Criar nova atribuição
                AtribuicaoPerifericoPA.objects.create(
                    periferico=periferico,
                    posicao_atendimento=pa,
                    data_atribuicao=data_atribuicao,
                    ativo=True
                )
                
                # Atualizar status do periférico
                periferico.status = 'em_uso'
                periferico.save()
                
                resultados.append({
                    'success': True,
                    'periferico': periferico_id,
                    'pa': pa_id
                })
                
            except Exception as e:
                resultados.append({
                    'success': False,
                    'error': str(e),
                    'periferico': item.get('periferico'),
                    'pa': item.get('posicao_atendimento')
                })
        
        # Verificar se todas as atribuições foram bem-sucedidas
        falhas = [r for r in resultados if not r['success']]
        
        return JsonResponse({
            'success': len(falhas) == 0,
            'message': f'{len(resultados) - len(falhas)} atribuições realizadas com sucesso, {len(falhas)} falhas',
            'resultados': resultados
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Formato JSON inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
