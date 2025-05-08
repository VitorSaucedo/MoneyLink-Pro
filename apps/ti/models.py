from django.db import models
from apps.funcionarios.models import Funcionario

# Create your models here.

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

class Sala(models.Model):
    nome = models.CharField(max_length=100)
    andar = models.CharField(max_length=20, blank=True, null=True)
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
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"PA {self.numero} - {self.ilha} ({self.sala})"
    
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
    
    def __str__(self):
        return f"{self.funcionario} - {self.posicao_atendimento}"
    
    class Meta:
        verbose_name = 'Atribuição de Funcionário a PA'
        verbose_name_plural = 'Atribuições de Funcionários a PAs'

class AtribuicaoPerifericoPA(models.Model):
    periferico = models.ForeignKey(Periferico, on_delete=models.CASCADE)
    posicao_atendimento = models.ForeignKey(PosicaoAtendimento, on_delete=models.CASCADE)
    data_atribuicao = models.DateField()
    data_remocao = models.DateField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.periferico} - {self.posicao_atendimento}"
    
    class Meta:
        verbose_name = 'Atribuição de Periférico a PA'
        verbose_name_plural = 'Atribuições de Periféricos a PAs'
