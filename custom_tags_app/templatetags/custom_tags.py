from django import template
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from ..permissions import get_user_info
from django.contrib.auth.models import Group

register = template.Library()

@register.simple_tag
def get_user_permissions(user):
    """
    Retorna o nível de permissão e o setor para o usuário autenticado.
    Para 'Administrador(a)' e 'Suporte', o setor não é necessário.
    """
    if not user.is_authenticated:
        return {'level': 0, 'setor': None}

    # Define o nível de permissão
    if user.groups.filter(name='Administrador(a)').exists():
        return {'level': 4, 'setor': None}
    elif user.groups.filter(name='Suporte').exists():
        return {'level': 3, 'setor': None}
    elif user.groups.filter(name='Supervisor(a)').exists():
        if user.groups.filter(name='SIAPE').exists():
            return {'level': 2, 'setor': 'SIAPE'}
        elif user.groups.filter(name='INSS').exists():
            return {'level': 2, 'setor': 'INSS'}
        elif user.groups.filter(name='LOJAS').exists():
            return {'level': 2, 'setor': 'LOJAS'}
    elif user.groups.filter(name='Atendente').exists():
        if user.groups.filter(name='SIAPE').exists():
            return {'level': 1, 'setor': 'SIAPE'}
        elif user.groups.filter(name='INSS').exists():
            return {'level': 1, 'setor': 'INSS'}
        elif user.groups.filter(name='LOJAS').exists():
            return {'level': 1, 'setor': 'LOJAS'}

    return {'level': 0, 'setor': None}

@register.simple_tag
def get_user_cargo(user):
    print(f"\n----- Obtendo cargo para o usuário: {user.username} -----")
    funcionario, departamento_nome, cargo, nivel = get_user_info(user)
    if funcionario:
        print(f"Funcionário: {funcionario}")
        print(f"Departamento: {departamento_nome}")
        print(f"Cargo: {cargo}")
        print(f"Nível: {nivel}")
        return {'departamento': departamento_nome, 'nivel': nivel, 'cargo': str(cargo)}
    else:
        print(f"Aviso: Usuário {user.username} não tem um funcionário associado.")
        return {'departamento': None, 'nivel': None, 'cargo': None}

@register.simple_tag
def can_view_button(user, button_type):
    """
    Verifica se o usuário pode ver determinado botão baseado em seu nível
    """
    funcionario, departamento_nome, cargo, nivel = get_user_info(user)
    
    if user.is_superuser:
        return True
        
    if not nivel:
        return False
        
    # Define a hierarquia de níveis
    niveis_hierarquia = {
        'TOTAL': 5,
        'SUPERVISOR GERAL': 4,
        'COORDENADOR': 3,
        'GERENTE': 2,
        'PADRÃO': 1,
        'ESTÁGIO': 0
    }
    
    # Pega o nível do usuário
    nivel_usuario = niveis_hierarquia.get(nivel, 0)
    
    # Define os níveis mínimos para cada tipo de botão
    niveis_minimos = {
        'consulta': 0,  # ESTÁGIO e acima
        'campanha': 5,  # TOTAL apenas
        'registro': 4,  # SUPERVISOR GERAL e acima
        'meta': 4       # SUPERVISOR GERAL e acima
    }
    
    # Verifica o nível mínimo necessário
    nivel_minimo = niveis_minimos.get(button_type, 5)  # Default para TOTAL
    
    return nivel_usuario >= nivel_minimo

@register.simple_tag
def get_user_groups(user):
    """
    Retorna os grupos do usuário e verifica permissões especiais
    """
    if not user.is_authenticated:
        return {'groups': [], 'is_admin': False}
        
    grupos = [group.name for group in user.groups.all()]
    is_admin = user.is_superuser or 'ADMINISTRAÇÃO' in grupos
    
    print(f"\n----- Obtendo grupos para o usuário: {user.username} -----")
    print(f"Grupos: {grupos}")
    print(f"É admin: {is_admin}")
    
    return {
        'groups': grupos,
        'is_admin': is_admin
    }

@register.simple_tag
def can_view_inss_button(user, button_type):
    """
    Verifica permissões específicas para botões do INSS
    """
    if user.is_superuser:
        return True
        
    funcionario, departamento_nome, cargo, nivel = get_user_info(user)
    
    # Função auxiliar para extrair o cargo base (antes do ' - ')
    def get_base_cargo(nome_cargo):
        return nome_cargo.split(' - ')[0] if ' - ' in nome_cargo else nome_cargo
    
    # Verifica se o usuário está no grupo correspondente
    is_atendente = any(get_base_cargo(group.name) == 'ATENDENTE' for group in user.groups.all())
    is_vendedor_loja = any(get_base_cargo(group.name) == 'VENDEDOR(A) LOJA' for group in user.groups.all())
    is_supervisor = any(group.name == 'VENDEDOR(A) - SUPERVISOR GERAL' for group in user.groups.all())
    
    # Verifica também o cargo do funcionário
    if cargo:
        cargo_grupo = Group.objects.get(id=cargo.id)
        cargo_base = get_base_cargo(cargo_grupo.name)
        is_atendente = is_atendente or cargo_base == 'ATENDENTE'
        is_vendedor_loja = is_vendedor_loja or cargo_base == 'VENDEDOR(A) LOJA'
        is_supervisor = is_supervisor or cargo_grupo.name == 'VENDEDOR(A) - SUPERVISOR GERAL'
    
    # Define permissões por tipo de botão
    if button_type in ['agendamento', 'confirmacao', 'reagendamento']:
        return is_atendente
    
    elif button_type in ['clientes_loja', 'todos_agendamentos']:
        return is_vendedor_loja
    
    elif button_type == 'agendamentos_tac':
        return is_vendedor_loja and is_supervisor
    
    return False

@register.simple_tag
def can_view_funcionarios_button(user, button_type):
    """
    Verifica permissões específicas para botões da área de funcionários
    """
    if user.is_superuser:
        return True
        
    funcionario, departamento_nome, cargo, nivel = get_user_info(user)
    
    # Verifica se o usuário está no departamento RH ou grupo RH
    is_rh = False
    if departamento_nome == 'RH' or user.groups.filter(name='RH').exists():
        is_rh = True
    
    # Verifica se o usuário é do TI (cargo ou grupo)
    is_ti = False
    if cargo and cargo.grupo.name == 'TI' or user.groups.filter(name='TI').exists():
        is_ti = True
    
    # Botões que requerem apenas RH
    rh_buttons = [
        'cadastro_funcionario',
        'cadastro_empresa',
        'cadastro_loja',
        'cadastro_departamento',
        'cadastro_cargo',
        'cadastro_horario',
        'lista_funcionarios'
    ]
    
    # Botões que requerem TI
    ti_buttons = [
        'cadastro_usuario',
        'associar_grupos'
    ]
    
    if button_type in rh_buttons:
        return is_rh
    elif button_type in ti_buttons:
        return is_ti
        
    return False


@register.simple_tag
def can_view_moneyplus(user):
    """
    Verifica se o usuário participa de alguma equipe ativa.
    """
    if not user.is_authenticated:
        return False

    return user.equipes.filter(status=True).exists()

@register.filter
def get_item(dictionary, key):
    """
    Filtro para acessar um item de um dicionário pela chave em templates
    Exemplo de uso: {{ meu_dicionario|get_item:minha_chave }}
    """
    if not dictionary:
        return None
    return dictionary.get(key)

@register.filter
def get_count(dictionary, key):
    """
    Retorna o valor de um dicionário para a chave especificada ou o próprio dicionário 
    se a chave não existir (para uso com múltiplos níveis de dicionários aninhados).
    Útil para acessar dicionários aninhados em templates.
    """
    if dictionary is None:
        return 0
    return dictionary.get(key, 0) if isinstance(dictionary, dict) else dictionary

@register.filter
def sum_values(dictionary):
    """
    Soma todos os valores em um dicionário.
    Útil para calcular totais em templates.
    """
    if not dictionary or not isinstance(dictionary, dict):
        return 0
    return sum(dictionary.values())

@register.filter
def format_chip_number(value):
    """
    Formata o número do chip no formato "xx x xxxx-xxxx".
    Exemplo: "85988887777" -> "85 9 8888-7777"
    """
    if not value:
        return value
    
    # Remove todos os caracteres não numéricos
    numero_limpo = ''.join(filter(str.isdigit, str(value)))
    
    # Verifica se tem pelo menos 10 dígitos para formatação
    if len(numero_limpo) < 10:
        return value  # Retorna o valor original se não tiver dígitos suficientes
    
    # Formata no padrão "xx x xxxx-xxxx"
    if len(numero_limpo) == 11:
        # Formato: 85988887777 -> 85 9 8888-7777
        return f"{numero_limpo[:2]} {numero_limpo[2]} {numero_limpo[3:7]}-{numero_limpo[7:]}"
    elif len(numero_limpo) == 10:
        # Formato: 8588887777 -> 85 8888-7777 (sem o dígito do meio)
        return f"{numero_limpo[:2]} {numero_limpo[2:6]}-{numero_limpo[6:]}"
    else:
        # Para outros tamanhos, tenta adaptar
        if len(numero_limpo) >= 11:
            return f"{numero_limpo[:2]} {numero_limpo[2]} {numero_limpo[3:7]}-{numero_limpo[7:11]}"
        else:
            return value  # Retorna o valor original se não conseguir formatar

@register.simple_tag
def get_pagination_range(current_page, total_pages, adjacents=2):
    """
    Gera uma lista de números de página para uma paginação "inteligente".
    Exemplo: [1, -1, 4, 5, 6, 7, 8, -1, 20] (onde -1 representa '...')
    adjacents: Quantos números de página mostrar de cada lado da página atual.
    """
    if total_pages <= 0 or current_page <= 0 or current_page > total_pages:
        return []

    # Quantas páginas mostrar no total, incluindo a atual e as adjacentes
    # (current) + (adjacents * 2) + (first) + (last) + (2 * ellipsis)
    # No máximo: 1 ... p-2 p-1 p p+1 p+2 ... N
    # Isso significa 7 números + 2 elipses no máximo
    MAX_PAGES_DISPLAYED_AROUND_CURRENT = 1 + (adjacents * 2) # current + 2*adjacents

    page_range = []

    # Caso 1: Total de páginas é pequeno, mostrar todas as páginas
    # (ex: 1 2 3 4 5 6 7)
    if total_pages <= MAX_PAGES_DISPLAYED_AROUND_CURRENT + 2: # +2 para a primeira e última página quando não há elipses
        page_range = list(range(1, total_pages + 1))
    else:
        # Caso 2: Total de páginas é grande, precisamos de "..."
        page_range.append(1) # Sempre mostrar a primeira página

        # "..." depois da primeira página?
        # Se a página atual está longe o suficiente da primeira página
        # (current_page - adjacents) > 1 (primeira página) + 1 (para o "...")
        if current_page - adjacents > 2:
            page_range.append(-1) # -1 representa "..."

        # Páginas ao redor da página atual
        start_page = max(2, current_page - adjacents)
        end_page = min(total_pages - 1, current_page + adjacents)
        
        # Ajustar start_page e end_page para garantir que tenhamos o número certo de páginas
        # Se current_page está perto do início
        if current_page - adjacents <= 2:
            end_page = min(total_pages -1, MAX_PAGES_DISPLAYED_AROUND_CURRENT)
        # Se current_page está perto do fim
        elif current_page + adjacents >= total_pages -1:
            start_page = max(2, total_pages - MAX_PAGES_DISPLAYED_AROUND_CURRENT + 1)

        for i in range(start_page, end_page + 1):
            page_range.append(i)

        # "..." antes da última página?
        # Se a página atual está longe o suficiente da última página
        # (current_page + adjacents) < total_pages - 1 (para o "...")
        if current_page + adjacents < total_pages - 1:
            page_range.append(-1)

        if total_pages > 1: # Só adiciona a última página se for diferente da primeira
            page_range.append(total_pages) # Sempre mostrar a última página

    # Remover duplicatas e garantir que -1 não fique ao lado de um número sequencial desnecessariamente
    # Ex: [1, -1, 2, 3, 4] deve ser [1, 2, 3, 4]
    # Ex: [1, 2, -1, 3, 4] não deve acontecer com a lógica acima, mas como precaução.
    final_range = []
    last_num = 0
    for num in page_range:
        if num == -1:
            if last_num != -1: # Evita "..." duplicados
                final_range.append(num)
        elif final_range and final_range[-1] == -1 and num == last_num + 1:
            # Se temos "... N" e N é last_num+1, removemos "..." e adicionamos N
            # Mas apenas se N-1 não estava já no range.
            # Isso é um pouco complexo de generalizar aqui, a lógica principal acima deve evitar a maioria dos casos.
            # Simplificação: se o num atual é sequencial ao número antes do -1, remove o -1.
            if len(final_range) > 1 and final_range[-2] == num -2 : # verifica se antes do -1 existia num-2
                 final_range.pop() # remove o -1
            final_range.append(num)
        elif last_num == -1 and num == 2 and 1 in final_range:
            # caso especial [1, -1, 2]
            if final_range == [1, -1]:
                final_range.pop()
            if num not in final_range: final_range.append(num)
        elif final_range and final_range[-1] == total_pages -1 and num == total_pages and -1 in final_range:
            # caso especial [..., N-1, N]
            idx_ellipsis = -1
            try:
                idx_ellipsis = final_range.index(-1)
                if final_range[idx_ellipsis+1] == total_pages - (MAX_PAGES_DISPLAYED_AROUND_CURRENT - (adjacents +1)):
                    pass # Não faz nada, pois o ... está correto
            except ValueError:
                 pass # Sem ellipsis, ok
            if num not in final_range: final_range.append(num)
        else:
            if num not in final_range: # Evita duplicatas de números (ex: 1 já adicionado, depois range começa em 1)
                final_range.append(num)
        last_num = num
    
    # Garante que se o range é [1, N], e N > 1, não haja duplicatas
    if len(final_range) == 2 and final_range[0] == 1 and final_range[1] == total_pages and total_pages > 1:
        pass # Ex: [1, 2] está ok.
    elif len(set(final_range)) < len(final_range):
        # Refaz sem a lógica de limpeza complexa se a limpeza introduziu problemas
        # Esta parte da limpeza é complexa e pode ser removida se causar problemas,
        # a lógica principal de construção do page_range é mais importante.
        pass

    return final_range