from django.db import models
from apps.funcionarios.models import *
from django.utils import timezone

# Create your models here.
# Nota: A classe Loja agora é importada de apps.funcionarios.models

class TipoPeriferico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Tipo de Periférico'
        verbose_name_plural = 'Tipos de Periféricos'

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
    status = models.CharField(max_length=20, choices=status_choices, default='disponivel')
    observacoes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.tipo} - {self.marca} {self.modelo}"
    
    class Meta:
        verbose_name = 'Periférico'
        verbose_name_plural = 'Periféricos'

class Computador(models.Model):
    marca = models.CharField(max_length=100)
    quantidade = models.PositiveIntegerField(default=1)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, null=True, blank=True, related_name='computadores')
    status_choices = [
        ('disponivel', 'Disponível'),
        ('em_uso', 'Em Uso'),
        ('manutencao', 'Em Manutenção'),
        ('inativo', 'Inativo')
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='disponivel')
    observacoes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.marca}"
    
    class Meta:
        verbose_name = 'Computador'
        verbose_name_plural = 'Computadores'

class Sala(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'

class Ilha(models.Model):
    nome = models.CharField(max_length=100)
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='ilhas')
    quantidade_pas = models.PositiveIntegerField(default=1)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.nome} - {self.sala}"
    
    class Meta:
        verbose_name = 'Ilha'
        verbose_name_plural = 'Ilhas'

class PosicaoAtendimento(models.Model):
    numero = models.CharField(max_length=20)
    ilha = models.ForeignKey(Ilha, on_delete=models.CASCADE, related_name='posicoes_atendimento', null=True, blank=True)
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, null=True, blank=True)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True)
    status_choices = [
        ('livre', 'Livre'),
        ('ocupada', 'Ocupada'),
        ('manutencao', 'Em Manutenção'),
        ('inativa', 'Inativa')
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='livre')
    observacoes = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Se não tiver número, atribui automaticamente baseado na ilha
        if not self.numero and self.ilha:
            pas_na_ilha = PosicaoAtendimento.objects.filter(ilha=self.ilha).count()
            self.numero = f"{pas_na_ilha + 1:02d}"
        
        # Adicionar lógica para garantir que sala da PA seja a mesma da ilha, se ilha estiver definida
        if self.ilha and self.sala != self.ilha.sala:
            self.sala = self.ilha.sala
        super().save(*args, **kwargs)
    
    def __str__(self):
        # Ajustar para caso ilha ou sala sejam None inicialmente
        ilha_nome = self.ilha.nome if self.ilha else "S/ Ilha"
        sala_nome = self.sala.nome if self.sala else "S/ Sala"
        return f"PA {self.numero} - {ilha_nome} ({sala_nome})"
    
    class Meta:
        verbose_name = 'Posição de Atendimento'
        verbose_name_plural = 'Posições de Atendimento'
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
        verbose_name = 'Atribuição de Funcionário a PA'
        verbose_name_plural = 'Atribuições de Funcionários a PAs'

class AtribuicaoPerifericoPA(models.Model):
    periferico = models.ForeignKey(Periferico, on_delete=models.CASCADE)
    posicao_atendimento = models.ForeignKey(PosicaoAtendimento, on_delete=models.CASCADE)
    data_atribuicao = models.DateTimeField()
    data_remocao = models.DateTimeField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.periferico} - {self.posicao_atendimento}"
    
    class Meta:
        verbose_name = 'Atribuição de Periférico a PA'
        verbose_name_plural = 'Atribuições de Periféricos a PAs'

class AtribuicaoComputadorPA(models.Model):
    computador = models.ForeignKey(Computador, on_delete=models.CASCADE)
    posicao_atendimento = models.ForeignKey(PosicaoAtendimento, on_delete=models.CASCADE)
    data_atribuicao = models.DateTimeField(auto_now_add=True)
    data_remocao = models.DateTimeField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.computador} - {self.posicao_atendimento}"
    
    class Meta:
        verbose_name = 'Atribuição de Computador a PA'
        verbose_name_plural = 'Atribuições de Computadores a PAs'
