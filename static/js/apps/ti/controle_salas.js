/**
 * controle_salas.js - Funcionalidades para o controle de salas do módulo TI
 * 
 * Este arquivo contém as funções para manipulação das abas de salas e ilhas,
 * animações de transição e ajuste de layout das PAs.
 */

$(document).ready(function() {
  // console.log('Document ready e controle_salas.js carregado.'); // Log de inicialização

  // Teste: Listener genérico de clique no documento
  // $(document).on('click', function(event) {
  //  console.log('Clique detectado no documento:', event.target);
  // });
  // Fim do Teste

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
  
  // Adicionar evento de clique aos indicadores de status das PAs
  document.querySelectorAll('.pa-status-indicator').forEach(statusIndicator => {
    statusIndicator.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      // console.log('Clique na bolinha de status detectado');
      
      const paCard = this.closest('.pa-card');
      const paId = paCard.getAttribute('data-pa-id');
      const currentStatus = this.classList[1].replace('status-', '');
      
      // Remover menus existentes
      document.querySelectorAll('.status-dropdown-menu').forEach(menu => menu.remove());
      
      // Criar menu dropdown com estilos inline para garantir a aparência correta
      const menuHtml = `
        <div class="status-dropdown-menu" style="position: absolute; z-index: 1000; background-color: white; border: 1px solid #ddd; border-radius: 6px; box-shadow: 0 3px 10px rgba(0,0,0,0.2); padding: 8px 0; min-width: 160px;">
          <div class="status-option" style="padding: 8px 12px; display: flex; align-items: center; cursor: pointer;" data-status="ocupada">
            <span style="width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 10px; background-color: #0d6efd;"></span>
            <span style="font-size: 0.9rem; color: #333;">Ocupada</span>
          </div>
          <div class="status-option" style="padding: 8px 12px; display: flex; align-items: center; cursor: pointer;" data-status="manutencao">
            <span style="width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 10px; background-color: #ffc107;"></span>
            <span style="font-size: 0.9rem; color: #333;">Manutenção</span>
          </div>
          <div class="status-option" style="padding: 8px 12px; display: flex; align-items: center; cursor: pointer;" data-status="inativa">
            <span style="width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 10px; background-color: #dc3545;"></span>
            <span style="font-size: 0.9rem; color: #333;">Vazia</span>
          </div>
        </div>
      `;
      
      // Adicionar menu ao DOM
      document.body.insertAdjacentHTML('beforeend', menuHtml);
      const menu = document.querySelector('.status-dropdown-menu');
      
      // console.log('Menu criado:', menu);
      
      // Posicionar o menu próximo à bolinha
      const rect = this.getBoundingClientRect();
      menu.style.position = 'absolute';
      menu.style.top = (rect.bottom + 5) + 'px';
      menu.style.left = (rect.left - 70) + 'px';
      
      // console.log('Posição do menu:', menu.style.top, menu.style.left);
      
      // Adicionar hover effect
      const options = menu.querySelectorAll('.status-option');
      options.forEach(option => {
        option.addEventListener('mouseover', function() {
          this.style.backgroundColor = '#f5f5f5';
        });
        option.addEventListener('mouseout', function() {
          this.style.backgroundColor = 'white';
        });
      });
      
      // Adicionar eventos de clique às opções do menu
      options.forEach(option => {
        option.addEventListener('click', function() {
          // console.log('Opção de status clicada');
          const novoStatus = this.getAttribute('data-status');
          
          // Remover o menu
          menu.remove();
          
          // Atualizar status no servidor
          atualizarStatusPA(paId, novoStatus, paCard);
        });
      });
      
      // Fechar o menu ao clicar fora dele
      document.addEventListener('click', function closeMenu(evt) {
        if (menu && !menu.contains(evt.target) && evt.target !== statusIndicator) {
          // console.log('Clique fora do menu - fechando');
          menu.remove();
          document.removeEventListener('click', closeMenu);
        }
      });
    });
  });
  
  // Função para atualizar o status da PA no servidor
  function atualizarStatusPA(paId, novoStatus, paCard) {
    $.ajax({
      url: '/ti/atualizar_status_pa/',
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      },
      data: {
        pa_id: paId,
        status: novoStatus,
        csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
      },
      success: function(response) {
        if (response.success) {
          // Atualizar elementos visuais
          atualizarVisualizacaoStatusPA(paCard, novoStatus);
          
          // Mostrar mensagem de sucesso
          mostrarMensagem('Status da PA atualizado com sucesso!', 'success');
        } else {
          mostrarMensagem('Erro ao atualizar status: ' + response.error, 'error');
        }
      },
      error: function() {
        mostrarMensagem('Erro ao comunicar com o servidor', 'error');
      }
    });
  }
  
  // Função para atualizar a visualização do status da PA
  function atualizarVisualizacaoStatusPA(paCard, novoStatus) {
    // Atualizar o indicador de status
    const statusIndicator = paCard.querySelector('.pa-status-indicator');
    statusIndicator.classList.remove('status-livre', 'status-ocupada', 'status-manutencao', 'status-inativa');
    statusIndicator.classList.add('status-' + novoStatus);
    
    // Atualizar o texto do title
    let title;
    switch(novoStatus) {
      case 'livre':
        title = 'Livre';
        break;
      case 'ocupada':
        title = 'Ocupada';
        break;
      case 'manutencao':
        title = 'Em Manutenção';
        break;
      case 'inativa':
        title = 'Inativa';
        break;
    }
    statusIndicator.setAttribute('title', title);
    
    // Atualizar o badge de status
    const statusBadge = paCard.querySelector('.pa-status .badge');
    statusBadge.classList.remove('bg-success', 'bg-primary', 'bg-warning', 'bg-danger', 'text-dark');
    
    switch(novoStatus) {
      case 'livre':
        statusBadge.classList.add('bg-success');
        statusBadge.textContent = 'Livre';
        break;
      case 'ocupada':
        statusBadge.classList.add('bg-primary');
        statusBadge.textContent = 'Ocupada';
        break;
      case 'manutencao':
        statusBadge.classList.add('bg-warning', 'text-dark');
        statusBadge.textContent = 'Em Manutenção';
        break;
      case 'inativa':
        statusBadge.classList.add('bg-danger');
        statusBadge.textContent = 'Inativa';
        break;
    }
  }
  
  // Função para mostrar mensagens de feedback
  function mostrarMensagem(mensagem, tipo) {
    const alertClass = tipo === 'success' ? 'alert-success' : 'alert-danger';
    const icon = tipo === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    const messageHTML = `
      <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
        <i class="${icon} me-2"></i> ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `;
    
    $('#message-container').html(messageHTML);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
      $('.alert').alert('close');
    }, 5000);
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
      // console.error('Elementos não encontrados para animação:', {
      //   container: containerSelector,
      //   currentPane: currentSelector,
      //   targetPane: targetSelector
      // });
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
  
  // --- Adicionado para remoção de periféricos --- 
  const modalBackdrop = $('#confirm-remove-periferico-backdrop');
  const modal = $('#confirm-remove-periferico-modal');
  const modalPerifericoNome = $('#modal-periferico-nome');
  const modalConfirmBtn = $('#modal-confirm-remove-btn');
  const modalCancelBtn = $('#modal-cancel-btn');
  const modalCloseBtn = $('#modal-close-btn');

  let dadosPerifericoParaRemover = null; // Para armazenar temporariamente os dados

  function abrirModalConfirmacao(perifericoId, paId, perifericoNome, perifericoElement) {
    dadosPerifericoParaRemover = { perifericoId, paId, perifericoElement };
    modalPerifericoNome.text(perifericoNome);
    modalBackdrop.addClass('show').fadeIn(200);
    modal.addClass('show').fadeIn(200);
    $('body').addClass('modal-open'); // Para desabilitar scroll da página se necessário
  }

  function fecharModalConfirmacao() {
    modalBackdrop.fadeOut(200, function() { $(this).removeClass('show'); });
    modal.fadeOut(200, function() { $(this).removeClass('show'); });
    $('body').removeClass('modal-open');
    dadosPerifericoParaRemover = null; // Limpar dados
  }

  $(document).on('click', '.periferico-tag', function(event) {
    const perifericoTag = $(this);
    const perifericoId = perifericoTag.data('periferico-id');
    const paCard = perifericoTag.closest('.pa-card');
    const paId = paCard.data('pa-id');
    const perifericoNome = perifericoTag.text();

    if (!perifericoId || !paId) {
      console.error('Não foi possível obter o ID do periférico ou da PA.');
      mostrarMensagem('Erro ao identificar o periférico ou a PA.', 'error');
      return;
    }

    abrirModalConfirmacao(perifericoId, paId, perifericoNome, perifericoTag);
  });

  modalConfirmBtn.on('click', function() {
    if (dadosPerifericoParaRemover) {
      removerPerifericoDaPA(
        dadosPerifericoParaRemover.perifericoId, 
        dadosPerifericoParaRemover.paId, 
        dadosPerifericoParaRemover.perifericoElement
      );
      fecharModalConfirmacao();
    }
  });

  modalCancelBtn.on('click', fecharModalConfirmacao);
  modalCloseBtn.on('click', fecharModalConfirmacao);
  modalBackdrop.on('click', function(event) {
    // Fechar se clicar diretamente no backdrop (não nos filhos)
    if (event.target === this) {
        fecharModalConfirmacao();
    }
  });

  // Função para enviar a requisição de remoção do periférico
  function removerPerifericoDaPA(perifericoId, paId, perifericoElement) {
    $.ajax({
      url: '/ti/remover_periferico_pa/', // Certifique-se que esta URL está correta
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val() // Garante o envio do token CSRF
      },
      data: JSON.stringify({ // Enviar dados como JSON
        periferico_id: perifericoId,
        pa_id: paId
      }),
      contentType: 'application/json; charset=utf-8',
      dataType: 'json',
      success: function(response) {
        if (response.success) {
          // Remover o elemento do periférico do DOM
          perifericoElement.fadeOut(300, function() { 
            $(this).remove(); 
            // Verificar se a lista de periféricos ficou vazia
            const perifericosList = paCard.find('.perifericos-list');
            if (perifericosList.children('.periferico-tag').length === 0) {
              perifericosList.html('<span class="text-muted">Nenhum periférico atribuído</span>');
            }
          });
          mostrarMensagem(response.message || 'Periférico removido com sucesso!', 'success');
        } else {
          mostrarMensagem('Erro ao remover periférico: ' + response.error, 'error');
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        console.error('Erro AJAX:', textStatus, errorThrown, jqXHR.responseText);
        let errorMsg = 'Erro ao comunicar com o servidor.';
        if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
          errorMsg = jqXHR.responseJSON.error;
        }
        mostrarMensagem(errorMsg, 'error');
      }
    });
  }
  // --- Fim da adição --- 

  // --- Lógica para Dropdown e Atribuição de Funcionários ---
  const funcionariosApiUrl = '/ti/api/funcionarios/'; // Certifique-se que esta URL está correta
  const atribuirFuncionarioApiUrl = '/ti/api/atribuir_funcionario_pa/'; // Certifique-se que esta URL está correta
  let funcionariosCache = null; // Cache simples para a lista de funcionários
  let activeDropdown = null; // Rastreia o dropdown ativo

  // Função para buscar funcionários (com cache)
  async function fetchFuncionarios() {
    if (funcionariosCache) {
      return funcionariosCache;
    }
    try {
      const response = await $.ajax({
        url: funcionariosApiUrl,
        method: 'GET',
        dataType: 'json'
      });
      if (response.funcionarios) {
        funcionariosCache = response.funcionarios;
        // Adicionar opção "Nenhum (Desatribuir)" no início
        // Verifica se a opção já não existe para evitar duplicação em re-fetches (embora cache deva prevenir)
        if (!funcionariosCache.find(f => f.id === 0)) {
          funcionariosCache.unshift({ id: 0, nome: "Nenhum (Desatribuir)", ramal: "" });
        }
        return funcionariosCache;
      } else {
        throw new Error(response.error || 'Erro desconhecido ao buscar funcionários.'); // Usar um erro mais específico
      }
    } catch (error) {
      console.error("Erro detalhado ao buscar funcionários:", error);
      let errorMsg = 'Erro desconhecido.';
      if (error.responseJSON && error.responseJSON.error) {
        // Erro vindo da nossa API Django
        errorMsg = error.responseJSON.error;
      } else if (error.statusText) {
        // Erro AJAX genérico (jqXHR object)
        errorMsg = `${error.statusText} (Status: ${error.status || 'N/A'})`;
      } else if (error.message) {
        // Erro JavaScript padrão
        errorMsg = error.message;
      } else if (typeof error === 'string'){
        // Se o erro for uma string
        errorMsg = error;
      }
      mostrarMensagem(`Erro ao buscar funcionários: ${errorMsg}`, 'error');
      return null;
    }
  }

  // Função para criar o HTML do dropdown
  function criarDropdownHTML(funcionarios, paId) {
    let itemsHTML = '';
    if (!funcionarios) return '<div class="funcionario-dropdown-menu p-2 text-danger">Erro ao carregar.</div>';

    funcionarios.forEach(func => {
      // Modificado para exibir o ramal próximo ao nome
      let nomeRamal = func.id === 0 ? 
        `<span class="nome">${func.nome}</span>` : 
        `<span class="nome">${func.nome} ${func.ramal ? `<span class="ramal-inline">(Ramal: ${func.ramal})</span>` : ''}</span>`;
      
      const itemClass = func.id === 0 ? 'desatribuir-item' : '';
      itemsHTML += `
        <div class="funcionario-dropdown-item ${itemClass}" data-funcionario-id="${func.id}" data-pa-id="${paId}">
          ${nomeRamal}
          ${func.id !== 0 && !func.ramal ? '<span class="ramal no-ramal">(Sem Ramal)</span>' : ''}
        </div>
      `;
    });

    return `<div class="funcionario-dropdown-menu" id="dropdown-pa-${paId}">${itemsHTML}</div>`;
  }

  // Função para mostrar/esconder e posicionar o dropdown
  async function toggleDropdownFuncionarios(button) {
    const paId = $(button).data('pa-id');
    const existingDropdown = $(`#dropdown-pa-${paId}`);

    // Fechar dropdown ativo se existir e não for o atual
    if (activeDropdown && activeDropdown.attr('id') !== `dropdown-pa-${paId}`) {
        activeDropdown.fadeOut(100, function() { $(this).remove(); });
        activeDropdown = null;
    }

    if (existingDropdown.length > 0) {
      // Se existe, apenas remove (fecha)
      existingDropdown.fadeOut(100, function() { $(this).remove(); });
      activeDropdown = null;
    } else {
      // Se não existe, busca dados, cria e mostra
      // Criar um loader flutuante próximo ao botão que clicamos
      const buttonRect = button.getBoundingClientRect();
      const loaderHTML = `<div id="dropdown-loader-${paId}" style="position: fixed; z-index: 9999; left: ${buttonRect.right + 10}px; top: ${buttonRect.top}px;">
                            <div class="spinner-border spinner-border-sm text-primary" role="status">
                              <span class="visually-hidden">Loading...</span>
                            </div>
                          </div>`;
      $('body').append(loaderHTML);
      
      const funcionarios = await fetchFuncionarios();
      $(`#dropdown-loader-${paId}`).remove(); // Remove o loader
      
      if (funcionarios) {
        const dropdownHTML = criarDropdownHTML(funcionarios, paId);
        
        // Anexar dropdown ao body em vez de dentro do card
        $('body').append(dropdownHTML);
        
        const newDropdown = $(`#dropdown-pa-${paId}`);
        activeDropdown = newDropdown;

        // Posicionar baseado na posição absoluta do botão na viewport
        const buttonRect = button.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        
        // Verificar se o dropdown ficará fora da janela à direita
        let leftPos = buttonRect.left;
        const dropdownWidth = newDropdown.outerWidth() || 300; // Uso estimado se ainda não calculado
        if (leftPos + dropdownWidth > viewportWidth - 20) {
          // Se vai sair da tela, posiciona à esquerda do botão
          leftPos = buttonRect.right - dropdownWidth;
        }
        
        newDropdown.css({
            position: 'fixed', // Posição fixa em relação à viewport
            top: (buttonRect.bottom + 5) + 'px',
            left: leftPos + 'px',
            display: 'none', // Começa escondido para o fadeIn
            zIndex: 9999 // Garante que fica acima de tudo
        });

        newDropdown.fadeIn(150);

        // Adicionar listener para seleção
        newDropdown.find('.funcionario-dropdown-item').on('click', function() {
          const selectedFuncId = $(this).data('funcionario-id');
          atribuirFuncionarioAPa(paId, selectedFuncId, $(`.pa-card[data-pa-id="${paId}"]`));
          if (activeDropdown) {
             activeDropdown.fadeOut(100, function() { $(this).remove(); });
             activeDropdown = null;
          }
        });
      } else {
          // Caso fetchFuncionarios falhe, mostrar mensagem de erro
          const errorHtml = `<div id="error-message-${paId}" style="position: fixed; z-index: 9999; left: ${buttonRect.right + 10}px; top: ${buttonRect.top}px; background: white; padding: 5px 10px; border-radius: 4px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); color: red;">
                              Falha ao carregar funcionários
                            </div>`;
          $('body').append(errorHtml);
          
          // Remover após alguns segundos
          setTimeout(() => {
            $(`#error-message-${paId}`).fadeOut(300, function() { $(this).remove(); });
          }, 3000);
      }
    }
  }

  // Função para atribuir funcionário via AJAX
  function atribuirFuncionarioAPa(paId, funcionarioId, paCardElement) {
    $.ajax({
      url: atribuirFuncionarioApiUrl,
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
      },
      data: JSON.stringify({
        pa_id: paId,
        funcionario_id: funcionarioId
      }),
      contentType: 'application/json; charset=utf-8',
      dataType: 'json',
      success: function(response) {
        if (response.success) {
          // Atualizar a interface da PA principal
          atualizarVisualizacaoFuncionarioPA(paCardElement, response.funcionario, response.novo_status);
          
          // Atualizar outras PAs afetadas (se funcionário foi removido de outras PAs)
          if (response.pas_afetadas && response.pas_afetadas.length > 0) {
            response.pas_afetadas.forEach(paAfetada => {
              // Encontrar o card da PA afetada
              const paAfetadaCard = $(`.pa-card[data-pa-id="${paAfetada.id}"]`);
              if (paAfetadaCard.length) {
                // Atualizar a interface da PA afetada (com funcionário = null)
                atualizarVisualizacaoFuncionarioPA(paAfetadaCard, null, paAfetada.status);
              }
            });
            
            // Mensagem específica mencionando a remoção de outras PAs
            if (response.funcionario) {
              // Construir a descrição da PA afetada
              let paAfetadaDesc = '';
              if (response.pas_afetadas.length > 0) {
                const paAfetada = response.pas_afetadas[0]; // Pega a primeira afetada para a mensagem
                paAfetadaDesc = ` Foi removido da PA ${paAfetada.numero} (Sala: ${paAfetada.sala}, Ilha: ${paAfetada.ilha}).`;
              } else {
                paAfetadaDesc = ''; // Nenhuma outra PA afetada
              }
              // Usar o número da PA alvo (response.pa_numero)
              mostrarMensagem(`Funcionário ${response.funcionario.nome} atribuído à PA ${response.pa_numero}.${paAfetadaDesc}`, 'success');
            } else {
              // Mensagem para desatribuição (funcionário removido)
              mostrarMensagem(`Funcionário removido da PA ${response.pa_numero}.`, 'success');
            }
          } else {
            // Mensagem padrão (caso não haja funcionário ou PAs afetadas - fallback)
            mostrarMensagem(response.message || `Funcionário atribuído à PA ${response.pa_numero} com sucesso!`, 'success');
          }
        } else {
          mostrarMensagem('Erro ao atribuir funcionário: ' + (response.error || 'Erro desconhecido'), 'error');
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        console.error('Erro AJAX ao atribuir funcionário:', textStatus, errorThrown, jqXHR.responseText);
        let errorMsg = 'Erro ao comunicar com o servidor para atribuição.';
        if (jqXHR.responseJSON && jqXHR.responseJSON.error) {
          errorMsg = jqXHR.responseJSON.error;
        }
        mostrarMensagem(errorMsg, 'error');
      }
    });
  }

  // Função para atualizar a UI do PA Card após atribuição/desatribuição
  function atualizarVisualizacaoFuncionarioPA(paCard, funcionarioData, novoStatus) {
    const paFuncionarioDiv = paCard.find('.pa-funcionario > div:first-child'); // O div que contém o nome/botão
    const paId = paCard.data('pa-id');

    // Limpar completamente o conteúdo da div
    paFuncionarioDiv.empty();
    
    // Sempre adicionar o label "Funcionário:" primeiro
    paFuncionarioDiv.append('<strong>Funcionário:</strong> ');

    if (funcionarioData) {
      // Adicionar nome do funcionário
      paFuncionarioDiv.append(`<span class="funcionario-nome">${funcionarioData.nome}</span>`);
      
      // Adicionar o botão de ramal
      let buttonHTML;
      if (funcionarioData.ramal) {
          buttonHTML = `
            <button type="button" class="btn btn-sm ramal-badge ms-2" data-pa-id="${paId}" data-action="change">
              Ramal: ${funcionarioData.ramal} <i class='bx bxs-down-arrow bx-xs ms-1'></i>
            </button>`;
      } else {
          buttonHTML = `
            <button type="button" class="btn btn-sm ramal-badge ms-2" data-pa-id="${paId}" data-action="change">
              Sem Ramal <i class='bx bxs-down-arrow bx-xs ms-1'></i>
            </button>`;
      }
      paFuncionarioDiv.append(buttonHTML);
    } else {
      // PA sem funcionário - adicionar "Não atribuído"
      paFuncionarioDiv.append('<span class="text-muted">Não atribuído</span>');
      
      // Adicionar botão de atribuir
      const assignButtonHTML = `
        <button type="button" class="btn btn-sm btn-outline-primary ms-2 assign-funcionario-btn" data-pa-id="${paId}" data-action="assign">
          <i class='bx bx-user-plus me-1'></i> Atribuir
        </button>`;
      paFuncionarioDiv.append(assignButtonHTML);
    }

    // Atualizar o status visual da PA (bolinha e badge)
    atualizarVisualizacaoStatusPA(paCard[0], novoStatus);
  }

  // Event Listener para os botões de ramal e atribuir (delegação de evento)
  $(document).on('click', '.ramal-badge, .assign-funcionario-btn', function(e) {
      e.preventDefault();
      e.stopPropagation(); // Impede que feche imediatamente se clicar no botão
      toggleDropdownFuncionarios(this);
  });

  // Event Listener para fechar dropdown ao clicar fora
  $(document).on('click', function(event) {
    if (activeDropdown && !$(event.target).closest('.funcionario-dropdown-menu').length && !$(event.target).closest('.ramal-badge, .assign-funcionario-btn').length) {
      activeDropdown.fadeOut(100, function() { $(this).remove(); });
      activeDropdown = null;
    }
  });

  // --- Fim da Lógica para Dropdown e Atribuição ---
}); 