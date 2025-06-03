from django.contrib import admin
from .models import (
    TipoPeriferico, 
    Periferico, 
    PosicaoAtendimento, 
    AtribuicaoFuncionarioPA, 
    AtribuicaoPerifericoPA,
    Sala,
    Ilha,
    Loja,
    Computador,
    AtribuicaoComputadorPA
)

# Register your models here.
@admin.register(TipoPeriferico)
class TipoPerifericoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(Periferico)
class PerifericoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'marca', 'modelo', 'numero_serie', 'status')
    list_filter = ('tipo', 'status', 'marca')
    search_fields = ('marca', 'modelo', 'numero_serie')

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)
    fields = ('nome', 'descricao')

@admin.register(Ilha)
class IlhaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sala', 'quantidade_pas')
    list_filter = ('sala',)
    search_fields = ('nome',)

@admin.register(PosicaoAtendimento)
class PosicaoAtendimentoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'sala', 'ilha', 'funcionario', 'status')
    list_filter = ('status', 'sala', 'ilha')
    search_fields = ('numero', 'funcionario__nome_completo')
    autocomplete_fields = ['funcionario']

@admin.register(AtribuicaoFuncionarioPA)
class AtribuicaoFuncionarioPAAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'posicao_atendimento', 'data_inicio', 'data_fim', 'ativo')
    list_filter = ('ativo', 'posicao_atendimento')
    search_fields = ('funcionario__nome_completo', 'posicao_atendimento__numero')

@admin.register(AtribuicaoPerifericoPA)
class AtribuicaoPerifericoPAAdmin(admin.ModelAdmin):
    list_display = ('periferico', 'posicao_atendimento', 'data_atribuicao', 'data_remocao', 'ativo')
    list_filter = ('ativo', 'posicao_atendimento')
    search_fields = ('periferico__modelo', 'posicao_atendimento__numero')

# Removida a administração da Loja, pois já está definida no app funcionarios

@admin.register(Computador)
class ComputadorAdmin(admin.ModelAdmin):
    list_display = ('marca', 'quantidade', 'loja', 'status')
    list_filter = ('status', 'loja', 'marca')
    search_fields = ('marca', 'observacoes')

@admin.register(AtribuicaoComputadorPA)
class AtribuicaoComputadorPAAdmin(admin.ModelAdmin):
    list_display = ('computador', 'posicao_atendimento', 'data_atribuicao', 'data_remocao', 'ativo')
    list_filter = ('ativo', 'posicao_atendimento')
    search_fields = ('computador__marca', 'posicao_atendimento__numero')
