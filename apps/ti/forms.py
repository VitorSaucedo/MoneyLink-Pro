from django import forms
from .models import (
    TipoPeriferico, 
    Periferico, 
    PosicaoAtendimento, 
    AtribuicaoFuncionarioPA, 
    AtribuicaoPerifericoPA,
    Sala,
    Ilha
)
from apps.funcionarios.models import Funcionario

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
        fields = ['tipo', 'marca', 'modelo', 'data_aquisicao', 'status', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'data_aquisicao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

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
            'data_atribuicao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.ativo = True
        instance.data_remocao = None
        
        if commit:
            periferico = instance.periferico
            periferico.status = 'em_uso'
            periferico.save()
            
            instance.save()
            
        return instance 