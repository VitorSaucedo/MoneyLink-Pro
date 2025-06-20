#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para popular o banco de dados do módulo TI
Cria dados de teste para as lojas especificadas
"""

import os
import django
import random
from faker import Faker

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

# Importar modelos após configurar o ambiente Django
from apps.funcionarios.models import (
    Empresa, Loja, Departamento, Setor, Cargo, 
    HorarioTrabalho, Funcionario
)
from apps.ti.models import (
    TipoPeriferico, Periferico, Computador, Monitor,
    Sala, Ilha, PosicaoAtendimento, AtribuicaoFuncionarioPA,
    AtribuicaoPerifericoPA, AtribuicaoComputadorPA, AtribuicaoMonitorPA,
    Chip, Email, Storm, Sistema
)

# Inicializar Faker para geração de dados aleatórios
fake = Faker('pt_BR')

def criar_lojas():
    """Cria as lojas especificadas pelo usuário"""
    print("Verificando e criando lojas...")
    
    # Buscar empresa existente
    try:
        empresa = Empresa.objects.get(nome="MONEY PROMOTORA DE CRÉDITO LTDA")
    except Empresa.DoesNotExist:
        print("Erro: Empresa 'MONEY PROMOTORA DE CRÉDITO LTDA' não encontrada!")
        print("Criando empresa...")
        empresa = Empresa.objects.create(
            nome="MONEY PROMOTORA DE CRÉDITO LTDA",
            cnpj="12.345.678/0001-90",
            status=True
        )
        print("Empresa criada com sucesso!")
    
    lojas_nomes = ["Cachoeirinha", "São Leopoldo", "Santa Maria", "Salgado Filho"]
    lojas = []
    
    # Verificar se a loja SEDE existe
    try:
        loja_sede = Loja.objects.get(nome="SEDE")
        print("Loja SEDE encontrada.")
    except Loja.DoesNotExist:
        print("Criando loja SEDE...")
        loja_sede = Loja.objects.create(
            nome="SEDE",
            empresa=empresa,
            filial=False,
            franquia=False,
            status=True
        )
        print("Loja SEDE criada.")
    
    for nome in lojas_nomes:
        loja, created = Loja.objects.get_or_create(
            nome=nome,
            defaults={
                'empresa': empresa,
                'filial': True,
                'franquia': False,
                'status': True
            }
        )
        if created:
            print(f"Loja {nome} criada com sucesso!")
        else:
            print(f"Loja {nome} já existe.")
        lojas.append(loja)
    
    return lojas

def criar_tipos_perifericos():
    """Cria tipos de periféricos se não existirem"""
    print("Criando tipos de periféricos...")
    
    tipos = [
        {"nome": "Mouse", "descricao": "Dispositivo de entrada para navegação"},
        {"nome": "Mousepad", "descricao": "Base para mouse"},
        {"nome": "Teclado", "descricao": "Dispositivo de entrada para digitação"},
        {"nome": "Fone", "descricao": "Fone de ouvido com microfone"}
    ]
    
    tipos_criados = []
    for tipo_data in tipos:
        tipo, created = TipoPeriferico.objects.get_or_create(
            nome=tipo_data["nome"],
            defaults={"descricao": tipo_data["descricao"]}
        )
        tipos_criados.append(tipo)
        if created:
            print(f"Tipo {tipo.nome} criado!")
    
    return tipos_criados

def criar_departamentos_setores():
    """Cria departamentos e setores necessários"""
    print("Criando departamentos e setores...")
    
    try:
        empresa = Empresa.objects.get(nome="MONEY PROMOTORA DE CRÉDITO LTDA")
    except Empresa.DoesNotExist:
        print("Erro: Empresa não encontrada!")
        return [], []
    
    # Criar departamentos
    dept_vendas, _ = Departamento.objects.get_or_create(
        nome="VENDAS",
        defaults={'empresa': empresa, 'status': True}
    )
    
    dept_admin, _ = Departamento.objects.get_or_create(
        nome="ADMINISTRATIVO",
        defaults={'empresa': empresa, 'status': True}
    )
    
    # Criar setores
    setor_inss, _ = Setor.objects.get_or_create(
        nome="INSS",
        defaults={'departamento': dept_vendas, 'status': True}
    )
    
    setor_siape, _ = Setor.objects.get_or_create(
        nome="SIAPE",
        defaults={'departamento': dept_vendas, 'status': True}
    )
    
    # Buscar setor TI existente
    try:
        setor_ti = Setor.objects.get(nome="TI")
        print("Setor TI já existe.")
    except Setor.DoesNotExist:
        setor_ti = Setor.objects.create(
            nome="TI",
            departamento=dept_admin,
            status=True
        )
        print("Setor TI criado.")
    
    return [dept_vendas, dept_admin], [setor_inss, setor_siape, setor_ti]

def criar_cargos():
    """Cria cargos necessários"""
    print("Criando cargos...")
    
    try:
        empresa = Empresa.objects.get(nome="MONEY PROMOTORA DE CRÉDITO LTDA")
    except Empresa.DoesNotExist:
        print("Erro: Empresa não encontrada!")
        return []
    
    cargos_nomes = [
        "NEGOCIADOR(A)", "ANALISTA FINANCEIRO(A)", "VENDEDOR(A)",
        "ANALISTA DE TI", "GERENTE", "ASSISTENTE ADMINISTRATIVO"
    ]
    
    cargos = []
    for nome in cargos_nomes:
        cargo, created = Cargo.objects.get_or_create(
            nome=nome,
            defaults={
                'empresa': empresa,
                'hierarquia': Cargo.HierarquiaChoices.PADRAO,
                'status': True
            }
        )
        cargos.append(cargo)
    
    return cargos

def criar_horario_trabalho():
    """Cria horário de trabalho padrão"""
    print("Criando horário de trabalho...")
    
    horario, created = HorarioTrabalho.objects.get_or_create(
        nome="HORÁRIO COMERCIAL",
        defaults={
            'entrada': "08:00",
            'saida_almoco': "12:00",
            'volta_almoco': "13:00",
            'saida': "18:00",
            'status': True
        }
    )
    
    return horario

def criar_funcionarios(lojas, setores, cargos, horario):
    """Cria funcionários para as lojas"""
    print("Criando funcionários...")
    
    funcionarios = []
    ramal_counter = 1001  # Começar ramais em 1001
    
    for loja in lojas:
        # Criar 8-12 funcionários por loja
        num_funcionarios = random.randint(8, 12)
        
        for i in range(num_funcionarios):
            nome = fake.first_name()
            sobrenome = fake.last_name()
            
            funcionario = Funcionario.objects.create(
                nome_completo=f"{nome} {sobrenome}",
                cpf=fake.cpf(),
                data_nascimento=fake.date_of_birth(minimum_age=18, maximum_age=65),
                endereco=fake.address(),
                celular1=fake.phone_number(),
                data_admissao=fake.date_between(start_date='-2y', end_date='today'),
                empresa=loja.empresa,
                loja=loja,
                departamento=setores[0].departamento,  # Usar departamento do setor
                setor=random.choice(setores[:2]),  # INSS ou SIAPE
                cargo=random.choice(cargos[:5]),  # Cargos operacionais
                horario=horario,
                ramal=str(ramal_counter),
                status=True
            )
            funcionarios.append(funcionario)
            ramal_counter += 1  # Incrementar ramal sequencialmente
    
    print(f"Criados {len(funcionarios)} funcionários com ramais de 1001 a {ramal_counter-1}.")
    return funcionarios

def criar_salas(lojas, setores):
    """Cria salas para as lojas"""
    print("Criando salas...")
    
    salas = []
    
    for loja in lojas:
        # Criar 2-3 salas por loja
        num_salas = random.randint(2, 3)
        
        for i in range(1, num_salas + 1):
            sala = Sala.objects.create(
                nome=f"Sala {i}",
                titulo=f"Sala de Atendimento {i}",
                descricao=f"Sala de atendimento da loja {loja.nome}",
                loja=loja,
                setor=random.choice(setores[:2])  # INSS ou SIAPE
            )
            salas.append(sala)
    
    print(f"Criadas {len(salas)} salas.")
    return salas

def criar_ilhas(salas):
    """Cria ilhas para as salas"""
    print("Criando ilhas...")
    
    ilhas = []
    
    for sala in salas:
        # Criar 2-4 ilhas por sala
        num_ilhas = random.randint(2, 4)
        
        for i in range(1, num_ilhas + 1):
            quantidade_pas = random.randint(3, 6)
            
            ilha = Ilha.objects.create(
                nome=f"Ilha {i}",
                titulo=f"Ilha de Atendimento {i}",
                sala=sala,
                quantidade_pas=quantidade_pas,
                descricao=f"Ilha {i} da {sala.nome}"
            )
            ilhas.append(ilha)
    
    print(f"Criadas {len(ilhas)} ilhas.")
    return ilhas

def criar_posicoes_atendimento(ilhas):
    """Cria posições de atendimento para as ilhas"""
    print("Criando posições de atendimento...")
    
    pas = []
    
    for ilha in ilhas:
        for i in range(1, ilha.quantidade_pas + 1):
            pa = PosicaoAtendimento.objects.create(
                numero=f"{i:02d}",
                titulo=f"PA {i:02d}",
                ilha=ilha,
                sala=ilha.sala,
                status=random.choice(['livre', 'ocupada', 'livre', 'livre'])  # Mais livres
            )
            pas.append(pa)
    
    print(f"Criadas {len(pas)} posições de atendimento.")
    return pas

def criar_equipamentos(lojas, tipos_perifericos):
    """Cria equipamentos para as lojas"""
    print("Criando equipamentos...")
    
    computadores = []
    monitores = []
    perifericos = []
    
    marcas_computador = ["Dell", "HP", "Lenovo", "Acer", "Asus"]
    modelos_computador = ["OptiPlex 3080", "EliteDesk 800", "ThinkCentre M720", "Veriton X2660G", "VivoPC"]
    
    marcas_monitor = ["Samsung", "LG", "Dell", "AOC", "Philips"]
    tamanhos_monitor = ["19", "21", "22", "24", "27"]
    resolucoes = ["1366x768", "1920x1080", "1920x1200"]
    
    for loja in lojas:
        # Criar equipamentos baseado no número de funcionários estimado
        num_equipamentos = random.randint(15, 25)
        
        # Computadores
        for i in range(num_equipamentos):
            computador = Computador.objects.create(
                marca=random.choice(marcas_computador),
                modelo=random.choice(modelos_computador),
                numero_serie=f"PC{fake.random_number(digits=8)}",
                quantidade=1,
                condicao=random.choice(['novo', 'antigo']),
                estado='funcionando',
                status=random.choice(['disponivel', 'em_uso', 'disponivel']),
                loja=loja
            )
            computadores.append(computador)
        
        # Monitores
        for i in range(num_equipamentos):
            tamanho = random.choice(tamanhos_monitor)
            monitor = Monitor.objects.create(
                marca=random.choice(marcas_monitor),
                modelo=f"Monitor {tamanho}\"",
                numero_serie=f"MON{fake.random_number(digits=8)}",
                tamanho=tamanho,
                resolucao=random.choice(resolucoes),
                condicao=random.choice(['novo', 'antigo']),
                estado='funcionando',
                status=random.choice(['disponivel', 'em_uso', 'disponivel']),
                loja=loja,
                data_aquisicao=fake.date_between(start_date='-3y', end_date='today')
            )
            monitores.append(monitor)
        
        # Periféricos
        for tipo in tipos_perifericos:
            quantidade = random.randint(10, 20)
            
            for i in range(quantidade):
                marcas = {
                    'Mouse': ['Logitech', 'Microsoft', 'Dell', 'HP'],
                    'Mousepad': ['Logitech', 'Razer', 'SteelSeries', 'Corsair'],
                    'Teclado': ['Logitech', 'Microsoft', 'Dell', 'ABNT2'],
                    'Fone': ['Logitech', 'Plantronics', 'Jabra', 'Microsoft']
                }
                
                marca = random.choice(marcas.get(tipo.nome, ['Genérico']))
                
                periferico = Periferico.objects.create(
                    tipo=tipo,
                    marca=marca,
                    modelo=f"{marca} {tipo.nome}",
                    numero_serie=f"{tipo.nome[:3].upper()}{fake.random_number(digits=6)}",
                    data_aquisicao=fake.date_between(start_date='-2y', end_date='today'),
                    quantidade=1,
                    loja=loja,
                    status=random.choice(['disponivel', 'em_uso', 'disponivel']),
                    condicao=random.choice(['novo', 'antigo']),
                    estado='funcionando'
                )
                perifericos.append(periferico)
    
    print(f"Criados {len(computadores)} computadores, {len(monitores)} monitores e {len(perifericos)} periféricos.")
    return computadores, monitores, perifericos

def criar_atribuicoes(funcionarios, pas, computadores, monitores, perifericos):
    """Cria atribuições de funcionários e equipamentos às PAs"""
    print("Criando atribuições...")
    
    # Atribuir funcionários às PAs
    funcionarios_disponiveis = funcionarios.copy()
    random.shuffle(funcionarios_disponiveis)
    
    for i, pa in enumerate(pas[:len(funcionarios_disponiveis)]):
        if funcionarios_disponiveis:
            funcionario = funcionarios_disponiveis.pop()
            AtribuicaoFuncionarioPA.objects.create(
                funcionario=funcionario,
                posicao_atendimento=pa,
                data_inicio=fake.date_between(start_date='-6m', end_date='today'),
                ativo=True
            )
            pa.status = 'ocupada'
            pa.save()
    
    # Atribuir equipamentos às PAs ocupadas
    pas_ocupadas = [pa for pa in pas if pa.status == 'ocupada']
    
    # Computadores
    computadores_disponiveis = [c for c in computadores if c.status == 'disponivel']
    for pa in pas_ocupadas[:len(computadores_disponiveis)]:
        if computadores_disponiveis:
            computador = computadores_disponiveis.pop()
            AtribuicaoComputadorPA.objects.create(
                computador=computador,
                posicao_atendimento=pa,
                ativo=True
            )
            computador.status = 'em_uso'
            computador.save()
    
    # Monitores
    monitores_disponiveis = [m for m in monitores if m.status == 'disponivel']
    for pa in pas_ocupadas[:len(monitores_disponiveis)]:
        if monitores_disponiveis:
            monitor = monitores_disponiveis.pop()
            AtribuicaoMonitorPA.objects.create(
                monitor=monitor,
                posicao_atendimento=pa,
                ativo=True
            )
            monitor.status = 'em_uso'
            monitor.save()
    
    # Periféricos (mouse, mousepad, teclado e fone para cada PA ocupada)
    tipos_essenciais = ['Mouse', 'Mousepad', 'Teclado', 'Fone']
    for pa in pas_ocupadas:
        for tipo_nome in tipos_essenciais:
            perifericos_tipo = [p for p in perifericos 
                              if p.tipo.nome == tipo_nome and p.status == 'disponivel' 
                              and p.loja == pa.loja]
            if perifericos_tipo:
                periferico = perifericos_tipo[0]
                AtribuicaoPerifericoPA.objects.create(
                    periferico=periferico,
                    posicao_atendimento=pa,
                    data_atribuicao=fake.date_time_between(start_date='-3m', end_date='now'),
                    ativo=True
                )
                periferico.status = 'em_uso'
                periferico.save()
    
    print("Atribuições criadas com sucesso!")

def criar_chips_emails(funcionarios):
    """Cria chips e emails para funcionários"""
    print("Criando chips e emails...")
    
    chips_criados = 0
    emails_criados = 0
    
    # Chips - criar para metade dos funcionários se não existirem
    for i, funcionario in enumerate(funcionarios[:len(funcionarios)//2]):
        if not Chip.objects.filter(funcionario=funcionario).exists():
            # Gerar número único para o chip
            tentativas = 0
            while tentativas < 100:  # Limite de tentativas para evitar loop infinito
                numero_chip = f"(51) 9{fake.random_number(digits=4)}-{fake.random_number(digits=4)}"
                if not Chip.objects.filter(numero=numero_chip).exists():
                    break
                tentativas += 1
            
            if tentativas < 100:  # Se conseguiu gerar um número único
                Chip.objects.create(
                    numero=numero_chip,
                    funcionario=funcionario,
                    ramal=funcionario,
                    status='ativo',
                    data_entrega=fake.date_between(start_date='-1y', end_date='today')
                )
                chips_criados += 1
    
    # Emails - criar para todos os funcionários se não existirem
    for funcionario in funcionarios:
        if not Email.objects.filter(funcionario=funcionario).exists():
            nome_email = funcionario.nome_completo.lower().replace(' ', '.').replace('ç', 'c').replace('ã', 'a').replace('õ', 'o')
            email_address = f"{nome_email}@moneypromotora.com.br"
            
            # Verificar se o email já existe para evitar duplicatas
            if not Email.objects.filter(email=email_address).exists():
                Email.objects.create(
                    funcionario=funcionario,
                    ramal=funcionario,
                    email=email_address,
                    senha=fake.password(length=12),
                    status='ativo',
                    tipo='corporativo'
                )
                emails_criados += 1
            else:
                # Se o email já existe, criar um email alternativo com número
                contador = 1
                while Email.objects.filter(email=f"{nome_email}{contador}@moneypromotora.com.br").exists():
                    contador += 1
                email_alternativo = f"{nome_email}{contador}@moneypromotora.com.br"
                
                Email.objects.create(
                    funcionario=funcionario,
                    ramal=funcionario,
                    email=email_alternativo,
                    senha=fake.password(length=12),
                    status='ativo',
                    tipo='corporativo'
                )
                emails_criados += 1
    
    print(f"Criados {chips_criados} chips e {emails_criados} emails para funcionários.")

def criar_acessos_storm(funcionarios):
    """Cria acessos Storm para funcionários"""
    print("Criando acessos Storm...")
    
    acessos_criados = 0
    
    # Criar acessos Storm para funcionários que não possuem
    for funcionario in funcionarios:
        if not Storm.objects.filter(funcionario=funcionario).exists():
            # Gerar usuário com apenas números (1 a 4 dígitos)
            # Começar com um número baseado no índice do funcionário
            usuario_num = (funcionarios.index(funcionario) + 1) % 10000  # Garantir máximo 4 dígitos
            usuario = str(usuario_num).zfill(1)  # Pelo menos 1 dígito
            
            # Verificar se o usuário já existe ou se a combinação funcionario+usuario já existe
            tentativas = 0
            while (Storm.objects.filter(usuario=usuario).exists() or 
                   Storm.objects.filter(funcionario=funcionario, usuario=usuario).exists()) and tentativas < 10000:
                usuario_num = (usuario_num + 1) % 10000
                usuario = str(usuario_num).zfill(1)
                tentativas += 1
            
            # Gerar email administrativo único
            email_admin = fake.email()
            while Storm.objects.filter(email_administrativo=email_admin).exists():
                email_admin = fake.email()
            
            if tentativas < 10000:  # Se conseguiu gerar um usuário único
                Storm.objects.create(
                    funcionario=funcionario,
                    email_administrativo=email_admin,
                    usuario=usuario,
                    senha=fake.password(length=10),
                    situacao='ativo'
                )
                acessos_criados += 1
    
    print(f"Criados {acessos_criados} acessos Storm.")

def criar_acessos_sistema(funcionarios):
    """Cria acessos a sistemas para funcionários"""
    print("Criando acessos a sistemas...")
    
    sistemas_disponiveis = [
        "SIAPE", "INSS", "Money Plus", "Sistema Financeiro", 
        "CRM", "ERP", "Sistema de Vendas", "Portal RH"
    ]
    
    acessos_criados = 0
    
    for funcionario in funcionarios:
        # Criar 1-3 acessos por funcionário baseado no setor
        num_acessos = random.randint(1, 3)
        sistemas_funcionario = random.sample(sistemas_disponiveis, min(num_acessos, len(sistemas_disponiveis)))
        
        # Gerar nome de acesso no formato 'nomedofuncionario_sobrenome'
        nome_completo_parts = funcionario.nome_completo.split()
        if len(nome_completo_parts) >= 2:
            primeiro_nome = nome_completo_parts[0].lower()
            sobrenome = nome_completo_parts[-1].lower()
            nome_acesso = f"{primeiro_nome}_{sobrenome}"
        else:
            # Caso tenha apenas um nome, usar o nome completo
            nome_acesso = funcionario.nome_completo.lower().replace(' ', '_')
        
        for sistema in sistemas_funcionario:
            # Verificar se já existe um acesso para este funcionário com este nome
            acesso_final = nome_acesso
            contador = 1
            
            # Se já existe, adicionar número sequencial
            while Sistema.objects.filter(funcionario=funcionario, acesso=acesso_final).exists():
                acesso_final = f"{nome_acesso}{contador}"
                contador += 1
            
            Sistema.objects.create(
            funcionario=funcionario,
            acesso=acesso_final,
            senha=fake.password(length=8)
            )
            acessos_criados += 1
            break  # Criar apenas um acesso por funcionário com o formato nome_sobrenome
    
    print(f"Criados {acessos_criados} acessos a sistemas.")



def main():
    """Função principal"""
    print("=== INICIANDO POPULAÇÃO DO MÓDULO TI ===")
    
    # Criar lojas primeiro (isso criará a empresa se necessário)
    lojas = criar_lojas()
    if not lojas:
        print("Erro: Não foi possível criar as lojas. Verifique se a empresa existe.")
        return
    
    # Criar estrutura básica (agora que a empresa existe)
    departamentos, setores = criar_departamentos_setores()
    cargos = criar_cargos()
    horario = criar_horario_trabalho()
    
    # Criar tipos de periféricos
    tipos_perifericos = criar_tipos_perifericos()
    
    # Criar funcionários
    funcionarios = criar_funcionarios(lojas, setores, cargos, horario)
    
    # Criar estrutura física
    salas = criar_salas(lojas, setores)
    ilhas = criar_ilhas(salas)
    pas = criar_posicoes_atendimento(ilhas)
    
    # Criar equipamentos
    computadores, monitores, perifericos = criar_equipamentos(lojas, tipos_perifericos)
    
    # Criar atribuições
    criar_atribuicoes(funcionarios, pas, computadores, monitores, perifericos)
    
    # Criar chips e emails
    criar_chips_emails(funcionarios)
    
    # Criar acessos Storm
    criar_acessos_storm(funcionarios)
    
    # Criar acessos a sistemas
    criar_acessos_sistema(funcionarios)
    
    print("\n=== POPULAÇÃO CONCLUÍDA COM SUCESSO! ===")
    print(f"Lojas processadas: {len(lojas)}")
    print(f"Funcionários criados: {len(funcionarios)} (ramais de 1001 em diante)")
    print(f"Salas criadas: {len(salas)}")
    print(f"Ilhas criadas: {len(ilhas)}")
    print(f"PAs criadas: {len(pas)}")
    print(f"Computadores criados: {len(computadores)}")
    print(f"Monitores criados: {len(monitores)}")
    print(f"Periféricos criados: {len(perifericos)}")
    print(f"\nTodos os modelos do TI foram populados:")
    print(f"- Funcionários com ramais sequenciais (1001+)")
    print(f"- Chips e Emails associados aos funcionários")
    print(f"- Acessos Storm com usuários únicos")
    print(f"- Acessos a Sistemas variados")
    print(f"- Equipamentos associados às PAs")
    print(f"- Atribuições corretas entre funcionários e PAs")
    print(f"\nVerifique o banco de dados para confirmar os dados criados.")

if __name__ == "__main__":
    main()