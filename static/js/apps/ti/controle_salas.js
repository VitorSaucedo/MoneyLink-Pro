/**
 * controle_salas.js - Controlador principal do sistema de controle de salas
 * 
 * DEPENDÊNCIAS: controle_salas_carregamento.js, controle_salas_perifericos.js, 
 * controle_salas_funcionarios.js, controle_salas_manutencao.js, controle_salas_computadores.js
 */

// =============================================================================
// CONFIGURAÇÕES E CONSTANTES
// =============================================================================

const CONFIG = {
  urls: {
    atualizarStatus: '/ti/atualizar_status_pa/'
  },
  classes: {
    salaTab: '#salas-tab .nav-link',
    ilhaTab: '.ilhas-tabs .nav-link',
    paCard: '.pa-card',
    paGrid: '.pa-grid-dual-column',
    statusIndicator: '.pa-status-indicator'
  },
  animation: {
    duration: 500,
    transitionClass: 'slider-wrapper'
  },
  timeouts: {
    autoRemoveMessage: 5000,
    layoutDelay: 100,
    animationBuffer: 50,
    reloadDelay: 300
  }
};

const TEMPLATES = {
  message: (tipo, mensagem, icon, alertClass) => `
    <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
      <i class="${icon} me-2"></i> ${mensagem}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>`,

  statusMenu: `
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
    </div>`,

  reloadButton: `
    <button class="btn btn-sm btn-outline-secondary btn-reload-sala" 
            style="position: absolute; right: 15px; top: 15px;"
            title="Recarregar dados desta sala">
      <i class="fas fa-sync-alt"></i> Atualizar
    </button>`
};

const MESSAGE_CONFIG = {
  success: { alertClass: 'alert-success', icon: 'fas fa-check-circle' },
  error: { alertClass: 'alert-danger', icon: 'fas fa-exclamation-circle' },
  warning: { alertClass: 'alert-warning', icon: 'fas fa-exclamation-triangle' },
  info: { alertClass: 'alert-info', icon: 'fas fa-info-circle' },
  default: { alertClass: 'alert-primary', icon: 'fas fa-info-circle' }
};

const STATUS_CONFIG = {
  livre: { 
    class: 'status-livre', 
    badgeClass: 'bg-success', 
    title: 'Livre', 
    text: 'Livre' 
  },
  ocupada: { 
    class: 'status-ocupada', 
    badgeClass: 'bg-primary', 
    title: 'Ocupada', 
    text: 'Ocupada' 
  },
  manutencao: { 
    class: 'status-manutencao', 
    badgeClass: 'bg-warning text-dark', 
    title: 'Em Manutenção', 
    text: 'Em Manutenção' 
  },
  inativa: { 
    class: 'status-inativa', 
    badgeClass: 'bg-danger', 
    title: 'Inativa', 
    text: 'Inativa' 
  }
};

// =============================================================================
// ESTADO GLOBAL
// =============================================================================

const STATE = {
  currentSalaId: null,
  currentIlhaIds: {},
  previousSalaId: null,
  previousIlhaIds: {}
};

// =============================================================================
// UTILITÁRIOS E FUNÇÕES AUXILIARES
// =============================================================================

function mostrarMensagem(mensagem, tipo) {
  const config = MESSAGE_CONFIG[tipo] || MESSAGE_CONFIG.default;
  $('#message-container').empty();
  
  const messageHTML = TEMPLATES.message(tipo, mensagem, config.icon, config.alertClass);
  const $messageElement = $(messageHTML).appendTo('#message-container');
  
  setTimeout(() => {
    try {
      $messageElement.alert('close');
    } catch (e) {
      $messageElement.fadeOut(300, function() { $(this).remove(); });
    }
  }, CONFIG.timeouts.autoRemoveMessage);
}

function createSliderWrapper() {
  const wrapper = document.createElement('div');
  wrapper.className = CONFIG.animation.transitionClass;
  wrapper.style.display = 'flex';
  wrapper.style.width = '200%';
  wrapper.style.transition = `transform ${CONFIG.animation.duration / 1000}s ease-in-out`;
  return wrapper;
}

function prepareAnimation(container, currentPane, targetPane) {
  [currentPane, targetPane].forEach(pane => pane.style.display = 'block');
  
  document.querySelectorAll(`${container.tagName.toLowerCase()}#${container.id} > .tab-pane`)
    .forEach(pane => {
      if (pane !== currentPane && pane !== targetPane) {
        pane.style.display = 'none';
      }
    });
  
  container.style.position = 'relative';
  container.style.overflow = 'hidden';
}

function cleanupAnimation(container, sliderWrapper, currentPane, targetPane, targetSelector) {
  while (sliderWrapper.firstChild) {
    container.appendChild(sliderWrapper.firstChild);
  }
  container.removeChild(sliderWrapper);
  
  [currentPane, targetPane].forEach(pane => {
    pane.style.width = '';
    pane.style.flexShrink = '';
  });
  
  currentPane.classList.remove('show', 'active');
  currentPane.style.display = 'none';
  targetPane.classList.add('show', 'active');
  targetPane.style.display = 'block';
  
  $(document).trigger('tabTransitionComplete', [targetSelector]);
  
  setTimeout(() => {
    container.style.position = '';
    container.style.overflow = '';
    organizarLayoutPAs();
  }, CONFIG.timeouts.animationBuffer);
}

// =============================================================================
// SISTEMA DE ANIMAÇÕES E LAYOUT
// =============================================================================

function animateTabTransition(containerSelector, currentSelector, targetSelector, direction) {
  const container = document.querySelector(containerSelector);
  const currentPane = document.querySelector(currentSelector);
  const targetPane = document.querySelector(targetSelector);
  
  if (!container || !currentPane || !targetPane) {
    console.error('Elementos não encontrados para animação');
    return;
  }
  
  prepareAnimation(container, currentPane, targetPane);
  
  const sliderWrapper = createSliderWrapper();
  sliderWrapper.appendChild(currentPane);
  sliderWrapper.appendChild(targetPane);
  container.appendChild(sliderWrapper);
  
  [currentPane, targetPane].forEach(pane => {
    pane.style.width = '50%';
    pane.style.flexShrink = '0';
  });
  
  sliderWrapper.style.transform = 'translateX(0)';
  void sliderWrapper.offsetWidth; // Forçar repaint
  
  if (direction === 'right') {
    sliderWrapper.style.transform = 'translateX(-50%)';
  } else {
    sliderWrapper.style.transition = 'none';
    sliderWrapper.insertBefore(targetPane, currentPane);
    sliderWrapper.style.transform = 'translateX(-50%)';
    void sliderWrapper.offsetWidth;
    sliderWrapper.style.transition = `transform ${CONFIG.animation.duration / 1000}s ease-in-out`;
    sliderWrapper.style.transform = 'translateX(0)';
  }
  
  setTimeout(() => {
    cleanupAnimation(container, sliderWrapper, currentPane, targetPane, targetSelector);
  }, CONFIG.animation.duration);
}

function organizarLayoutPAs() {
  document.querySelectorAll(CONFIG.classes.paGrid).forEach(grid => {
    const leftColumn = grid.querySelector('.pa-column-left');
    const rightColumn = grid.querySelector('.pa-column-right');
    
    if (!leftColumn || !rightColumn) return;
    
    const todasPAs = Array.from(grid.querySelectorAll(CONFIG.classes.paCard))
      .map(pa => ({
        element: pa,
        numero: parseInt(pa.querySelector('.pa-title span').textContent.replace('PA ', ''))
      }))
      .sort((a, b) => a.numero - b.numero);
    
    if (todasPAs.length === 0) return;
    
    leftColumn.innerHTML = '';
    rightColumn.innerHTML = '';
    
    const metade = Math.ceil(todasPAs.length / 2);
    const grupoPAsEsquerda = todasPAs.filter(pa => pa.numero <= metade).sort((a, b) => b.numero - a.numero);
    const grupoPAsDireita = todasPAs.filter(pa => pa.numero > metade).sort((a, b) => b.numero - a.numero);
    
    grupoPAsEsquerda.forEach(pa => leftColumn.appendChild(pa.element));
    grupoPAsDireita.forEach(pa => rightColumn.appendChild(pa.element));
  });
}

function adjustResponsiveLayout() {
  const windowWidth = window.innerWidth;
  const paGrids = document.querySelectorAll(CONFIG.classes.paGrid);
  
  paGrids.forEach(grid => {
    grid.classList.toggle('mobile-layout', windowWidth <= 992);
  });
  
  organizarLayoutPAs();
}

// =============================================================================
// SISTEMA DE STATUS DAS PAs
// =============================================================================

function atualizarStatusPA(paId, novoStatus, paCard) {
  $.ajax({
    url: CONFIG.urls.atualizarStatus,
    method: 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    data: {
      pa_id: paId,
      status: novoStatus,
      csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
    },
    success: function(response) {
      if (response.success) {
        atualizarVisualizacaoStatusPA(paCard, novoStatus);
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

function atualizarVisualizacaoStatusPA(paCard, novoStatus) {
  const config = STATUS_CONFIG[novoStatus];
  if (!config) return;
  
  // Atualizar indicador de status
  const statusIndicator = paCard.querySelector(CONFIG.classes.statusIndicator);
  statusIndicator.className = `pa-status-indicator ${config.class}`;
  statusIndicator.setAttribute('title', config.title);
  
  // Atualizar badge de status
  const statusBadge = paCard.querySelector('.pa-status .badge');
  statusBadge.className = `badge ${config.badgeClass}`;
  statusBadge.textContent = config.text;
}

function criarMenuStatus(statusIndicator, paId, paCard) {
  document.querySelectorAll('.status-dropdown-menu').forEach(menu => menu.remove());
  
  document.body.insertAdjacentHTML('beforeend', TEMPLATES.statusMenu);
  const menu = document.querySelector('.status-dropdown-menu');
  
  const rect = statusIndicator.getBoundingClientRect();
  menu.style.top = (rect.bottom + 5) + 'px';
  menu.style.left = (rect.left - 70) + 'px';
  
  // Adicionar hover effects e eventos
  menu.querySelectorAll('.status-option').forEach(option => {
    option.addEventListener('mouseover', () => option.style.backgroundColor = '#f5f5f5');
    option.addEventListener('mouseout', () => option.style.backgroundColor = 'white');
    option.addEventListener('click', function() {
      const novoStatus = this.getAttribute('data-status');
      menu.remove();
      atualizarStatusPA(paId, novoStatus, paCard);
    });
  });
  
  // Fechar menu ao clicar fora
  const closeHandler = (evt) => {
    if (menu && !menu.contains(evt.target) && evt.target !== statusIndicator) {
      menu.remove();
      document.removeEventListener('click', closeHandler);
    }
  };
  document.addEventListener('click', closeHandler);
}

// =============================================================================
// SISTEMA DE NAVEGAÇÃO E ABAS
// =============================================================================

function initializeTabState() {
  $('.tab-pane').not('.active').hide().css('display', 'none');
  
  const firstSalaButton = document.querySelector('#salas-tab .nav-link.active');
  if (firstSalaButton) {
    STATE.currentSalaId = firstSalaButton.getAttribute('data-sala-id');
    STATE.previousSalaId = STATE.currentSalaId;
    
    document.querySelectorAll('.tab-pane[id^="sala-"]').forEach(salaPane => {
      const salaId = salaPane.id.replace('sala-', '');
      const activeIlhaTab = salaPane.querySelector('.ilhas-tabs .nav-link.active');
      if (activeIlhaTab) {
        STATE.currentIlhaIds[salaId] = activeIlhaTab.getAttribute('data-ilha-id');
        STATE.previousIlhaIds[salaId] = STATE.currentIlhaIds[salaId];
      }
    });
  }
}

function handleSalaNavigation(tab) {
  const targetSalaId = tab.getAttribute('data-sala-id');
  
  if (STATE.currentSalaId === targetSalaId) return;
  
  // Carregamento otimizado se disponível
  if (window.modoCarregamento === 'otimizado') {
    window.mostrarLoadingNaSala(targetSalaId);
    window.carregarDadosSala(targetSalaId);
  }
  
  // Atualizar classes ativas
  document.querySelectorAll('#salas-tab .nav-link').forEach(t => {
    t.classList.remove('active');
    t.setAttribute('aria-selected', 'false');
  });
  tab.classList.add('active');
  tab.setAttribute('aria-selected', 'true');
  
  // Determinar direção e animar
  const direction = parseInt(targetSalaId) > parseInt(STATE.currentSalaId) ? 'right' : 'left';
  
  const currentPane = document.querySelector(`#sala-${STATE.currentSalaId}`);
  const targetPane = document.querySelector(`#sala-${targetSalaId}`);
  
  if (currentPane && targetPane) {
    [currentPane, targetPane].forEach(pane => pane.style.display = 'block');
  }
  
  animateTabTransition(
    '#salas-tab-content',
    `#sala-${STATE.currentSalaId}`,
    `#sala-${targetSalaId}`,
    direction
  );
  
  STATE.previousSalaId = STATE.currentSalaId;
  STATE.currentSalaId = targetSalaId;
  
  setTimeout(organizarLayoutPAs, CONFIG.timeouts.layoutDelay);
}

function handleIlhaNavigation(tab) {
  const novoIlhaId = tab.getAttribute('data-ilha-id');
  const salaId = tab.closest('.tab-pane').id.replace('sala-', '');
  const ilhaAtivaAntesDoClique = STATE.currentIlhaIds[salaId];

  if (ilhaAtivaAntesDoClique === novoIlhaId) return;

  // Carregamento otimizado se disponível
  if (window.modoCarregamento === 'otimizado') {
    window.mostrarLoadingNaSala(salaId, novoIlhaId);
    window.carregarDadosSala(salaId, novoIlhaId);
  }
  
  // Atualizar classes ativas
  document.querySelectorAll(`#ilhas-sala-${salaId}-tab .nav-link`).forEach(t => {
    t.classList.remove('active');
    t.setAttribute('aria-selected', 'false');
  });
  tab.classList.add('active');
  tab.setAttribute('aria-selected', 'true');
  
  const direction = parseInt(novoIlhaId) > parseInt(ilhaAtivaAntesDoClique || 0) ? 'right' : 'left';
  
  const currentIlhaPaneSelector = `#ilha-${ilhaAtivaAntesDoClique}-sala-${salaId}`;
  const targetIlhaPaneSelector = `#ilha-${novoIlhaId}-sala-${salaId}`;
  
  const currentIlhaPane = document.querySelector(currentIlhaPaneSelector);
  const targetIlhaPane = document.querySelector(targetIlhaPaneSelector);

  if (!targetIlhaPane) {
    // Reverter alterações se o painel não existe
    tab.classList.remove('active');
    tab.setAttribute('aria-selected', 'false');
    const abaAnterior = document.querySelector(`#ilhas-sala-${salaId}-tab .nav-link[data-ilha-id="${ilhaAtivaAntesDoClique}"]`);
    if (abaAnterior) {
      abaAnterior.classList.add('active');
      abaAnterior.setAttribute('aria-selected', 'true');
    }
    mostrarMensagem(`Erro: Conteúdo da ilha ${novoIlhaId} não encontrado.`, 'error');
    return;
  }
  
  if (currentIlhaPane && targetIlhaPane) {
    [currentIlhaPane, targetIlhaPane].forEach(pane => pane.style.display = 'block');
    
    animateTabTransition(
      `#ilhas-sala-${salaId}-content`,
      currentIlhaPaneSelector,
      targetIlhaPaneSelector,
      direction
    );
  } else if (!currentIlhaPane && targetIlhaPane) {
    targetIlhaPane.style.display = 'block';
    targetIlhaPane.classList.add('show', 'active');
    setTimeout(organizarLayoutPAs, CONFIG.timeouts.layoutDelay);
    $(document).trigger('tabTransitionComplete', [targetIlhaPaneSelector]);
    
    STATE.previousIlhaIds[salaId] = ilhaAtivaAntesDoClique;
    STATE.currentIlhaIds[salaId] = novoIlhaId;
    return;
  }
  
  STATE.previousIlhaIds[salaId] = ilhaAtivaAntesDoClique;
  STATE.currentIlhaIds[salaId] = novoIlhaId;
  
  setTimeout(organizarLayoutPAs, CONFIG.animation.duration + CONFIG.timeouts.animationBuffer);
}

// =============================================================================
// SISTEMA DE BOTÃO DE RECARGA
// =============================================================================

function adicionarBotaoRecarga() {
  $('.btn-reload-sala').remove();
  
  if (STATE.currentSalaId) {
    const $salaPane = $(`#sala-${STATE.currentSalaId}`);
    if ($salaPane.length > 0 && $salaPane.find('.btn-reload-sala').length === 0) {
      const $headerSection = $salaPane.find('.sala-header').length > 0 ? 
                            $salaPane.find('.sala-header') : 
                            $salaPane.find('.container-fluid');
      
      if ($headerSection.length > 0) {
        $headerSection.css('position', 'relative').append(TEMPLATES.reloadButton);
        
        $headerSection.find('.btn-reload-sala').on('click', function() {
          const $icon = $(this).find('i');
          $icon.addClass('fa-spin');
          $(this).prop('disabled', true);
          
          const ilhaAtiva = STATE.currentIlhaIds[STATE.currentSalaId];
          window.mostrarLoadingNaSala(STATE.currentSalaId, ilhaAtiva);
          window.carregarDadosSala(STATE.currentSalaId, ilhaAtiva, true).finally(() => {
            $icon.removeClass('fa-spin');
            $(this).prop('disabled', false);
          });
        });
      }
    }
  }
}

// =============================================================================
// SISTEMA DE FILTRO DE LOJA
// =============================================================================

function setupLojaFilter() {
  $('#select-loja').on('change', function() {
    const lojaId = $(this).val();
    const url = new URL(window.location.href);
    
    // Sempre definir o parâmetro loja, já que não temos mais opção "Todas as Lojas"
    if (lojaId) {
      url.searchParams.set('loja', lojaId);
    }
    
    mostrarMensagem('Carregando salas da loja selecionada...', 'info');
    window.location.href = url.toString();
  });
  
  $('#form-filtro-loja').on('submit', function(e) {
    e.preventDefault();
    $('#select-loja').trigger('change');
  });
}

// =============================================================================
// EVENT HANDLERS
// =============================================================================

const EventHandlers = {
  init() {
    this.setupStatusIndicators();
    this.setupTabNavigation();
    this.setupResponsiveLayout();
    this.setupTabClicks();
  },
  
  setupStatusIndicators() {
    document.querySelectorAll(CONFIG.classes.statusIndicator).forEach(statusIndicator => {
      statusIndicator.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const paCard = this.closest(CONFIG.classes.paCard);
        const paId = paCard.getAttribute('data-pa-id');
        
        criarMenuStatus(this, paId, paCard);
      });
    });
  },
  
  setupTabNavigation() {
    // Salas
    document.querySelectorAll(CONFIG.classes.salaTab).forEach(tab => {
      tab.addEventListener('click', function(e) {
        e.preventDefault();
        handleSalaNavigation(this);
      });
    });
    
    // Ilhas
    document.querySelectorAll(CONFIG.classes.ilhaTab).forEach(tab => {
      tab.addEventListener('click', function(e) {
        e.preventDefault();
        handleIlhaNavigation(this);
      });
    });
  },
  
  setupResponsiveLayout() {
    adjustResponsiveLayout();
    window.addEventListener('resize', adjustResponsiveLayout);
    
    document.querySelectorAll('.nav-tabs .nav-link').forEach(tabLink => {
      tabLink.addEventListener('click', function() {
        setTimeout(organizarLayoutPAs, 600);
      });
    });
  },
  
  setupTabClicks() {
    // Garantir que as abas de Bootstrap não controlem a exibição
    $('button[data-bs-toggle="tab"]').on('click', function(e) {
      e.preventDefault();
      return false;
    });
    
    // Adicionar botão de recarga nas mudanças de sala
    document.querySelectorAll('#salas-tab .nav-link').forEach(tab => {
      const originalClickHandler = tab.onclick;
      tab.onclick = function(e) {
        if (originalClickHandler) originalClickHandler.call(this, e);
        setTimeout(adicionarBotaoRecarga, CONFIG.timeouts.reloadDelay);
      };
    });
  }
};

// =============================================================================
// INICIALIZAÇÃO
// =============================================================================

$(document).ready(function() {
  setupLojaFilter();
  initializeTabState();
  EventHandlers.init();
  adicionarBotaoRecarga();
  
  // Executar organização do layout
  organizarLayoutPAs();
  setTimeout(organizarLayoutPAs, CONFIG.animation.duration);
  
  // Adicionar eventos para reorganizar PAs
  document.addEventListener('DOMContentLoaded', organizarLayoutPAs);
});

// =============================================================================
// EXPOSIÇÃO GLOBAL
// =============================================================================

Object.assign(window, {
  mostrarMensagem,
  animateTabTransition,
  organizarLayoutPAs,
  adjustResponsiveLayout,
  atualizarStatusPA,
  atualizarVisualizacaoStatusPA
});