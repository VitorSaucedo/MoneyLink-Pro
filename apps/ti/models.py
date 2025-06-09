from django.db import models
from apps.funcionarios.models import Funcionario, Loja, Setor  # Importação específica em vez de "*"
from django.utils import timezone

# Create your models here.
# Nota: A classe Loja agora é importada de apps.funcionarios.models

class TipoPeriferico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Tipo'
        verbose_name_plural = 'Periféricos - Tipos'

class Periferico(models.Model):
    tipo = models.ForeignKey(TipoPeriferico, on_delete=models.CASCADE)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    data_aquisicao = models.DateField(blank=True, null=True)
    quantidade = models.PositiveIntegerField(default=1)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='perifericos')
    status_choices = [
        ('disponivel', 'Disponível'),
        ('em_uso', 'Em Uso'),
        ('manutencao', 'Em Manutenção'),
        ('inativo', 'Inativo')
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='disponivel', verbose_name="Status")
    
    # Campos do fluxograma
    condicao_choices = [
        ('novo', 'Novo'),
        ('antigo', 'Antigo')
    ]
    condicao = models.CharField(max_length=20, choices=condicao_choices, default='novo', verbose_name="Condição")
    
    estado_choices = [
        ('funcionando', 'Funcionando'),
        ('com_defeito', 'Com Defeito'),
        ('em_reparo', 'Em Reparo')
    ]
    estado = models.CharField(max_length=20, choices=estado_choices, default='funcionando', verbose_name="Estado")
    
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    def __str__(self):
        return f"{self.tipo} - {self.marca} {self.modelo}"
    
    class Meta:
        verbose_name = 'Periférico'
        verbose_name_plural = 'Periféricos'

class Computador(models.Model):
    marca = models.CharField(max_length=100, verbose_name="Marca")
    modelo = models.CharField(max_length=100, default='Não Informado', verbose_name="Modelo")
    numero_serie = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de Série")
    quantidade = models.PositiveIntegerField(default=1)
    
    # Campos do fluxograma
    condicao_choices = [
        ('novo', 'Novo'),
        ('antigo', 'Antigo')
    ]
    condicao = models.CharField(max_length=20, choices=condicao_choices, default='novo', verbose_name="Condição")
    
    estado_choices = [
        ('funcionando', 'Funcionando'),
        ('com_defeito', 'Com Defeito'),
        ('em_reparo', 'Em Reparo')
    ]
    estado = models.CharField(max_length=20, choices=estado_choices, default='funcionando', verbose_name="Estado")
    
    status_choices = [
        ('disponivel', 'Disponível'),
        ('em_uso', 'Em Uso'),
        ('manutencao', 'Em Manutenção'),
        ('inativo', 'Inativo')
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='disponivel', verbose_name="Status")
    
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, null=True, blank=True, related_name='computadores')
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    def __str__(self):
        return f"{self.marca} {self.modelo}" if self.modelo else self.marca
    
    class Meta:
        verbose_name = 'Computador'
        verbose_name_plural = 'Computadores'

class Monitor(models.Model):
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    marca = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca")
    numero_serie = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de Série")
    tamanho = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tamanho")  # Ex: "24", "27"
    resolucao = models.CharField(max_length=50, blank=True, null=True, verbose_name="Resolução")  # Ex: "1920x1080"
    
    # Campos do fluxograma
    condicao_choices = [
        ('novo', 'Novo'),
        ('antigo', 'Antigo')
    ]
    condicao = models.CharField(max_length=20, choices=condicao_choices, default='novo', verbose_name="Condição")
    
    estado_choices = [
        ('funcionando', 'Funcionando'),
        ('com_defeito', 'Com Defeito'),
        ('em_reparo', 'Em Reparo')
    ]
    estado = models.CharField(max_length=20, choices=estado_choices, default='funcionando', verbose_name="Estado")
    
    status_choices = [
        ('disponivel', 'Disponível'),
        ('em_uso', 'Em Uso'),
        ('manutencao', 'Em Manutenção'),
        ('inativo', 'Inativo')
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='disponivel', verbose_name="Status")
    
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='monitores')
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    data_aquisicao = models.DateField(blank=True, null=True, verbose_name="Data de Aquisição")
    
    def __str__(self):
        return f"{self.marca} {self.modelo}" if self.marca else self.modelo
    
    class Meta:
        verbose_name = 'Monitor'
        verbose_name_plural = 'Monitores'

class Sala(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    titulo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Título")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='salas', null=True)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name='salas_ti', null=True, blank=True, verbose_name="Setor")
    funcionario_responsavel = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='salas_responsavel', verbose_name="Funcionário Responsável")
    
    @property
    def status(self):
        return self.loja.status if self.loja else False
    
    def __str__(self):
        loja_nome = self.loja.nome if self.loja else "S/ Loja"
        return f"{self.nome} ({loja_nome})"
    
    class Meta:
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'

class Ilha(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    titulo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Título")
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='ilhas')
    quantidade_pas = models.PositiveIntegerField(default=1, verbose_name="Quantidade de PAs")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    funcionario_responsavel = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='ilhas_responsavel', verbose_name="Funcionário Responsável")
    
    @property
    def loja(self):
        return self.sala.loja if self.sala else None
    
    @property
    def setor(self):
        return self.sala.setor if self.sala else None
    
    @property
    def status(self):
        return self.sala.loja.status if self.sala and self.sala.loja else False
    
    def __str__(self):
        sala_nome = self.sala.nome if self.sala else "S/ Sala"
        loja_nome = self.sala.loja.nome if self.sala and self.sala.loja else "S/ Loja"
        return f"{self.nome} - {sala_nome} ({loja_nome})"
    
    class Meta:
        verbose_name = 'Ilha'
        verbose_name_plural = 'Ilhas'

class PosicaoAtendimento(models.Model):
    numero = models.CharField(max_length=20, verbose_name="Número")
    titulo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Título")
    ilha = models.ForeignKey(Ilha, on_delete=models.CASCADE, related_name='posicoes_atendimento', null=True, blank=True)
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, null=True, blank=True)
    status_choices = [
        ('livre', 'Livre'),
        ('ocupada', 'Ocupada'),
        ('manutencao', 'Em Manutenção'),
        ('inativa', 'Inativa')
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='livre', verbose_name="Status")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    def save(self, *args, **kwargs):
        # Se não tiver número, atribui automaticamente baseado na ilha
        if not self.numero and self.ilha:
            pas_na_ilha = PosicaoAtendimento.objects.filter(ilha=self.ilha).count()
            self.numero = f"{pas_na_ilha + 1:02d}"
        
        # Adicionar lógica para garantir que sala da PA seja a mesma da ilha, se ilha estiver definida
        if self.ilha and self.sala != self.ilha.sala:
            self.sala = self.ilha.sala
        super().save(*args, **kwargs)
    
    @property
    def loja(self):
        if self.sala and self.sala.loja:
            return self.sala.loja
        elif self.ilha and self.ilha.sala and self.ilha.sala.loja:
            return self.ilha.sala.loja
        return None
    
    @property  
    def setor(self):
        if self.sala and self.sala.setor:
            return self.sala.setor
        elif self.ilha and self.ilha.sala and self.ilha.sala.setor:
            return self.ilha.sala.setor
        return None
    
    @property
    def funcionario_atual(self):
        """Retorna o funcionário atualmente atribuído a esta posição de atendimento, se existir"""
        atribuicao = self.atribuicaofuncionariopa_set.filter(ativo=True).order_by('-data_inicio').first()
        return atribuicao.funcionario if atribuicao else None
    
    def __str__(self):
        # Ajustar para caso ilha ou sala sejam None inicialmente
        ilha_nome = self.ilha.nome if self.ilha else "S/ Ilha"
        sala_nome = self.sala.nome if self.sala else "S/ Sala"
        return f"PA {self.numero} - {ilha_nome} ({sala_nome})"
    
    class Meta:
        verbose_name = 'PA'
        verbose_name_plural = 'PAs'
        ordering = ['ilha', 'numero']

class AtribuicaoFuncionarioPA(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    posicao_atendimento = models.ForeignKey(PosicaoAtendimento, on_delete=models.CASCADE)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        # Se a atribuição está sendo marcada como ativa e não tem data de início, define agora.
        if self.ativo and not self.data_inicio:
            self.data_inicio = timezone.now().date() # Para DateField
        
        # Se a atribuição está sendo inativada e não tem data de fim, define agora.
        if not self.ativo and self.data_fim is None:
            self.data_fim = timezone.now().date() # Para DateField
        
        # Se está reativando uma atribuição que tinha data_fim, limpar data_fim.
        if self.ativo and self.data_fim is not None:
            self.data_fim = None
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "Ativa" if self.ativo else f"Finalizada em {self.data_fim.strftime('%d/%m/%Y') if self.data_fim else '-'}"
        # Garante que self.funcionario e self.posicao_atendimento não causem erro se forem None (improvável com ForeignKey)
        func_str = str(self.funcionario) if self.funcionario else "Funcionário não definido"
        pa_str = str(self.posicao_atendimento) if self.posicao_atendimento else "PA não definida"
        return f"{func_str} - {pa_str} ({status})"
    
    class Meta:
        verbose_name = 'Atribuição de Funcionário'
        verbose_name_plural = 'PAs - Atribuições de Funcionários'

class AtribuicaoPerifericoPA(models.Model):
    periferico = models.ForeignKey(Periferico, on_delete=models.CASCADE)
    posicao_atendimento = models.ForeignKey(PosicaoAtendimento, on_delete=models.CASCADE)
    data_atribuicao = models.DateTimeField()
    data_remocao = models.DateTimeField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        # Se não tem data de atribuição, define para agora
        if not self.data_atribuicao:
            self.data_atribuicao = timezone.now()
        
        # Se está inativando e não tem data de remoção, define para agora
        if not self.ativo and self.data_remocao is None:
            self.data_remocao = timezone.now()
            
        # Se está reativando, limpa a data de remoção
        if self.ativo and self.data_remocao is not None:
            self.data_remocao = None
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "Ativo" if self.ativo else f"Removido em {self.data_remocao.strftime('%d/%m/%Y %H:%M') if self.data_remocao else '-'}"
        return f"{self.periferico} - {self.posicao_atendimento} ({status})"
    
    class Meta:
        verbose_name = 'Atribuição de Periférico'
        verbose_name_plural = 'Periféricos - Atribuições'

class AtribuicaoComputadorPA(models.Model):
    computador = models.ForeignKey(Computador, on_delete=models.CASCADE)
    posicao_atendimento = models.ForeignKey(PosicaoAtendimento, on_delete=models.CASCADE)
    data_atribuicao = models.DateTimeField(auto_now_add=True)
    data_remocao = models.DateTimeField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        # Se está inativando e não tem data de remoção, define para agora
        if not self.ativo and self.data_remocao is None:
            self.data_remocao = timezone.now()
            
        # Se está reativando, limpa a data de remoção
        if self.ativo and self.data_remocao is not None:
            self.data_remocao = None
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "Ativo" if self.ativo else f"Removido em {self.data_remocao.strftime('%d/%m/%Y %H:%M') if self.data_remocao else '-'}"
        return f"{self.computador} - {self.posicao_atendimento} ({status})"
    
    class Meta:
        verbose_name = 'Atribuição de Computador'
        verbose_name_plural = 'Computadores - Atribuições'

class AtribuicaoMonitorPA(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE)
    posicao_atendimento = models.ForeignKey(PosicaoAtendimento, on_delete=models.CASCADE)
    data_atribuicao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Atribuição")
    data_remocao = models.DateTimeField(blank=True, null=True, verbose_name="Data de Remoção")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    def save(self, *args, **kwargs):
        # Se está inativando e não tem data de remoção, define para agora
        if not self.ativo and self.data_remocao is None:
            self.data_remocao = timezone.now()
            
        # Se está reativando, limpa a data de remoção
        if self.ativo and self.data_remocao is not None:
            self.data_remocao = None
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "Ativo" if self.ativo else f"Removido em {self.data_remocao.strftime('%d/%m/%Y %H:%M') if self.data_remocao else '-'}"
        return f"{self.monitor} - {self.posicao_atendimento} ({status})"
    
    class Meta:
        verbose_name = 'Atribuição de Monitor'
        verbose_name_plural = 'Monitores - Atribuições'
