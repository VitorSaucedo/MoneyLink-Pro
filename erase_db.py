#!/usr/bin/env python
"""
Script para limpar os dados dos módulos de TI e Funcionários do sistema MoneyLink-Pro.
Este script remove todos os dados criados pelo script populate.py.
"""
import os
import sys
import django
from datetime import datetime

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

# Importar os modelos após configurar o ambiente
from django.contrib.auth.models import User
from apps.funcionarios.models import (
    Empresa, Loja, Departamento, Setor, Cargo, Equipe, HorarioTrabalho, Funcionario,
    ArquivoFuncionario, Comissionamento
)
from apps.ti.models import (
    TipoPeriferico, Periferico, Computador, Sala, Ilha, PosicaoAtendimento,
    AtribuicaoFuncionarioPA, AtribuicaoPerifericoPA, AtribuicaoComputadorPA
)

def limpar_modulo_ti():
    """Limpa todos os dados do módulo de TI"""
    print("Limpando dados do módulo TI...")
    
    # Limpar atribuições (primeiro as dependências)
    print("  Removendo atribuições...")
    count_atrib_comp = AtribuicaoComputadorPA.objects.all().count()
    AtribuicaoComputadorPA.objects.all().delete()
    
    count_atrib_perif = AtribuicaoPerifericoPA.objects.all().count()
    AtribuicaoPerifericoPA.objects.all().delete()
    
    count_atrib_func = AtribuicaoFuncionarioPA.objects.all().count()
    AtribuicaoFuncionarioPA.objects.all().delete()
    
    # Limpar PAs
    print("  Removendo posições de atendimento...")
    count_pas = PosicaoAtendimento.objects.all().count()
    PosicaoAtendimento.objects.all().delete()
    
    # Limpar ilhas e salas
    print("  Removendo ilhas e salas...")
    count_ilhas = Ilha.objects.all().count()
    Ilha.objects.all().delete()
    
    count_salas = Sala.objects.all().count()
    Sala.objects.all().delete()
    
    # Limpar periféricos e tipos
    print("  Removendo periféricos...")
    count_perif = Periferico.objects.all().count()
    Periferico.objects.all().delete()
    
    count_tipos = TipoPeriferico.objects.all().count()
    TipoPeriferico.objects.all().delete()
    
    # Limpar computadores
    print("  Removendo computadores...")
    count_comps = Computador.objects.all().count()
    Computador.objects.all().delete()
    
    print(f"  Total de registros removidos do módulo TI: {count_atrib_comp + count_atrib_perif + count_atrib_func + count_pas + count_ilhas + count_salas + count_perif + count_tipos + count_comps}")

def limpar_modulo_funcionarios(limpar_tudo=False):
    """
    Limpa os dados do módulo de Funcionários
    
    Args:
        limpar_tudo (bool): Se True, remove todos os dados, incluindo empresas e lojas.
                           Se False, remove apenas funcionários e configurações, mantendo
                           estrutura básica.
    """
    print("Limpando dados do módulo Funcionários...")
    
    # Limpar arquivos de funcionários primeiro
    print("  Removendo arquivos de funcionários...")
    count_arquivos = ArquivoFuncionario.objects.all().count()
    ArquivoFuncionario.objects.all().delete()
    
    # Limpar comissionamentos
    print("  Removendo regras de comissionamento...")
    count_comissoes = Comissionamento.objects.all().count()
    Comissionamento.objects.all().delete()
    
    # Limpar funcionários
    print("  Removendo funcionários...")
    count_funcs = Funcionario.objects.all().count()
    Funcionario.objects.all().delete()
    
    # Limpar horários e equipes
    print("  Removendo horários de trabalho...")
    count_horarios = HorarioTrabalho.objects.all().count()
    HorarioTrabalho.objects.all().delete()
    
    print("  Removendo equipes...")
    count_equipes = Equipe.objects.all().count()
    Equipe.objects.all().delete()
    
    if limpar_tudo:
        # Limpar estrutura completa
        print("  Removendo cargos...")
        count_cargos = Cargo.objects.all().count()
        Cargo.objects.all().delete()
        
        print("  Removendo setores...")
        count_setores = Setor.objects.all().count()
        Setor.objects.all().delete()
        
        print("  Removendo departamentos...")
        count_depts = Departamento.objects.all().count()
        Departamento.objects.all().delete()
        
        print("  Removendo lojas...")
        count_lojas = Loja.objects.all().count()
        Loja.objects.all().delete()
        
        print("  Removendo empresas...")
        count_empresas = Empresa.objects.all().count()
        Empresa.objects.all().delete()
        
        total = count_arquivos + count_comissoes + count_funcs + count_horarios + count_equipes + count_cargos + count_setores + count_depts + count_lojas + count_empresas
    else:
        # Manter estrutura básica
        count_cargos = count_setores = count_depts = count_lojas = count_empresas = 0
        total = count_arquivos + count_comissoes + count_funcs + count_horarios + count_equipes
    
    print(f"  Total de registros removidos do módulo Funcionários: {total}")

def main():
    """Função principal para limpar o banco de dados"""
    print("=" * 60)
    print(f"Iniciando limpeza dos dados dos módulos de TI e Funcionários...")
    print(f"Data e hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    confirmar = input("Esta operação irá remover TODOS os dados dos módulos TI e Funcionários. Deseja continuar? (s/n): ")
    if confirmar.lower() not in ['s', 'sim', 'y', 'yes']:
        print("Operação cancelada pelo usuário.")
        return
    
    limpar_estrutura = input("Deseja remover também a estrutura básica (empresas, lojas, departamentos, etc.)? (s/n): ")
    limpar_tudo = limpar_estrutura.lower() in ['s', 'sim', 'y', 'yes']
    
    # Limpeza do módulo TI primeiro (devido às dependências)
    try:
        limpar_modulo_ti()
    except Exception as e:
        print(f"ERRO ao limpar módulo TI: {e}")
    
    # Depois limpar o módulo de Funcionários
    try:
        limpar_modulo_funcionarios(limpar_tudo=limpar_tudo)
    except Exception as e:
        print(f"ERRO ao limpar módulo Funcionários: {e}")
    
    print("=" * 60)
    print("Limpeza concluída!")
    print("=" * 60)

if __name__ == "__main__":
    main() 