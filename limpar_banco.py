import os
import sys
import django

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")
django.setup()

# Importar os modelos que queremos limpar
from apps.ti.models import (
    Sala, Ilha, PosicaoAtendimento, TipoPeriferico, 
    Periferico, AtribuicaoFuncionarioPA, AtribuicaoPerifericoPA
)

def limpar_banco():
    print("Iniciando limpeza do banco de dados da aba de TI...")
    
    # Limpar atribuições primeiro para evitar erros de integridade
    print("Removendo atribuições de periféricos às PAs...")
    AtribuicaoPerifericoPA.objects.all().delete()
    
    print("Removendo atribuições de funcionários às PAs...")
    AtribuicaoFuncionarioPA.objects.all().delete()
    
    # Limpar periféricos
    print("Removendo periféricos...")
    Periferico.objects.all().delete()
    
    # Limpar posições de atendimento, ilhas e salas
    print("Removendo posições de atendimento...")
    PosicaoAtendimento.objects.all().delete()
    
    print("Removendo ilhas...")
    Ilha.objects.all().delete()
    
    print("Removendo salas...")
    Sala.objects.all().delete()
    
    # Limpar tipos de periféricos
    print("Removendo tipos de periféricos...")
    TipoPeriferico.objects.all().delete()
    
    print("Limpeza concluída com sucesso!")

if __name__ == "__main__":
    limpar_banco() 