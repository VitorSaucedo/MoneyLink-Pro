from django.urls import path
from . import views

app_name = 'ti'

urlpatterns = [
    path('controle-estoque/', views.controle_estoque, name='controle_estoque'),
    path('admin/', views.admin, name='admin'),
    path('controle-salas/', views.controle_salas, name='controle_salas'),
    path('all_forms/', views.controle_estoque, name='all_forms'),
    

    
    # URLs para Controle de Manutenção
    path('controle-manutencao/', views.controle_manutencao, name='controle_manutencao'),
    path('marcar-consertado/<int:item_id>/<slug:tipo_item_slug>/', views.marcar_consertado, name='marcar_consertado'),
    path('excluir-periferico/<int:item_id>/<slug:tipo_item_slug>/', views.excluir_periferico, name='excluir_periferico'),
    
    # URLs para API
    path('api/ilhas-por-sala/<int:sala_id>/', views.api_ilhas_por_sala, name='api_ilhas_por_sala'),
    path('api/ilha-info/<int:ilha_id>/', views.api_ilha_info, name='api_ilha_info'),
    path('api/computadores_disponiveis/', views.api_computadores_disponiveis, name='api_computadores_disponiveis'),
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
    
    # URLs para Ramais
    path('ramais/', views.ramal_list, name='ramal_list'),
    path('ramais/cadastrar/', views.ramal_create, name='ramal_create'),
    path('ramais/atualizar/', views.ramal_update, name='ramal_update'),
    path('ramais/editar/<int:pk>/', views.ramal_edit, name='ramal_edit'),
    path('ramais/excluir/<int:pk>/', views.ramal_delete, name='ramal_delete'),
    
    # URLs para Coordenadores de Sala
    path('coordenadores-sala/cadastrar/', views.coordenador_sala_create, name='coordenador_sala_create'),
    
    # URLs para Computadores
    path('computadores/cadastrar/', views.computador_create, name='computador_create'),
    path('computadores/atribuir/', views.atribuicao_computador_pa_create, name='atribuicao_computador_pa_create'),
    
    # URLs para Monitores
    path('monitores/', views.monitor_list, name='monitor_list'),
    path('monitores/cadastrar/', views.monitor_create, name='monitor_create'),
    path('monitores/editar/<int:pk>/', views.monitor_update, name='monitor_update'),
    path('monitores/excluir/<int:pk>/', views.monitor_delete, name='monitor_delete'),
    path('monitores/atribuir/', views.atribuicao_monitor_pa_create, name='atribuicao_monitor_pa_create'),
    
    # URLs para Salas
    path('salas/', views.sala_list, name='sala_list'),
    path('salas/cadastrar/', views.sala_create, name='sala_create'),
    path('salas/editar/<int:pk>/', views.sala_update, name='sala_update'),
    path('salas/excluir/<int:pk>/', views.sala_delete, name='sala_delete'),
    
    # URLs para Lojas removidas - funcionalidade já existe em outro módulo
    
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
    path('api/funcionarios/', views.api_funcionarios, name='api_funcionarios'),
    # URL antiga mantida por compatibilidade (redirecionando para a nova)
    path('api/get_funcionarios/', views.api_funcionarios, name='api_get_funcionarios'),
    path('api/atribuir_funcionario_pa/', views.atribuir_funcionario_pa, name='api_atribuir_funcionario_pa'),
    path('api/pa/<int:pa_id>/adicionar_computador/', views.api_adicionar_computador_pa, name='api_adicionar_computador_pa'),
    path('api/pa/<int:pa_id>/remover_computador/', views.api_remover_computador_pa, name='api_remover_computador_pa'),
    path('api/periferico/<int:periferico_id>/atualizar_status/', views.api_atualizar_status_periferico, name='api_atualizar_status_periferico'),
    path('api/computador/<int:computador_id>/atualizar_status/', views.api_atualizar_status_computador, name='api_atualizar_status_computador'),
    path('api/perifericos-disponiveis-por-tipo/<int:tipo_id>/', views.api_listar_perifericos_disponiveis_por_tipo, name='api_listar_perifericos_disponiveis_por_tipo'),
    
    # APIs para Monitores
    path('api/monitores_disponiveis/', views.api_monitores_disponiveis, name='api_monitores_disponiveis'),
    path('api/pa/<int:pa_id>/adicionar_monitor/', views.api_adicionar_monitor_pa, name='api_adicionar_monitor_pa'),
    path('api/pa/<int:pa_id>/remover_monitor/', views.api_remover_monitor_pa, name='api_remover_monitor_pa'),
    path('api/monitor/<int:monitor_id>/atualizar_status/', views.api_atualizar_status_monitor, name='api_atualizar_status_monitor'),
    
    # URLs para gerenciamento de ramais
    # path('ramal/update/', views.ramal_update, name='ramal_update'),
    path('api/verificar-ramal/', views.api_verificar_ramal, name='api_verificar_ramal'),

    # Nova rota para atribuições em lote
    path('atribuicoes-perifericos/cadastrar-lote/', views.cadastrar_atribuicoes_perifericos_lote, name='cadastrar_atribuicoes_lote'),

    # Novas APIs para carregamento rápido de dados
    path('api/admin-dashboard-data/', views.api_admin_dashboard_data, name='api_admin_dashboard_data'),
    path('api/controle-salas-data/', views.api_controle_salas_data, name='api_controle_salas_data'),
    path('api/controle-estoque-data/', views.api_controle_estoque_data, name='api_controle_estoque_data'),
    path('api/controle-manutencao-data/', views.api_controle_manutencao_data, name='api_controle_manutencao_data'),

    path('api/listar-perifericos/', views.api_listar_perifericos, name='api_listar_perifericos'),
    path('api/listar-computadores/', views.api_listar_computadores, name='api_listar_computadores'),
    path('api/listar-posicoes-atendimento/', views.api_listar_posicoes_atendimento, name='api_listar_posicoes_atendimento'),
    path('api/funcionarios/', views.api_funcionarios, name='api_funcionarios'),

    # Novas APIs para salas por loja e ilhas por sala
    path('api/salas-por-loja/<int:loja_id>/', views.api_salas_por_loja, name='api_salas_por_loja'),
    path('api/ilhas-por-sala/<int:sala_id>/', views.api_ilhas_por_sala, name='api_ilhas_por_sala'),
    
    # URLs para Controle de Chips
    path('controle-chips/', views.controle_chips, name='controle_chips'),
    path('chips/cadastrar/', views.chip_create, name='chip_create'),
    path('chips/editar/<int:pk>/', views.chip_update, name='chip_update'),
    path('chips/excluir/<int:pk>/', views.chip_delete, name='chip_delete'),
    path('api/chips-data/', views.api_chips_data, name='api_chips_data'),
    
    # URLs para Controle de E-mails
    path('controle-emails/', views.controle_emails, name='controle_emails'),
    path('emails/cadastrar/', views.email_create, name='email_create'),
    path('emails/editar/<int:pk>/', views.email_update, name='email_update'),
    path('emails/excluir/<int:pk>/', views.email_delete, name='email_delete'),
    path('api/emails-data/', views.api_emails_data, name='api_emails_data'),
    
    # URLs para Controle de Acessos
    path('controle-acessos/', views.controle_acessos, name='controle_acessos'),
    path('storm/cadastrar/', views.storm_create, name='storm_create'),
    path('storm/editar/<int:pk>/', views.storm_update, name='storm_update'),
    path('storm/excluir/<int:pk>/', views.storm_delete, name='storm_delete'),
    path('sistema/cadastrar/', views.sistema_create, name='sistema_create'),
    path('sistema/editar/<int:pk>/', views.sistema_update, name='sistema_update'),
    path('sistema/excluir/<int:pk>/', views.sistema_delete, name='sistema_delete'),
    
    # URLs AJAX para formulários (evitar reload da página)
    path('ajax/periferico/cadastrar/', views.ajax_periferico_create, name='ajax_periferico_create'),
    path('ajax/computador/cadastrar/', views.ajax_computador_create, name='ajax_computador_create'),
    path('ajax/sala/cadastrar/', views.ajax_sala_create, name='ajax_sala_create'),
    path('ajax/ilha/cadastrar/', views.ajax_ilha_create, name='ajax_ilha_create'),
    path('ajax/posicao-atendimento/cadastrar/', views.ajax_posicao_atendimento_create, name='ajax_posicao_atendimento_create'),
    path('ajax/tipo-periferico/cadastrar/', views.ajax_tipo_periferico_create, name='ajax_tipo_periferico_create'),
    path('ajax/monitor/cadastrar/', views.ajax_monitor_create, name='ajax_monitor_create'),
    path('ajax/chip/cadastrar/', views.ajax_chip_create, name='ajax_chip_create'),
    path('ajax/email/cadastrar/', views.ajax_email_create, name='ajax_email_create'),
]