import os
import sys
import django
import time

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")
django.setup()

# Importar django.apps para obter todos os modelos
from django.apps import apps
from django.db import connection
from django.conf import settings

# Importar os modelos específicos de TI para manter compatibilidade com a função original
from apps.ti.models import (
    Sala, Ilha, PosicaoAtendimento, TipoPeriferico, 
    Periferico, AtribuicaoFuncionarioPA, AtribuicaoPerifericoPA,
    Computador, AtribuicaoComputadorPA
)

# Modelos que devem ser preservados (usuários admin, permissões, etc.)
MODELOS_PRESERVADOS = [
    'auth.permission',
    'auth.group',
    'admin.logentry',
    'sessions.session',
    'contenttypes.contenttype',
]

def limpar_ti(confirmar=True, limpar_tudo=True, limpar_atribuicoes=False, 
             limpar_perifericos=False, limpar_computadores=False, 
             limpar_pas=False, limpar_ilhas=False, limpar_salas=False, 
             limpar_tipos=False):
    """
    Função para limpar dados do módulo TI do banco de dados.
    
    Parâmetros:
    - confirmar: Solicita confirmação antes de executar (padrão: True)
    - limpar_tudo: Limpa todos os dados (padrão: True)
    - Outros parâmetros permitem limpeza seletiva de entidades específicas
    """
    if confirmar:
        print("\n⚠️  ATENÇÃO! ⚠️")
        print("Você está prestes a excluir dados do banco. Esta ação é irreversível.")
        
        if limpar_tudo:
            resposta = input("\nDeseja realmente limpar TODOS os dados de TI? (s/N): ")
        else:
            print("\nVocê selecionou limpeza dos seguintes itens:")
            if limpar_atribuicoes:
                print("- Atribuições de funcionários e periféricos")
            if limpar_computadores:
                print("- Computadores e suas atribuições")
            if limpar_perifericos:
                print("- Periféricos")
            if limpar_pas:
                print("- Posições de Atendimento (PAs)")
            if limpar_ilhas:
                print("- Ilhas")
            if limpar_salas:
                print("- Salas")
            if limpar_tipos:
                print("- Tipos de Periféricos")
            
            resposta = input("\nDeseja continuar com a limpeza seletiva? (s/N): ")
        
        if resposta.lower() not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada pelo usuário.")
            return
    
    print("\nIniciando limpeza do banco de dados da aba de TI...")
    
    try:
        # Definir o que será limpo
        if limpar_tudo:
            limpar_atribuicoes = limpar_computadores = limpar_perifericos = True
            limpar_pas = limpar_ilhas = limpar_salas = limpar_tipos = True
        
        # Limpar atribuições primeiro para evitar erros de integridade
        if limpar_atribuicoes:
            print("Removendo atribuições de periféricos às PAs...")
            AtribuicaoPerifericoPA.objects.all().delete()
            
            print("Removendo atribuições de funcionários às PAs...")
            AtribuicaoFuncionarioPA.objects.all().delete()
        
        # Limpar computadores e suas atribuições
        if limpar_computadores:
            print("Removendo atribuições de computadores às PAs...")
            AtribuicaoComputadorPA.objects.all().delete()
            
            print("Removendo computadores...")
            Computador.objects.all().delete()
        
        # Limpar periféricos
        if limpar_perifericos:
            print("Removendo periféricos...")
            Periferico.objects.all().delete()
        
        # Limpar posições de atendimento, ilhas e salas
        if limpar_pas:
            print("Removendo posições de atendimento...")
            PosicaoAtendimento.objects.all().delete()
        
        if limpar_ilhas:
            print("Removendo ilhas...")
            Ilha.objects.all().delete()
        
        if limpar_salas:
            print("Removendo salas...")
            Sala.objects.all().delete()
        
        # Limpar tipos de periféricos
        if limpar_tipos:
            print("Removendo tipos de periféricos...")
            TipoPeriferico.objects.all().delete()
        
        print("Limpeza concluída com sucesso!")
    
    except Exception as e:
        print(f"Erro durante a limpeza: {e}")
        print("A operação foi interrompida. Alguns dados podem já ter sido excluídos.")

def limpar_banco():
    """
    Função legada para compatibilidade, chama a nova função limpar_ti
    """
    limpar_ti()


def limpar_tudo_completo(confirmar=True, preservar_admin=True):
    """
    Limpa completamente o banco de dados, exceto modelos de sistema.
    
    Parâmetros:
    - confirmar: Solicita confirmação antes de executar (padrão: True)
    - preservar_admin: Preserva o usuário admin e suas permissões (padrão: True)
    """
    if confirmar:
        print("\n⚠️  ATENÇÃO! ⚠️")
        print("\n⚠️  PERIGO EXTREMO! ⚠️")
        print("Você está prestes a excluir TODOS OS DADOS do banco.")
        print("Esta ação é IRREVERSÍVEL e afetará TODOS OS MÓDULOS do sistema.")
        
        resposta = input("\nDigite 'CONFIRMO' (em maiúsculas) para continuar: ")
        
        if resposta != "CONFIRMO":
            print("Operação cancelada. Banco de dados não foi alterado.")
            return
    
    print("\nIniciando limpeza completa do banco de dados...")
    print("Este processo pode demorar alguns minutos, dependendo do tamanho do banco.")
    
    # Obter todos os modelos registrados
    todos_modelos = []
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            model_name = f"{model._meta.app_label}.{model._meta.model_name}"
            
            # Pular modelos que devem ser preservados
            if preservar_admin and model_name in MODELOS_PRESERVADOS:
                print(f"Preservando modelo de sistema: {model_name}")
                continue
                
            # Adicionar à lista para limpeza
            todos_modelos.append((model_name, model))
    
    # Ordenar modelos para evitar problemas de integridade referencial
    # Primeiro limpar modelos que têm chaves estrangeiras para outros modelos
    for model_name, model in sorted(todos_modelos, key=lambda x: x[0]):
        try:
            count = model.objects.count()
            if count > 0:
                print(f"Removendo {count} registros de {model_name}...")
                # Usar SQL direto para ser mais rápido e evitar triggers/signals
                with connection.cursor() as cursor:
                    table_name = model._meta.db_table
                    cursor.execute(f"DELETE FROM \"{ table_name }\";")
                print(f"✓ {model_name} limpo")
            else:
                print(f"Pulando {model_name} (vazio)")
        except Exception as e:
            print(f"Erro ao limpar {model_name}: {e}")
    
    print("\nRestaurando sequências (IDs) no banco de dados...")
    # Resetar sequências de IDs
    with connection.cursor() as cursor:
        if 'postgresql' in connection.vendor:
            cursor.execute("""
                DO $$
                DECLARE
                    seq_name text;
                BEGIN
                    FOR seq_name IN (SELECT relname FROM pg_class WHERE relkind = 'S')
                    LOOP
                        EXECUTE 'ALTER SEQUENCE ' || seq_name || ' RESTART WITH 1';
                    END LOOP;
                END $$;
            """)
    
    print("\n✅ Limpeza completa do banco de dados concluída com sucesso!")
    print("O banco de dados está agora vazio (exceto pelos modelos de sistema preservados).")

if __name__ == "__main__":
    # Verificar argumentos de linha de comando
    if len(sys.argv) > 1:
        # Nova opção para limpar todo o banco de dados
        if "--completo" in sys.argv:
            confirmar = "--sem-confirmar" not in sys.argv
            limpar_tudo_completo(confirmar=confirmar)
            sys.exit(0)
        
        # Modo de limpeza seletiva (apenas TI)
        if "--help" in sys.argv or "-h" in sys.argv:
            print("\nUso: python limpar_banco.py [opções]")
            print("\nOpções:")
            print("  --completo          Limpa TODOS os dados do banco (todos os módulos)")
            print("\nOpções para limpeza de TI apenas:")
            print("  --sem-confirmar     Executa sem pedir confirmação")
            print("  --atribuicoes       Limpa apenas atribuições")
            print("  --computadores      Limpa apenas computadores")
            print("  --perifericos       Limpa apenas periféricos")
            print("  --pas               Limpa apenas PAs")
            print("  --ilhas             Limpa apenas ilhas")
            print("  --salas             Limpa apenas salas")
            print("  --tipos             Limpa apenas tipos de periféricos")
            print("  --tudo              Limpa tudo do módulo TI (padrão)")
            print("  --help, -h          Mostra esta mensagem de ajuda")
            sys.exit(0)
        
        confirmar = "--sem-confirmar" not in sys.argv
        
        # Se alguma opção específica for dada, não limpar tudo
        opcoes_especificas = ["--atribuicoes", "--computadores", "--perifericos", 
                             "--pas", "--ilhas", "--salas", "--tipos"]
        
        tem_opcao_especifica = any(opcao in sys.argv for opcao in opcoes_especificas)
        limpar_tudo = "--tudo" in sys.argv or not tem_opcao_especifica
        
        limpar_ti(
            confirmar=confirmar,
            limpar_tudo=limpar_tudo,
            limpar_atribuicoes="--atribuicoes" in sys.argv,
            limpar_computadores="--computadores" in sys.argv,
            limpar_perifericos="--perifericos" in sys.argv,
            limpar_pas="--pas" in sys.argv,
            limpar_ilhas="--ilhas" in sys.argv,
            limpar_salas="--salas" in sys.argv,
            limpar_tipos="--tipos" in sys.argv
        )
    else:
        # Perguntar ao usuário o que deseja limpar
        print("\nOpções de limpeza:")
        print("1. Limpar apenas módulo TI")
        print("2. Limpar COMPLETAMENTE o banco de dados (todos os módulos)")
        
        try:
            opcao = int(input("\nEscolha uma opção (1-2): "))
            if opcao == 1:
                limpar_ti()
            elif opcao == 2:
                limpar_tudo_completo()
            else:
                print("Opção inválida. Operação cancelada.")
        except ValueError:
            print("Entrada inválida. Operação cancelada.")
            sys.exit(1)