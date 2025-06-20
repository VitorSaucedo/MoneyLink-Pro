/**
 * admin_dropdown_updates.js - Sistema de atualização de dropdowns para páginas de administração do TI
 * 
 * Funções para atualizar dropdowns dinamicamente nas funcionalidades de administração
 */

// Função para atualizar dropdowns após cadastros nas páginas de admin
function updateAdminDropdowns() {
  const lojaId = window.TIAdminUtils ? window.TIAdminUtils.getSelectedLojaAdmin() : (
    $('select[name="loja"]').val() || 
    $('#loja_selecionada').val() || 
    $('[data-loja-id]').data('loja-id') || 
    new URLSearchParams(window.location.search).get('loja')
  );
  
  // Atualizar lista de salas (específico para admin)
  if ($('#sala, #sala_em_uso, select[name="sala"]').length > 0) {
    updateAdminSalasDropdown(lojaId);
  }
  
  // Atualizar lista de periféricos disponíveis para cadastro
  if ($('select[name="periferico"], #periferico').length > 0) {
    updateAdminPerifericosDropdown(lojaId);
  }
  
  // Atualizar lista de computadores disponíveis para atribuição
  if ($('select[name="computador"], #computador').length > 0) {
    updateAdminComputadoresDropdown(lojaId);
  }
  
  // Atualizar lista de monitores disponíveis para atribuição
  if ($('select[name="monitor"], #monitor').length > 0) {
    updateAdminMonitoresDropdown(lojaId);
  }
}

// Função para atualizar dropdown de salas nas páginas de admin
function updateAdminSalasDropdown(lojaId) {
  if (!lojaId) return;
  
  $.ajax({
    url: `/ti/api/salas-por-loja/${lojaId}/`,
    type: 'GET',
    success: function(data) {
      if (data.salas) {
        const $selects = $('#sala, #sala_em_uso, select[name="sala"]');
        $selects.each(function() {
          const $select = $(this);
          const currentVal = $select.val();
          
          // Limpar todas as opções exceto a primeira
          $select.find('option').not(':first').remove();
          
          $.each(data.salas, function(index, sala) {
            // Verificar se a opção já existe para evitar duplicação
            if ($select.find('option[value="' + sala.id + '"]').length === 0) {
              $select.append(`<option value="${sala.id}">${sala.nome}</option>`);
            }
          });
          
          // Manter seleção se ainda existir
          if (currentVal) {
            $select.val(currentVal);
          }
        });
        
        // Limpar dropdowns dependentes quando as salas são atualizadas
        $('#ilha, #ilha_em_uso, select[name="ilha"]').each(function() {
          $(this).empty().html('<option value="">-- Selecione uma Ilha --</option>');
        });
      }
    },
    error: function(xhr, status, error) {
      console.error('Erro ao carregar salas para admin:', error);
      if (window.TIAdminNotifications) {
        window.TIAdminNotifications.showAdminNotification('error', 'Erro ao carregar lista de salas');
      }
    }
  });
}

// Função para atualizar dropdown de periféricos disponíveis
function updateAdminPerifericosDropdown(lojaId) {
  $.ajax({
    url: '/ti/api/listar-perifericos/',
    type: 'GET',
    data: { 
      status: 'disponivel', 
      loja: lojaId,
      per_page: 100 
    },
    success: function(response) {
      if (response.success && response.data) {
        const $selects = $('select[name="periferico"], #periferico');
        $selects.each(function() {
          const $select = $(this);
          const currentVal = $select.val();
          $select.find('option:not(:first)').remove();
          
          $.each(response.data, function(index, periferico) {
            $select.append(`<option value="${periferico.id}">${periferico.tipo.nome} - ${periferico.marca} ${periferico.modelo}</option>`);
          });
          
          if (currentVal) {
            $select.val(currentVal);
          }
        });
      }
    },
    error: function(xhr, status, error) {
      console.error('Erro ao carregar periféricos para admin:', error);
    }
  });
}

// Função para atualizar dropdown de computadores disponíveis
function updateAdminComputadoresDropdown(lojaId) {
  $.ajax({
    url: '/ti/api/computadores_disponiveis/',
    type: 'GET',
    data: { loja: lojaId },
    success: function(response) {
      if (response.success && response.computadores) {
        const $selects = $('select[name="computador"], #computador');
        $selects.each(function() {
          const $select = $(this);
          const currentVal = $select.val();
          $select.find('option:not(:first)').remove();
          
          $.each(response.computadores, function(index, computador) {
            $select.append(`<option value="${computador.id}">${computador.marca}</option>`);
          });
          
          if (currentVal) {
            $select.val(currentVal);
          }
        });
      }
    },
    error: function(xhr, status, error) {
      console.error('Erro ao carregar computadores para admin:', error);
    }
  });
}

// Função para atualizar dropdown de monitores disponíveis
function updateAdminMonitoresDropdown(lojaId) {
  $.ajax({
    url: '/ti/api/monitores_disponiveis/',
    type: 'GET',
    data: { loja: lojaId },
    success: function(response) {
      if (response.success && response.monitores) {
        const $selects = $('select[name="monitor"], #monitor');
        $selects.each(function() {
          const $select = $(this);
          const currentVal = $select.val();
          $select.find('option:not(:first)').remove();
          
          $.each(response.monitores, function(index, monitor) {
            $select.append(`<option value="${monitor.id}">${monitor.marca} (${monitor.tamanho})</option>`);
          });
          
          if (currentVal) {
            $select.val(currentVal);
          }
        });
      }
    },
    error: function(xhr, status, error) {
      console.error('Erro ao carregar monitores para admin:', error);
    }
  });
}

// Função para carregar PAs por ilha (movida do admin.js)
function carregarPAsPorIlha(ilhaId, targetSelect, lojaId) {
  if (!ilhaId || !targetSelect || !targetSelect.length) return;
  
  // Limpar e resetar dropdown de PAs
  targetSelect.empty().html('<option value="">-- Selecione uma PA --</option>');
  
  // Buscar PAs da ilha selecionada
  $.ajax({
    url: '/ti/api/listar-posicoes-atendimento/',
    type: 'GET',
    data: {
      ilha: ilhaId,
      loja: lojaId,
      per_page: 100 // Usar um valor alto para garantir que todas as PAs sejam retornadas
    },
    dataType: 'json',
    success: function(data) {
      if (data.success && data.data) {
        $.each(data.data, function(index, pa) {
          // Verificar se a opção já existe para evitar duplicação
          if (targetSelect.find('option[value="' + pa.id + '"]').length === 0) {
            const $option = $('<option></option>');
            $option.val(pa.id);
            $option.text('PA ' + pa.numero);
            targetSelect.append($option);
          }
        });
      }
    },
    error: function(error) {
      console.error('Erro ao carregar PAs:', error);
    }
  });
}

// Função para obter informações detalhadas de uma ilha
function obterInfoIlha(ilhaId, callback) {
  if (!ilhaId) {
    if (callback) callback(null);
    return;
  }
  
  $.ajax({
    url: '/ti/api/ilha-info/' + ilhaId + '/',
    type: 'GET',
    dataType: 'json',
    success: function(data) {
      if (callback) callback(data);
    },
    error: function(error) {
      console.error('Erro ao obter informações da ilha:', error);
      if (callback) callback(null);
    }
  });
}

// Função para atualizar informações de quantidade de PAs baseada na ilha selecionada (movida do admin.js)
function atualizarQuantidadePAs(ilhaId, $quantidadePasInput, $infoText) {
  if (!ilhaId) {
    // Se nenhuma ilha selecionada, limitar para 1
    $quantidadePasInput.attr('max', 1);
    $quantidadePasInput.val(1);
    if ($infoText && $infoText.length) {
      $infoText.text('');
    }
    return;
  }
  
  // Obter informações detalhadas da ilha
  obterInfoIlha(ilhaId, function(data) {
    if (data && data.success && data.ilha) {
      const capacidadeDisponivel = data.ilha.pas_disponiveis || 1;
      $quantidadePasInput.attr('max', capacidadeDisponivel);
      $quantidadePasInput.val(Math.min($quantidadePasInput.val() || 1, capacidadeDisponivel));
      
      // Atualizar texto informativo
      if ($infoText && $infoText.length) {
        $infoText.text('Máximo disponível: ' + capacidadeDisponivel + ' PAs');
      }
    } else {
      console.error('Erro ao obter informações da ilha:', ilhaId);
      $quantidadePasInput.attr('max', 1);
      $quantidadePasInput.val(1);
      if ($infoText && $infoText.length) {
        $infoText.text('Erro ao carregar informações da ilha');
      }
    }
  });
}

// Exportar funções para uso global
window.TIAdminDropdowns = {
  updateAdminDropdowns: updateAdminDropdowns,
  updateAdminSalasDropdown: updateAdminSalasDropdown,
  updateAdminPerifericosDropdown: updateAdminPerifericosDropdown,
  updateAdminComputadoresDropdown: updateAdminComputadoresDropdown,
  updateAdminMonitoresDropdown: updateAdminMonitoresDropdown,
  carregarPAsPorIlha: carregarPAsPorIlha,
  obterInfoIlha: obterInfoIlha,
  atualizarQuantidadePAs: atualizarQuantidadePAs
};