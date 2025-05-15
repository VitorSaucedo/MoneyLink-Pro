import os
import sys
import django

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")
django.setup()

# Importar os modelos que queremos limpar
from apps.ti.models import (
    Sala, Ilha, PosicaoAtendimento, TipoPeriferico, 
    Periferico, AtribuicaoFuncionarioPA, AtribuicaoPerifericoPA,
    Computador, AtribuicaoComputadorPA  # Adicionado novos modelos
)

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

if __name__ == "__main__":
    # Verificar argumentos de linha de comando
    if len(sys.argv) > 1:
        # Modo de limpeza seletiva
        if "--help" in sys.argv or "-h" in sys.argv:
            print("\nUso: python limpar_banco.py [opções]")
            print("\nOpções:")
            print("  --sem-confirmar     Executa sem pedir confirmação")
            print("  --atribuicoes       Limpa apenas atribuições")
            print("  --computadores      Limpa apenas computadores")
            print("  --perifericos       Limpa apenas periféricos")
            print("  --pas               Limpa apenas PAs")
            print("  --ilhas             Limpa apenas ilhas")
            print("  --salas             Limpa apenas salas")
            print("  --tipos             Limpa apenas tipos de periféricos")
            print("  --tudo              Limpa tudo (padrão)")
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
        # Modo padrão: limpar tudo com confirmação
        limpar_ti() 