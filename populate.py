#!/usr/bin/env python
"""
Script para popular os módulos de TI e Funcionários do sistema MoneyLink-Pro.
Este script cria dados de exemplo para teste e demonstração.
"""
import os
import sys
import django
import random
from datetime import date, timedelta, datetime

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

# Importar os modelos após configurar o ambiente
from django.contrib.auth.models import User
from apps.funcionarios.models import (
    Empresa, Loja, Departamento, Setor, Cargo, Equipe, HorarioTrabalho, Funcionario
)
from apps.ti.models import (
    TipoPeriferico, Periferico, Computador, Sala, Ilha, PosicaoAtendimento,
    AtribuicaoFuncionarioPA, AtribuicaoPerifericoPA, AtribuicaoComputadorPA
)

# Função para limpar dados existentes
def limpar_dados():
    """Limpa os dados existentes nas tabelas relevantes"""
    print("Limpando dados existentes...")
    
    # Limpar módulo TI
    AtribuicaoComputadorPA.objects.all().delete()
    AtribuicaoPerifericoPA.objects.all().delete()
    AtribuicaoFuncionarioPA.objects.all().delete()
    PosicaoAtendimento.objects.all().delete()
    Ilha.objects.all().delete()
    Sala.objects.all().delete()
    Periferico.objects.all().delete()
    TipoPeriferico.objects.all().delete()
    Computador.objects.all().delete()
    
    # Limpar módulo Funcionários (com cuidado para preservar usuários existentes)
    # Não excluiremos funcionários existentes, apenas adicionaremos novos

# Função para criar dados de empresas e lojas
def criar_empresas_e_lojas():
    """Cria empresas e lojas de exemplo"""
    print("Criando empresas e lojas...")
    
    # Criar empresas
    empresa1 = Empresa.objects.create(
        nome="MONEY PROMOTORA",
        cnpj="12.345.678/0001-01",
        endereco="Av. Principal, 1000, Centro",
        status=True
    )
    
    empresa2 = Empresa.objects.create(
        nome="MONEY CORRESPONDENTE",
        cnpj="98.765.432/0001-02",
        endereco="Rua Secundária, 500, Bairro Sul",
        status=True
    )
    
    # Criar lojas
    loja1 = Loja.objects.create(
        nome="SEDE",
        empresa=empresa1,
        franquia=False,
        filial=False,
        status=True
    )
    
    loja2 = Loja.objects.create(
        nome="SALGADO FILHO",
        empresa=empresa1,
        franquia=False,
        filial=True,
        status=True
    )
    
    loja3 = Loja.objects.create(
        nome="SANTA MARIA",
        empresa=empresa1,
        franquia=True,
        filial=False,
        status=True
    )
    
    loja4 = Loja.objects.create(
        nome="CACHOEIRINHA",
        empresa=empresa2,
        franquia=False,
        filial=True,
        status=True
    )

    loja5 = Loja.objects.create(
        nome="SÃO LEOPOLDO",
        empresa=empresa2,
        franquia=True,
        filial=False,
        status=True
    )
    
    return [empresa1, empresa2], [loja1, loja2, loja3, loja4, loja5]

# Função para criar departamentos e setores
def criar_departamentos_e_setores(empresas):
    """Cria departamentos e setores de exemplo"""
    print("Criando departamentos e setores...")
    
    departamentos = []
    setores = []
    
    # Para empresa 1
    dept1 = Departamento.objects.create(nome="ADMINISTRATIVO", empresa=empresas[0], status=True)
    dept2 = Departamento.objects.create(nome="COMERCIAL", empresa=empresas[0], status=True)
    dept3 = Departamento.objects.create(nome="TI", empresa=empresas[0], status=True)
    departamentos.extend([dept1, dept2, dept3])
    
    # Setores para Administrativo
    setores.append(Setor.objects.create(nome="FINANCEIRO", departamento=dept1, status=True))
    setores.append(Setor.objects.create(nome="RECURSOS HUMANOS", departamento=dept1, status=True))
    
    # Setores para Comercial
    setores.append(Setor.objects.create(nome="VENDAS", departamento=dept2, status=True))
    setores.append(Setor.objects.create(nome="MARKETING", departamento=dept2, status=True))
    
    # Setores para TI
    setores.append(Setor.objects.create(nome="SUPORTE", departamento=dept3, status=True))
    setores.append(Setor.objects.create(nome="DESENVOLVIMENTO", departamento=dept3, status=True))
    
    # Para empresa 2
    dept4 = Departamento.objects.create(nome="OPERACIONAL", empresa=empresas[1], status=True)
    dept5 = Departamento.objects.create(nome="COMERCIAL", empresa=empresas[1], status=True)
    departamentos.extend([dept4, dept5])
    
    # Setores para Operacional
    setores.append(Setor.objects.create(nome="ATENDIMENTO", departamento=dept4, status=True))
    setores.append(Setor.objects.create(nome="PROCESSAMENTO", departamento=dept4, status=True))
    
    # Setores para Comercial
    setores.append(Setor.objects.create(nome="VENDAS", departamento=dept5, status=True))
    
    return departamentos, setores

# Função para criar cargos
def criar_cargos(empresas):
    """Cria cargos de exemplo"""
    print("Criando cargos...")
    
    cargos = []
    
    # Cargos para empresa 1
    cargos.append(Cargo.objects.create(
        nome="DESENVOLVEDOR", 
        empresa=empresas[0], 
        hierarquia=Cargo.HierarquiaChoices.PADRAO, 
        status=True
    ))
    
    cargos.append(Cargo.objects.create(
        nome="ANALISTA DE SUPORTE", 
        empresa=empresas[0], 
        hierarquia=Cargo.HierarquiaChoices.PADRAO, 
        status=True
    ))
    
    cargos.append(Cargo.objects.create(
        nome="GERENTE DE TI", 
        empresa=empresas[0], 
        hierarquia=Cargo.HierarquiaChoices.GERENTE, 
        status=True
    ))
    
    cargos.append(Cargo.objects.create(
        nome="ANALISTA FINANCEIRO", 
        empresa=empresas[0], 
        hierarquia=Cargo.HierarquiaChoices.PADRAO, 
        status=True
    ))
    
    cargos.append(Cargo.objects.create(
        nome="VENDEDOR", 
        empresa=empresas[0], 
        hierarquia=Cargo.HierarquiaChoices.PADRAO, 
        status=True
    ))
    
    # Cargos para empresa 2
    cargos.append(Cargo.objects.create(
        nome="ATENDENTE", 
        empresa=empresas[1], 
        hierarquia=Cargo.HierarquiaChoices.PADRAO, 
        status=True
    ))
    
    cargos.append(Cargo.objects.create(
        nome="SUPERVISOR", 
        empresa=empresas[1], 
        hierarquia=Cargo.HierarquiaChoices.SUPERVISOR_GERAL, 
        status=True
    ))
    
    return cargos

# Função para criar horários de trabalho
def criar_horarios_trabalho():
    """Cria horários de trabalho de exemplo"""
    print("Criando horários de trabalho...")
    
    horarios = []
    
    horarios.append(HorarioTrabalho.objects.create(
        nome="COMERCIAL PADRÃO",
        entrada="09:00",
        saida_almoco="12:00",
        volta_almoco="13:00",
        saida="18:00",
        status=True
    ))
    
    horarios.append(HorarioTrabalho.objects.create(
        nome="TURNO MANHÃ",
        entrada="08:00",
        saida_almoco="11:30",
        volta_almoco="12:30",
        saida="17:00",
        status=True
    ))
    
    horarios.append(HorarioTrabalho.objects.create(
        nome="TURNO TARDE",
        entrada="13:00",
        saida_almoco="16:00",
        volta_almoco="17:00",
        saida="22:00",
        status=True
    ))
    
    return horarios

# Função para criar equipes
def criar_equipes():
    """Cria equipes de exemplo"""
    print("Criando equipes...")
    
    equipes = []
    
    equipes.append(Equipe.objects.create(nome="EQUIPE DESENVOLVIMENTO", status=True))
    equipes.append(Equipe.objects.create(nome="EQUIPE SUPORTE", status=True))
    equipes.append(Equipe.objects.create(nome="EQUIPE VENDAS", status=True))
    
    return equipes

# Função para criar funcionários
def criar_funcionarios(empresas, lojas, departamentos, setores, cargos, horarios, equipes):
    """Cria funcionários de exemplo"""
    print("Criando funcionários...")
    
    funcionarios = []
    
    # Dados para criar funcionários base
    dados_funcionarios = [
        {
            "nome_completo": "João da Silva",
            "cpf": "111.222.333-01",
            "empresa": empresas[0],
            "loja": lojas[0],
            "departamento": departamentos[2],  # TI
            "setor": setores[5],  # DESENVOLVIMENTO
            "cargo": cargos[0],  # DESENVOLVEDOR
            "horario": horarios[0],  # COMERCIAL PADRÃO
            "equipe": equipes[0],  # EQUIPE DESENVOLVIMENTO
        },
        {
            "nome_completo": "Maria Oliveira",
            "cpf": "222.333.444-02",
            "empresa": empresas[0],
            "loja": lojas[0],
            "departamento": departamentos[2],  # TI
            "setor": setores[4],  # SUPORTE
            "cargo": cargos[1],  # ANALISTA DE SUPORTE
            "horario": horarios[0],  # COMERCIAL PADRÃO
            "equipe": equipes[1],  # EQUIPE SUPORTE
        },
        {
            "nome_completo": "Pedro Santos",
            "cpf": "333.444.555-03",
            "empresa": empresas[0],
            "loja": lojas[0],
            "departamento": departamentos[2],  # TI
            "setor": setores[4],  # SUPORTE
            "cargo": cargos[1],  # ANALISTA DE SUPORTE
            "horario": horarios[1],  # TURNO MANHÃ
            "equipe": equipes[1],  # EQUIPE SUPORTE
        },
        {
            "nome_completo": "Carlos Ferreira",
            "cpf": "444.555.666-04",
            "empresa": empresas[0],
            "loja": lojas[0],
            "departamento": departamentos[2],  # TI
            "setor": setores[5],  # DESENVOLVIMENTO
            "cargo": cargos[2],  # GERENTE DE TI
            "horario": horarios[0],  # COMERCIAL PADRÃO
            "equipe": equipes[0],  # EQUIPE DESENVOLVIMENTO
        },
        {
            "nome_completo": "Ana Pereira",
            "cpf": "555.666.777-05",
            "empresa": empresas[0],
            "loja": lojas[1],
            "departamento": departamentos[1],  # COMERCIAL
            "setor": setores[2],  # VENDAS
            "cargo": cargos[4],  # VENDEDOR
            "horario": horarios[0],  # COMERCIAL PADRÃO
            "equipe": equipes[2],  # EQUIPE VENDAS
        },
        {
            "nome_completo": "Lúcia Almeida",
            "cpf": "666.777.888-06",
            "empresa": empresas[1],
            "loja": lojas[3],
            "departamento": departamentos[3],  # OPERACIONAL
            "setor": setores[6],  # ATENDIMENTO
            "cargo": cargos[5],  # ATENDENTE
            "horario": horarios[1],  # TURNO MANHÃ
            "equipe": None,
        },
    ]
    
    # Criar os funcionários base
    for i, dados in enumerate(dados_funcionarios):
        # Calcular data de nascimento (entre 25 e 45 anos atrás)
        anos_atras = random.randint(25, 45)
        data_nasc = date.today() - timedelta(days=anos_atras*365)
        
        # Calcular data de admissão (entre 1 e 5 anos atrás)
        anos_atras_adm = random.randint(1, 5)
        data_adm = date.today() - timedelta(days=anos_atras_adm*365)
        
        funcionario = Funcionario.objects.create(
            nome_completo=dados["nome_completo"],
            cpf=dados["cpf"],
            data_nascimento=data_nasc,
            empresa=dados["empresa"],
            loja=dados["loja"],
            departamento=dados["departamento"],
            setor=dados["setor"],
            cargo=dados["cargo"],
            horario=dados["horario"],
            equipe=dados["equipe"],
            status=True,
            data_admissao=data_adm,
            matricula=f"F{i+1000:04d}",
        )
        
        funcionarios.append(funcionario)
    
    # Criar funcionários adicionais para todas as PAs
    # Precisamos de pelo menos 48 funcionários para cobrir todas as PAs (10+8+12+12+6)
    nomes = ["Roberto", "Fernanda", "Ricardo", "Juliana", "Marcelo", "Patricia", 
             "Gabriel", "Camila", "Felipe", "Amanda", "Lucas", "Bianca", 
             "Eduardo", "Renata", "Gustavo", "Carolina", "André", "Larissa", 
             "Daniel", "Natália", "Paulo", "Sofia", "Rafael", "Isabela", 
             "Rodrigo", "Mariana", "Henrique", "Vanessa", "Leonardo", "Carla",
             "Mateus", "Gabriela", "Marcos", "Tatiana", "Thiago", "Débora",
             "Vinícius", "Priscila", "Douglas", "Alessandra", "Bruno", "Jéssica"]
    
    sobrenomes = ["Silva", "Santos", "Oliveira", "Souza", "Pereira", "Lima", 
                  "Costa", "Ferreira", "Martins", "Rodrigues", "Almeida", "Nascimento",
                  "Lopes", "Carvalho", "Gomes", "Araujo", "Fernandes", "Ramos", 
                  "Vieira", "Barbosa", "Moreira", "Ribeiro", "Alves", "Dias"]
    
    # Gerando 50 funcionários adicionais
    for i in range(50):
        nome = random.choice(nomes)
        sobrenome1 = random.choice(sobrenomes)
        sobrenome2 = random.choice(sobrenomes)
        nome_completo = f"{nome} {sobrenome1} {sobrenome2}"
        
        # CPF único
        cpf = f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}"
        
        # Dados aleatórios
        empresa = random.choice(empresas)
        loja = random.choice([l for l in lojas if l.empresa == empresa])
        departamento = random.choice([d for d in departamentos if d.empresa == empresa])
        setor = random.choice([s for s in setores if s.departamento == departamento])
        cargo = random.choice([c for c in cargos if c.empresa == empresa])
        horario = random.choice(horarios)
        equipe = random.choice([None] + equipes) if random.random() > 0.3 else None
        
        # Calcular datas
        anos_atras = random.randint(20, 50)
        data_nasc = date.today() - timedelta(days=anos_atras*365)
        
        anos_atras_adm = random.randint(1, 3)
        data_adm = date.today() - timedelta(days=anos_atras_adm*365)
        
        funcionario = Funcionario.objects.create(
            nome_completo=nome_completo,
            cpf=cpf,
            data_nascimento=data_nasc,
            empresa=empresa,
            loja=loja,
            departamento=departamento,
            setor=setor,
            cargo=cargo,
            horario=horario,
            equipe=equipe,
            status=True,
            data_admissao=data_adm,
            matricula=f"F{i+2000:04d}",
        )
        
        funcionarios.append(funcionario)
    
    return funcionarios

# Função para criar elementos do módulo TI
def criar_ti(lojas, funcionarios):
    """Cria elementos do módulo TI"""
    print("Criando itens do módulo TI...")
    
    # Criar tipos de periféricos
    tipos_perifericos = [
        TipoPeriferico.objects.create(nome="Monitor", descricao="Monitores de vídeo"),
        TipoPeriferico.objects.create(nome="Teclado", descricao="Teclados USB e sem fio"),
        TipoPeriferico.objects.create(nome="Mouse", descricao="Mouses USB e sem fio"),
        TipoPeriferico.objects.create(nome="Headset", descricao="Fones de ouvido com microfone"),
        TipoPeriferico.objects.create(nome="Webcam", descricao="Câmeras para videoconferência"),
    ]
    
    # Criar periféricos
    perifericos = []
    marcas_perifericos = {
        "Monitor": ["Samsung", "LG", "Dell", "AOC"],
        "Teclado": ["Logitech", "Microsoft", "Multilaser", "Razer"],
        "Mouse": ["Logitech", "Microsoft", "Multilaser", "Razer"],
        "Headset": ["Logitech", "Razer", "HyperX", "JBL"],
        "Webcam": ["Logitech", "Microsoft", "Multilaser"],
    }
    
    modelos_perifericos = {
        "Monitor": ["LED 22\"", "LCD 24\"", "IPS 27\"", "Curvo 32\""],
        "Teclado": ["K120", "Office", "Wireless", "Gamer"],
        "Mouse": ["M100", "Wireless", "Office", "Gamer"],
        "Headset": ["H390", "Kraken", "Cloud", "Quantum"],
        "Webcam": ["C270", "LifeCam", "HD 1080p"],
    }
    
    # Criar periféricos para cada tipo e loja
    for tipo in tipos_perifericos:
        for loja in lojas:
            for _ in range(random.randint(10, 15)):  # 10-15 periféricos de cada tipo por loja
                marca = random.choice(marcas_perifericos[tipo.nome])
                modelo = random.choice(modelos_perifericos[tipo.nome])
                
                periferico = Periferico.objects.create(
                    tipo=tipo,
                    marca=marca,
                    modelo=modelo,
                    numero_serie=f"SN-{random.randint(10000, 99999)}",
                    data_aquisicao=date.today() - timedelta(days=random.randint(30, 730)),
                    quantidade=random.randint(1, 3),
                    loja=loja,
                    status='disponivel',
                )
                perifericos.append(periferico)
    
    # Criar computadores
    computadores = []
    marcas_computadores = ["Dell", "HP", "Lenovo", "Positivo"]
    
    for loja in lojas:
        for _ in range(random.randint(10, 15)):  # 10-15 computadores por loja
            marca = random.choice(marcas_computadores)
            
            computador = Computador.objects.create(
                marca=marca,
                quantidade=1,
                loja=loja,
                status='disponivel',
            )
            computadores.append(computador)
    
    # Criar salas conforme especificado
    salas = [
        Sala.objects.create(nome="Sala 1", descricao="Sala principal"),
        Sala.objects.create(nome="Sala 2", descricao="Sala secundária"),
        Sala.objects.create(nome="Sala 3", descricao="Sala auxiliar"),
    ]
    
    # Configuração específica de ilhas e PAs
    configuracao_ilhas = [
        {"sala": 0, "nome": "Ilha 1", "pas": 10},
        {"sala": 0, "nome": "Ilha 2", "pas": 8},
        {"sala": 1, "nome": "Ilha 1", "pas": 12},
        {"sala": 1, "nome": "Ilha 2", "pas": 12},
        {"sala": 2, "nome": "Ilha 1", "pas": 6},
    ]
    
    # Criar ilhas com a configuração específica
    ilhas = []
    pas = []
    
    for config in configuracao_ilhas:
        ilha = Ilha.objects.create(
            nome=config["nome"],
            sala=salas[config["sala"]],
            quantidade_pas=config["pas"],
        )
        ilhas.append(ilha)
        
        # Criar PAs para esta ilha
        for i in range(1, config["pas"] + 1):
            pa = PosicaoAtendimento.objects.create(
                numero=f"{i:02d}",
                ilha=ilha,
                sala=ilha.sala,
                status='livre',
            )
            pas.append(pa)
    
    # Atribuir funcionários a PAs (para todas as PAs)
    atribuicoes_func = []
    for i, pa in enumerate(pas):
        if i < len(funcionarios):
            funcionario = funcionarios[i]
            atribuicao = AtribuicaoFuncionarioPA.objects.create(
                funcionario=funcionario,
                posicao_atendimento=pa,
                data_inicio=date.today() - timedelta(days=random.randint(30, 180)),
                ativo=True,
            )
            
            # Atualizar status da PA
            pa.status = 'ocupada'
            pa.funcionario = funcionario
            pa.save()
            
            atribuicoes_func.append(atribuicao)
    
    # Atribuir periféricos a PAs
    atribuicoes_periferico = []
    tipos_disponiveis = {tipo.id: tipo.nome for tipo in tipos_perifericos}
    
    for pa in pas:  # Todas as PAs
        # Para cada PA, atribuir um item de cada tipo de periférico (se disponível)
        for tipo_id, tipo_nome in tipos_disponiveis.items():
            perifericos_disponiveis = [p for p in perifericos if p.tipo.id == tipo_id and p.status == 'disponivel']
            
            if perifericos_disponiveis:
                periferico = random.choice(perifericos_disponiveis)
                
                atribuicao = AtribuicaoPerifericoPA.objects.create(
                    periferico=periferico,
                    posicao_atendimento=pa,
                    data_atribuicao=datetime.now(),
                    ativo=True,
                )
                
                # Atualizar status do periférico
                periferico.status = 'em_uso'
                periferico.save()
                
                atribuicoes_periferico.append(atribuicao)
    
    # Atribuir computadores a PAs
    atribuicoes_computador = []
    for pa in pas:  # Todas as PAs
        computadores_disponiveis = [c for c in computadores if c.status == 'disponivel']
        
        if computadores_disponiveis:
            computador = random.choice(computadores_disponiveis)
            
            atribuicao = AtribuicaoComputadorPA.objects.create(
                computador=computador,
                posicao_atendimento=pa,
                ativo=True,
            )
            
            # Atualizar status do computador
            computador.status = 'em_uso'
            computador.save()
            
            atribuicoes_computador.append(atribuicao)
    
    return {
        'tipos_perifericos': tipos_perifericos,
        'perifericos': perifericos,
        'computadores': computadores,
        'salas': salas,
        'ilhas': ilhas,
        'pas': pas,
        'atribuicoes_func': atribuicoes_func,
        'atribuicoes_periferico': atribuicoes_periferico,
        'atribuicoes_computador': atribuicoes_computador,
    }

def main():
    """Função principal para popular o sistema"""
    print("Iniciando população dos módulos de TI e Funcionários...")
    
    limpar_dados()
    
    # Criar entidades de funcionários
    empresas, lojas = criar_empresas_e_lojas()
    departamentos, setores = criar_departamentos_e_setores(empresas)
    cargos = criar_cargos(empresas)
    horarios = criar_horarios_trabalho()
    equipes = criar_equipes()
    funcionarios = criar_funcionarios(empresas, lojas, departamentos, setores, cargos, horarios, equipes)
    
    # Criar entidades de TI
    ti_itens = criar_ti(lojas, funcionarios)
    
    print("População concluída com sucesso!")
    print(f"\nForam criados:")
    print(f"- {len(empresas)} empresas")
    print(f"- {len(lojas)} lojas")
    print(f"- {len(departamentos)} departamentos")
    print(f"- {len(setores)} setores")
    print(f"- {len(cargos)} cargos")
    print(f"- {len(horarios)} horários de trabalho")
    print(f"- {len(equipes)} equipes")
    print(f"- {len(funcionarios)} funcionários")
    print(f"- {len(ti_itens['tipos_perifericos'])} tipos de periféricos")
    print(f"- {len(ti_itens['perifericos'])} periféricos")
    print(f"- {len(ti_itens['computadores'])} computadores")
    print(f"- {len(ti_itens['salas'])} salas")
    print(f"- {len(ti_itens['ilhas'])} ilhas")
    print(f"- {len(ti_itens['pas'])} posições de atendimento")
    print(f"- {len(ti_itens['atribuicoes_func'])} atribuições de funcionários")
    print(f"- {len(ti_itens['atribuicoes_periferico'])} atribuições de periféricos")
    print(f"- {len(ti_itens['atribuicoes_computador'])} atribuições de computadores")

if __name__ == "__main__":
    main() 