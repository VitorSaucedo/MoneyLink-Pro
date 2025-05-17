from django.urls import path
from . import views

app_name = 'ti'

urlpatterns = [
    path('controle-estoque/', views.controle_estoque, name='controle_estoque'),
    path('admin/', views.admin, name='admin'),
    path('controle-salas/', views.controle_salas, name='controle_salas'),
    path('all_forms/', views.controle_estoque, name='all_forms'),
    
    # URLs para Auto Atribuição de PA
    path('auto-atribuicao-pa/', views.auto_atribuicao_pa, name='auto_atribuicao_pa'),
    
    # URLs para Controle de Manutenção
    path('controle-manutencao/', views.controle_manutencao, name='controle_manutencao'),
    path('marcar-consertado/<int:item_id>/<slug:tipo_item_slug>/', views.marcar_consertado, name='marcar_consertado'),
    
    # URLs para API
    path('api/ilhas-por-sala/<int:sala_id>/', views.api_ilhas_por_sala, name='api_ilhas_por_sala'),
    path('atualizar_status_pa/', views.atualizar_status_pa, name='atualizar_status_pa'),
    path('remover_periferico_pa/', views.remover_periferico_pa, name='remover_periferico_pa'),
    path('api/controle-salas-dados/', views.api_controle_salas, name='api_controle_salas'),
    
    # URLs para Tipos de Periféricos
    path('tipos-perifericos/', views.tipo_periferico_list, name='tipo_periferico_list'),
    path('tipos-perifericos/cadastrar/', views.tipo_periferico_create, name='tipo_periferico_create'),
    path('tipos-perifericos/editar/<int:pk>/', views.tipo_periferico_update, name='tipo_periferico_update'),
    path('tipos-perifericos/excluir/<int:pk>/', views.tipo_periferico_delete, name='tipo_periferico_delete'),
    
    # URLs para Periféricos
    path('perifericos/', views.periferico_list, name='periferico_list'),
    path('perifericos/cadastrar/', views.periferico_create, name='periferico_create'),
    path('perifericos/editar/<int:pk>/', views.periferico_update, name='periferico_update'),
    path('perifericos/excluir/<int:pk>/', views.periferico_delete, name='periferico_delete'),
    
    # URLs para Computadores
    path('computadores/cadastrar/', views.computador_create, name='computador_create'),
    path('computadores/atribuir/', views.atribuicao_computador_pa_create, name='atribuicao_computador_pa_create'),
    
    # URLs para Salas
    path('salas/', views.sala_list, name='sala_list'),
    path('salas/cadastrar/', views.sala_create, name='sala_create'),
    path('salas/editar/<int:pk>/', views.sala_update, name='sala_update'),
    path('salas/excluir/<int:pk>/', views.sala_delete, name='sala_delete'),
    
    # URLs para Ilhas
    path('ilhas/', views.ilha_list, name='ilha_list'),
    path('ilhas/cadastrar/', views.ilha_create, name='ilha_create'),
    path('ilhas/editar/<int:pk>/', views.ilha_update, name='ilha_update'),
    path('ilhas/excluir/<int:pk>/', views.ilha_delete, name='ilha_delete'),
    
    # URLs para Posições de Atendimento
    path('posicoes-atendimento/', views.posicao_atendimento_list, name='posicao_atendimento_list'),
    path('posicoes-atendimento/cadastrar/', views.posicao_atendimento_create, name='posicao_atendimento_create'),
    path('posicoes-atendimento/editar/<int:pk>/', views.posicao_atendimento_update, name='posicao_atendimento_update'),
    path('posicoes-atendimento/excluir/<int:pk>/', views.posicao_atendimento_delete, name='posicao_atendimento_delete'),
    
    # URLs para Atribuição de Funcionários a PAs
    path('atribuicoes-funcionarios/', views.atribuicao_funcionario_pa_list, name='atribuicao_funcionario_pa_list'),
    path('atribuicoes-funcionarios/cadastrar/', views.atribuicao_funcionario_pa_create, name='atribuicao_funcionario_pa_create'),
    path('atribuicoes-funcionarios/editar/<int:pk>/', views.atribuicao_funcionario_pa_update, name='atribuicao_funcionario_pa_update'),
    path('atribuicoes-funcionarios/excluir/<int:pk>/', views.atribuicao_funcionario_pa_delete, name='atribuicao_funcionario_pa_delete'),
    
    # URLs para Atribuição de Periféricos a PAs
    path('atribuicao-perifericos/', views.atribuicao_periferico, name='atribuicao_periferico'),
    path('atribuicoes-perifericos/cadastrar/', views.atribuicao_periferico_pa_create, name='atribuicao_periferico_pa_create'),
    path('atribuicoes-perifericos/editar/<int:pk>/', views.atribuicao_periferico_pa_update, name='atribuicao_periferico_pa_update'),
    path('atribuicoes-perifericos/excluir/<int:pk>/', views.atribuicao_periferico_pa_delete, name='atribuicao_periferico_pa_delete'),

    # API para filtrar PAs para atribuição de periférico
    path('api/pas-para-atribuicao-periferico/<int:periferico_id>/', views.api_pas_para_atribuicao_periferico, name='api_pas_para_atribuicao_periferico'),

    # URLs da API para controle de PAs
    path('api/funcionarios/', views.get_funcionarios_json, name='api_get_funcionarios'),
    path('api/atribuir_funcionario_pa/', views.atribuir_funcionario_pa, name='api_atribuir_funcionario_pa'),
    path('api/computadores_disponiveis/', views.api_listar_computadores_disponiveis, name='api_listar_computadores_disponiveis'),
    path('api/pa/<int:pa_id>/adicionar_computador/', views.api_adicionar_computador_pa, name='api_adicionar_computador_pa'),
    path('api/pa/<int:pa_id>/remover_computador/', views.api_remover_computador_pa, name='api_remover_computador_pa'),
    path('api/periferico/<int:periferico_id>/atualizar_status/', views.api_atualizar_status_periferico, name='api_atualizar_status_periferico'),
    path('api/computador/<int:computador_id>/atualizar_status/', views.api_atualizar_status_computador, name='api_atualizar_status_computador'),
    path('api/perifericos-disponiveis-por-tipo/<int:tipo_id>/', views.api_listar_perifericos_disponiveis_por_tipo, name='api_listar_perifericos_disponiveis_por_tipo'),
    
    # URLs para gerenciamento de ramais
    path('ramal/update/', views.ramal_update, name='ramal_update'),
    path('api/verificar-ramal/', views.api_verificar_ramal, name='api_verificar_ramal'),
] 