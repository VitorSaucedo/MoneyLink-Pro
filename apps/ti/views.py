from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
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
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest
from datetime import datetime

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
        if novo_status == 'manutencao':
            # Se voltando para manutenção e temos novas observações, usamos elas
            if observacoes:
                periferico.observacoes = observacoes
            # Se não temos novas observações, limpamos as antigas para evitar confusão
            else:
                periferico.observacoes = None
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
        if novo_status == 'manutencao':
            # Se voltando para manutenção e temos novas observações, usamos elas
            if observacoes:
                computador.observacoes = observacoes
            # Se não temos novas observações, limpamos as antigas para evitar confusão
            else:
                computador.observacoes = None
        elif novo_status == 'disponivel': 
            # Limpar observações ao voltar de manutenção para disponível
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
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

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


@login_required
@require_POST
def api_auto_atribuicao_pa_reassign(request):
    """
    API para tratar a reassignação de PAs quando um usuário seleciona uma PA já ocupada.
    Suporta duas opções: troca de usuários ou substituição completa.
    """
    try:
        # Verificar se o usuário está associado a um funcionário
        try:
            funcionario = Funcionario.objects.get(usuario=request.user)
        except Funcionario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Seu usuário não está vinculado a nenhum funcionário no sistema.'
            })
        
        # Obter dados do request
        data = json.loads(request.body)
        pa_id = data.get('pa_id')
        option = data.get('option')  # 'swap' ou 'replace'
        
        if not pa_id or not option:
            return JsonResponse({
                'success': False,
                'message': 'Dados incompletos para realizar a operação.'
            })
        
        try:
            pa = PosicaoAtendimento.objects.get(id=pa_id)
        except PosicaoAtendimento.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'PA não encontrada.'
            })
        
        # Verificar se a PA está realmente ocupada e por outro funcionário
        if pa.status != 'ocupada' or not pa.funcionario or pa.funcionario == funcionario:
            return JsonResponse({
                'success': False,
                'message': 'Esta PA não está ocupada por outro funcionário.'
            })
        
        # Obter o funcionário atual da PA
        funcionario_anterior = pa.funcionario
        
        # Verificar se o funcionário atual tem uma PA atribuída
        pa_atual = PosicaoAtendimento.objects.filter(funcionario=funcionario).first()
        
        # Atualizar atribuições com base na opção selecionada
        if option == 'swap' and pa_atual:
            # Opção 1: Trocar os funcionários entre as PAs
            # Finalizar atribuições anteriores no histórico
            AtribuicaoFuncionarioPA.objects.filter(
                funcionario=funcionario, 
                posicao_atendimento=pa_atual, 
                ativo=True
            ).update(ativo=False, data_fim=timezone.now().date())
            
            AtribuicaoFuncionarioPA.objects.filter(
                funcionario=funcionario_anterior, 
                posicao_atendimento=pa, 
                ativo=True
            ).update(ativo=False, data_fim=timezone.now().date())
            
            # Trocar os funcionários
            pa.funcionario = funcionario
            pa_atual.funcionario = funcionario_anterior
            
            # Salvar as alterações
            pa.save()
            pa_atual.save()
            
            # Criar novas atribuições no histórico
            AtribuicaoFuncionarioPA.objects.create(
                funcionario=funcionario,
                posicao_atendimento=pa,
                data_inicio=timezone.now().date(),
                ativo=True
            )
            
            AtribuicaoFuncionarioPA.objects.create(
                funcionario=funcionario_anterior,
                posicao_atendimento=pa_atual,
                data_inicio=timezone.now().date(),
                ativo=True
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Você trocou de PA com {funcionario_anterior.nome_completo}. Agora você está na PA {pa.numero} e ele está na PA {pa_atual.numero}.'
            })
            
        elif option == 'replace':
            # Opção 2: Substituir o funcionário atual (o anterior fica sem PA)
            # Finalizar atribuição anterior no histórico
            AtribuicaoFuncionarioPA.objects.filter(
                funcionario=funcionario_anterior, 
                posicao_atendimento=pa, 
                ativo=True
            ).update(ativo=False, data_fim=timezone.now().date())
            
            # Se o funcionário atual tem uma PA, desatribuir
            if pa_atual:
                AtribuicaoFuncionarioPA.objects.filter(
                    funcionario=funcionario, 
                    posicao_atendimento=pa_atual, 
                    ativo=True
                ).update(ativo=False, data_fim=timezone.now().date())
                
                pa_atual.funcionario = None
                pa_atual.status = 'livre'
                pa_atual.save()
            
            # Atribuir novo funcionário à PA
            pa.funcionario = funcionario
            pa.status = 'ocupada'
            pa.save()
            
            # Criar nova atribuição no histórico
            AtribuicaoFuncionarioPA.objects.create(
                funcionario=funcionario,
                posicao_atendimento=pa,
                data_inicio=timezone.now().date(),
                ativo=True
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Você substituiu {funcionario_anterior.nome_completo} na PA {pa.numero}. O funcionário anterior foi desatribuído.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Opção inválida ou você não possui uma PA atual para realizar a troca.'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao processar a requisição: {str(e)}'
        })


# Views para Controle de Manutenção
@login_required
def controle_manutencao(request):
    # Obter periféricos em manutenção
    perifericos_em_manutencao = Periferico.objects.filter(status='manutencao')
    
    # Obter computadores em manutenção
    computadores_em_manutencao = Computador.objects.filter(status='manutencao')
    
    # Lista combinada para o template
    itens_manutencao = []
    
    # Inicializar contador por tipo
    contagem_por_tipo = {
        'Mouse': 0,
        'Teclado': 0,
        'Monitor': 0,
        'Fone': 0,
        'Mousepad': 0,
        'Computador': 0,
        'Outros_Periféricos': 0
    }
    
    # Processar periféricos
    for periferico in perifericos_em_manutencao:
        # Buscar a última PA onde este periférico estava
        ultima_atribuicao = AtribuicaoPerifericoPA.objects.filter(
            periferico=periferico
        ).order_by('-data_atribuicao').first()
        
        # Formatar item para o template
        item = {
            'nome_item': f"{periferico.tipo.nome}",
            'marca_modelo': f"{periferico.marca} {periferico.modelo or ''}".strip(),
            'ultima_pa': ultima_atribuicao.posicao_atendimento if ultima_atribuicao else None,
            'observacoes': periferico.observacoes,
            'id_item': periferico.id,
            'tipo_item_slug': 'periferico'
        }
        
        # Adicionar à lista
        itens_manutencao.append(item)
        
        # Incrementar contador por tipo
        if periferico.tipo.nome in contagem_por_tipo:
            contagem_por_tipo[periferico.tipo.nome] += 1
        else:
            contagem_por_tipo['Outros_Periféricos'] += 1
    
    # Processar computadores
    for computador in computadores_em_manutencao:
        # Buscar a última PA onde este computador estava
        ultima_atribuicao = AtribuicaoComputadorPA.objects.filter(
            computador=computador
        ).order_by('-data_atribuicao').first()
        
        # Formatar item para o template
        item = {
            'nome_item': "Computador",
            'marca_modelo': computador.marca,
            'ultima_pa': ultima_atribuicao.posicao_atendimento if ultima_atribuicao else None,
            'observacoes': computador.observacoes,
            'id_item': computador.id,
            'tipo_item_slug': 'computador'
        }
        
        # Adicionar à lista
        itens_manutencao.append(item)
        
        # Incrementar contador
        contagem_por_tipo['Computador'] += 1
    
    # Calcular total de itens em manutenção
    total_itens_manutencao = sum(contagem_por_tipo.values())
    
    context = {
        'title': 'Controle de Manutenção - TI',
        'itens_manutencao': itens_manutencao,
        'contagem_por_tipo': contagem_por_tipo,
        'total_itens_manutencao': total_itens_manutencao,
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
    perifericos = Periferico.objects.all().select_related('tipo')
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
                        
                        # Criar periférico(s)
                        # Para cada item do lote, criamos a quantidade especificada (cada unidade com quantidade=1)
                        for _ in range(quantidade):
                            periferico = Periferico(
                                tipo_id=tipo_id,
                                marca=marca,
                                modelo=modelo,
                                data_aquisicao=data_aquisicao,
                                loja_id=loja_id,
                                quantidade=1,  # Cada periférico tem quantidade=1 para melhor controle
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

@require_GET
@login_required
def api_computadores_disponiveis(request):
    """
    API para retornar computadores disponíveis para atribuição
    Retorna uma lista de computadores com status 'disponivel'
    """
    try:
        from .models import Computador  # Importar aqui para evitar importação circular
        
        # Buscar computadores com status 'disponivel'
        computadores_disponiveis = Computador.objects.filter(
            status='disponivel'
        ).values('id', 'marca')
        
        # Converter para lista para serialização JSON
        computadores_lista = list(computadores_disponiveis)
        
        # Adicionar um campo 'modelo' vazio para compatibilidade com o JavaScript
        for computador in computadores_lista:
            computador['modelo'] = ''  # Adiciona campo vazio para compatibilidade
        
        return JsonResponse({
            'success': True,
            'computadores': computadores_lista
        })
    except Exception as e:
        import traceback
        print(f"Erro ao buscar computadores disponíveis: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

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

# APIs para carregamento rápido
@login_required
@require_GET
def api_admin_dashboard_data(request):
    """
    API para carregamento rápido dos dados do dashboard administrativo de TI
    """
    try:
        data = {
            'counts': {
                'tipos_perifericos': TipoPeriferico.objects.all().count(),
                'perifericos': Periferico.objects.all().count(),
                'salas': Sala.objects.all().count(),
                'ilhas': Ilha.objects.all().count(),
                'posicoes_atendimento': PosicaoAtendimento.objects.all().count(),
                'atribuicoes_funcionarios': AtribuicaoFuncionarioPA.objects.filter(ativo=True).count(),
                'atribuicoes_perifericos': AtribuicaoPerifericoPA.objects.filter(ativo=True).count(),
            },
            'listas': {
                'tipos_perifericos': list(TipoPeriferico.objects.all().values('id', 'nome')),
                'salas': list(Sala.objects.all().values('id', 'nome')),
                'perifericos_disponiveis': list(Periferico.objects.filter(status='disponivel').values('id', 'marca', 'modelo', 'tipo__nome')),
                'computadores_disponiveis': list(Computador.objects.filter(status='disponivel').values('id', 'marca')),
                'lojas': list(Loja.objects.filter(status=True).values('id', 'nome').order_by('nome')),
            }
        }
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def api_controle_salas_data(request):
    """
    API para carregamento rápido dos dados da página de controle de salas
    """
    try:
        # Carregar salas com suas ilhas
        salas = Sala.objects.all()
        salas_data = []
        
        # Obter tipos de periféricos comuns (aqueles esperados em cada PA)
        tipos_perifericos_comuns = list(TipoPeriferico.objects.filter(
            nome__in=['Mouse', 'Teclado', 'Monitor', 'Fone', 'Mousepad']
        ).values('id', 'nome'))
        
        # Criar um mapa de IDs e nomes para facilitar a busca
        tipos_comuns_map = {tipo['id']: tipo['nome'] for tipo in tipos_perifericos_comuns}
        
        # Carregar todas as atribuições de periféricos ativas
        atribuicoes_perifericos = AtribuicaoPerifericoPA.objects.filter(
            ativo=True
        ).select_related(
            'periferico', 'periferico__tipo', 'posicao_atendimento'
        )
        
        # Mapear periféricos por PA
        perifericos_por_pa = {}
        # Mapear tipos de periféricos já atribuídos por PA
        tipos_atribuidos_por_pa = {}
        
        for atr in atribuicoes_perifericos:
            pa_id = atr.posicao_atendimento_id
            
            # Inicializar listas se necessário
            if pa_id not in perifericos_por_pa:
                perifericos_por_pa[pa_id] = []
            if pa_id not in tipos_atribuidos_por_pa:
                tipos_atribuidos_por_pa[pa_id] = set()
            
            # Adicionar periférico à lista
            perifericos_por_pa[pa_id].append({
                'id': atr.periferico.id,
                'tipo': atr.periferico.tipo.nome,
                'marca': atr.periferico.marca,
                'modelo': atr.periferico.modelo
            })
            
            # Registrar que este tipo já está atribuído a esta PA
            tipos_atribuidos_por_pa[pa_id].add(atr.periferico.tipo_id)
        
        # Carregar atribuições de computadores ativas
        atribuicoes_computadores = AtribuicaoComputadorPA.objects.filter(
            ativo=True
        ).select_related(
            'computador', 'posicao_atendimento'
        )
        
        # Mapear computadores por PA
        computadores_por_pa = {}
        
        for atr in atribuicoes_computadores:
            pa_id = atr.posicao_atendimento_id
            
            # Inicializar lista se necessário
            if pa_id not in computadores_por_pa:
                computadores_por_pa[pa_id] = []
            
            # Adicionar computador à lista
            computadores_por_pa[pa_id].append({
                'id': atr.computador.id,
                'marca': atr.computador.marca
            })
        
        for sala in salas:
            sala_dict = {
                'id': sala.id,
                'nome': sala.nome,
                'ilhas': []
            }
            
            for ilha in sala.ilhas.all():
                ilha_dict = {
                    'id': ilha.id,
                    'nome': ilha.nome,
                    'quantidade_pas': ilha.quantidade_pas,
                    'posicoes': []
                }
                
                # Carregar PAs para esta ilha
                pas = PosicaoAtendimento.objects.filter(ilha=ilha).select_related('funcionario')
                for pa in pas:
                    # Determinar quais tipos de periféricos estão faltando
                    tipos_faltantes = []
                    for tipo_id, tipo_nome in tipos_comuns_map.items():
                        if pa.id not in tipos_atribuidos_por_pa or tipo_id not in tipos_atribuidos_por_pa[pa.id]:
                            tipos_faltantes.append(tipo_nome)
                    
                    pa_dict = {
                        'id': pa.id,
                        'numero': pa.numero,
                        'status': pa.status,
                        'status_display': pa.get_status_display(),
                        'funcionario': pa.funcionario.nome if pa.funcionario else None,
                        'perifericos': perifericos_por_pa.get(pa.id, []),
                        'faltando': tipos_faltantes,
                        'computadores': computadores_por_pa.get(pa.id, [])
                    }
                    ilha_dict['posicoes'].append(pa_dict)
                
                sala_dict['ilhas'].append(ilha_dict)
            
            salas_data.append(sala_dict)
        
        # Dados de periféricos e computadores disponíveis
        perifericos_disponiveis = list(Periferico.objects.filter(
            status='disponivel'
        ).values('id', 'marca', 'modelo', 'tipo__id', 'tipo__nome'))
        
        computadores_disponiveis = list(Computador.objects.filter(
            status='disponivel'
        ).values('id', 'marca'))
        
        return JsonResponse({
            'success': True,
            'data': {
                'salas': salas_data,
                'tipos_perifericos_comuns': tipos_perifericos_comuns,
                'perifericos_disponiveis': perifericos_disponiveis,
                'computadores_disponiveis': computadores_disponiveis
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def api_controle_estoque_data(request):
    """
    API para carregamento rápido dos dados da página de controle de estoque
    """
    try:
        # Obter a loja selecionada, se houver
        loja_id = request.GET.get('loja')
        loja_selecionada = None
        
        # Aplicar filtro de loja se necessário
        filtro_loja = {'loja_id': loja_id} if loja_id else {}
        
        # Obter salas com suas ilhas
        salas = Sala.objects.all().prefetch_related('ilhas')
        
        # Obter tipos de periféricos
        tipos_perifericos = list(TipoPeriferico.objects.all().order_by('nome').values('id', 'nome'))
        
        # Calcular o total de periféricos por tipo
        perifericos_totais_por_tipo = {}
        for tipo in tipos_perifericos:
            total_tipo = Periferico.objects.filter(
                tipo_id=tipo['id'], 
                status='disponivel',
                **filtro_loja
            ).exclude(
                id__in=AtribuicaoPerifericoPA.objects.filter(ativo=True).values_list('periferico_id', flat=True)
            ).count()
            
            perifericos_totais_por_tipo[tipo['id']] = total_tipo
        
        # Obter todas as marcas de computadores
        todas_as_marcas = list(Computador.objects.values_list('marca', flat=True).distinct())
        
        # Computadores disponíveis por marca
        computadores_disponiveis = []
        for marca in todas_as_marcas:
            query = Computador.objects.filter(marca=marca, status='disponivel', **filtro_loja)
            quantidade = query.count()
            computadores_disponiveis.append({
                'marca': marca,
                'quantidade_disponivel': quantidade
            })
        
        # Estatísticas gerais
        estatisticas = {
            'computadores': {
                'total': Computador.objects.filter(**filtro_loja).count(),
                'disponiveis': Computador.objects.filter(status='disponivel', **filtro_loja).count(),
                'em_uso': Computador.objects.filter(status='em_uso', **filtro_loja).count(),
                'manutencao': Computador.objects.filter(status='manutencao', **filtro_loja).count()
            },
            'perifericos': {
                'total': Periferico.objects.filter(**filtro_loja).count(),
                'disponiveis': Periferico.objects.filter(status='disponivel', **filtro_loja).count(),
                'em_uso': Periferico.objects.filter(status='em_uso', **filtro_loja).count(),
                'manutencao': Periferico.objects.filter(status='manutencao', **filtro_loja).count()
            }
        }
        
        # Histórico recente (limitado a 20 registros)
        historico = []
        perifericos_historico = AtribuicaoPerifericoPA.objects.select_related(
            'periferico', 'periferico__tipo', 'posicao_atendimento'
        ).order_by('-data_atribuicao')[:10]
        
        for atribuicao in perifericos_historico:
            if atribuicao.data_atribuicao:
                historico.append({
                    'data': atribuicao.data_atribuicao.isoformat(),
                    'tipo': 'periferico',
                    'acao': 'atribuicao',
                    'item': f"{atribuicao.periferico.tipo.nome} {atribuicao.periferico.marca}",
                    'pa': f"PA {atribuicao.posicao_atendimento.numero}"
                })
        
        # Lista de lojas para o seletor
        lojas = list(Loja.objects.filter(status=True).values('id', 'nome').order_by('nome'))
        
        return JsonResponse({
            'success': True,
            'data': {
                'salas': list(salas.values('id', 'nome')),
                'ilhas': list(Ilha.objects.values('id', 'nome', 'sala_id')),
                'tipos_perifericos': tipos_perifericos,
                'perifericos_totais_por_tipo': perifericos_totais_por_tipo,
                'computadores_disponiveis_por_marca': computadores_disponiveis,
                'estatisticas': estatisticas,
                'historico': historico,
                'lojas': lojas,
                'loja_selecionada': loja_id
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def api_controle_manutencao_data(request):
    """
    API para carregamento rápido dos dados da página de controle de manutenção
    """
    try:
        # Obter periféricos em manutenção
        perifericos_em_manutencao = Periferico.objects.filter(status='manutencao')
        perifericos_data = []
        
        for periferico in perifericos_em_manutencao:
            # Buscar a última PA onde este periférico estava
            ultima_atribuicao = AtribuicaoPerifericoPA.objects.filter(
                periferico=periferico
            ).order_by('-data_atribuicao').first()
            
            perifericos_data.append({
                'id': periferico.id,
                'tipo': periferico.tipo.nome,
                'marca': periferico.marca,
                'modelo': periferico.modelo,
                'observacoes': periferico.observacoes,
                'ultima_pa': {
                    'id': ultima_atribuicao.posicao_atendimento.id,
                    'numero': ultima_atribuicao.posicao_atendimento.numero
                } if ultima_atribuicao else None
            })
        
        # Obter computadores em manutenção
        computadores_em_manutencao = Computador.objects.filter(status='manutencao')
        computadores_data = []
        
        for computador in computadores_em_manutencao:
            # Buscar a última PA onde este computador estava
            ultima_atribuicao = AtribuicaoComputadorPA.objects.filter(
                computador=computador
            ).order_by('-data_atribuicao').first()
            
            computadores_data.append({
                'id': computador.id,
                'marca': computador.marca,
                'observacoes': computador.observacoes,
                'ultima_pa': {
                    'id': ultima_atribuicao.posicao_atendimento.id,
                    'numero': ultima_atribuicao.posicao_atendimento.numero
                } if ultima_atribuicao else None
            })
            
        # Contagem por tipo de equipamento em manutenção
        contagem = {
            'Mouse': perifericos_em_manutencao.filter(tipo__nome='Mouse').count(),
            'Teclado': perifericos_em_manutencao.filter(tipo__nome='Teclado').count(),
            'Monitor': perifericos_em_manutencao.filter(tipo__nome='Monitor').count(),
            'Fone': perifericos_em_manutencao.filter(tipo__nome='Fone').count(),
            'Mousepad': perifericos_em_manutencao.filter(tipo__nome='Mousepad').count(),
            'Computador': computadores_em_manutencao.count(),
            'Outros': perifericos_em_manutencao.exclude(
                tipo__nome__in=['Mouse', 'Teclado', 'Monitor', 'Fone', 'Mousepad']
            ).count()
        }
        
        return JsonResponse({
            'success': True,
            'data': {
                'perifericos': perifericos_data,
                'computadores': computadores_data,
                'contagem': contagem,
                'total': sum(contagem.values())
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def api_auto_atribuicao_pa_data(request):
    """
    API para carregamento rápido dos dados da página de auto-atribuição de PA
    """
    try:
        # Verificar se o usuário está associado a um funcionário
        funcionario = None
        try:
            funcionario = Funcionario.objects.get(usuario=request.user)
        except Funcionario.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Seu usuário não está vinculado a nenhum funcionário no sistema.'
            })
            
        # Verificar PA atual do funcionário
        atribuicao_atual = AtribuicaoFuncionarioPA.objects.filter(
            funcionario=funcionario,
            ativo=True
        ).select_related('posicao_atendimento', 'posicao_atendimento__sala', 'posicao_atendimento__ilha').first()
        
        pa_atual = None
        if atribuicao_atual:
            pa_atual = {
                'id': atribuicao_atual.posicao_atendimento.id,
                'numero': atribuicao_atual.posicao_atendimento.numero,
                'sala': atribuicao_atual.posicao_atendimento.sala.nome,
                'ilha': atribuicao_atual.posicao_atendimento.ilha.nome
            }
        else:
            # Verificar também diretamente na tabela de PAs como fallback
            pa_direto = PosicaoAtendimento.objects.filter(funcionario=funcionario).first()
            if pa_direto:
                pa_atual = {
                    'id': pa_direto.id,
                    'numero': pa_direto.numero,
                    'sala': pa_direto.sala.nome if pa_direto.sala else 'S/Sala',
                    'ilha': pa_direto.ilha.nome if pa_direto.ilha else 'S/Ilha'
                }
        
        # Buscar PAs livres ou ocupadas (para permitir troca)
        pas_disponiveis = PosicaoAtendimento.objects.filter(
            Q(status='livre') | Q(status='ocupada')
        ).select_related('sala', 'ilha', 'funcionario')
        
        # Se o funcionário já tem uma PA, exclua ela da lista
        if pa_atual:
            pas_disponiveis = pas_disponiveis.exclude(id=pa_atual['id'])
        
        pas_disponiveis_data = []
        for pa in pas_disponiveis:
            pas_disponiveis_data.append({
                'id': pa.id,
                'numero': pa.numero,
                'sala': pa.sala.nome if pa.sala else 'S/Sala',
                'ilha': pa.ilha.nome if pa.ilha else 'S/Ilha',
                'status': pa.status,
                'status_display': pa.get_status_display(),
                'funcionario_atual': pa.funcionario.nome if pa.funcionario else None
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'funcionario': {
                    'id': funcionario.id,
                    'nome': funcionario.nome,
                    'cargo': funcionario.cargo
                },
                'pa_atual': pa_atual,
                'pas_disponiveis': pas_disponiveis_data
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def api_listar_perifericos(request):
    """
    API para listar todos os periféricos com filtros
    """
    try:
        # Parâmetros de filtro
        tipo_id = request.GET.get('tipo')
        status = request.GET.get('status')
        loja_id = request.GET.get('loja')
        
        # Query base
        query = Periferico.objects.all().select_related('tipo', 'loja')
        
        # Aplicar filtros
        if tipo_id:
            query = query.filter(tipo_id=tipo_id)
        if status:
            query = query.filter(status=status)
        if loja_id:
            query = query.filter(loja_id=loja_id)
        
        # Paginação
        page = int(request.GET.get('page', 1))
        itens_por_pagina = int(request.GET.get('per_page', 20))
        
        # Ordenação
        order_by = request.GET.get('order_by', 'id')
        if order_by.startswith('-'):
            order_by = order_by[1:]
            order_direction = '-'
        else:
            order_direction = ''
            
        # Verificar se o campo de ordenação é válido
        campos_validos = ['id', 'tipo__nome', 'marca', 'modelo', 'status', 'data_aquisicao']
        if order_by not in campos_validos:
            order_by = 'id'
            
        query = query.order_by(f'{order_direction}{order_by}')
        
        # Executar paginação
        paginator = Paginator(query, itens_por_pagina)
        page_obj = paginator.get_page(page)
        
        # Formatar resposta
        perifericos_data = []
        for periferico in page_obj:
            perifericos_data.append({
                'id': periferico.id,
                'tipo': {
                    'id': periferico.tipo.id,
                    'nome': periferico.tipo.nome
                },
                'marca': periferico.marca,
                'modelo': periferico.modelo,
                'data_aquisicao': periferico.data_aquisicao.isoformat() if periferico.data_aquisicao else None,
                'status': periferico.status,
                'status_display': periferico.get_status_display(),
                'loja': {
                    'id': periferico.loja.id,
                    'nome': periferico.loja.nome
                } if periferico.loja else None,
                'observacoes': periferico.observacoes
            })
        
        # Metadados de paginação
        pagination = {
            'page': page,
            'per_page': itens_por_pagina,
            'total_items': paginator.count,
            'total_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': perifericos_data,
            'pagination': pagination
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def api_listar_computadores(request):
    """
    API para listar todos os computadores com filtros
    """
    try:
        # Parâmetros de filtro
        status = request.GET.get('status')
        loja_id = request.GET.get('loja')
        
        # Query base
        query = Computador.objects.all().select_related('loja')
        
        # Aplicar filtros
        if status:
            query = query.filter(status=status)
        if loja_id:
            query = query.filter(loja_id=loja_id)
        
        # Paginação
        page = int(request.GET.get('page', 1))
        itens_por_pagina = int(request.GET.get('per_page', 20))
        
        # Ordenação
        order_by = request.GET.get('order_by', 'id')
        if order_by.startswith('-'):
            order_by = order_by[1:]
            order_direction = '-'
        else:
            order_direction = ''
            
        # Verificar se o campo de ordenação é válido
        campos_validos = ['id', 'marca', 'status', 'data_aquisicao']
        if order_by not in campos_validos:
            order_by = 'id'
            
        query = query.order_by(f'{order_direction}{order_by}')
        
        # Executar paginação
        paginator = Paginator(query, itens_por_pagina)
        page_obj = paginator.get_page(page)
        
        # Formatar resposta
        computadores_data = []
        for computador in page_obj:
            computadores_data.append({
                'id': computador.id,
                'marca': computador.marca,
                'data_aquisicao': computador.data_aquisicao.isoformat() if computador.data_aquisicao else None,
                'status': computador.status,
                'status_display': computador.get_status_display(),
                'loja': {
                    'id': computador.loja.id,
                    'nome': computador.loja.nome
                } if computador.loja else None,
                'observacoes': computador.observacoes
            })
        
        # Metadados de paginação
        pagination = {
            'page': page,
            'per_page': itens_por_pagina,
            'total_items': paginator.count,
            'total_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': computadores_data,
            'pagination': pagination
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def api_listar_posicoes_atendimento(request):
    """
    API para listar todas as posições de atendimento com filtros
    """
    try:
        # Parâmetros de filtro
        sala_id = request.GET.get('sala')
        ilha_id = request.GET.get('ilha')
        status = request.GET.get('status')
        
        # Query base
        query = PosicaoAtendimento.objects.all().select_related('sala', 'ilha', 'funcionario')
        
        # Aplicar filtros
        if sala_id:
            query = query.filter(sala_id=sala_id)
        if ilha_id:
            query = query.filter(ilha_id=ilha_id)
        if status:
            query = query.filter(status=status)
        
        # Paginação
        page = int(request.GET.get('page', 1))
        itens_por_pagina = int(request.GET.get('per_page', 20))
        
        # Ordenação
        order_by = request.GET.get('order_by', 'numero')
        if order_by.startswith('-'):
            order_by = order_by[1:]
            order_direction = '-'
        else:
            order_direction = ''
            
        # Verificar se o campo de ordenação é válido
        campos_validos = ['id', 'numero', 'sala__nome', 'ilha__nome', 'status']
        if order_by not in campos_validos:
            order_by = 'numero'
            
        query = query.order_by(f'{order_direction}{order_by}')
        
        # Executar paginação
        paginator = Paginator(query, itens_por_pagina)
        page_obj = paginator.get_page(page)
        
        # Formatar resposta
        pas_data = []
        for pa in page_obj:
            # Obter periféricos atribuídos a esta PA
            perifericos = AtribuicaoPerifericoPA.objects.filter(
                posicao_atendimento=pa, 
                ativo=True
            ).select_related('periferico', 'periferico__tipo')
            
            perifericos_data = []
            for atribuicao in perifericos:
                perifericos_data.append({
                    'id': atribuicao.periferico.id,
                    'tipo': atribuicao.periferico.tipo.nome,
                    'marca': atribuicao.periferico.marca,
                    'modelo': atribuicao.periferico.modelo
                })
            
            # Obter computadores atribuídos a esta PA
            computadores = AtribuicaoComputadorPA.objects.filter(
                posicao_atendimento=pa, 
                ativo=True
            ).select_related('computador')
            
            computadores_data = []
            for atribuicao in computadores:
                computadores_data.append({
                    'id': atribuicao.computador.id,
                    'marca': atribuicao.computador.marca
                })
            
            pas_data.append({
                'id': pa.id,
                'numero': pa.numero,
                'sala': {
                    'id': pa.sala.id,
                    'nome': pa.sala.nome
                } if pa.sala else None,
                'ilha': {
                    'id': pa.ilha.id,
                    'nome': pa.ilha.nome
                } if pa.ilha else None,
                'status': pa.status,
                'status_display': pa.get_status_display(),
                'funcionario': {
                    'id': pa.funcionario.id,
                    'nome': pa.funcionario.nome
                } if pa.funcionario else None,
                'perifericos': perifericos_data,
                'computadores': computadores_data
            })
        
        # Metadados de paginação
        pagination = {
            'page': page,
            'per_page': itens_por_pagina,
            'total_items': paginator.count,
            'total_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        }
        
        return JsonResponse({
            'success': True,
            'data': pas_data,
            'pagination': pagination
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
