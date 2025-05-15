import os
import sys
import django
import random
from datetime import datetime, date, timedelta
from django.utils import timezone

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")
django.setup()

# Importar os modelos necessários
from django.contrib.auth.models import User
from apps.ti.models import (
    Sala, Ilha, PosicaoAtendimento, TipoPeriferico, 
    Periferico, AtribuicaoFuncionarioPA, AtribuicaoPerifericoPA,
    Computador, AtribuicaoComputadorPA  # Adicionados os novos modelos
)
from apps.funcionarios.models import (
    Empresa, Departamento, Setor, Cargo, 
    HorarioTrabalho, Funcionario, Loja
)

# Função para criar dados básicos necessários
def criar_dados_basicos():
    print("Criando dados básicos...")
    
    # Criando empresa se não existir
    empresa, created = Empresa.objects.get_or_create(
        nome="EMPRESA TESTE",
        cnpj="12.345.678/0001-99",
        endereco="Rua Teste, 123"
    )
    if created:
        print("Empresa criada!")
    
    # Criando departamento de TI se não existir
    departamento, created = Departamento.objects.get_or_create(
        nome="TI",
        empresa=empresa
    )
    if created:
        print("Departamento de TI criado!")
    
    # Criando setor de Suporte se não existir
    setor, created = Setor.objects.get_or_create(
        nome="SUPORTE",
        departamento=departamento
    )
    if created:
        print("Setor de Suporte criado!")
    
    # Criando cargo de Analista se não existir
    cargo, created = Cargo.objects.get_or_create(
        nome="ANALISTA DE SUPORTE",
        empresa=empresa,
        hierarquia=2  # PADRAO
    )
    if created:
        print("Cargo de Analista de Suporte criado!")
    
    # Criando horário de trabalho padrão se não existir
    horario, created = HorarioTrabalho.objects.get_or_create(
        nome="COMERCIAL",
        defaults={
            "entrada": "08:00",
            "saida_almoco": "12:00",
            "volta_almoco": "13:00",
            "saida": "18:00"
        }
    )
    if created:
        print("Horário de trabalho criado!")
    
    # Criando loja se não existir
    loja, created = Loja.objects.get_or_create(
        nome="LOJA CENTRAL",
        empresa=empresa
    )
    if created:
        print("Loja Central criada!")
    
    # Criando tipos de periféricos
    tipos_perifericos = ["MOUSE", "MOUSEPAD", "TECLADO", "FONE", "MONITOR"]
    for tipo in tipos_perifericos:
        tipo_obj, created = TipoPeriferico.objects.get_or_create(nome=tipo)
        if created:
            print(f"Tipo de periférico {tipo} criado!")
    
    return {
        "empresa": empresa,
        "departamento": departamento,
        "setor": setor,
        "cargo": cargo,
        "horario": horario,
        "loja": loja
    }

# Função para criar salas, ilhas e PAs
def criar_estrutura_ti():
    print("\nCriando estrutura de TI...")
    
    # Limpando dados antigos se necessário
    Sala.objects.all().delete()
    print("Dados anteriores de salas, ilhas e PAs excluídos!")
    
    # Criando as 3 salas
    salas = []
    for i in range(1, 4):
        sala = Sala.objects.create(
            nome=f"SALA {i}",
            descricao=f"Sala de trabalho número {i}"
        )
        salas.append(sala)
        print(f"Sala {i} criada!")
    
    # Distribuição de ilhas por sala
    configuracao_ilhas = [
        {"sala": salas[0], "n_ilhas": 2, "pas_por_ilha": [10, 8]},
        {"sala": salas[1], "n_ilhas": 2, "pas_por_ilha": [12, 12]},
        {"sala": salas[2], "n_ilhas": 1, "pas_por_ilha": [6]}
    ]
    
    # Criando as ilhas
    ilhas = []
    for config in configuracao_ilhas:
        sala = config["sala"]
        for i in range(config["n_ilhas"]):
            ilha = Ilha.objects.create(
                nome=f"ILHA {i+1}",
                sala=sala,
                quantidade_pas=config["pas_por_ilha"][i],
                descricao=f"Ilha {i+1} da {sala.nome}"
            )
            ilhas.append({"ilha": ilha, "qtd_pas": config["pas_por_ilha"][i]})
            print(f"Ilha {i+1} criada na {sala.nome} com {config['pas_por_ilha'][i]} PAs!")
    
    # Criando as PAs
    pas = []
    for ilha_config in ilhas:
        ilha = ilha_config["ilha"]
        for i in range(1, ilha_config["qtd_pas"] + 1):
            numero = f"{i:02d}"  # Formata o número com zeros à esquerda
            pa = PosicaoAtendimento.objects.create(
                numero=numero,
                ilha=ilha,
                sala=ilha.sala,
                status="livre"
            )
            pas.append(pa)
            print(f"PA {numero} criada na {ilha.nome} da {ilha.sala.nome}!")
    
    return {"salas": salas, "ilhas": ilhas, "pas": pas}

# Função para criar periféricos
def criar_perifericos(tipos_perifericos=None):
    print("\nCriando periféricos...")
    
    if tipos_perifericos is None:
        tipos_perifericos = TipoPeriferico.objects.all()
    
    marcas = {
        "MOUSE": ["Logitech", "Microsoft", "Dell", "HP"],
        "MOUSEPAD": ["Logitech", "Multilaser", "Razer", "HyperX"],
        "TECLADO": ["Logitech", "Microsoft", "Dell", "HP"],
        "FONE": ["Logitech", "Microsoft", "JBL", "Sony"],
        "MONITOR": ["Dell", "Samsung", "LG", "HP"]
    }
    
    modelos = {
        "MOUSE": ["M170", "M220", "G203", "MS3320W"],
        "MOUSEPAD": ["MP1100", "Standard", "Gaming Pro", "RGB Edge"],
        "TECLADO": ["K120", "Wireless 850", "KB216", "Smart Keyboard"],
        "FONE": ["H390", "LifeChat LX-3000", "T110", "WH-CH510"],
        "MONITOR": ["P2422H", "S24R350", "22MP410", "P22v G5"]
    }
    
    perifericos = []
    
    for tipo in tipos_perifericos:
        tipo_nome = tipo.nome.upper()
        marcas_disponiveis = marcas.get(tipo_nome, ["Genérico"])
        modelos_disponiveis = modelos.get(tipo_nome, ["Básico"])
        
        for _ in range(50):  # Criar periféricos suficientes
            periferico = Periferico.objects.create(
                tipo=tipo,
                marca=random.choice(marcas_disponiveis),
                modelo=random.choice(modelos_disponiveis),
                numero_serie=f"SN{random.randint(10000, 99999)}",
                data_aquisicao=date.today() - timedelta(days=random.randint(0, 365)),
                status="disponivel"
            )
            perifericos.append(periferico)
    
    print(f"Criados {len(perifericos)} periféricos!")
    return perifericos

# Função para criar computadores
def criar_computadores(quantidade=60):
    print("\nCriando computadores...")
    
    marcas = ["Dell", "HP", "Lenovo", "Acer", "Asus", "Positivo"]
    
    computadores = []
    
    for i in range(quantidade):
        marca = random.choice(marcas)
        quantidade_computador = 1  # Por padrão, cada registro representa 1 computador
        
        computador = Computador.objects.create(
            marca=marca,
            quantidade=quantidade_computador,
            status="disponivel",
            observacoes=f"Computador {i+1} para uso corporativo"
        )
        computadores.append(computador)
    
    print(f"Criados {len(computadores)} computadores!")
    return computadores

# Função para criar funcionários
def criar_funcionarios(dados_basicos, quantidade=50):
    print("\nCriando funcionários...")
    
    funcionarios = []
    
    nomes = ["João", "Maria", "Pedro", "Ana", "Carlos", "Julia", "Lucas", "Fernanda", 
             "Marcos", "Amanda", "Rafael", "Camila", "Fernando", "Juliana", "Rodrigo",
             "Paulo", "Beatriz", "Gabriel", "Laura", "Leonardo", "Mariana", "Guilherme",
             "Isabela", "Daniel", "Larissa", "Bruno", "Natália", "Felipe", "Bianca"]
    sobrenomes = ["Silva", "Santos", "Oliveira", "Souza", "Pereira", "Lima", "Costa", 
                  "Ferreira", "Rodrigues", "Almeida", "Nascimento", "Carvalho", "Gomes",
                  "Martins", "Araújo", "Ribeiro", "Barbosa", "Cardoso", "Teixeira",
                  "Moreira", "Campos", "Dias", "Freitas", "Mendes", "Fernandes"]
    
    # Adicionando timestamp para garantir matrículas únicas
    timestamp = int(datetime.now().timestamp())
    
    for i in range(1, quantidade + 1):
        nome = random.choice(nomes)
        sobrenome = random.choice(sobrenomes)
        nome_completo = f"{nome} {sobrenome}"
        
        # CPF único
        cpf = f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}"
        
        # Data de nascimento
        ano = random.randint(1980, 2000)
        mes = random.randint(1, 12)
        dia = random.randint(1, 28)
        data_nascimento = date(ano, mes, dia)
        
        # Ramal aleatório começando em 1000
        ramal = str(1000 + i - 1)
        
        # Matrícula única usando timestamp
        matricula = f"F{timestamp}{i:03d}"
        
        funcionario = Funcionario.objects.create(
            nome_completo=nome_completo,
            cpf=cpf,
            data_nascimento=data_nascimento,
            empresa=dados_basicos["empresa"],
            departamento=dados_basicos["departamento"],
            setor=dados_basicos["setor"],
            cargo=dados_basicos["cargo"],
            horario=dados_basicos["horario"],
            loja=dados_basicos["loja"],
            data_admissao=date.today() - timedelta(days=random.randint(30, 365)),
            matricula=matricula,
            ramal=ramal
        )
        funcionarios.append(funcionario)
    
    print(f"Criados {len(funcionarios)} funcionários!")
    return funcionarios

# Função para atribuir funcionários e periféricos às PAs
def atribuir_a_pas(pas, funcionarios, perifericos, computadores):
    print("\nAtribuindo funcionários, periféricos e computadores às PAs...")
    
    # Agrupando os periféricos por tipo
    perifericos_por_tipo = {}
    for periferico in perifericos:
        tipo_nome = periferico.tipo.nome
        if tipo_nome not in perifericos_por_tipo:
            perifericos_por_tipo[tipo_nome] = []
        perifericos_por_tipo[tipo_nome].append(periferico)
    
    # Shuffle dos computadores para distribuição aleatória
    computadores_disponiveis = list(computadores)
    random.shuffle(computadores_disponiveis)
    
    # Definir quantas PAs terão todos os itens completos (funcionário, periféricos e computador)
    # e quantas terão apenas alguns itens
    pas_totalmente_ocupadas = min(len(pas), len(funcionarios), len(computadores_disponiveis) // 2)
    
    # Atribuindo itens às PAs
    for i, pa in enumerate(pas):
        # ATRIBUIÇÃO DE FUNCIONÁRIOS
        if i < pas_totalmente_ocupadas:
            # Atribuir funcionário
            funcionario = funcionarios[i]
            pa.funcionario = funcionario
            pa.status = "ocupada"
            pa.save()
            
            # Registrar a atribuição do funcionário
            atribuicao_funcionario = AtribuicaoFuncionarioPA.objects.create(
                funcionario=funcionario,
                posicao_atendimento=pa,
                data_inicio=date.today(),
                ativo=True
            )
            
            # ATRIBUIÇÃO DE PERIFÉRICOS
            # Atribuir um periférico de cada tipo
            for tipo_nome, perifericos_disponiveis in perifericos_por_tipo.items():
                if perifericos_disponiveis:
                    periferico = perifericos_disponiveis.pop(0)
                    periferico.status = "em_uso"
                    periferico.save()
                    
                    # Registrar a atribuição do periférico
                    atribuicao_periferico = AtribuicaoPerifericoPA.objects.create(
                        periferico=periferico,
                        posicao_atendimento=pa,
                        data_atribuicao=timezone.now(),
                        ativo=True
                    )
            
            # ATRIBUIÇÃO DE COMPUTADORES
            # Algumas PAs terão mais de um computador
            # 70% terá 1 computador, 20% terá 2 computadores, 10% não terá
            computadores_por_pa = 1
            if random.random() < 0.2:  # 20% com 2 computadores
                computadores_por_pa = 2
            
            for _ in range(computadores_por_pa):
                if computadores_disponiveis:
                    computador = computadores_disponiveis.pop(0)
                    computador.status = "em_uso"
                    computador.save()
                    
                    # Registrar a atribuição do computador
                    AtribuicaoComputadorPA.objects.create(
                        computador=computador,
                        posicao_atendimento=pa,
                        data_atribuicao=timezone.now(),
                        ativo=True
                    )
        
        elif i < len(pas) * 0.7:  # 70% das restantes terão PAs vazias
            pa.status = "inativa"  # Status "Vazia"
            pa.save()
        
        elif i < len(pas) * 0.9:  # 20% das restantes terão PAs livres
            pa.status = "livre"
            pa.save()
        
        else:  # 10% das restantes terão PAs em manutenção
            pa.status = "manutencao"
            pa.save()
    
    print("Funcionários, periféricos e computadores atribuídos às PAs com sucesso!")

# Função principal
def main():
    print("Iniciando população da base de dados para a aba de TI...")
    
    if len(sys.argv) > 1 and (sys.argv[1] == '--help' or sys.argv[1] == '-h'):
        print("\nUso: python populate.py [opções]")
        print("\nOpções:")
        print("  --computadores-extras   Cria computadores extras (total 100)")
        print("  --perifericos-extras    Cria periféricos extras (100 por tipo)")
        print("  --funcionarios-extras   Cria funcionários extras (total 100)")
        print("  --sem-confirmar         Executa sem pedir confirmação")
        print("  --help, -h              Mostra esta mensagem de ajuda")
        sys.exit(0)
    
    # Verificar se o usuário deseja confirmação
    confirmar = '--sem-confirmar' not in sys.argv
    
    # Se pede confirmação, perguntar ao usuário
    if confirmar:
        print("\n⚠️  ATENÇÃO! ⚠️")
        print("Este script irá popular o banco de dados com dados de teste.")
        print("Isso pode incluir a substituição de dados existentes.")
        resposta = input("\nDeseja continuar? (s/N): ")
        
        if resposta.lower() not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada pelo usuário.")
            return
    
    # Verificar opções extras
    computadores_extras = '--computadores-extras' in sys.argv
    perifericos_extras = '--perifericos-extras' in sys.argv
    funcionarios_extras = '--funcionarios-extras' in sys.argv
    
    # Configurações para quantidades
    qtd_computadores = 100 if computadores_extras else 60
    qtd_perifericos_por_tipo = 100 if perifericos_extras else 50
    qtd_funcionarios = 100 if funcionarios_extras else 50
    
    try:
        # Criar dados básicos
        dados_basicos = criar_dados_basicos()
        
        # Criar estrutura física de TI
        estrutura_ti = criar_estrutura_ti()
        
        # Criar periféricos
        tipos_perifericos = TipoPeriferico.objects.all()
        perifericos = criar_perifericos(tipos_perifericos)
        
        # Criar computadores
        computadores = criar_computadores(qtd_computadores)
        
        # Criar funcionários
        funcionarios = criar_funcionarios(dados_basicos, quantidade=qtd_funcionarios)
        
        # Atribuir funcionários, periféricos e computadores às PAs
        atribuir_a_pas(estrutura_ti["pas"], funcionarios, perifericos, computadores)
        
        print("\nPopulação da base de dados concluída com sucesso!")
    
    except Exception as e:
        print(f"\nErro durante o processo de população: {e}")
        print("A operação foi interrompida. Alguns dados podem já ter sido criados.")

if __name__ == "__main__":
    main() 