/**
 * JavaScript para a funcionalidade de Auto Atribuição de PA
 * 
 * Funcionalidades:
 * - Validação de formulário
 * - Verificação de PAs ocupadas
 * - Modal de confirmação para troca/substituição
 * - Processamento de atribuições via AJAX
 * 
 * Convertido para jQuery para padronização com o restante do projeto
 */

// Variáveis globais
var $modalElement = null;
var $closeBtn = null;
var $footerCloseBtn = null;

// Implementação de modal personalizado
var customModal = {
  show: function() {
    // Tentar obter o elemento modal caso ainda não tenha sido encontrado
    if (!$modalElement || !$modalElement.length) {
      $modalElement = $('#pa-reassign-modal');
    }
    
    if (!$modalElement.length) {
      console.error('Elemento do modal não encontrado');
      return;
    }
    console.log('Mostrando modal personalizado');
    // Adicionar classe para mostrar o modal
    $modalElement.addClass('visible');
    
    // Impedir o scroll no body
    $('body').css('overflow', 'hidden');
  },
  hide: function() {
    if (!$modalElement || !$modalElement.length) {
      $modalElement = $('#pa-reassign-modal');
    }
    
    if (!$modalElement.length) {
      console.error('Elemento do modal não encontrado para ocultar');
      return;
    }
    console.log('Escondendo modal personalizado');
    // Remover classe para esconder o modal
    $modalElement.removeClass('visible');
    
    // Restaurar o scroll no body
    $('body').css('overflow', '');
  }
};

// Garantir que o modal e outros elementos estejam inicializados corretamente
function initializeElements() {
  $modalElement = $('#pa-reassign-modal');
  $closeBtn = $('#modal-close-btn');
  $footerCloseBtn = $('#modal-footer-close');
  
  console.log('Modal element:', $modalElement);
  
  // Adicionar eventos de fechamento aos botões
  if ($closeBtn.length) {
    $closeBtn.on('click', function() {
      customModal.hide();
    });
  }
  
  if ($footerCloseBtn.length) {
    $footerCloseBtn.on('click', function() {
      customModal.hide();
    });
  }
  
  // Permitir fechar o modal ao clicar fora dele
  if ($modalElement.length) {
    $modalElement.on('click', function(e) {
      if (e.target === this) {
        customModal.hide();
      }
    });
  }
}

// Funções auxiliares - definidas fora do escopo document.ready para evitar duplicação

// Verificar se a PA selecionada está ocupada
function isPaOcupada($paSelectElement) {
  if (!$paSelectElement || !$paSelectElement.length || $paSelectElement.prop('selectedIndex') < 0) {
    console.log('PA não selecionada ou elemento select inválido');
    return false;
  }
  
  const optionText = $paSelectElement.find('option:selected').text() || '';
  console.log('Texto da opção selecionada:', optionText);
  const isOcupada = optionText.includes('[Ocupada por:');
  console.log('PA está ocupada?', isOcupada);
  return isOcupada;
}

// Extrair o nome do funcionário que ocupa a PA
function getOccupantName($paSelectElement) {
  if (!$paSelectElement || !$paSelectElement.length || $paSelectElement.prop('selectedIndex') < 0) return '';
  
  const optionText = $paSelectElement.find('option:selected').text() || '';
  const match = optionText.match(/\[Ocupada por: (.+?)\]/);
  
  return (match && match[1]) ? match[1].trim() : '';
}

// Extrair o número da PA
function getPaNumber($paSelectElement) {
  if (!$paSelectElement || !$paSelectElement.length || $paSelectElement.prop('selectedIndex') < 0) return '';
  
  const optionText = $paSelectElement.find('option:selected').text() || '';
  const match = optionText.match(/PA\s+(\d+)/);
  
  return (match && match[1]) ? match[1].trim() : '';
}

// Mostrar o modal de reatribuição com informações específicas
function showReassignModal(paInfo) {
  // Verificar se o elemento do modal existe
  if (!$modalElement || !$modalElement.length) {
    $modalElement = $('#pa-reassign-modal');
  }
  
  if (!$modalElement.length) {
    console.error('Elemento do modal não encontrado');
    return;
  }
  
  // Atualizar o conteúdo do modal com as informações da PA
  const $titleElement = $modalElement.find('.custom-modal-title');
  if ($titleElement.length) {
    $titleElement.html(`<i class='bx bx-transfer-alt'></i>PA ${paInfo.numero} já está ocupada`);
  }
  
  const $bodyElement = $modalElement.find('.custom-modal-body');
  if ($bodyElement.length) {
    // Atualizar texto no alerta do modal
    const $paOcupadaInfo = $modalElement.find('#pa-ocupada-info');
    if ($paOcupadaInfo.length) {
      $paOcupadaInfo.text(`A PA selecionada já está atribuída ao funcionário ${paInfo.funcionario_nome}.`);
    }
    
    // Atualizar números da PA e nome do funcionário nos campos dinâmicos
    $modalElement.find('#target-pa-num, #target-pa-num2').text(paInfo.numero);
    $modalElement.find('#other-user-name, #other-user-name2').text(paInfo.funcionario_nome);
  }
  
  // Configurar os botões de ação
  setupModalOptions(paInfo.id, null);
  
  // Exibir o modal personalizado
  customModal.show();
}

// Configurar eventos para as opções do modal
function setupModalOptions(paId, funcionarioId) {
  const $optionSwap = $('#option-swap');
  const $optionReplace = $('#option-replace');
  const $optionCancel = $('#option-cancel');
  
  // Remover handlers antigos para evitar duplicação
  $optionSwap.off('click');
  $optionReplace.off('click');
  $optionCancel.off('click');
  
  if ($optionSwap.length) {
    $optionSwap.on('click', function() {
      handleReassignment(paId, 'swap');
      customModal.hide();
    });
  }
  
  if ($optionReplace.length) {
    $optionReplace.on('click', function() {
      handleReassignment(paId, 'replace');
      customModal.hide();
    });
  }
  
  if ($optionCancel.length) {
    $optionCancel.on('click', function() {
      customModal.hide();
    });
  }
}

// Processar a reatribuição (troca ou substituição)
function handleReassignment(paId, option) {
  // Mostrar indicador de carregamento
  var $messageContainer = $('#message-container');
  $messageContainer.html(
    '<div class="alert alert-info alert-dismissible fade show" role="alert">'+
      '<i class="bx bx-loader-alt bx-spin me-2"></i> Processando sua solicitação...'+
      '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'+
    '</div>'
  );
  
  // Obter o token CSRF do formulário
  var csrfToken = $('[name=csrfmiddlewaretoken]').val();
  
  // Preparar os dados para envio
  var data = {
    pa_id: paId,
    option: option
  };
  
  console.log('Enviando dados para reatribuição:', data);
  
  // Usando jQuery para fazer a requisição AJAX
  $.ajax({
    url: '/ti/api/auto-atribuicao-pa-reassign/',
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'X-Requested-With': 'XMLHttpRequest'
    },
    contentType: 'application/json',
    data: JSON.stringify(data),
    success: function(response) {
      if (response.success) {
        $messageContainer.html(
          '<div class="alert alert-success alert-dismissible fade show" role="alert">'+
            '<i class="bx bx-check-circle me-2"></i> '+ response.message +
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'+
          '</div>'
        );
        
        // Recarregar a página após 2 segundos
        setTimeout(function() {
          window.location.reload();
        }, 2000);
      } else {
        $messageContainer.html(
          '<div class="alert alert-danger alert-dismissible fade show" role="alert">'+
            '<i class="bx bx-error-circle me-2"></i> '+ (response.message || 'Ocorreu um erro ao processar sua solicitação.') +
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'+
          '</div>'
        );
      }
    },
    error: function(error) {
      console.error('Erro:', error);
      $messageContainer.html(
        '<div class="alert alert-danger alert-dismissible fade show" role="alert">'+
          '<i class="bx bx-error-circle me-2"></i> Ocorreu um erro ao processar sua solicitação.'+
          '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'+
        '</div>'
      );
    }
  });
}

// Inicialização quando o DOM está pronto
$(document).ready(function() {
  // Elementos DOM
  var $form = $('#pa-form');
  var $paSelect = $('#pa-select'); // Seleciona o elemento do select de PA
  
  // Inicializar elementos ao carregar a página
  initializeElements();
  
  // Mover o modal para o corpo do documento, se necessário
  setTimeout(function() {
    console.log('Verificando posição do modal...');
    var $modalElement = $('#pa-reassign-modal');
    if ($modalElement.length) {
      // Mover o modal para o final do body
      $modalElement.detach().appendTo('body');
    }
  });
  
  // Configurar o formulário
  if ($form.length) {
    $form.on('submit', function(e) {
      e.preventDefault();
      console.log('Formulário submetido');
      
      if (!$paSelect.val()) {
        // Criar alerta se nenhuma PA foi selecionada
        var $messageContainer = $('#message-container');
        $messageContainer.html(
          '<div class="alert alert-warning alert-dismissible fade show" role="alert">'+
            '<i class="bx bx-error me-2"></i> Por favor, selecione uma PA.'+
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'+
          '</div>'
        );
        return;
      }
      
      console.log('PA selecionada:', $paSelect.val());
      
      // Verificar se a PA está ocupada após clicar no botão de confirmação
      if (isPaOcupada($paSelect)) {
        console.log('PA está ocupada, exibindo modal de confirmação');
        // Obter informações para o modal
        var occupantName = getOccupantName($paSelect);
        var paNumber = getPaNumber($paSelect);
        var paId = $paSelect.val();
        
        try {
          // Criar um objeto com as informações para o modal
          var paInfo = {
            id: paId,
            funcionario_nome: occupantName,
            numero: paNumber,
            funcionario_id: null // Valor a ser preenchido pela API se necessário
          };
          
          // Mostrar o modal de confirmação
          showReassignModal(paInfo);
        } catch (error) {
          console.error('Erro ao exibir o modal:', error);
        }
        return;
      }
      
      console.log('PA não ocupada, prosseguindo com atribuição normal');
      // Se a PA não está ocupada, proceder normalmente
      var formData = new FormData(this);
      
      // Usar jQuery Ajax para enviar o formulário
      $.ajax({
        url: '/ti/auto-atribuicao-pa/',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(data) {
          var $messageContainer = $('#message-container');
          
          if (data.success) {
            $messageContainer.html(
              '<div class="alert alert-success alert-dismissible fade show" role="alert">'+
                '<i class="bx bx-check-circle me-2"></i> '+ data.message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'+
              '</div>'
            );
            
            // Atualizar a página após 2 segundos
            setTimeout(function() {
              window.location.reload();
            }, 2000);
          } else {
            $messageContainer.html(
              '<div class="alert alert-danger alert-dismissible fade show" role="alert">'+
                '<i class="bx bx-error-circle me-2"></i> '+ data.message +
                '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'+
              '</div>'
            );
          }
        },
        error: function(error) {
          console.error('Erro:', error);
          var $messageContainer = $('#message-container');
          $messageContainer.html(
            '<div class="alert alert-danger alert-dismissible fade show" role="alert">'+
              '<i class="bx bx-error-circle me-2"></i> Ocorreu um erro ao processar sua solicitação.'+
              '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'+
            '</div>'
          );
        }
      });
    });
  }
});