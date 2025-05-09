import os
import sys
import django
import random
from datetime import datetime, date, timedelta

# Configurar o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")
django.setup()

# Importar os modelos necessários
from django.contrib.auth.models import User
from apps.ti.models import (
    Sala, Ilha, PosicaoAtendimento, TipoPeriferico, 
    Periferico, AtribuicaoFuncionarioPA, AtribuicaoPerifericoPA
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

# Função para criar funcionários
def criar_funcionarios(dados_basicos, quantidade=50):
    print("\nCriando funcionários...")
    
    funcionarios = []
    
    nomes = ["João", "Maria", "Pedro", "Ana", "Carlos", "Julia", "Lucas", "Fernanda", 
             "Marcos", "Amanda", "Rafael", "Camila", "Fernando", "Juliana", "Rodrigo"]
    sobrenomes = ["Silva", "Santos", "Oliveira", "Souza", "Pereira", "Lima", "Costa", 
                  "Ferreira", "Rodrigues", "Almeida", "Nascimento", "Carvalho", "Gomes"]
    
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
def atribuir_a_pas(pas, funcionarios, perifericos):
    print("\nAtribuindo funcionários e periféricos às PAs...")
    
    # Agrupando os periféricos por tipo
    perifericos_por_tipo = {}
    for periferico in perifericos:
        tipo_nome = periferico.tipo.nome
        if tipo_nome not in perifericos_por_tipo:
            perifericos_por_tipo[tipo_nome] = []
        perifericos_por_tipo[tipo_nome].append(periferico)
    
    # Atribuindo um funcionário e os periféricos necessários a cada PA
    for i, pa in enumerate(pas):
        if i < len(funcionarios):
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
                        data_atribuicao=date.today(),
                        ativo=True
                    )
    
    print("Funcionários e periféricos atribuídos às PAs com sucesso!")

# Função principal
def main():
    print("Iniciando população da base de dados para a aba de TI...")
    
    # Criar dados básicos
    dados_basicos = criar_dados_basicos()
    
    # Criar estrutura física de TI
    estrutura_ti = criar_estrutura_ti()
    
    # Criar periféricos
    tipos_perifericos = TipoPeriferico.objects.all()
    perifericos = criar_perifericos(tipos_perifericos)
    
    # Criar funcionários
    funcionarios = criar_funcionarios(dados_basicos, quantidade=len(estrutura_ti["pas"]))
    
    # Atribuir funcionários e periféricos às PAs
    atribuir_a_pas(estrutura_ti["pas"], funcionarios, perifericos)
    
    print("\nPopulação da base de dados concluída com sucesso!")

if __name__ == "__main__":
    main() 