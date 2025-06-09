import os
import sys
import django
import random
from datetime import datetime, timedelta
from faker import Faker

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

# Importar modelos após configurar o ambiente Django
from django.contrib.auth.models import User
from apps.funcionarios.models import (
    Empresa, Loja, Departamento, Setor, Cargo, 
    HorarioTrabalho, Funcionario, Equipe
)
from apps.ti.models import (
    TipoPeriferico, Periferico, Computador, Monitor,
    Sala, Ilha, PosicaoAtendimento, AtribuicaoFuncionarioPA,
    AtribuicaoPerifericoPA, AtribuicaoComputadorPA, AtribuicaoMonitorPA
)

# Inicializar Faker para geração de dados aleatórios
fake = Faker('pt_BR')

# Limpar dados existentes (opcional - remova ou comente se não quiser limpar)
def limpar_dados():
    print("Limpando dados existentes...")
    # Remover atribuições primeiro para evitar problemas de integridade referencial
    AtribuicaoMonitorPA.objects.all().delete()
    AtribuicaoComputadorPA.objects.all().delete()
    AtribuicaoPerifericoPA.objects.all().delete()
    AtribuicaoFuncionarioPA.objects.all().delete()
    
    # Remover equipamentos e estrutura física
    PosicaoAtendimento.objects.all().delete()
    Ilha.objects.all().delete()
    Sala.objects.all().delete()
    Periferico.objects.all().delete()
    TipoPeriferico.objects.all().delete()
    Monitor.objects.all().delete()
    Computador.objects.all().delete()
    
    # Remover funcionários e estrutura organizacional
    Funcionario.objects.all().delete()
    Equipe.objects.all().delete()
    Cargo.objects.all().delete()
    Setor.objects.all().delete()
    Departamento.objects.all().delete()
    Loja.objects.all().delete()
    Empresa.objects.all().delete()
    
    # Remover horários
    HorarioTrabalho.objects.all().delete()
    
    print("Dados existentes removidos com sucesso!")

# Criar empresa
def criar_empresa():
    print("Criando empresa...")
    empresa = Empresa.objects.create(
        nome="MONEY PROMOTORA DE CRÉDITO LTDA",
        cnpj="12.345.678/0001-99",
        endereco="Av. Principal, 1000, Centro, Porto Alegre - RS",
        status=True
    )
    return empresa

# Criar lojas
def criar_lojas(empresa):
    print("Criando lojas...")
    lojas = [
        Loja.objects.create(
            nome="SEDE",
            empresa=empresa,
            filial=False,
            franquia=False,
            status=True
        ),
        Loja.objects.create(
            nome="CACHOEIRINHA",
            empresa=empresa,
            filial=True,
            franquia=False,
            status=True
        ),
        Loja.objects.create(
            nome="SÃO LEOPOLDO",
            empresa=empresa,
            filial=True,
            franquia=False,
            status=True
        ),
        Loja.objects.create(
            nome="SALGADO FILHO",
            empresa=empresa,
            filial=True,
            franquia=False,
            status=True
        ),
        Loja.objects.create(
            nome="SANTA MARIA",
            empresa=empresa,
            filial=True,
            franquia=False,
            status=True
        )
    ]
    return lojas

# Criar departamentos
def criar_departamentos(empresa):
    print("Criando departamentos...")
    departamentos = [
        Departamento.objects.create(
            nome="VENDAS",
            empresa=empresa,
            status=True
        ),
        Departamento.objects.create(
            nome="ADMINISTRATIVO",
            empresa=empresa,
            status=True
        ),
        Departamento.objects.create(
            nome="ZELADORIA",
            empresa=empresa,
            status=True
        )
    ]
    return departamentos

# Criar setores
def criar_setores(departamentos):
    print("Criando setores...")
    # Associamos os setores ao departamento de VENDAS
    setores = [
        Setor.objects.create(
            nome="INSS",
            departamento=departamentos[0],  # VENDAS
            status=True
        ),
        Setor.objects.create(
            nome="SIAPE",
            departamento=departamentos[0],  # VENDAS
            status=True
        )
    ]
    return setores

# Criar cargos
def criar_cargos(empresa):
    print("Criando cargos...")
    cargos = [
        Cargo.objects.create(
            nome="NEGOCIADOR(A)",
            empresa=empresa,
            hierarquia=Cargo.HierarquiaChoices.PADRAO,
            status=True
        ),
        Cargo.objects.create(
            nome="ANALISTA FINANCEIRO(A)",
            empresa=empresa,
            hierarquia=Cargo.HierarquiaChoices.PADRAO,
            status=True
        ),
        Cargo.objects.create(
            nome="VENDEDOR(A)",
            empresa=empresa,
            hierarquia=Cargo.HierarquiaChoices.PADRAO,
            status=True
        ),
        Cargo.objects.create(
            nome="RH",
            empresa=empresa,
            hierarquia=Cargo.HierarquiaChoices.PADRAO,
            status=True
        ),
        Cargo.objects.create(
            nome="ANALISTA DE TI",
            empresa=empresa,
            hierarquia=Cargo.HierarquiaChoices.PADRAO,
            status=True
        )
    ]
    return cargos

# Criar horário de trabalho
def criar_horario_trabalho():
    print("Criando horário de trabalho...")
    horario = HorarioTrabalho.objects.create(
        nome="HORÁRIO COMERCIAL",
        entrada="08:00",
        saida_almoco="12:00",
        volta_almoco="13:00",
        saida="18:00",
        status=True
    )
    return horario

# Criar funcionários
def criar_funcionarios(empresa, lojas, departamentos, setores, cargos, horario, quantidade=50):
    print(f"Criando {quantidade} funcionários...")
    funcionarios = []
    
    for i in range(quantidade):
        # Distribuir funcionários entre lojas, departamentos, setores e cargos
        loja = random.choice(lojas)
        departamento = random.choice(departamentos)
        setor = random.choice(setores)
        cargo = random.choice(cargos)
        
        # Gerar dados pessoais aleatórios
        nome_completo = fake.name()
        cpf = fake.cpf()
        data_nascimento = fake.date_of_birth(minimum_age=18, maximum_age=65)
        genero = random.choice(["MASCULINO", "FEMININO"])
        estado_civil = random.choice(["SOLTEIRO(A)", "CASADO(A)", "DIVORCIADO(A)", "VIÚVO(A)"])
        
        # Gerar dados de endereço
        cep = fake.postcode()
        endereco = fake.street_address()
        bairro = fake.bairro()
        cidade = fake.city()
        estado = fake.estado_sigla()
        celular = fake.phone_number()
        
        # Gerar dados profissionais
        matricula = f"F{i+1:04d}"
        data_admissao = fake.date_between(start_date="-5y", end_date="today")
        
        # Criar funcionário
        funcionario = Funcionario.objects.create(
            nome_completo=nome_completo,
            cpf=cpf,
            data_nascimento=data_nascimento,
            genero=genero,
            estado_civil=estado_civil,
            cep=cep,
            endereco=endereco,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
            celular1=celular,
            matricula=matricula,
            empresa=empresa,
            loja=loja,
            departamento=departamento,
            setor=setor,
            cargo=cargo,
            horario=horario,
            status=True,
            data_admissao=data_admissao
        )
        funcionarios.append(funcionario)
    
    return funcionarios

# Criar tipos de periféricos
def criar_tipos_perifericos():
    print("Criando tipos de periféricos...")
    tipos = [
        TipoPeriferico.objects.create(nome="MOUSE", descricao="Mouse para computador"),
        TipoPeriferico.objects.create(nome="TECLADO", descricao="Teclado para computador"),
        TipoPeriferico.objects.create(nome="MOUSEPAD", descricao="Base para mouse"),
        TipoPeriferico.objects.create(nome="FONE", descricao="Fone de ouvido")
    ]
    return tipos

# Criar salas
def criar_salas(lojas):
    print("Criando salas...")
    salas = []
    
    # 3 salas para a sede
    for i in range(3):
        salas.append(Sala.objects.create(
            nome=f"SALA {i+1}",
            titulo=f"Sala {i+1} da Sede",
            descricao=f"Sala {i+1} localizada na Sede",
            loja=lojas[0]  # Sede
        ))
    
    # 2 salas para cada uma das outras lojas
    for loja in lojas[1:]:  # Todas exceto a sede
        for i in range(2):
            salas.append(Sala.objects.create(
                nome=f"SALA {i+1}",
                titulo=f"Sala {i+1} da {loja.nome}",
                descricao=f"Sala {i+1} localizada na {loja.nome}",
                loja=loja
            ))
    
    return salas

# Criar ilhas
def criar_ilhas(salas):
    print("Criando ilhas...")
    ilhas = []
    
    for sala in salas:
        # Número aleatório de ilhas por sala (máximo 3)
        num_ilhas = random.randint(1, 3)
        for i in range(num_ilhas):
            ilhas.append(Ilha.objects.create(
                nome=f"ILHA {i+1}",
                titulo=f"Ilha {i+1} da {sala.nome}",
                sala=sala,
                quantidade_pas=random.randint(2, 4)  # Entre 2 e 4 PAs por ilha
            ))
    
    return ilhas

# Criar posições de atendimento (PAs)
def criar_pas(ilhas, max_pas_por_sala=12):
    print("Criando posições de atendimento (PAs)...")
    pas = []
    
    # Dicionário para controlar o número de PAs por sala
    pas_por_sala = {}
    
    for ilha in ilhas:
        sala_id = ilha.sala.id
        if sala_id not in pas_por_sala:
            pas_por_sala[sala_id] = 0
        
        # Número de PAs para esta ilha (respeitando o máximo por sala)
        pas_restantes = max_pas_por_sala - pas_por_sala[sala_id]
        if pas_restantes <= 0:
            continue
        
        num_pas = min(ilha.quantidade_pas, pas_restantes)
        
        for i in range(num_pas):
            pa = PosicaoAtendimento.objects.create(
                numero=f"{i+1:02d}",
                titulo=f"PA {i+1} da {ilha.nome}",
                ilha=ilha,
                sala=ilha.sala,
                status="livre"
            )
            pas.append(pa)
            pas_por_sala[sala_id] += 1
    
    return pas

# Criar computadores
def criar_computadores(lojas):
    print("Criando computadores...")
    computadores = []
    
    marcas = ["DELL", "HP", "LENOVO", "ACER", "ASUS"]
    modelos = ["Optiplex", "EliteDesk", "ThinkCentre", "Aspire", "ProDesk"]
    
    # Criar computadores suficientes para todas as PAs
    # Vamos criar mais do que o necessário para ter alguns disponíveis
    total_computadores = 100
    
    for i in range(total_computadores):
        marca = random.choice(marcas)
        modelo = f"{random.choice(modelos)} {random.choice(['3000', '5000', '7000'])}"
        loja = random.choice(lojas)
        
        computador = Computador.objects.create(
            marca=marca,
            modelo=modelo,
            numero_serie=f"SN{i+1:06d}",
            condicao=random.choice(["novo", "antigo"]),
            estado="funcionando",
            status="disponivel",
            loja=loja
        )
        computadores.append(computador)
    
    return computadores

# Criar monitores
def criar_monitores(lojas):
    print("Criando monitores...")
    monitores = []
    
    marcas = ["DELL", "LG", "SAMSUNG", "AOC", "PHILIPS"]
    modelos = ["P2419H", "24MP55", "S24F350", "24B1H", "242V8A"]
    tamanhos = ["21.5", "23.8", "24", "27"]
    resolucoes = ["1920x1080", "2560x1440", "3840x2160"]
    
    # Criar monitores suficientes para todas as PAs
    # Vamos criar mais do que o necessário para ter alguns disponíveis
    total_monitores = 100
    
    for i in range(total_monitores):
        marca = random.choice(marcas)
        modelo = random.choice(modelos)
        tamanho = random.choice(tamanhos)
        resolucao = random.choice(resolucoes)
        loja = random.choice(lojas)
        
        monitor = Monitor.objects.create(
            marca=marca,
            modelo=modelo,
            numero_serie=f"MON{i+1:06d}",
            tamanho=tamanho,
            resolucao=resolucao,
            condicao=random.choice(["novo", "antigo"]),
            estado="funcionando",
            status="disponivel",
            loja=loja,
            data_aquisicao=fake.date_between(start_date="-3y", end_date="today")
        )
        monitores.append(monitor)
    
    return monitores

# Criar periféricos
def criar_perifericos(tipos_perifericos, lojas):
    print("Criando periféricos...")
    perifericos = []
    
    marcas_por_tipo = {
        "MOUSE": ["LOGITECH", "MICROSOFT", "DELL", "HP"],
        "TECLADO": ["LOGITECH", "MICROSOFT", "DELL", "HP"],
        "MOUSEPAD": ["LOGITECH", "MULTILASER", "HUSKY", "HAVIT"],
        "FONE": ["LOGITECH", "HYPERX", "JBL", "HAVIT"]
    }
    
    # Criar periféricos suficientes para todas as PAs
    # Para cada tipo, vamos criar mais do que o necessário
    for tipo in tipos_perifericos:
        marcas = marcas_por_tipo.get(tipo.nome, ["GENÉRICO"])
        
        # 50 de cada tipo
        for i in range(50):
            marca = random.choice(marcas)
            modelo = f"Modelo {tipo.nome} {i+1}"
            loja = random.choice(lojas)
            
            periferico = Periferico.objects.create(
                tipo=tipo,
                marca=marca,
                modelo=modelo,
                numero_serie=f"{tipo.nome[:3]}{i+1:04d}",
                data_aquisicao=fake.date_between(start_date="-2y", end_date="today"),
                quantidade=1,
                loja=loja,
                status="disponivel",
                condicao=random.choice(["novo", "antigo"]),
                estado="funcionando"
            )
            perifericos.append(periferico)
    
    return perifericos

# Atribuir equipamentos às PAs
def atribuir_equipamentos(pas, computadores, monitores, perifericos, funcionarios):
    print("Atribuindo equipamentos às PAs...")
    
    # Agrupar periféricos por tipo
    perifericos_por_tipo = {}
    for p in perifericos:
        tipo_nome = p.tipo.nome
        if tipo_nome not in perifericos_por_tipo:
            perifericos_por_tipo[tipo_nome] = []
        perifericos_por_tipo[tipo_nome].append(p)
    
    # Para cada PA, atribuir um computador, um monitor e um conjunto de periféricos
    for pa in pas:
        # Atribuir computador
        computador = computadores.pop(0) if computadores else None
        if computador:
            computador.status = "em_uso"
            computador.save()
            AtribuicaoComputadorPA.objects.create(
                computador=computador,
                posicao_atendimento=pa,
                ativo=True
            )
        
        # Atribuir monitor
        monitor = monitores.pop(0) if monitores else None
        if monitor:
            monitor.status = "em_uso"
            monitor.save()
            AtribuicaoMonitorPA.objects.create(
                monitor=monitor,
                posicao_atendimento=pa,
                ativo=True
            )
        
        # Atribuir um periférico de cada tipo
        for tipo_nome, perifericos_tipo in perifericos_por_tipo.items():
            if perifericos_tipo:
                periferico = perifericos_tipo.pop(0)
                periferico.status = "em_uso"
                periferico.save()
                AtribuicaoPerifericoPA.objects.create(
                    periferico=periferico,
                    posicao_atendimento=pa,
                    data_atribuicao=datetime.now(),
                    ativo=True
                )
        
        # Atribuir funcionário (opcional)
        if funcionarios:
            funcionario = random.choice(funcionarios)
            AtribuicaoFuncionarioPA.objects.create(
                funcionario=funcionario,
                posicao_atendimento=pa,
                data_inicio=datetime.now().date(),
                ativo=True
            )
            # Atualizar status da PA
            pa.status = "ocupada"
            pa.save()

# Função principal
def popular_dados():
    print("Iniciando população de dados...")
    
    # Limpar dados existentes (opcional)
    limpar_dados()
    
    # Criar estrutura organizacional
    empresa = criar_empresa()
    lojas = criar_lojas(empresa)
    departamentos = criar_departamentos(empresa)
    setores = criar_setores(departamentos)
    cargos = criar_cargos(empresa)
    horario = criar_horario_trabalho()
    
    # Criar funcionários
    funcionarios = criar_funcionarios(empresa, lojas, departamentos, setores, cargos, horario, quantidade=50)
    
    # Criar estrutura física
    tipos_perifericos = criar_tipos_perifericos()
    salas = criar_salas(lojas)
    ilhas = criar_ilhas(salas)
    pas = criar_pas(ilhas)
    
    # Criar equipamentos
    computadores = criar_computadores(lojas)
    monitores = criar_monitores(lojas)
    perifericos = criar_perifericos(tipos_perifericos, lojas)
    
    # Atribuir equipamentos às PAs
    atribuir_equipamentos(pas, computadores, monitores, perifericos, funcionarios)
    
    print("\nPopulação de dados concluída com sucesso!")
    print(f"Foram criados:")
    print(f"- 1 Empresa")
    print(f"- {len(lojas)} Lojas")
    print(f"- {len(departamentos)} Departamentos")
    print(f"- {len(setores)} Setores")
    print(f"- {len(cargos)} Cargos")
    print(f"- {len(funcionarios)} Funcionários")
    print(f"- {len(salas)} Salas")
    print(f"- {len(ilhas)} Ilhas")
    print(f"- {len(pas)} PAs")
    print(f"- {len(tipos_perifericos)} Tipos de Periféricos")
    print(f"- {len(computadores)} Computadores")
    print(f"- {len(monitores)} Monitores")
    print(f"- {len(perifericos)} Periféricos")

# Executar o script
if __name__ == "__main__":
    popular_dados()