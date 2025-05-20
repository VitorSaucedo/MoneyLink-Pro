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
  
  // ===== Início do carregamento otimizado =====
  // Variáveis globais para controle de dados
  let dadosCarregados = {}; // Armazena dados já carregados por sala/ilha
  let carregamentosEmCurso = {}; // Evita carregamentos duplicados
  let modoCarregamento = document.getElementById('modo-carregamento')?.value || 'tradicional';
  
  // Inicializar com a sala ativa se estivermos no modo otimizado
  if (modoCarregamento === 'otimizado' && currentSalaId) {
    // Mostrar loader enquanto carregamos os dados iniciais
    mostrarLoadingNaSala(currentSalaId);
    // Iniciar carregamento da primeira sala
    carregarDadosSala(currentSalaId, currentIlhaIds[currentSalaId]);
  }
  
  // Função para mostrar o indicador de carregamento em uma sala específica
  function mostrarLoadingNaSala(salaId, ilhaId = null) {
    const containerSeletor = ilhaId 
      ? `#ilha-${ilhaId}`
      : `#sala-${salaId}`;
    
    const container = document.querySelector(containerSeletor);
    if (container) {
      // Adicionar overlay de carregamento se não existir
      if (!container.querySelector('.loading-overlay')) {
        const loadingHtml = `
          <div class="loading-overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                                        background-color: rgba(255,255,255,0.7); z-index: 1000; display: flex; 
                                        justify-content: center; align-items: center;">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Carregando...</span>
            </div>
          </div>
        `;
        container.style.position = 'relative'; // Assegurar posicionamento relativo
        container.insertAdjacentHTML('beforeend', loadingHtml);
      }
    }
  }
  
  // Função para remover o indicador de carregamento
  function esconderLoadingNaSala(salaId, ilhaId = null) {
    const containerSeletor = ilhaId 
      ? `#ilha-${ilhaId}`
      : `#sala-${salaId}`;
    
    const container = document.querySelector(containerSeletor);
    if (container) {
      const overlay = container.querySelector('.loading-overlay');
      if (overlay) {
        overlay.remove();
      }
    }
  }
  
  // Função para carregar dados de uma sala específica
  async function carregarDadosSala(salaId, ilhaId = null, forcarRecarga = false) {
    // Chave única para esta combinação de sala/ilha
    const cacheKey = `sala_${salaId}_ilha_${ilhaId || 'todas'}`;
    
    // Evitar múltiplas requisições simultâneas para a mesma sala/ilha
    if (carregamentosEmCurso[cacheKey]) {
      return;
    }
    
    // Verificar se já temos os dados em cache, exceto se forçar recarga
    if (!forcarRecarga && dadosCarregados[cacheKey]) {
      renderizarDadosSala(dadosCarregados[cacheKey], salaId, ilhaId);
      return;
    }
    
    // Marcar que estamos carregando esta sala/ilha
    carregamentosEmCurso[cacheKey] = true;
    
    try {
      // Construir URL com parâmetros de filtro
      let url = '/ti/api/controle-salas-dados/?sala_id=' + salaId;
      if (ilhaId) {
        url += '&ilha_id=' + ilhaId;
      }
      
      // Fazer a requisição
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erro na requisição: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Armazenar dados em cache
        dadosCarregados[cacheKey] = data;
        
        // Renderizar os dados na interface
        renderizarDadosSala(data, salaId, ilhaId);
      } else {
        throw new Error(data.error || 'Erro ao carregar dados da sala');
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      mostrarMensagem(`Erro ao carregar dados: ${error.message}`, 'error');
    } finally {
      // Finalizar indicadores de carregamento
      esconderLoadingNaSala(salaId, ilhaId);
      delete carregamentosEmCurso[cacheKey];
    }
  }
  
  // Função para renderizar os dados recebidos da API na interface
  function renderizarDadosSala(data, salaId, ilhaId = null) {
    // Obtemos as posições da resposta 
    const posicoes = data.posicoes || [];
    
    // Para cada posição, encontramos o elemento correspondente e atualizamos
    posicoes.forEach(pa => {
      const paCardElement = document.querySelector(`.pa-card[data-pa-id="${pa.id}"]`);
      if (!paCardElement) return; // Pular se o elemento não for encontrado
      
      // Atualizar status da PA
      atualizarVisualizacaoStatusPA(paCardElement, pa.status);
      
      // Atualizar funcionário
      if (pa.funcionario) {
        atualizarVisualizacaoFuncionarioPA(paCardElement, pa.funcionario, pa.status);
      } else {
        // Limpar dados de funcionário
        const funcionarioInfoElem = paCardElement.querySelector('.funcionario-info');
        if (funcionarioInfoElem) {
          funcionarioInfoElem.innerHTML = '<span class="text-muted">Sem funcionário atribuído</span>';
        }
      }
      
      // Atualizar periféricos
      atualizarPerifericosNaPA(paCardElement, pa.perifericos, pa.faltando);
      
      // Atualizar computadores
      atualizarVisualizacaoComputadoresPA(paCardElement, pa.computadores);
    });
    
    // Se temos mais dados para carregar (paginação)
    if (data.meta && data.meta.mais_resultados) {
      // Implementar lógica para "carregar mais" se necessário
      console.log('Há mais resultados disponíveis');
    }
  }
  
  // Função para adicionar botão de recarga na aba ativa
  function adicionarBotaoRecarga() {
    // Remover botões existentes primeiro para evitar duplicação
    document.querySelectorAll('.btn-reload-sala').forEach(btn => btn.remove());
    
    // Adicionar botão na sala ativa
    if (currentSalaId) {
      const salaPane = document.querySelector(`#sala-${currentSalaId}`);
      if (salaPane && !salaPane.querySelector('.btn-reload-sala')) {
        const headerSection = salaPane.querySelector('.sala-header') || salaPane.querySelector('.container-fluid');
        
        if (headerSection) {
          const btnHtml = `
            <button class="btn btn-sm btn-outline-secondary btn-reload-sala" 
                    style="position: absolute; right: 15px; top: 15px;"
                    title="Recarregar dados desta sala">
              <i class="fas fa-sync-alt"></i> Atualizar
            </button>
          `;
          headerSection.style.position = 'relative';
          headerSection.insertAdjacentHTML('beforeend', btnHtml);
          
          // Adicionar evento de click
          const btnReload = headerSection.querySelector('.btn-reload-sala');
          btnReload.addEventListener('click', function() {
            // Rotação do ícone para indicar carregamento
            const icon = this.querySelector('i');
            icon.classList.add('fa-spin');
            this.disabled = true;
            
            // Forçar recarga dos dados (ignorando cache)
            const ilhaAtiva = currentIlhaIds[currentSalaId];
            mostrarLoadingNaSala(currentSalaId, ilhaAtiva);
            carregarDadosSala(currentSalaId, ilhaAtiva, true).finally(() => {
              // Parar rotação quando carregamento terminar
              icon.classList.remove('fa-spin');
              this.disabled = false;
            });
          });
        }
      }
    }
  }
  
  // Adicionar o botão quando o DOM estiver pronto
  adicionarBotaoRecarga();
  
  // Adicionar o botão também quando trocar de sala
  document.querySelectorAll('#salas-tab .nav-link').forEach(tab => {
    const originalClickHandler = tab.onclick;
    tab.onclick = function(e) {
      // Chamar handler original se existir
      if (originalClickHandler) {
        originalClickHandler.call(this, e);
      }
      
      // Adicionar botão com um pequeno delay para garantir que a sala esteja visível
      setTimeout(adicionarBotaoRecarga, 300);
    };
  });
  
  // Função para atualizar periféricos em uma PA
  function atualizarPerifericosNaPA(paCardElement, perifericos = [], tiposFaltantes = []) {
    const perifericosContainer = paCardElement.querySelector('.perifericos-container');
    if (!perifericosContainer) return;
    
    // Limpar container
    perifericosContainer.innerHTML = '';
    
    // Adicionar cada periférico
    perifericos.forEach(periferico => {
      const perifericoHtml = `
        <div class="periferico-tag" data-periferico-id="${periferico.id}" data-tipo="${periferico.tipo}">
          <span class="periferico-tipo">${periferico.tipo}</span>: 
          <span class="periferico-marca">${periferico.marca}</span>
          ${periferico.modelo ? `<span class="periferico-modelo">${periferico.modelo}</span>` : ''}
        </div>
      `;
      perifericosContainer.insertAdjacentHTML('beforeend', perifericoHtml);
    });
    
    // Adicionar indicadores de periféricos faltantes
    const faltantesContainer = paCardElement.querySelector('.perifericos-faltantes');
    if (faltantesContainer) {
      faltantesContainer.innerHTML = '';
      
      if (tiposFaltantes.length > 0) {
        const faltantesHtml = tiposFaltantes.map(tipo => 
          `<span class="badge rounded-pill bg-warning text-dark me-1">${tipo}</span>`
        ).join('');
        
        faltantesContainer.innerHTML = `
          <div class="mt-2">
            <small class="text-muted">Faltando: </small>
            ${faltantesHtml}
          </div>
        `;
      }
    }
    
    // Reativar os eventos nos novos elementos
    paCardElement.querySelectorAll('.periferico-tag').forEach(tag => {
      tag.addEventListener('click', function(e) {
        e.stopPropagation();
        abrirMenuAcoesPeriferico($(this));
      });
    });
  }
  
  // Event listener para troca de abas de sala (modificado para carregamento otimizado)
  document.querySelectorAll('#salas-tab .nav-link').forEach(tab => {
    tab.addEventListener('click', function() {
      const salaId = this.getAttribute('data-sala-id');
      const targetPaneId = this.getAttribute('data-bs-target').replace('#', '');
      
      // Se estivermos no modo de carregamento otimizado
      if (modoCarregamento === 'otimizado') {
        // Mostrar loading na sala
        mostrarLoadingNaSala(salaId);
        // Carregar dados da sala selecionada
        carregarDadosSala(salaId);
      }
      
      // Armazenar sala anterior e atual
      previousSalaId = currentSalaId;
      currentSalaId = salaId;
      
      // Continuar com a lógica de animação existente...
    });
  });
  
  // Event listener para troca de abas de ilha (modificado para carregamento otimizado)
  // REMOVER ESTE BLOCO INTEIRO:
  // document.querySelectorAll('.ilhas-tabs .nav-link').forEach(tab => {
  //   tab.addEventListener('click', function() {
  //     const salaId = this.closest('.tab-pane').id.replace('sala-', '');
  //     const ilhaId = this.getAttribute('data-ilha-id');
      
  //     // Se estivermos no modo de carregamento otimizado
  //     if (modoCarregamento === 'otimizado') {
  //       // Mostrar loading na ilha
  //       mostrarLoadingNaSala(salaId, ilhaId);
  //       // Carregar dados específicos da ilha
  //       carregarDadosSala(salaId, ilhaId);
  //     }
      
  //     // Armazenar ilha anterior e atual para esta sala
  //     previousIlhaIds[salaId] = currentIlhaIds[salaId];
  //     currentIlhaIds[salaId] = ilhaId;
      
  //     // Continuar com a lógica de animação existente...
  //   });
  // });
  // ===== Fim do carregamento otimizado =====
  
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
      
      const novoIlhaId = this.getAttribute('data-ilha-id');
      const salaId = this.closest('.tab-pane').id.replace('sala-', '');
      const ilhaAtivaAntesDoClique = currentIlhaIds[salaId]; // ID da ilha que estava ativa

      // Não fazer nada se clicar na mesma ilha
      if (ilhaAtivaAntesDoClique === novoIlhaId) {
        return;
      }

      // Se estivermos no modo de carregamento otimizado
      if (modoCarregamento === 'otimizado') {
        // Mostrar loading na NOVA ilha
        mostrarLoadingNaSala(salaId, novoIlhaId);
        // Carregar dados da NOVA ilha
        carregarDadosSala(salaId, novoIlhaId);
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
      // Usar ilhaAtivaAntesDoClique para determinar a direção correta
      const direction = parseInt(novoIlhaId) > parseInt(ilhaAtivaAntesDoClique || 0) ? 'right' : 'left';
      
      // Selecionar os painéis
      const currentIlhaPaneSelector = `#ilha-${ilhaAtivaAntesDoClique}-sala-${salaId}`;
      const targetIlhaPaneSelector = `#ilha-${novoIlhaId}-sala-${salaId}`;
      
      const currentIlhaPane = document.querySelector(currentIlhaPaneSelector);
      const targetIlhaPane = document.querySelector(targetIlhaPaneSelector);
      
      // console.log(`[ILHAS] Tentando transição: DE ${currentIlhaPaneSelector} PARA ${targetIlhaPaneSelector}`);
      // console.log('[ILHAS] currentIlhaPane:', currentIlhaPane);
      // console.log('[ILHAS] targetIlhaPane:', targetIlhaPane);

      if (!targetIlhaPane) {
        // console.error(`[ILHAS] Painel alvo ${targetIlhaPaneSelector} não encontrado! Revertendo ativação da aba.`);
        // Reverter a ativação da aba
        this.classList.remove('active');
        this.setAttribute('aria-selected', 'false');
        // Reativar a aba anterior
        const abaAnterior = document.querySelector(`#ilhas-sala-${salaId}-tab .nav-link[data-ilha-id="${ilhaAtivaAntesDoClique}"]`);
        if (abaAnterior) {
          abaAnterior.classList.add('active');
          abaAnterior.setAttribute('aria-selected', 'true');
        }
        mostrarMensagem(`Erro: Conteúdo da ilha ${novoIlhaId} não encontrado.`, 'error');
        return; // Interrompe a execução
      }
      
      if (currentIlhaPane && targetIlhaPane) {
        // Importante: garantir que ambos estejam visíveis durante a transição
        targetIlhaPane.style.display = 'block';
        currentIlhaPane.style.display = 'block';
      } else if (!currentIlhaPane && targetIlhaPane) {
        // console.warn(`[ILHAS] Painel atual ${currentIlhaPaneSelector} não encontrado, mas o alvo ${targetIlhaPaneSelector} foi. Prosseguindo apenas com o alvo.`);
        // Se o painel atual não existe (ex: primeiro carregamento ou estado inconsistente),
        // apenas mostre o painel alvo sem animação de saída.
        targetIlhaPane.style.display = 'block';
        targetIlhaPane.classList.add('show', 'active');
        
        // Atualizar referências de ilhas APÓS determinar seletores
        previousIlhaIds[salaId] = ilhaAtivaAntesDoClique;
        currentIlhaIds[salaId] = novoIlhaId;
        
        setTimeout(organizarLayoutPAs, 100);
        $(document).trigger('tabTransitionComplete', [targetIlhaPaneSelector]); // Disparar evento para outros scripts
        return; // Pular animação se currentPane não existe
      }
      
      // Animar transição
      animateTabTransition(
        `#ilhas-sala-${salaId}-content`,
        currentIlhaPaneSelector, // Usar o ID da ilha que ESTAVA ativa
        targetIlhaPaneSelector,  // Usar o ID da NOVA ilha
        direction
      );
      
      // Atualizar referências de ilhas APÓS de obter os seletores corretos e iniciar a animação
      previousIlhaIds[salaId] = ilhaAtivaAntesDoClique;
      currentIlhaIds[salaId] = novoIlhaId;
      
      // Garantir que as PAs sejam organizadas corretamente após a mudança de ilha
      // O tempo aqui deve ser consistente com o tempo da animação em animateTabTransition
      setTimeout(organizarLayoutPAs, 550); // Ajustado para após a animação de 500ms + pequeno buffer
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
      console.error('Elementos não encontrados para animação');
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
    container.style.position = 'relative';
    container.style.overflow = 'hidden';
    
    // Criar um wrapper temporário para a animação
    const sliderWrapper = document.createElement('div');
    sliderWrapper.className = 'slider-wrapper';
    sliderWrapper.style.display = 'flex';
    sliderWrapper.style.width = '200%';
    sliderWrapper.style.transition = 'transform 0.5s ease-in-out';
    
    // Adicionar os painéis ao wrapper
    sliderWrapper.appendChild(currentPane);
    sliderWrapper.appendChild(targetPane);
    container.appendChild(sliderWrapper);
    
    // Preparar os painéis
    currentPane.style.width = '50%';
    currentPane.style.flexShrink = '0';
    targetPane.style.width = '50%';
    targetPane.style.flexShrink = '0';
    
    // Iniciar a animação
    // Configuração inicial: painel atual à esquerda, painel alvo à direita
    sliderWrapper.style.transform = 'translateX(0)';
    
    // Forçar repaint
    void sliderWrapper.offsetWidth;
    
    // Animar na direção apropriada
    if (direction === 'right') {
      // Deslizar para a esquerda (mostra o segundo painel)
      sliderWrapper.style.transform = 'translateX(-50%)';
    } else {
      // Para animação para a direita, precisamos reorganizar os painéis
      sliderWrapper.style.transition = 'none';
      sliderWrapper.insertBefore(targetPane, currentPane);
      sliderWrapper.style.transform = 'translateX(-50%)';
      
      // Forçar repaint novamente
      void sliderWrapper.offsetWidth;
      
      // Restaurar transição e animar
      sliderWrapper.style.transition = 'transform 0.5s ease-in-out';
      sliderWrapper.style.transform = 'translateX(0)';
    }
    
    // Após o término da animação
    setTimeout(() => {
      // Restaurar os painéis ao DOM normal
      while (sliderWrapper.firstChild) {
        container.appendChild(sliderWrapper.firstChild);
      }
      container.removeChild(sliderWrapper);
      
      // Restaurar estilos originais
      currentPane.style.width = '';
      currentPane.style.flexShrink = '';
      targetPane.style.width = '';
      targetPane.style.flexShrink = '';
      
      // Atualizar classes e visibilidade
      currentPane.classList.remove('show', 'active');
      currentPane.style.display = 'none';
      targetPane.classList.add('show', 'active');
      targetPane.style.display = 'block';
      
      // Disparar evento personalizado
      $(document).trigger('tabTransitionComplete', [targetSelector]);
      
      // Remover a altura mínima após um pequeno atraso para permitir que a renderização ocorra
      setTimeout(() => {
        // Definir para 'auto' permite que o container se ajuste ao conteúdo exibido
        container.style.minHeight = 'auto';
        container.style.position = '';
        container.style.overflow = '';
        
        // Organizar as PAs com o layout correto
        organizarLayoutPAs();
      }, 50);
    }, 500); // Tempo igual à duração da animação
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
  let activePerifericoActionMenu = null; // Para o menu de Ações do Periférico
  let activePerifericoStatusMenu = null; // Para o menu de Status do Periférico

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

  // --- Funções para o novo menu de ações do periférico ---

  // Função para fechar qualquer menu de periférico ativo
  function fecharMenusPerifericoAtivos() {
    if (activePerifericoActionMenu) {
      activePerifericoActionMenu.remove();
      activePerifericoActionMenu = null;
    }
    if (activePerifericoStatusMenu) {
      activePerifericoStatusMenu.remove();
      activePerifericoStatusMenu = null;
    }
  }

  function abrirMenuAcoesPeriferico(perifericoTag) {
    fecharMenusPerifericoAtivos(); // Fecha menus anteriores

    const perifericoId = perifericoTag.data('periferico-id');
    const paCard = perifericoTag.closest('.pa-card');
    const paId = paCard.data('pa-id');
    const perifericoNomeCompleto = perifericoTag.text().trim(); // ex: "Teclado Dell"
    const perifericoTipo = perifericoTag.data('periferico-tipo') || perifericoNomeCompleto.split(' ')[0]; // Tenta pegar o tipo específico
    
    // Verificar se estamos no tema escuro
    const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';
    
    // Definir cores com base no tema
    const bgColor = isDarkTheme ? '#202534' : 'white';
    const borderColor = isDarkTheme ? '#404758' : '#ccc';
    const textColor = isDarkTheme ? '#E1E2E6' : 'inherit';
    const shadowColor = isDarkTheme ? 'rgba(0,0,0,0.4)' : 'rgba(0,0,0,0.15)';
    const hoverBgColor = isDarkTheme ? '#343B4E' : '#f5f5f5';
    const removeTextColor = isDarkTheme ? '#EF6D7A' : '#dc3545';

    const menuHtml = `
      <div class="periferico-action-menu">
        <div class="periferico-action-item" data-action="update-status">
          <i class='bx bx-edit-alt me-2'></i>Atualizar Status
        </div>
        <div class="periferico-action-item remove-action" data-action="remove">
          <i class='bx bx-trash me-2'></i>Remover da PA
        </div>
      </div>
    `;

    $('body').append(menuHtml);
    activePerifericoActionMenu = $('.periferico-action-menu');

    const rect = perifericoTag[0].getBoundingClientRect();
    activePerifericoActionMenu.css({
      top: (rect.bottom + window.scrollY + 5) + 'px',
      left: (rect.left + window.scrollX) + 'px',
    });

    activePerifericoActionMenu.find('.periferico-action-item').hover(
      function() { $(this).addClass('hover'); },
      function() { $(this).removeClass('hover'); }
    );

    activePerifericoActionMenu.find('.periferico-action-item[data-action="update-status"]').on('click', function(event) {
      event.stopPropagation(); // IMPEDE PROPAGAÇÃO
      fecharMenusPerifericoAtivos();
      abrirMenuAtualizarStatusPeriferico(perifericoId, perifericoNomeCompleto, perifericoTipo, paId, perifericoTag);
    });

    activePerifericoActionMenu.find('.periferico-action-item[data-action="remove"]').on('click', function(event) {
      event.stopPropagation(); // IMPEDE PROPAGAÇÃO
      fecharMenusPerifericoAtivos();
      abrirModalConfirmacao(perifericoId, paId, perifericoNomeCompleto, perifericoTag);
    });

    // Fechar ao clicar fora
    $(document).on('click.closePerifericoActionMenu', function(event) {
      if (activePerifericoActionMenu && !$(event.target).closest('.periferico-action-menu').length && !perifericoTag.is(event.target) && !perifericoTag.find(event.target).length) {
        fecharMenusPerifericoAtivos();
        $(document).off('click.closePerifericoActionMenu');
      }
    });
  }

  function abrirMenuAtualizarStatusPeriferico(perifericoId, perifericoNome, perifericoTipo, paId, perifericoTagElement) {
    console.log('[LOG] abrirMenuAtualizarStatusPeriferico INICIADA para periférico:', perifericoNome, 'ID:', perifericoId, 'PA ID:', paId);
    fecharMenusPerifericoAtivos(); // Fecha action menu e qualquer status menu anterior

    // Verificar se estamos no tema escuro
    const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';
    
    // Definir cores com base no tema
    const bgColor = isDarkTheme ? '#202534' : 'white';
    const borderColor = isDarkTheme ? '#404758' : '#ccc';
    const textColor = isDarkTheme ? '#E1E2E6' : 'inherit';
    const shadowColor = isDarkTheme ? 'rgba(0,0,0,0.4)' : 'rgba(0,0,0,0.15)';
    const headerBorderColor = isDarkTheme ? '#404758' : '#eee';
    
    // Cores dos status permanecem iguais para manter a semântica das cores
    const manutencaoColor = '#ffc107'; // Amarelo para manutenção
    const disponivelColor = '#198754'; // Verde para disponível

    // Os status são: 'Em Uso', 'Em Manutenção', 'Livre' (Disponível no backend)
    const menuHtml = `
      <div class="periferico-status-menu">
        <div class="periferico-status-header">Atualizar Status: ${perifericoNome}</div>
        <div class="periferico-status-item" data-status="manutencao">
          <span class="status-indicator status-manutencao"></span>Em Manutenção
        </div>
        <div class="periferico-status-item" data-status="disponivel">
          <span class="status-indicator status-disponivel"></span>Livre (Disponível)
        </div>
      </div>
    `;

    $('body').append(menuHtml);
    activePerifericoStatusMenu = $('.periferico-status-menu');
    
    if (activePerifericoStatusMenu.length === 0) {
      console.error('[LOG] ERRO: Menu de status do periférico NÃO foi encontrado no DOM após o append.');
      return; // Sai da função se o menu não pôde ser criado/encontrado
    }
    console.log('[LOG] Menu de status do periférico adicionado ao DOM.');

    const rect = perifericoTagElement[0].getBoundingClientRect();
    activePerifericoStatusMenu.css({
      top: (rect.bottom + window.scrollY + 5) + 'px',
      left: (rect.left + window.scrollX) + 'px',
      display: 'block' // Garante que display não é none
    }).show(); // Força a exibição

    console.log('[LOG] Menu de status do periférico posicionado e tornado visível.');

    activePerifericoStatusMenu.find('.periferico-status-item').hover(
      function() { $(this).addClass('hover'); },
      function() { $(this).removeClass('hover'); }
    );

    activePerifericoStatusMenu.find('.periferico-status-item').on('click', function(event) {
      event.stopPropagation(); // IMPEDE PROPAGAÇÃO
      const novoStatus = $(this).data('status');
      fecharMenusPerifericoAtivos();
      if (novoStatus === 'manutencao') {
        dadosParaManutencao = {
            tipoItem: 'periferico',
            itemId: perifericoId,
            paId: paId,
            itemNome: perifericoNome,
            itemElement: perifericoTagElement,
            perifericoTipo: perifericoTipo // Guardar tipo para o caso de precisar na atualização
        };
        abrirModalObservacoesManutencao(perifericoNome);
      } else {
        atualizarStatusPerifericoNoServidor(perifericoId, novoStatus, paId, perifericoTagElement, perifericoTipo, null);
      }
    });
    
    // Fechar ao clicar fora
    $(document).off('click.closePerifericoStatusMenu'); // Garante que não haja listeners duplicados
    $(document).on('click.closePerifericoStatusMenu', function(event) {
      if (activePerifericoStatusMenu && 
          !$(event.target).closest('.periferico-status-menu').length && 
          !perifericoTagElement.is(event.target) && 
          !$(event.target).closest(perifericoTagElement).length // Verifica se o clique não foi na tag ou em seus filhos
         ) {
        fecharMenusPerifericoAtivos();
        $(document).off('click.closePerifericoStatusMenu');
      }
    });
  }

  function atualizarStatusPerifericoNoServidor(perifericoId, novoStatus, paId, perifericoTagElement, perifericoTipo, observacoes) {
    $.ajax({
      url: `/ti/api/periferico/${perifericoId}/atualizar_status/`, // Nova URL da API
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
      },
      data: JSON.stringify({
        status: novoStatus,
        pa_id: paId, // Enviar pa_id para lógica condicional no backend (se necessário)
        observacoes: observacoes // Adicionado
      }),
      contentType: 'application/json; charset=utf-8',
      dataType: 'json',
      success: function(response) {
        if (response.success) {
          mostrarMensagem(response.message || 'Status do periférico atualizado com sucesso!', 'success');
          // Atualizar visualização da tag do periférico, se necessário
          // Ex: mudar cor de fundo ou adicionar um ícone.
          // A remoção da PA, se aplicável (ex: status 'disponivel'), será tratada pelo backend.
          // Se o periférico foi removido da PA (ex: ao setar para 'disponivel'),
          // o backend deve indicar e o frontend deve remover a tag da PA.
          if (response.periferico_removido_da_pa) {
            perifericoTagElement.fadeOut(300, function() { 
                const perifericosList = $(this).closest('.perifericos-list');
                $(this).remove();
                if (perifericosList.children('.periferico-tag').length === 0) {
                    perifericosList.html('<span class="text-muted">Nenhum periférico atribuído</span>');
                }
            });
          } else if (response.novo_status_display) {
             // Poderia adicionar um data-attribute para o status e mudar a cor da tag se houvesse CSS para isso.
             // Ex: perifericoTagElement.attr('data-status', novoStatus);
             // Ou atualizar o texto se a API retornar o nome do periférico completo com novo status.
          }

        } else {
          mostrarMensagem('Erro ao atualizar status do periférico: ' + response.error, 'error');
        }
      },
      error: function(jqXHR) {
        console.error('Erro AJAX ao atualizar status do periférico:', jqXHR.responseText);
        let errorMsg = jqXHR.responseJSON?.error || 'Erro ao comunicar com o servidor para atualizar status do periférico.';
        mostrarMensagem(errorMsg, 'error');
      }
    });
  }

  // --- Fim das funções do menu de ações do periférico ---

  $(document).on('click', '.periferico-tag', function(event) {
    event.preventDefault(); // Previne qualquer comportamento padrão
    event.stopPropagation(); // Impede que o clique se propague para fechar o menu imediatamente

    const perifericoTag = $(this);
    // Em vez de abrir o modal de confirmação diretamente, abre o novo menu de ações
    abrirMenuAcoesPeriferico(perifericoTag);
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

  // --- Lógica para Dropdown e Atribuição de Computadores ---
  const computadoresDisponiveisApiUrl = '/ti/api/computadores_disponiveis/'; // GET
  const adicionarComputadorApiUrl = '/ti/api/pa/{pa_id}/adicionar_computador/'; // POST, pa_id na URL
  const removerComputadorApiUrl = '/ti/api/pa/{pa_id}/remover_computador/'; // POST, pa_id na URL
  let computadoresDisponiveisCache = null;
  let activeComputadorDropdown = null;
  let activeComputadorActionMenu = null;
  let activeComputadorStatusMenu = null;

  // --- Adicionado para Modal de Observações de Manutenção ---
  const manutencaoObsModalBackdrop = $('#manutencao-obs-backdrop');
  const manutencaoObsModal = $('#manutencao-obs-modal');
  const manutencaoItemNome = $('#manutencao-item-nome');
  const manutencaoObsInput = $('#manutencao-observacoes-input');
  const manutencaoObsModalSaveBtn = $('#manutencao-obs-modal-save-btn');
  const manutencaoObsModalCancelBtn = $('#manutencao-obs-modal-cancel-btn');
  const manutencaoObsModalCloseBtn = $('#manutencao-obs-modal-close-btn');
  let dadosParaManutencao = null; // Para armazenar { tipoItem: 'periferico'/'computador', itemId, paId, itemNome, itemElement }
  // --- Fim da adição do Modal de Observações ---

  // Função para fechar qualquer menu de computador ativo
  function fecharMenusComputadorAtivos() {
    if (activeComputadorActionMenu) {
      activeComputadorActionMenu.remove();
      activeComputadorActionMenu = null;
    }
    if (activeComputadorStatusMenu) {
      activeComputadorStatusMenu.remove();
      activeComputadorStatusMenu = null;
    }
  }

  // Função para buscar computadores disponíveis (com cache)
  async function fetchDisponiveisComputadores() {
    if (computadoresDisponiveisCache) {
      return computadoresDisponiveisCache;
    }
    try {
      const response = await $.ajax({
        url: computadoresDisponiveisApiUrl,
        method: 'GET',
        dataType: 'json'
      });
      if (response.computadores) {
        computadoresDisponiveisCache = response.computadores;
        return computadoresDisponiveisCache;
      } else {
        throw new Error(response.error || 'Erro desconhecido ao buscar computadores disponíveis.');
      }
    } catch (error) {
      console.error("Erro detalhado ao buscar computadores disponíveis:", error);
      let errorMsg = 'Erro desconhecido.';
      if (error.responseJSON && error.responseJSON.error) {
        errorMsg = error.responseJSON.error;
      } else if (error.statusText) {
        errorMsg = `${error.statusText} (Status: ${error.status || 'N/A'})`;
      } else if (error.message) {
        errorMsg = error.message;
      }
      mostrarMensagem(`Erro ao buscar computadores disponíveis: ${errorMsg}`, 'error');
      return null;
    }
  }

  // Função para criar o HTML do dropdown de computadores disponíveis
  function criarDisponiveisComputadorDropdownHTML(computadores, paId) {
    if (!computadores || computadores.length === 0) {
      return `<div class="computador-dropdown-menu p-2 text-muted" id="dropdown-computador-pa-${paId}">Nenhum computador disponível para atribuição.</div>`;
    }

    let itemsHTML = '';
    // Adicionando uma mensagem informativa sobre a limitação de um computador por PA
    itemsHTML += `<div class="dropdown-info-message" style="padding:8px 15px; font-size:0.9em; color:#666; border-bottom:1px solid #eee; margin-bottom:5px; background-color:#f8f9fa;">
      <i class='bx bx-info-circle me-1'></i> Clique na marca para atribuir um computador aleatório.
      </div>`;
    
    // Agrupar computadores por marca
    const computadoresPorMarca = computadores.reduce((acc, comp) => {
      acc[comp.marca] = acc[comp.marca] || [];
      acc[comp.marca].push(comp);
      return acc;
    }, {});

    // Para cada marca, mostrar apenas uma entrada com a contagem
    for (const marca in computadoresPorMarca) {
      const qtdComputadores = computadoresPorMarca[marca].length;
      if (qtdComputadores > 0) {
        // Armazenar todos os IDs de computadores desta marca como atributo data para seleção aleatória
        const computadoresIds = computadoresPorMarca[marca].map(comp => comp.id);
        
        // Criar um item dropdown por marca, com a quantidade de computadores disponíveis
        itemsHTML += `
          <div class="computador-marca-dropdown" 
               data-marca="${marca}" 
               data-computadores-ids="${JSON.stringify(computadoresIds)}"
               style="padding:10px 15px; cursor:pointer; border-bottom:1px solid #f0f0f0; display:flex; justify-content:space-between; align-items:center;">
            <span class="nome" style="font-weight:500;">${marca}</span>
            <span class="badge bg-info" style="font-size:0.8em;">${qtdComputadores} ${qtdComputadores === 1 ? 'disponível' : 'disponíveis'}</span>
          </div>`;
      }
    }

    const dropdownHtml = `<div class="computador-dropdown-menu" id="dropdown-computador-pa-${paId}" style="min-width:320px;">${itemsHTML}</div>`;
    
    return dropdownHtml;
  }

  // Função para mostrar/esconder e posicionar o dropdown de computadores
  async function toggleDropdownDisponiveisComputadores(button) {
    const paId = $(button).data('pa-id');
    const existingDropdown = $(`#dropdown-computador-pa-${paId}`);

    if (activeComputadorDropdown && activeComputadorDropdown.attr('id') !== `dropdown-computador-pa-${paId}`) {
      activeComputadorDropdown.fadeOut(100, function() { $(this).remove(); });
      activeComputadorDropdown = null;
    }

    if (existingDropdown.length > 0) {
      existingDropdown.fadeOut(100, function() { $(this).remove(); });
      activeComputadorDropdown = null;
    } else {
      const buttonRect = button.getBoundingClientRect();
      const loaderHTML = `<div id="dropdown-loader-computador-${paId}" style="position: fixed; z-index: 9999; left: ${buttonRect.right + 10}px; top: ${buttonRect.top}px;">
                            <div class="spinner-border spinner-border-sm text-primary" role="status">
                              <span class="visually-hidden">Loading...</span>
                            </div>
                          </div>`;
      $('body').append(loaderHTML);

      const computadores = await fetchDisponiveisComputadores();
      $(`#dropdown-loader-computador-${paId}`).remove();

      if (computadores) {
        const dropdownHTML = criarDisponiveisComputadorDropdownHTML(computadores, paId);
        $('body').append(dropdownHTML);
        
        const newDropdown = $(`#dropdown-computador-pa-${paId}`);
        activeComputadorDropdown = newDropdown;

        // Posicionamento inteligente para evitar que o dropdown fique fora da tela ou debaixo da barra de tarefas
        const viewportHeight = window.innerHeight;
        const dropdownHeight = 450; // Altura máxima do dropdown (definida no CSS)
        const dropdownWidth = newDropdown.outerWidth() || 320;
        
        // Verificar se há espaço suficiente abaixo do botão para mostrar o dropdown
        const spaceBelow = viewportHeight - buttonRect.bottom;
        
        // Decidir se deve abrir para cima ou para baixo
        const openUpwards = spaceBelow < dropdownHeight;
        
        // Ajustar posição horizontal
        let leftPos = buttonRect.left;
        if (leftPos + dropdownWidth > window.innerWidth - 20) {
          leftPos = Math.max(20, buttonRect.right - dropdownWidth);
        }
        
        // Ajustar posição vertical
        let topPos;
        if (openUpwards) {
          // Abrir para cima
          topPos = Math.max(20, buttonRect.top - dropdownHeight);
          newDropdown.css('max-height', buttonRect.top - 40 + 'px'); // 40px de margem do topo
        } else {
          // Abrir para baixo
          topPos = buttonRect.bottom + 5;
          newDropdown.css('max-height', viewportHeight - topPos - 20 + 'px'); // 20px de margem do fundo
        }

        newDropdown.css({
          position: 'fixed',
          top: topPos + 'px',
          left: leftPos + 'px',
          display: 'none',
          zIndex: 999999, // Aumentado para garantir que fique acima de tudo
          maxHeight: openUpwards ? (buttonRect.top - 40) + 'px' : (viewportHeight - topPos - 20) + 'px',
          overflowY: 'auto' // Garantir que o scroll seja habilitado
        }).fadeIn(150);

        // Modificado: Agora ao clicar na marca, já atribui diretamente um computador aleatório
        newDropdown.find('.computador-marca-dropdown').on('click', function() {
          const marca = $(this).data('marca');
          const computadoresIds = $(this).data('computadores-ids');
          const paCardElement = $(`.pa-card[data-pa-id="${paId}"]`);
          
          if (computadoresIds && computadoresIds.length > 0) {
            // Selecionar um computador aleatório desta marca
            const indiceAleatorio = Math.floor(Math.random() * computadoresIds.length);
            const computadorIdAleatorio = computadoresIds[indiceAleatorio];
            
            // Efeito visual de feedback no item clicado
            $(this).css('background-color', '#e6f7ff');
            $(this).find('.badge').removeClass('bg-info').addClass('bg-primary');
            
            // Atribuir o computador selecionado aleatoriamente
            adicionarComputadorAPa(paId, computadorIdAleatorio, paCardElement);
            
            // Fechar o dropdown após a seleção
            if (activeComputadorDropdown) {
              activeComputadorDropdown.fadeOut(100, function() { $(this).remove(); });
              activeComputadorDropdown = null;
            }
          }
        });

        // Adicionar efeito hover nos itens
        newDropdown.find('.computador-marca-dropdown').hover(
          function() { 
            $(this).css('background-color', '#f0f8ff'); 
          },
          function() { 
            $(this).css('background-color', ''); 
          }
        );
      } else {
        const errorHtml = `<div id="error-message-computador-${paId}" style="position: fixed; z-index: 9999; left: ${buttonRect.right + 10}px; top: ${buttonRect.top}px; background: white; padding: 5px 10px; border-radius: 4px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); color: red;">
                            Falha ao carregar computadores
                          </div>`;
        $('body').append(errorHtml);
        setTimeout(() => {
          $(`#error-message-computador-${paId}`).fadeOut(300, function() { $(this).remove(); });
        }, 3000);
      }
    }
  }

  // Função para remover computador da PA via AJAX
  function removerComputadorDaPa(paId, computadorId, paCardElement, tagElement) {
    const url = removerComputadorApiUrl.replace('{pa_id}', paId);
    $.ajax({
      url: url,
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
      },
      data: JSON.stringify({ computador_id: computadorId }),
      contentType: 'application/json; charset=utf-8',
      dataType: 'json',
      success: function(response) {
        if (response.success) {
          atualizarVisualizacaoComputadoresPA(paCardElement, response.lista_computadores_pa || []);
          // Forçar recarga da lista de disponíveis, pois um pode ter voltado
          computadoresDisponiveisCache = null; 
          mostrarMensagem(response.message || 'Computador removido com sucesso!', 'success');
        } else {
          mostrarMensagem('Erro ao remover computador: ' + (response.error || 'Erro desconhecido'), 'error');
        }
      },
      error: function(jqXHR) {
        console.error('Erro AJAX ao remover computador:', jqXHR.responseText);
        mostrarMensagem(jqXHR.responseJSON?.error ||'Erro ao comunicar com o servidor para remover computador.', 'error');
      }
    });
  }

  // Função para atualizar a UI da seção de computadores da PA
  function atualizarVisualizacaoComputadoresPA(paCard, listaComputadoresAtribuidos) {
    const paId = paCard.data('pa-id');
    const container = paCard.find('.computadores-list-container');
    container.empty();

    // Modificado: Considerar apenas o primeiro computador (se existir)
    const computador = listaComputadoresAtribuidos && listaComputadoresAtribuidos.length > 0 
                     ? listaComputadoresAtribuidos[0] 
                     : null;

    if (computador) {
      const tagHTML = `
        <span class="computador-tag" data-computador-id="${computador.id}" data-pa-id="${paId}">
          ${computador.marca} ${computador.modelo ? `(${computador.modelo})` : ''}
          <i class='bx bx-x-circle remove-computador-btn ms-1' title='Remover este computador' style="cursor:pointer; vertical-align: middle;"></i>
        </span>`;
      container.append(tagHTML);
      
      // Removido o botão "Adicionar" quando já existe um computador
      // pois agora é permitido apenas um computador por PA
    } else {
      const assignButtonHTML = `
        <button type="button" class="btn btn-sm btn-info assign-computador-btn-main" data-pa-id="${paId}" data-action="open_computador_add_dropdown">
          <i class='bx bx-plus-circle me-1'></i> Atribuir Computador
        </button>`;
      container.append(assignButtonHTML);
    }
  }
  
  // Event Listeners para computadores
  $(document).on('click', '.assign-computador-btn-main, .add-computador-btn', function(e) {
    e.preventDefault();
    e.stopPropagation();
    fecharMenusComputadorAtivos(); // Fecha outros menus de computador se abertos
    toggleDropdownDisponiveisComputadores(this);
  });

  // Modificado: Clicar na TAG do computador abre o menu de ações
  $(document).on('click', '.computador-tag', function(e) {
    e.preventDefault();
    e.stopPropagation();
    const computadorTag = $(this);
    // Não abrir menu de ações se o clique foi no botão de remover DENTRO da tag
    if ($(e.target).hasClass('remove-computador-btn')) {
        // A lógica de remover diretamente pelo ícone será mantida se desejado,
        // ou pode ser removida para forçar o uso do menu.
        // Por ora, se o ícone de remover é clicado, ele ainda chama a função de remoção direta.
        const computadorId = computadorTag.data('computador-id');
        const paId = computadorTag.data('pa-id');
        const paCard = computadorTag.closest('.pa-card');
        removerComputadorDaPa(paId, computadorId, paCard, computadorTag); // Passando a tag para remoção visual
        return; 
    }
    abrirMenuAcoesComputador(computadorTag);
  });

  function abrirMenuAcoesComputador(computadorTag) {
    fecharMenusComputadorAtivos();
    fecharMenusPerifericoAtivos(); // Fecha menus de periféricos também

    const computadorId = computadorTag.data('computador-id');
    const paId = computadorTag.data('pa-id');
    const computadorNome = computadorTag.contents().filter(function() {
        return this.nodeType === 3; // Pega apenas o nó de texto (nome do computador)
    }).text().trim();
    const paCard = computadorTag.closest('.pa-card');

    const menuHtml = `
      <div class="computador-action-menu">
        <div class="computador-action-option" data-action="update-status">
          <i class='bx bx-edit-alt me-2'></i>Atualizar Status
        </div>
        <div class="computador-action-option remove-action" data-action="remove">
          <i class='bx bx-trash me-2'></i>Remover da PA
        </div>
      </div>
    `;

    $('body').append(menuHtml);
    activeComputadorActionMenu = $('.computador-action-menu');

    const rect = computadorTag[0].getBoundingClientRect();
    activeComputadorActionMenu.css({
      top: (rect.bottom + window.scrollY + 5) + 'px',
      left: (rect.left + window.scrollX) + 'px',
    }).show();

    activeComputadorActionMenu.find('.computador-action-option').hover(
      function() { $(this).addClass('hover'); },
      function() { $(this).removeClass('hover'); }
    );

    activeComputadorActionMenu.find('[data-action="update-status"]').on('click', function(event) {
      event.stopPropagation();
      fecharMenusComputadorAtivos();
      abrirMenuAtualizarStatusComputador(computadorId, computadorNome, paId, computadorTag);
    });

    activeComputadorActionMenu.find('[data-action="remove"]').on('click', function(event) {
      event.stopPropagation();
      fecharMenusComputadorAtivos();
      // A função removerComputadorDaPa já existe e será chamada aqui
      removerComputadorDaPa(paId, computadorId, paCard, computadorTag);
    });

    $(document).off('click.closeComputadorActionMenu');
    $(document).on('click.closeComputadorActionMenu', function(event) {
      if (activeComputadorActionMenu && !$(event.target).closest('.computador-action-menu').length && !computadorTag.is(event.target) && !computadorTag.has(event.target).length) {
        fecharMenusComputadorAtivos();
        $(document).off('click.closeComputadorActionMenu');
      }
    });
  }

  function abrirMenuAtualizarStatusComputador(computadorId, computadorNome, paId, computadorTagElement) {
    fecharMenusComputadorAtivos();
    const menuHtml = `
      <div class="computador-status-menu">
        <div class="computador-status-header">Atualizar Status: ${computadorNome}</div>
        <div class="computador-status-item" data-status="manutencao">
          <span class="status-indicator status-manutencao"></span>Em Manutenção
        </div>
        <div class="computador-status-item" data-status="disponivel">
          <span class="status-indicator status-disponivel"></span>Livre (Disponível)
        </div>
      </div>
    `;

    $('body').append(menuHtml);
    activeComputadorStatusMenu = $('.computador-status-menu');

    const rect = computadorTagElement[0].getBoundingClientRect();
    activeComputadorStatusMenu.css({
      top: (rect.bottom + window.scrollY + 5) + 'px',
      left: (rect.left + window.scrollX) + 'px',
    }).show();

    activeComputadorStatusMenu.find('.computador-status-item').hover(
      function() { $(this).addClass('hover'); },
      function() { $(this).removeClass('hover'); }
    );

    activeComputadorStatusMenu.find('.computador-status-item').on('click', function(event) {
      event.stopPropagation();
      const novoStatus = $(this).data('status');
      fecharMenusComputadorAtivos();
      if (novoStatus === 'manutencao') {
        dadosParaManutencao = {
            tipoItem: 'computador',
            itemId: computadorId,
            paId: paId,
            itemNome: computadorNome,
            itemElement: computadorTagElement
        };
        abrirModalObservacoesManutencao(computadorNome);
      } else {
        atualizarStatusComputadorNoServidor(computadorId, novoStatus, paId, computadorTagElement, null);
      }
    });

    $(document).off('click.closeComputadorStatusMenu');
    $(document).on('click.closeComputadorStatusMenu', function(event) {
      if (activeComputadorStatusMenu && !$(event.target).closest('.computador-status-menu').length && !computadorTagElement.is(event.target) && !computadorTagElement.has(event.target).length) {
        fecharMenusComputadorAtivos();
        $(document).off('click.closeComputadorStatusMenu');
      }
    });
  }

  function atualizarStatusComputadorNoServidor(computadorId, novoStatus, paId, computadorTagElement, observacoes) {
    $.ajax({
      url: `/ti/api/computador/${computadorId}/atualizar_status/`, // Nova URL
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
      },
      data: JSON.stringify({
        status: novoStatus,
        pa_id: paId,
        observacoes: observacoes // Adicionado
      }),
      contentType: 'application/json; charset=utf-8',
      dataType: 'json',
      success: function(response) {
        if (response.success) {
          mostrarMensagem(response.message || 'Status do computador atualizado!', 'success');
          if (response.computador_removido_da_pa) {
            // A função atualizarVisualizacaoComputadoresPA será chamada se a remoção ocorreu.
            // O backend já retorna a lista atualizada de computadores para a PA.
            // Precisamos do paCard para chamar a função.
            const paCardElement = computadorTagElement.closest('.pa-card');
            atualizarVisualizacaoComputadoresPA(paCardElement, response.lista_computadores_pa || []);
            computadoresDisponiveisCache = null; // Força recarga da lista de disponíveis
          } else {
            // Se não foi removido, pode haver outra lógica de UI aqui, mas por enquanto nada.
          }
        } else {
          mostrarMensagem('Erro ao atualizar status: ' + response.error, 'error');
        }
      },
      error: function(jqXHR) {
        console.error('Erro AJAX status computador:', jqXHR.responseText);
        mostrarMensagem(jqXHR.responseJSON?.error || 'Erro servidor (status comp.)', 'error');
      }
    });
  }

  $(document).on('click', '.remove-computador-btn', function(e) {
    e.preventDefault();
    e.stopPropagation();
    if (activeComputadorDropdown && 
        !$(event.target).closest('.computador-dropdown-menu').length && 
        !$(event.target).closest('.assign-computador-btn-main, .add-computador-btn').length) {
      activeComputadorDropdown.fadeOut(100, function() { $(this).remove(); });
      activeComputadorDropdown = null;
    }

    // Adicionado para fechar menus de periféricos se abertos
    if (!$(event.target).closest('.periferico-action-menu, .periferico-status-menu, .periferico-tag').length) {
        fecharMenusPerifericoAtivos();
    }
    // Adicionado para fechar menus de COMPUTADOR se abertos
    if (!$(event.target).closest('.computador-action-menu, .computador-status-menu, .computador-tag').length &&
        !$(event.target).hasClass('assign-computador-btn-main') && !$(event.target).hasClass('add-computador-btn')) {
        fecharMenusComputadorAtivos();
    }
  });

  // Event Listener para fechar dropdown de computador ao clicar fora
  $(document).on('click', function(event) {
    if (activeComputadorDropdown && 
        !$(event.target).closest('.computador-dropdown-menu').length && 
        !$(event.target).closest('.assign-computador-btn-main, .add-computador-btn').length) {
      activeComputadorDropdown.fadeOut(100, function() { $(this).remove(); });
      activeComputadorDropdown = null;
    }

    // Adicionado para fechar menus de periféricos se abertos
    if (!$(event.target).closest('.periferico-action-menu, .periferico-status-menu, .periferico-tag').length) {
        fecharMenusPerifericoAtivos();
    }
  });

  // --- Fim da Lógica para Dropdown e Atribuição de Computadores ---

  // --- Funções para o Modal de Observações de Manutenção ---
  function abrirModalObservacoesManutencao(itemNome) {
    manutencaoItemNome.text(itemNome);
    manutencaoObsInput.val(''); // Limpar input anterior
    manutencaoObsModalBackdrop.addClass('show').fadeIn(200);
    manutencaoObsModal.addClass('show').fadeIn(200);
    $('body').addClass('modal-open');
  }

  function fecharModalObservacoesManutencao() {
    manutencaoObsModalBackdrop.fadeOut(200, function() { $(this).removeClass('show'); });
    manutencaoObsModal.fadeOut(200, function() { $(this).removeClass('show'); });
    $('body').removeClass('modal-open');
    dadosParaManutencao = null; // Limpar dados temporários
  }

  manutencaoObsModalSaveBtn.on('click', function() {
    if (!dadosParaManutencao) return;

    const observacoes = manutencaoObsInput.val().trim();
    const { tipoItem, itemId, paId, itemElement, perifericoTipo } = dadosParaManutencao;

    if (tipoItem === 'periferico') {
      atualizarStatusPerifericoNoServidor(itemId, 'manutencao', paId, itemElement, perifericoTipo, observacoes);
    } else if (tipoItem === 'computador') {
      atualizarStatusComputadorNoServidor(itemId, 'manutencao', paId, itemElement, observacoes);
    }
    fecharModalObservacoesManutencao();
  });

  manutencaoObsModalCancelBtn.on('click', fecharModalObservacoesManutencao);
  manutencaoObsModalCloseBtn.on('click', fecharModalObservacoesManutencao);
  manutencaoObsModalBackdrop.on('click', function(event) {
    if (event.target === this) {
        fecharModalObservacoesManutencao();
    }
  });
  // --- Fim das Funções do Modal de Observações ---

  // Inicializar visualização dos computadores para cada PA no carregamento da página
  // O Django já renderiza o estado inicial. Esta função pode ser chamada se uma atualização geral for necessária.
  // function inicializarTodasAsVisualizacoesDeComputadores() {
  //   $('.pa-card').each(function() {
  //     const paCard = $(this);
  //     const paId = paCard.data('pa-id');
       // Aqui você precisaria de uma forma de obter a lista de computadores para esta PA,
       // talvez de um endpoint ou dados embutidos, se a renderização do Django não for suficiente.
       // Por ora, a renderização do Django + atualizações AJAX cobrem o ciclo.
  //   });
  // }
  // if ($('.pa-card').length > 0) {
  //  inicializarTodasAsVisualizacoesDeComputadores();
  // }

  // --- Funções para periféricos faltantes ---
  const perifericosDisponiveisPorTipoApiUrl = '/ti/api/perifericos-disponiveis-por-tipo/'; // Base URL
  const atribuirPerifericoApiUrl = '/ti/atribuicoes-perifericos/cadastrar/'; // URL para atribuir periférico
  
  // Elementos do modal
  const perifericosDisponiveisBackdrop = $('#perifericos-disponiveis-backdrop');
  const perifericosDisponiveisModal = $('#perifericos-disponiveis-modal');
  const perifericosDisponiveisClose = $('#perifericos-disponiveis-close');
  const perifericosDisponiveisCancel = $('#perifericos-disponiveis-cancel');
  const modalTipoNome = $('#modal-tipo-nome');
  const perifericosDisponiveisLoading = $('#perifericos-disponiveis-loading');
  const perifericosDisponiveisEmpty = $('#perifericos-disponiveis-empty');
  const perifericosDisponiveisError = $('#perifericos-disponiveis-error');
  const perifericosDisponiveisErrorMessage = $('#perifericos-disponiveis-error-message');
  const perifericosDisponiveisContent = $('#perifericos-disponiveis-content');
  
  // Dados para o modal atual
  let modalDadosPa = null;
  let modalDadosTipo = null;
  
  // Event Listener para botões de adicionar periférico faltante
  $(document).on('click', '.add-periferico-btn', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const paId = $(this).data('pa-id');
    const tipoId = $(this).data('tipo-id');
    const tipoNome = $(this).data('tipo-nome');
    
    // Armazenar dados para uso posterior
    modalDadosPa = {
      id: paId
    };
    
    modalDadosTipo = {
      id: tipoId,
      nome: tipoNome
    };
    
    // Abrir modal
    abrirModalPerifericosDisponiveis(tipoId, tipoNome);
  });
  
  // Função para abrir o modal
  function abrirModalPerifericosDisponiveis(tipoId, tipoNome) {
    // Resetar estado do modal
    resetarModalPerifericosDisponiveis();
    
    // Definir o título
    modalTipoNome.text(tipoNome);
    
    // Mostrar modal e backdrop
    perifericosDisponiveisBackdrop.fadeIn(200);
    perifericosDisponiveisModal.fadeIn(200);
    
    // Carregar periféricos disponíveis
    carregarPerifericosDisponiveis(tipoId);
  }
  
  // Função para fechar o modal
  function fecharModalPerifericosDisponiveis() {
    perifericosDisponiveisBackdrop.fadeOut(200);
    perifericosDisponiveisModal.fadeOut(200);
    
    // Limpar dados
    modalDadosPa = null;
    modalDadosTipo = null;
  }
  
  // Função para resetar o estado do modal
  function resetarModalPerifericosDisponiveis() {
    perifericosDisponiveisLoading.show();
    perifericosDisponiveisEmpty.hide();
    perifericosDisponiveisError.hide();
    perifericosDisponiveisContent.empty().hide();
  }
  
  // Função para carregar periféricos disponíveis
  async function carregarPerifericosDisponiveis(tipoId) {
    try {
      const response = await $.ajax({
        url: `${perifericosDisponiveisPorTipoApiUrl}${tipoId}/`,
        method: 'GET',
        dataType: 'json'
      });
      
      // Ocultar carregamento
      perifericosDisponiveisLoading.hide();
      
      if (response.success) {
        if (response.perifericos && response.perifericos.length > 0) {
          // Renderizar lista de periféricos
          renderizarPerifericosDisponiveis(response.perifericos);
          perifericosDisponiveisContent.show();
        } else {
          // Mostrar mensagem de vazio
          perifericosDisponiveisEmpty.show();
        }
      } else {
        // Mostrar erro
        perifericosDisponiveisErrorMessage.text(response.error || 'Erro desconhecido');
        perifericosDisponiveisError.show();
      }
    } catch (error) {
      console.error('Erro ao carregar periféricos disponíveis:', error);
      perifericosDisponiveisLoading.hide();
      perifericosDisponiveisErrorMessage.text(error.responseJSON?.error || error.statusText || error.message || 'Erro ao comunicar com o servidor');
      perifericosDisponiveisError.show();
    }
  }
  
  // Função para renderizar a lista de periféricos disponíveis
  function renderizarPerifericosDisponiveis(perifericos) {
    perifericosDisponiveisContent.empty();
    
    perifericos.forEach(periferico => {
      const itemHTML = `
        <div class="periferico-disponivel-item">
          <div class="periferico-disponivel-info">
            <div class="periferico-disponivel-marca">${periferico.marca}</div>
            <div class="periferico-disponivel-modelo">${periferico.modelo || ''}</div>
          </div>
          <button class="atribuir-periferico-btn" data-periferico-id="${periferico.id}">
            <i class='bx bx-link me-1'></i> Atribuir
          </button>
        </div>
      `;
      
      perifericosDisponiveisContent.append(itemHTML);
    });
  }
  
  // Event Listener para atribuir periférico
  $(document).on('click', '.atribuir-periferico-btn', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const button = $(this);
    const perifericoId = button.data('periferico-id');
    
    // Desabilitar o botão e mostrar indicador de carregamento
    button.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Atribuindo...');
    
    // Verificar se temos os dados necessários
    if (modalDadosPa && modalDadosTipo) {
      atribuirPerifericoAPa(perifericoId, modalDadosPa.id, button);
    } else {
      console.error('Dados incompletos para atribuição de periférico');
      mostrarMensagem('Erro: Dados incompletos para atribuição', 'error');
      // Restaurar o botão
      button.prop('disabled', false).html('<i class="bx bx-link me-1"></i> Atribuir');
    }
  });
  
  // Função para atribuir periférico à PA
  async function atribuirPerifericoAPa(perifericoId, paId, button) {
    try {
      // Mostrar loader no modal
      perifericosDisponiveisContent.hide();
      perifericosDisponiveisLoading.show();
      
      // Obter a data/hora atual no formato ISO para o Django
      const agora = new Date();
      const dataHoraFormatada = agora.toISOString().replace('Z', '');
      
      console.log('Enviando dados para atribuição:', {
        periferico: perifericoId,
        posicao_atendimento: paId,
        data_atribuicao: dataHoraFormatada
      });
      
      const response = await $.ajax({
        url: atribuirPerifericoApiUrl,
        method: 'POST',
        headers: {
          'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
          'X-Requested-With': 'XMLHttpRequest'
        },
        data: {
          periferico: perifericoId,
          posicao_atendimento: paId,
          data_atribuicao: dataHoraFormatada // Formato correto para DateTime no Django
        }
      });
      
      console.log('Resposta do servidor:', response);
      
      // Fechar modal
      fecharModalPerifericosDisponiveis();
      
      // Mostrar mensagem de sucesso
      mostrarMensagem('Periférico atribuído com sucesso!', 'success');
      
      // Recarregar a página para atualizar os dados
      setTimeout(() => {
        window.location.reload();
      }, 1500);
      
    } catch (error) {
      console.error('Erro ao atribuir periférico:', error);
      console.error('Detalhes do erro:', error.responseText);
      
      // Restaurar a interface do modal
      perifericosDisponiveisLoading.hide();
      perifericosDisponiveisContent.show();
      
      // Restaurar o botão
      if (button) {
        button.prop('disabled', false).html('<i class="bx bx-link me-1"></i> Atribuir');
      }
      
      // Mostrar mensagem de erro
      perifericosDisponiveisErrorMessage.text(error.responseJSON?.error || error.statusText || error.message || 'Erro ao comunicar com o servidor');
      perifericosDisponiveisError.show();
    }
  }
  
  // Event Listeners para o modal
  perifericosDisponiveisClose.on('click', fecharModalPerifericosDisponiveis);
  perifericosDisponiveisCancel.on('click', fecharModalPerifericosDisponiveis);
  perifericosDisponiveisBackdrop.on('click', function(e) {
    if (e.target === this) {
      fecharModalPerifericosDisponiveis();
    }
  });
  
  // --- Fim das funções para periféricos faltantes ---

  // Função para adicionar computador à PA via AJAX
  function adicionarComputadorAPa(paId, computadorId, paCardElement) {
    // Verificar se já existe um computador atribuído
    const computadorAtual = paCardElement.find('.computador-tag');
    let mensagemConfirmacao = '';
    
    if (computadorAtual.length > 0) {
      const computadorAtualNome = computadorAtual.text().trim();
      // Perguntar ao usuário se deseja substituir o computador existente
      if (!confirm(`A PA já possui o computador "${computadorAtualNome}" atribuído.\n\nDeseja substituí-lo por outro computador?\n\nAtenção: Cada PA pode ter apenas um computador.`)) {
        return; // Usuário cancelou a operação
      }
    }
    
    const url = adicionarComputadorApiUrl.replace('{pa_id}', paId);
    $.ajax({
      url: url,
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
      },
      data: JSON.stringify({ computador_id: computadorId }),
      contentType: 'application/json; charset=utf-8',
      dataType: 'json',
      success: function(response) {
        if (response.success) {
          atualizarVisualizacaoComputadoresPA(paCardElement, response.lista_computadores_pa || []);
          // Forçar recarga da lista de disponíveis, pois um foi usado
          computadoresDisponiveisCache = null;
          mostrarMensagem(response.message || 'Computador atribuído com sucesso!', 'success');
        } else {
          mostrarMensagem('Erro ao atribuir computador: ' + (response.error || 'Erro desconhecido'), 'error');
        }
      },
      error: function(jqXHR) {
        console.error('Erro AJAX ao atribuir computador:', jqXHR.responseText);
        mostrarMensagem(jqXHR.responseJSON?.error || 'Erro ao comunicar com o servidor para atribuição de computador.', 'error');
      }
    });
  }

  // Função para mostrar/esconder e posicionar o dropdown de computadores
  async function toggleDropdownDisponiveisComputadores(button) {
    const paId = $(button).data('pa-id');
    const existingDropdown = $(`#dropdown-computador-pa-${paId}`);

    if (activeComputadorDropdown && activeComputadorDropdown.attr('id') !== `dropdown-computador-pa-${paId}`) {
      activeComputadorDropdown.fadeOut(100, function() { $(this).remove(); });
      activeComputadorDropdown = null;
    }

    if (existingDropdown.length > 0) {
      existingDropdown.fadeOut(100, function() { $(this).remove(); });
      activeComputadorDropdown = null;
    } else {
      const buttonRect = button.getBoundingClientRect();
      const loaderHTML = `<div id="dropdown-loader-computador-${paId}" style="position: fixed; z-index: 9999; left: ${buttonRect.right + 10}px; top: ${buttonRect.top}px;">
                            <div class="spinner-border spinner-border-sm text-primary" role="status">
                              <span class="visually-hidden">Loading...</span>
                            </div>
                          </div>`;
      $('body').append(loaderHTML);

      const computadores = await fetchDisponiveisComputadores();
      $(`#dropdown-loader-computador-${paId}`).remove();

      if (computadores) {
        const dropdownHTML = criarDisponiveisComputadorDropdownHTML(computadores, paId);
        $('body').append(dropdownHTML);
        
        const newDropdown = $(`#dropdown-computador-pa-${paId}`);
        activeComputadorDropdown = newDropdown;

        // Posicionamento inteligente para evitar que o dropdown fique fora da tela ou debaixo da barra de tarefas
        const viewportHeight = window.innerHeight;
        const dropdownHeight = 450; // Altura máxima do dropdown (definida no CSS)
        const dropdownWidth = newDropdown.outerWidth() || 320;
        
        // Verificar se há espaço suficiente abaixo do botão para mostrar o dropdown
        const spaceBelow = viewportHeight - buttonRect.bottom;
        
        // Decidir se deve abrir para cima ou para baixo
        const openUpwards = spaceBelow < dropdownHeight;
        
        // Ajustar posição horizontal
        let leftPos = buttonRect.left;
        if (leftPos + dropdownWidth > window.innerWidth - 20) {
          leftPos = Math.max(20, buttonRect.right - dropdownWidth);
        }
        
        // Ajustar posição vertical
        let topPos;
        if (openUpwards) {
          // Abrir para cima
          topPos = Math.max(20, buttonRect.top - dropdownHeight);
          newDropdown.css('max-height', buttonRect.top - 40 + 'px'); // 40px de margem do topo
        } else {
          // Abrir para baixo
          topPos = buttonRect.bottom + 5;
          newDropdown.css('max-height', viewportHeight - topPos - 20 + 'px'); // 20px de margem do fundo
        }

        newDropdown.css({
          position: 'fixed',
          top: topPos + 'px',
          left: leftPos + 'px',
          display: 'none',
          zIndex: 999999, // Aumentado para garantir que fique acima de tudo
          maxHeight: openUpwards ? (buttonRect.top - 40) + 'px' : (viewportHeight - topPos - 20) + 'px',
          overflowY: 'auto' // Garantir que o scroll seja habilitado
        }).fadeIn(150);

        // Modificado: Agora ao clicar na marca, já atribui diretamente um computador aleatório
        newDropdown.find('.computador-marca-dropdown').on('click', function() {
          const marca = $(this).data('marca');
          const computadoresIds = $(this).data('computadores-ids');
          const paCardElement = $(`.pa-card[data-pa-id="${paId}"]`);
          
          if (computadoresIds && computadoresIds.length > 0) {
            // Selecionar um computador aleatório desta marca
            const indiceAleatorio = Math.floor(Math.random() * computadoresIds.length);
            const computadorIdAleatorio = computadoresIds[indiceAleatorio];
            
            // Efeito visual de feedback no item clicado
            $(this).css('background-color', '#e6f7ff');
            $(this).find('.badge').removeClass('bg-info').addClass('bg-primary');
            
            // Atribuir o computador selecionado aleatoriamente
            adicionarComputadorAPa(paId, computadorIdAleatorio, paCardElement);
            
            // Fechar o dropdown após a seleção
            if (activeComputadorDropdown) {
              activeComputadorDropdown.fadeOut(100, function() { $(this).remove(); });
              activeComputadorDropdown = null;
            }
          }
        });

        // Adicionar efeito hover nos itens
        newDropdown.find('.computador-marca-dropdown').hover(
          function() { 
            $(this).css('background-color', '#f0f8ff'); 
          },
          function() { 
            $(this).css('background-color', ''); 
          }
        );
      } else {
        const errorHtml = `<div id="error-message-computador-${paId}" style="position: fixed; z-index: 9999; left: ${buttonRect.right + 10}px; top: ${buttonRect.top}px; background: white; padding: 5px 10px; border-radius: 4px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); color: red;">
                            Falha ao carregar computadores
                          </div>`;
        $('body').append(errorHtml);
        setTimeout(() => {
          $(`#error-message-computador-${paId}`).fadeOut(300, function() { $(this).remove(); });
        }, 3000);
      }
    }
  }
}); 