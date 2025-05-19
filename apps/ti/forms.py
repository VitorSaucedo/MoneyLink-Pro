from django import forms
from django.utils import timezone
from .models import (
    TipoPeriferico, 
    Periferico, 
    PosicaoAtendimento, 
    AtribuicaoFuncionarioPA, 
    AtribuicaoPerifericoPA,
    Sala,
    Ilha,
    Computador,
    AtribuicaoComputadorPA
)
from apps.funcionarios.models import Funcionario
from .utils import atribuir_item_pa, desatribuir_item_pa, verificar_disponibilidade_periferico, verificar_disponibilidade_computador

class TipoPerifericoForm(forms.ModelForm):
    class Meta:
        model = TipoPeriferico
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PerifericoForm(forms.ModelForm):
    class Meta:
        model = Periferico
        fields = ['tipo', 'marca', 'modelo', 'data_aquisicao', 'quantidade', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'data_aquisicao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.quantidade > 0:
            instance.status = 'disponivel'
        else:
            instance.status = 'inativo'
        
        if commit:
            instance.save()
        return instance

class SalaForm(forms.ModelForm):
    class Meta:
        model = Sala
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class IlhaForm(forms.ModelForm):
    class Meta:
        model = Ilha
        fields = ['nome', 'sala', 'quantidade_pas', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sala': forms.Select(attrs={'class': 'form-control'}),
            'quantidade_pas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PosicaoAtendimentoForm(forms.ModelForm):
    class Meta:
        model = PosicaoAtendimento
        fields = ['numero', 'sala', 'ilha', 'funcionario', 'status', 'observacoes']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'sala': forms.Select(attrs={'class': 'form-control'}),
            'ilha': forms.Select(attrs={'class': 'form-control'}),
            'funcionario': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero'].required = False
        if 'ilha' in self.data:
            try:
                ilha_id = int(self.data.get('ilha'))
                self.fields['numero'].help_text = "Deixe em branco para numeração automática baseada na ilha."
            except (ValueError, TypeError):
                pass

class AtribuicaoFuncionarioPAForm(forms.ModelForm):
    class Meta:
        model = AtribuicaoFuncionarioPA
        fields = ['funcionario', 'posicao_atendimento', 'data_inicio', 'data_fim', 'ativo']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-control'}),
            'posicao_atendimento': forms.Select(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AtribuicaoPerifericoPAForm(forms.ModelForm):
    class Meta:
        model = AtribuicaoPerifericoPA
        fields = ['periferico', 'posicao_atendimento', 'data_atribuicao']
        widgets = {
            'periferico': forms.Select(attrs={'class': 'form-control'}),
            'posicao_atendimento': forms.Select(attrs={'class': 'form-control'}),
            'data_atribuicao': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        periferico = cleaned_data.get('periferico')
        posicao_atendimento = cleaned_data.get('posicao_atendimento')
        
        if periferico and posicao_atendimento:
            # Verificar disponibilidade do periférico
            disponivel, mensagem = verificar_disponibilidade_periferico(
                periferico.id, 
                pa_id=self.instance.posicao_atendimento.id if self.instance.pk else None
            )
            
            if not disponivel:
                self.add_error('periferico', mensagem)
        
        return cleaned_data
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Se estamos atualizando, retornamos a instância normalmente
        if self.instance.pk:
            if commit:
                instance.save()
            return instance
        
        # Se estamos criando, usamos nossa função auxiliar
        if commit:
            # Usar a função auxiliar para atribuir o periférico à PA
            atribuicao, _ = atribuir_item_pa(
                item=self.cleaned_data['periferico'],
                pa=self.cleaned_data['posicao_atendimento'],
                model_atribuicao=AtribuicaoPerifericoPA,
                data_atribuicao=self.cleaned_data.get('data_atribuicao') or timezone.now()
            )
            return atribuicao
        else:
            # Definir valores básicos para retornar a instância não salva
            instance.data_atribuicao = self.cleaned_data.get('data_atribuicao') or timezone.now()
            instance.ativo = True
            return instance

class ComputadorForm(forms.ModelForm):
    class Meta:
        model = Computador
        fields = ['marca', 'quantidade', 'status', 'observacoes']
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AtribuicaoComputadorPAForm(forms.ModelForm):
    class Meta:
        model = AtribuicaoComputadorPA
        fields = ['computador', 'posicao_atendimento']
        widgets = {
            'computador': forms.Select(attrs={'class': 'form-control'}),
            'posicao_atendimento': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        computador = cleaned_data.get('computador')
        posicao_atendimento = cleaned_data.get('posicao_atendimento')
        
        if computador and posicao_atendimento:
            # Verificar disponibilidade do computador
            disponivel, mensagem = verificar_disponibilidade_computador(
                computador.id, 
                pa_id=self.instance.posicao_atendimento.id if self.instance.pk else None
            )
            
            if not disponivel:
                self.add_error('computador', mensagem)
        
        return cleaned_data
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Se estamos atualizando, retornamos a instância normalmente
        if self.instance.pk:
            if commit:
                instance.save()
            return instance
        
        # Se estamos criando, usamos nossa função auxiliar
        if commit:
            # Usar a função auxiliar para atribuir o computador à PA
            atribuicao, _ = atribuir_item_pa(
                item=self.cleaned_data['computador'],
                pa=self.cleaned_data['posicao_atendimento'],
                model_atribuicao=AtribuicaoComputadorPA
            )
            return atribuicao
        else:
            # Definir valores básicos para retornar a instância não salva
            instance.data_atribuicao = timezone.now()
            instance.ativo = True
            return instance