from django.contrib import admin
from django.db.models import Q
from apps.funcionarios.models import Funcionario
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
    AtribuicaoMonitorPA,
    Chip,
    Email
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
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "funcionario":
            kwargs["queryset"] = Funcionario.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
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

# Admin para Chips com informações de ramal
@admin.register(Chip)
class ChipAdmin(TIModelAdmin):
    list_display = ('id', 'numero', 'get_funcionario_nome', 'get_ramal_readonly', 'get_setor_readonly', 'status', 'data_entrega')
    list_filter = ('status', 'funcionario__loja', 'funcionario__setor')
    search_fields = ('numero', 'funcionario__nome_completo')
    autocomplete_fields = ['funcionario']
    
    fieldsets = (
        ('Informações do Chip', {
            'fields': ('numero', 'status')
        }),
        ('Atribuições', {
            'fields': ('funcionario', 'get_ramal_readonly', 'get_setor_readonly')
        }),
        ('Datas', {
            'fields': ('data_entrega', 'data_banimento'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('get_ramal_readonly', 'get_setor_readonly')
    
    def get_funcionario_nome(self, obj):
        if obj.funcionario:
            return obj.funcionario.nome_completo
        return "-"
    get_funcionario_nome.short_description = 'Funcionário'
    get_funcionario_nome.admin_order_field = 'funcionario__nome_completo'
    
    def get_ramal_funcionario(self, obj):
        if obj.ramal:
            ramal_info = f"{obj.ramal.ramal}" if obj.ramal.ramal else "S/ Ramal"
            return f"{obj.ramal.nome_completo} ({ramal_info})"
        return "-"
    get_ramal_funcionario.short_description = 'Funcionário (Ramal)'
    get_ramal_funcionario.admin_order_field = 'ramal__nome_completo'
    
    def get_setor_funcionario(self, obj):
        if obj.setor:
            return f"{obj.setor.nome_completo} - {obj.setor.setor.nome if obj.setor.setor else 'S/ Setor'}"
        return "-"
    get_setor_funcionario.short_description = 'Funcionário do Setor'
    get_setor_funcionario.admin_order_field = 'setor__nome_completo'
    
    def get_ramal_readonly(self, obj):
        if obj.funcionario and obj.funcionario.ramal:
            return obj.funcionario.ramal
        return "Sem ramal"
    get_ramal_readonly.short_description = 'Ramal'
    
    def get_setor_readonly(self, obj):
        if obj.funcionario and obj.funcionario.setor:
            return obj.funcionario.setor.nome
        return "Sem setor"
    get_setor_readonly.short_description = 'Setor'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "funcionario":
            # Personaliza o queryset e a exibição para mostrar apenas o nome completo
            kwargs["queryset"] = Funcionario.objects.all().order_by('nome_completo')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Admin personalizado para visualizar ramais dos funcionários
class RamalFuncionarioProxy(Funcionario):
    """Proxy model para administrar ramais dos funcionários"""
    class Meta:
        proxy = True
        verbose_name = 'Ramal de Funcionário'
        verbose_name_plural = 'Ramais dos Funcionários'

@admin.register(RamalFuncionarioProxy)
class RamalFuncionarioAdmin(TIModelAdmin):
    list_display = ('id', 'nome_completo', 'ramal', 'loja', 'setor', 'cargo', 'status', 'get_chips_count')
    list_filter = ('status', 'loja', 'setor', 'cargo')
    search_fields = ('nome_completo', 'ramal', 'cpf')
    ordering = ['ramal', 'nome_completo']
    
    # Filtrar apenas funcionários que têm ramal
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(Q(ramal__isnull=False) & ~Q(ramal=''))
    
    fieldsets = (
        ('Informações do Funcionário', {
            'fields': ('nome_completo', 'cpf', 'foto')
        }),
        ('Ramal e Contato', {
            'fields': ('ramal', 'celular1', 'celular2')
        }),
        ('Localização Profissional', {
            'fields': ('loja', 'setor', 'cargo', 'departamento')
        }),
        ('Status', {
            'fields': ('status', 'data_admissao', 'data_demissao')
        }),
    )
    
    readonly_fields = ('nome_completo', 'cpf', 'foto', 'celular1', 'celular2', 
                      'loja', 'setor', 'cargo', 'departamento', 'status', 
                      'data_admissao', 'data_demissao')
    
    def get_chips_count(self, obj):
        chips_ramal = obj.chips_ramal.count()
        chips_setor = obj.chips_setor.count()
        total = chips_ramal + chips_setor
        if total > 0:
            return f"{total} ({chips_ramal} ramal, {chips_setor} setor)"
        return "0"
    get_chips_count.short_description = 'Chips Atribuídos'
    
    def has_add_permission(self, request):
        # Não permitir adicionar novos através desta interface
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Não permitir deletar através desta interface
        return False

# Admin para Emails
@admin.register(Email)
class EmailAdmin(TIModelAdmin):
    list_display = ('id', 'email', 'get_funcionario_nome', 'get_ramal_info', 'tipo', 'status', 'data_criacao')
    list_filter = ('status', 'tipo', 'funcionario__loja', 'funcionario__setor')
    search_fields = ('email', 'funcionario__nome_completo', 'ramal__nome_completo', 'setor__nome_completo')
    autocomplete_fields = ['funcionario', 'ramal', 'setor']
    
    fieldsets = (
        ('Informações do E-mail', {
            'fields': ('email', 'senha', 'tipo', 'status')
        }),
        ('Atribuições', {
            'fields': ('funcionario', 'ramal', 'setor')
        }),
        ('E-mail de Recuperação', {
            'fields': ('email_recuperacao',),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('data_criacao', 'data_atualizacao')
    
    def get_funcionario_nome(self, obj):
        if obj.funcionario:
            return obj.funcionario.nome_completo
        return "-"
    get_funcionario_nome.short_description = 'Funcionário'
    get_funcionario_nome.admin_order_field = 'funcionario__nome_completo'
    
    def get_ramal_info(self, obj):
        if obj.ramal:
            ramal_info = f"({obj.ramal.ramal})" if obj.ramal.ramal else "(S/ Ramal)"
            return f"{obj.ramal.nome_completo} {ramal_info}"
        return "-"
    get_ramal_info.short_description = 'Ramal'
    get_ramal_info.admin_order_field = 'ramal__nome_completo'

# Removendo os registros individuais das atribuições que agora são inlines
# Não registrar estes modelos diretamente no admin
# admin.site.unregister(AtribuicaoFuncionarioPA)
# admin.site.unregister(AtribuicaoPerifericoPA)
# admin.site.unregister(AtribuicaoComputadorPA)
