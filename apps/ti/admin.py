from django.contrib import admin
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
    Monitor,
    AtribuicaoMonitorPA
)

# Classes base e inlines
class TIModelAdmin(admin.ModelAdmin):
    """Classe base para todos os admin models do módulo TI"""
    list_per_page = 25
    show_full_result_count = True
    save_on_top = True

# Inlines para as atribuições
class AtribuicaoComputadorPAInline(admin.TabularInline):
    model = AtribuicaoComputadorPA
    extra = 0
    fields = ('posicao_atendimento', 'data_remocao', 'ativo')
    readonly_fields = ('data_atribuicao',)
    autocomplete_fields = ['posicao_atendimento']
    verbose_name = "Atribuição a PA"
    verbose_name_plural = "Atribuições a PAs"

class AtribuicaoPerifericoPAInline(admin.TabularInline):
    model = AtribuicaoPerifericoPA
    extra = 0
    fields = ('posicao_atendimento', 'data_atribuicao', 'data_remocao', 'ativo')
    autocomplete_fields = ['posicao_atendimento']
    verbose_name = "Atribuição a PA"
    verbose_name_plural = "Atribuições a PAs"

class AtribuicaoMonitorPAInline(admin.TabularInline):
    model = AtribuicaoMonitorPA
    extra = 0
    fields = ('posicao_atendimento', 'data_remocao', 'ativo')
    readonly_fields = ('data_atribuicao',)
    autocomplete_fields = ['posicao_atendimento']
    verbose_name = "Atribuição a PA"
    verbose_name_plural = "Atribuições a PAs"

class AtribuicaoFuncionarioPAInline(admin.TabularInline):
    model = AtribuicaoFuncionarioPA
    extra = 0
    fields = ('funcionario', 'data_inicio', 'data_fim', 'ativo')
    autocomplete_fields = ['funcionario']
    verbose_name = "Funcionário atribuído"
    verbose_name_plural = "Funcionários atribuídos"

class IlhaPAInline(admin.TabularInline):
    model = PosicaoAtendimento
    fields = ('numero', 'status', 'funcionario_atual')
    readonly_fields = ('funcionario_atual',)
    extra = 0
    verbose_name = "PA na ilha"
    verbose_name_plural = "PAs nesta ilha"
    show_change_link = True

class SalaIlhaInline(admin.TabularInline):
    model = Ilha
    fields = ('nome', 'quantidade_pas')
    extra = 0
    verbose_name = "Ilha na sala"
    verbose_name_plural = "Ilhas nesta sala"
    show_change_link = True

# Admin para Tipos de Periféricos
@admin.register(TipoPeriferico)
class TipoPerifericoAdmin(TIModelAdmin):
    list_display = ('id', 'nome', 'descricao')
    search_fields = ('nome',)

# Admin para Periféricos com atribuições embutidas
@admin.register(Periferico)
class PerifericoAdmin(TIModelAdmin):
    list_display = ('id', 'tipo', 'marca', 'modelo', 'numero_serie', 'status')
    list_filter = ('tipo', 'status', 'marca')
    search_fields = ('marca', 'modelo', 'numero_serie')
    inlines = [AtribuicaoPerifericoPAInline]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo', 'marca', 'modelo', 'numero_serie')
        }),
        ('Condição e Estado', {
            'fields': ('condicao', 'estado', 'status')
        }),
        ('Localização', {
            'fields': ('loja', 'quantidade')
        }),
        ('Detalhes', {
            'fields': ('data_aquisicao', 'observacoes'),
            'classes': ('collapse',)
        }),
    )

# Admin para Salas com ilhas embutidas
@admin.register(Sala)
class SalaAdmin(TIModelAdmin):
    list_display = ('id', 'nome', 'loja', 'setor', 'descricao', 'contagem_ilhas', 'contagem_total_pas')
    search_fields = ('nome', 'loja__nome', 'setor__nome')
    list_filter = ('loja', 'setor')
    inlines = [SalaIlhaInline]
    
    def contagem_ilhas(self, obj):
        return obj.ilhas.count()
    contagem_ilhas.short_description = 'Ilhas'
    
    def contagem_total_pas(self, obj):
        return PosicaoAtendimento.objects.filter(ilha__sala=obj).count()
    contagem_total_pas.short_description = 'Total de PAs'

# Admin para Ilhas com PAs embutidas
@admin.register(Ilha)
class IlhaAdmin(TIModelAdmin):
    list_display = ('id', 'nome', 'sala', 'get_loja', 'quantidade_pas', 'contagem_pas')
    search_fields = ('nome', 'sala__nome', 'sala__loja__nome')
    list_filter = ('sala__loja', 'sala')
    inlines = [IlhaPAInline]
    
    def get_loja(self, obj):
        return obj.sala.loja if obj.sala and obj.sala.loja else '-'
    get_loja.short_description = 'Loja'
    get_loja.admin_order_field = 'sala__loja__nome'
    
    def contagem_pas(self, obj):
        return obj.posicoes_atendimento.count()
    contagem_pas.short_description = 'PAs Cadastradas'

# Admin para PAs com atribuições embutidas
@admin.register(PosicaoAtendimento)
class PosicaoAtendimentoAdmin(TIModelAdmin):
    list_display = ('id', 'numero', 'ilha', 'sala', 'get_loja', 'funcionario_atual', 'status')
    list_filter = ('status', 'sala__loja', 'sala', 'ilha')
    search_fields = ('numero', 'ilha__nome', 'sala__nome', 'sala__loja__nome')
    inlines = [AtribuicaoFuncionarioPAInline, AtribuicaoPerifericoPAInline, AtribuicaoComputadorPAInline, AtribuicaoMonitorPAInline]
    
    def get_loja(self, obj):
        return obj.loja
    get_loja.short_description = 'Loja'
    get_loja.admin_order_field = 'sala__loja__nome'

# Admin para Computadores com atribuições embutidas
@admin.register(Computador)
class ComputadorAdmin(TIModelAdmin):
    list_display = ('id', 'marca', 'modelo', 'condicao', 'estado', 'quantidade', 'loja', 'status', 'pa_atual')
    list_filter = ('status', 'condicao', 'estado', 'loja', 'marca')
    search_fields = ('marca', 'modelo', 'numero_serie', 'observacoes')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('marca', 'modelo', 'numero_serie')
        }),
        ('Condição e Estado', {
            'fields': ('condicao', 'estado', 'status')
        }),
        ('Localização', {
            'fields': ('loja', 'quantidade')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )
    inlines = [AtribuicaoComputadorPAInline]
    
    def pa_atual(self, obj):
        atrib = AtribuicaoComputadorPA.objects.filter(computador=obj, ativo=True).first()
        if atrib:
            return atrib.posicao_atendimento
        return "-"
    pa_atual.short_description = 'PA Atual'

# Admin para Monitores com atribuições embutidas
@admin.register(Monitor)
class MonitorAdmin(TIModelAdmin):
    list_display = ('id', 'marca', 'modelo', 'tamanho', 'condicao', 'estado', 'loja', 'status', 'pa_atual')
    list_filter = ('status', 'condicao', 'estado', 'loja', 'marca')
    search_fields = ('marca', 'modelo', 'numero_serie', 'tamanho', 'resolucao', 'observacoes')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('marca', 'modelo', 'numero_serie')
        }),
        ('Especificações', {
            'fields': ('tamanho', 'resolucao')
        }),
        ('Condição e Estado', {
            'fields': ('condicao', 'estado', 'status')
        }),
        ('Localização', {
            'fields': ('loja',)
        }),
        ('Detalhes', {
            'fields': ('data_aquisicao', 'observacoes'),
            'classes': ('collapse',)
        }),
    )
    inlines = [AtribuicaoMonitorPAInline]
    
    def pa_atual(self, obj):
        from .models import AtribuicaoMonitorPA
        atrib = AtribuicaoMonitorPA.objects.filter(monitor=obj, ativo=True).first()
        if atrib:
            return atrib.posicao_atendimento
        return "-"
    pa_atual.short_description = 'PA Atual'

# Removendo os registros individuais das atribuições que agora são inlines
# Não registrar estes modelos diretamente no admin
# admin.site.unregister(AtribuicaoFuncionarioPA)
# admin.site.unregister(AtribuicaoPerifericoPA)
# admin.site.unregister(AtribuicaoComputadorPA)
