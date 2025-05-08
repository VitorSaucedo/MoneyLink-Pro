from django.urls import path
from . import views

app_name = 'ti'

urlpatterns = [
    path('controle-estoque/', views.controle_estoque, name='controle_estoque'),
    path('admin/', views.admin, name='admin'),
    path('controle-salas/', views.controle_salas, name='controle_salas'),
    path('all_forms/', views.controle_estoque, name='all_forms'),
    
    # URLs para API
    path('api/ilhas-por-sala/<int:sala_id>/', views.api_ilhas_por_sala, name='api_ilhas_por_sala'),
    
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
    path('atribuicoes-perifericos/', views.atribuicao_periferico_pa_list, name='atribuicao_periferico_pa_list'),
    path('atribuicoes-perifericos/cadastrar/', views.atribuicao_periferico_pa_create, name='atribuicao_periferico_pa_create'),
    path('atribuicoes-perifericos/editar/<int:pk>/', views.atribuicao_periferico_pa_update, name='atribuicao_periferico_pa_update'),
    path('atribuicoes-perifericos/excluir/<int:pk>/', views.atribuicao_periferico_pa_delete, name='atribuicao_periferico_pa_delete'),
] 