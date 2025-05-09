/**
 * controle_salas.js - Funcionalidades para o controle de salas do módulo TI
 * 
 * Este arquivo contém as funções para manipulação das abas de salas e ilhas,
 * animações de transição e ajuste de layout das PAs.
 */

$(document).ready(function() {
  // Armazenar IDs ativos
  let currentSalaId = null;
  let currentIlhaIds = {};
  let previousSalaId = null;
  let previousIlhaIds = {};
  
  // Forçar a ocultação de abas não ativas
  $('.tab-pane').not('.active').hide();
  $('.tab-pane').not('.active').css('display', 'none');
  
  // Inicializar com o primeiro item ativo
  const firstSalaButton = document.querySelector('#salas-tab .nav-link.active');
  if (firstSalaButton) {
    currentSalaId = firstSalaButton.getAttribute('data-sala-id');
    previousSalaId = currentSalaId;
    
    // Para cada sala, registrar a ilha ativa inicial
    document.querySelectorAll('.tab-pane[id^="sala-"]').forEach(salaPane => {
      const salaId = salaPane.id.replace('sala-', '');
      const activeIlhaTab = salaPane.querySelector('.ilhas-tabs .nav-link.active');
      if (activeIlhaTab) {
        currentIlhaIds[salaId] = activeIlhaTab.getAttribute('data-ilha-id');
        previousIlhaIds[salaId] = currentIlhaIds[salaId];
      }
    });
  }
  
  // Garantir que as abas de Bootstrap não controlem a exibição
  $('button[data-bs-toggle="tab"]').on('click', function(e) {
    e.preventDefault();
    return false;
  });
  
  // Manipulação das abas de salas
  document.querySelectorAll('#salas-tab .nav-link').forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault(); // Prevenir comportamento padrão
      
      const targetSalaId = this.getAttribute('data-sala-id');
      
      // Não fazer nada se clicar na mesma sala
      if (currentSalaId === targetSalaId) {
        return;
      }
      
      // Remover classes ativas de todas as abas
      document.querySelectorAll('#salas-tab .nav-link').forEach(tab => {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
      });
      
      // Adicionar classe ativa para a aba clicada
      this.classList.add('active');
      this.setAttribute('aria-selected', 'true');
      
      // Determinar a direção baseada na comparação dos IDs
      const direction = parseInt(targetSalaId) > parseInt(currentSalaId) ? 'right' : 'left';
      
      // Mostrar o alvo antes da animação para garantir que o conteúdo esteja visível
      const currentSalaPane = document.querySelector(`#sala-${currentSalaId}`);
      const targetSalaPane = document.querySelector(`#sala-${targetSalaId}`);
      
      if (currentSalaPane && targetSalaPane) {
        // Importante: garantir que ambos estejam visíveis durante a transição
        targetSalaPane.style.display = 'block';
        currentSalaPane.style.display = 'block';
      }
      
      // Animar transição
      animateTabTransition(
        '#salas-tab-content',
        `#sala-${currentSalaId}`,
        `#sala-${targetSalaId}`,
        direction
      );
      
      // Atualizar referências de salas
      previousSalaId = currentSalaId;
      currentSalaId = targetSalaId;
      
      // Garantir que as PAs sejam organizadas corretamente após a mudança de sala
      setTimeout(organizarLayoutPAs, 100);
    });
  });
  
  // Manipulação das abas de ilhas para cada sala
  document.querySelectorAll('.ilhas-tabs .nav-link').forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault(); // Prevenir comportamento padrão
      
      const ilhaId = this.getAttribute('data-ilha-id');
      const salaId = this.closest('.tab-pane').id.replace('sala-', '');
      
      // Não fazer nada se clicar na mesma ilha
      if (currentIlhaIds[salaId] === ilhaId) {
        return;
      }
      
      // Remover classes ativas apenas das abas desta sala
      document.querySelectorAll(`#ilhas-sala-${salaId}-tab .nav-link`).forEach(tab => {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
      });
      
      // Adicionar classe ativa para a aba clicada
      this.classList.add('active');
      this.setAttribute('aria-selected', 'true');
      
      // Determinar a direção baseada na comparação dos IDs
      const direction = parseInt(ilhaId) > parseInt(currentIlhaIds[salaId] || 0) ? 'right' : 'left';
      
      // Mostrar o alvo antes da animação para garantir que o conteúdo esteja visível
      const currentIlhaPane = document.querySelector(`#ilha-${currentIlhaIds[salaId]}-sala-${salaId}`);
      const targetIlhaPane = document.querySelector(`#ilha-${ilhaId}-sala-${salaId}`);
      
      if (currentIlhaPane && targetIlhaPane) {
        // Importante: garantir que ambos estejam visíveis durante a transição
        targetIlhaPane.style.display = 'block';
        currentIlhaPane.style.display = 'block';
      }
      
      // Animar transição
      animateTabTransition(
        `#ilhas-sala-${salaId}-content`,
        `#ilha-${currentIlhaIds[salaId]}-sala-${salaId}`,
        `#ilha-${ilhaId}-sala-${salaId}`,
        direction
      );
      
      // Atualizar referências de ilhas
      previousIlhaIds[salaId] = currentIlhaIds[salaId];
      currentIlhaIds[salaId] = ilhaId;
      
      // Garantir que as PAs sejam organizadas corretamente após a mudança de ilha
      setTimeout(organizarLayoutPAs, 100);
    });
  });
  
  /**
   * Função para animar transição entre abas com slide horizontal
   * @param {string} containerSelector - Seletor do container das abas
   * @param {string} currentSelector - Seletor da aba atual
   * @param {string} targetSelector - Seletor da aba alvo
   * @param {string} direction - Direção da animação: 'left' ou 'right'
   */
  function animateTabTransition(containerSelector, currentSelector, targetSelector, direction) {
    const container = document.querySelector(containerSelector);
    const currentPane = document.querySelector(currentSelector);
    const targetPane = document.querySelector(targetSelector);
    
    if (!container || !currentPane || !targetPane) {
      console.error('Elementos não encontrados para animação:', {
        container: containerSelector,
        currentPane: currentSelector,
        targetPane: targetSelector
      });
      return;
    }
    
    // Garantir que ambos os painéis estejam visíveis antes da animação
    currentPane.style.display = 'block';
    targetPane.style.display = 'block';
    
    // Calcular a altura máxima entre os dois painéis antes de iniciar a animação
    const currentHeight = currentPane.offsetHeight;
    const targetHeight = targetPane.offsetHeight;
    const maxHeight = Math.max(currentHeight, targetHeight) + 50; // Adicionar margem extra
    
    // Definir altura mínima para o container para evitar redimensionamento durante a transição
    container.style.minHeight = `${maxHeight}px`;
    
    // Ocultar todos os painéis não envolvidos na transição
    document.querySelectorAll(`${containerSelector} > .tab-pane`).forEach(pane => {
      if (pane !== currentPane && pane !== targetPane) {
        pane.style.display = 'none';
      }
    });
    
    // Preparar os elementos para animação tipo slider
    // Configuração do container para a animação
    container.style.position = 'relative';
    container.style.overflow = 'hidden';
    
    // Em vez de usar position:absolute que pode causar bugs de layout,
    // vamos usar um wrapper para o efeito de slide
    
    // Criar um wrapper temporário para a animação
    const sliderWrapper = document.createElement('div');
    sliderWrapper.style.display = 'flex';
    sliderWrapper.style.width = '200%';
    sliderWrapper.style.transition = 'transform 0.5s ease-in-out';
    
    // Remover os painéis do container e adicioná-los ao wrapper
    container.appendChild(sliderWrapper);
    
    // Preparar o painel atual
    currentPane.style.width = '50%';
    currentPane.style.flexShrink = '0';
    currentPane.classList.add('show', 'active');
    
    // Preparar o painel alvo
    targetPane.style.width = '50%'; 
    targetPane.style.flexShrink = '0';
    
    // Adicionar os painéis ao wrapper na ordem correta dependendo da direção
    if (direction === 'right') {
      sliderWrapper.appendChild(currentPane);
      sliderWrapper.appendChild(targetPane);
      // Iniciar com o primeiro painel visível
      sliderWrapper.style.transform = 'translateX(0)';
    } else {
      sliderWrapper.appendChild(targetPane);
      sliderWrapper.appendChild(currentPane);
      // Iniciar com o segundo painel visível
      sliderWrapper.style.transform = 'translateX(-50%)';
    }
    
    // Forçar repaint
    void sliderWrapper.offsetWidth;
    
    // Iniciar animação deslizante
    if (direction === 'right') {
      // Deslizar para a esquerda para mostrar o segundo painel
      sliderWrapper.style.transform = 'translateX(-50%)';
    } else {
      // Deslizar para a direita para mostrar o primeiro painel
      sliderWrapper.style.transform = 'translateX(0)';
    }
    
    // Após o término da animação
    setTimeout(() => {
      // Restaurar os elementos para o DOM normal
      container.removeChild(sliderWrapper);
      
      // Restaurar estilos originais
      currentPane.style.width = '';
      currentPane.style.flexShrink = '';
      targetPane.style.width = '';
      targetPane.style.flexShrink = '';
      
      // Restaurar classes e visibilidade
      currentPane.classList.remove('show', 'active');
      currentPane.style.display = 'none';
      
      targetPane.classList.add('show', 'active');
      targetPane.style.display = 'block';
      
      container.appendChild(currentPane);
      container.appendChild(targetPane);
      
      // Deixar o container com altura automática após a transição completar
      setTimeout(() => {
        container.style.minHeight = '';
        container.style.position = '';
        container.style.overflow = '';
        
        // Disparar evento personalizado para que outros scripts possam reagir à conclusão da transição
        $(document).trigger('tabTransitionComplete', [targetSelector]);
        
        // Organizar as PAs após a animação com um pequeno atraso para garantir renderização
        setTimeout(organizarLayoutPAs, 50);
      }, 50);
    }, 500); // Tempo da animação
  }
  
  /**
   * Organiza as PAs na visualização para seguir o layout solicitado
   * Coluna esquerda: PA05 a PA01 de cima para baixo
   * Coluna direita: PA10 a PA06 de cima para baixo
   */
  function organizarLayoutPAs() {
    document.querySelectorAll('.pa-grid-dual-column').forEach(grid => {
      const leftColumn = grid.querySelector('.pa-column-left');
      const rightColumn = grid.querySelector('.pa-column-right');
      
      if (!leftColumn || !rightColumn) return;
      
      // Obter todas as PAs disponíveis na ilha
      const todasPAs = Array.from(grid.querySelectorAll('.pa-card'));
      
      if (todasPAs.length === 0) return;
      
      // Fazer uma cópia de segurança de todos os elementos PA antes de limpar as colunas
      const paBackups = todasPAs.map(pa => {
        return {
          element: pa,
          numero: parseInt(pa.querySelector('.pa-title span').textContent.replace('PA ', ''))
        };
      });
      
      // Limpar as colunas existentes
      leftColumn.innerHTML = '';
      rightColumn.innerHTML = '';
      
      // Ordenar todas as PAs por número
      paBackups.sort((a, b) => a.numero - b.numero); // Ordem crescente pelo número
      
      // Dividir as PAs em dois grupos - primeiro metade e segunda metade
      const metade = Math.ceil(paBackups.length / 2);
      const grupoPAsEsquerda = [];
      const grupoPAsDireita = [];
      
      // Separar PAs em dois grupos (1-5) e (6-10)
      paBackups.forEach(pa => {
        if (pa.numero <= metade) {
          // PAs de 1 a 5 vão para coluna esquerda
          grupoPAsEsquerda.push(pa);
        } else {
          // PAs de 6 a 10 vão para coluna direita
          grupoPAsDireita.push(pa);
        }
      });
      
      // Inverter a ordem para que os números maiores fiquem no topo
      grupoPAsEsquerda.sort((a, b) => b.numero - a.numero); // Ordem decrescente (5,4,3,2,1)
      grupoPAsDireita.sort((a, b) => b.numero - a.numero); // Ordem decrescente (10,9,8,7,6)
      
      // Adicionar PAs ordenadas às colunas
      grupoPAsEsquerda.forEach(pa => leftColumn.appendChild(pa.element));
      grupoPAsDireita.forEach(pa => rightColumn.appendChild(pa.element));
    });
  }
  
  // Executar a organização após o carregamento do DOM
  organizarLayoutPAs();
  
  // Executar novamente após um pequeno atraso para garantir que todos os elementos foram carregados
  setTimeout(organizarLayoutPAs, 500);
  
  // Ajustar responsividade para dispositivos móveis
  function adjustResponsiveLayout() {
    const windowWidth = window.innerWidth;
    const paGrids = document.querySelectorAll('.pa-grid-dual-column');
    
    if (windowWidth <= 992) {
      paGrids.forEach(grid => {
        grid.classList.add('mobile-layout');
      });
    } else {
      paGrids.forEach(grid => {
        grid.classList.remove('mobile-layout');
      });
    }
    
    // Reorganizar PAs sempre que a responsividade mudar
    organizarLayoutPAs();
  }
  
  // Chamar responsividade inicial
  adjustResponsiveLayout();
  
  // Ajustar quando a janela for redimensionada
  window.addEventListener('resize', adjustResponsiveLayout);
  
  // Reorganizar PAs quando abas são clicadas
  document.querySelectorAll('.nav-tabs .nav-link').forEach(tabLink => {
    tabLink.addEventListener('click', function() {
      // Aguardar a transição completar antes de reorganizar
      setTimeout(organizarLayoutPAs, 600);
    });
  });
  
  // Adicionar um ouvinte para o evento DOMContentLoaded para garantir que as PAs sejam organizadas
  document.addEventListener('DOMContentLoaded', function() {
    organizarLayoutPAs();
  });
}); 