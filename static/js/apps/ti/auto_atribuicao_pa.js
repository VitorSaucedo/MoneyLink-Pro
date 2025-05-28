/**
 * JavaScript para a funcionalidade de Auto Atribuição de PA
 * 
 * Funcionalidades:
 * - Validação de formulário
 * - Verificação de PAs ocupadas
 * - Modal de confirmação para troca/substituição
 * - Processamento de atribuições via AJAX
 */

// Variáveis globais
let modalElement = null;
let closeBtn = null;
let footerCloseBtn = null;

// Implementação de modal personalizado
const customModal = {
  show: function() {
    // Tentar obter o elemento modal caso ainda não tenha sido encontrado
    if (!modalElement) {
      modalElement = document.getElementById('pa-reassign-modal');
    }
    
    if (!modalElement) {
      console.error('Elemento do modal não encontrado');
      return;
    }
    console.log('Mostrando modal personalizado');
    // Adicionar classe para mostrar o modal
    modalElement.classList.add('visible');
    
    // Impedir o scroll no body
    document.body.style.overflow = 'hidden';
  },
  hide: function() {
    if (!modalElement) {
      modalElement = document.getElementById('pa-reassign-modal');
    }
    
    if (!modalElement) {
      console.error('Elemento do modal não encontrado para ocultar');
      return;
    }
    console.log('Escondendo modal personalizado');
    // Remover classe para esconder o modal
    modalElement.classList.remove('visible');
    
    // Restaurar o scroll no body
    document.body.style.overflow = '';
  }
};

// Garantir que o modal e outros elementos estejam inicializados corretamente
function initializeElements() {
  modalElement = document.getElementById('pa-reassign-modal');
  closeBtn = document.getElementById('modal-close-btn');
  footerCloseBtn = document.getElementById('modal-footer-close');
  
  console.log('Modal element:', modalElement);
  
  // Adicionar eventos de fechamento aos botões
  if (closeBtn) {
    closeBtn.addEventListener('click', function() {
      customModal.hide();
    });
  }
  
  if (footerCloseBtn) {
    footerCloseBtn.addEventListener('click', function() {
      customModal.hide();
    });
  }
  
  // Permitir fechar o modal ao clicar fora dele
  if (modalElement) {
    modalElement.addEventListener('click', function(e) {
      if (e.target === modalElement) {
        customModal.hide();
      }
    });
  }
}

// Funções auxiliares - definidas fora do escopo DOMContentLoaded para evitar duplicação

// Verificar se a PA selecionada está ocupada
function isPaOcupada(paSelectElement) {
  if (!paSelectElement || !paSelectElement.selectedIndex || paSelectElement.selectedIndex < 0) return false;
  
  const selectedOption = paSelectElement.options[paSelectElement.selectedIndex];
  if (!selectedOption) return false;
  
  const optionText = selectedOption.textContent || '';
  return optionText.includes('[Ocupada por:');
}

// Extrair o nome do funcionário que ocupa a PA
function getOccupantName(paSelectElement) {
  if (!paSelectElement || !paSelectElement.selectedIndex || paSelectElement.selectedIndex < 0) return '';
  
  const selectedOption = paSelectElement.options[paSelectElement.selectedIndex];
  if (!selectedOption) return '';
  
  const optionText = selectedOption.textContent || '';
  const match = optionText.match(/\[Ocupada por: (.+?)\]/);
  
  return (match && match[1]) ? match[1].trim() : '';
}

// Extrair o número da PA
function getPaNumber(paSelectElement) {
  if (!paSelectElement || !paSelectElement.selectedIndex || paSelectElement.selectedIndex < 0) return '';
  
  const selectedOption = paSelectElement.options[paSelectElement.selectedIndex];
  if (!selectedOption) return '';
  
  const optionText = selectedOption.textContent || '';
  const match = optionText.match(/PA\s+(\d+)/);
  
  return (match && match[1]) ? match[1].trim() : '';
}

// Mostrar o modal de reatribuição com informações específicas
function showReassignModal(paInfo) {
  // Verificar se o elemento do modal existe
  if (!modalElement) {
    modalElement = document.getElementById('pa-reassign-modal');
  }
  
  if (!modalElement) {
    console.error('Elemento do modal não encontrado');
    return;
  }
  
  // Preencher os detalhes no modal
  const paInfoElement = document.getElementById('pa-ocupada-info');
  if (paInfoElement) {
    paInfoElement.textContent = `A PA ${paInfo.numero} está ocupada por ${paInfo.funcionario_nome}.`;
  }
      
  // Preencher informações para as opções
  document.querySelectorAll('#target-pa-num, #target-pa-num2').forEach(el => {
    if (el) el.textContent = paInfo.numero;
  });
  
  document.querySelectorAll('#other-user-name, #other-user-name2').forEach(el => {
    if (el) el.textContent = paInfo.funcionario_nome;
  });
  
  // Configurar eventos para as opções
  setupModalOptions(paInfo.id, paInfo.funcionario_id);
  
  // Exibir o modal personalizado
  customModal.show();
}

// Configurar eventos para as opções do modal
function setupModalOptions(paId, funcionarioId) {
  const optionSwap = document.getElementById('option-swap');
  const optionReplace = document.getElementById('option-replace');
  const optionCancel = document.getElementById('option-cancel');
  
  if (optionSwap) {
    optionSwap.onclick = function() {
      handleReassignment(paId, 'swap');
      customModal.hide();
    };
  }
  
  if (optionReplace) {
    optionReplace.onclick = function() {
      handleReassignment(paId, 'replace');
      customModal.hide();
    };
  }
  
  if (optionCancel) {
    optionCancel.onclick = function() {
      customModal.hide();
    };
  }
}

// Processar a reatribuição (troca ou substituição)
async function handleReassignment(paId, option) {
  // Mostrar indicador de carregamento
  const messageContainer = document.getElementById('message-container');
  messageContainer.innerHTML = `
    <div class="alert alert-info alert-dismissible fade show" role="alert">
      <i class='bx bx-loader-alt bx-spin me-2'></i> Processando sua solicitação...
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  `;
  
  try {
    // Obter o token CSRF do formulário
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Preparar os dados para envio
    const data = {
      pa_id: paId,
      option: option
    };
    
    console.log('Enviando dados para reatribuição:', data);
    
    // Enviar a solicitação para a API com a URL correta
    const response = await fetch('/ti/api/auto-atribuicao-pa-reassign/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`Erro na requisição: ${response.status}`);
    }
    
    const responseData = await response.json();
    
    if (responseData.success) {
      messageContainer.innerHTML = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
          <i class='bx bx-check-circle me-2'></i> ${responseData.message}
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      `;
      
      // Recarregar a página após 2 segundos
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } else {
      messageContainer.innerHTML = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
          <i class='bx bx-error-circle me-2'></i> ${responseData.message || 'Ocorreu um erro ao processar sua solicitação.'}
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      `;
    }
  } catch (error) {
    console.error('Erro:', error);
    messageContainer.innerHTML = `
      <div class="alert alert-danger alert-dismissible fade show" role="alert">
        <i class='bx bx-error-circle me-2'></i> Ocorreu um erro ao processar sua solicitação.
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>
    `;
  }
}

// Inicialização quando o DOM está pronto
document.addEventListener('DOMContentLoaded', function() {
  // Elementos DOM
  const form = document.getElementById('pa-form');
  const paSelect = document.getElementById('pa-select');
  
  // Inicializar elementos ao carregar a página
  initializeElements();
  
  // Garantir que o modal está inicializado quando a página terminar de carregar
  window.addEventListener('load', function() {
    // Tentar inicializar elementos novamente, caso não tenham sido encontrados no DOMContentLoaded
    if (!modalElement) {
      console.log('Tentando inicializar elementos novamente...');
      initializeElements();
    }
    
    // Garantir que o modal esteja no fim do documento
    const modalElement = document.getElementById('pa-reassign-modal');
    if (modalElement) {
      // Remover o modal se estiver dentro de outro container
      if (modalElement.parentNode) {
        modalElement.parentNode.removeChild(modalElement);
      }
      // Adicionar ao final do body
      document.body.appendChild(modalElement);
    }
  });
  
  // Configurar o formulário
  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      console.log('Formulário submetido');
      
      if (!paSelect.value) {
        // Criar alerta se nenhuma PA foi selecionada
        const messageContainer = document.getElementById('message-container');
        messageContainer.innerHTML = `
          <div class="alert alert-warning alert-dismissible fade show" role="alert">
            <i class='bx bx-error me-2'></i> Por favor, selecione uma PA.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          </div>
        `;
        return;
      }
      
      console.log('PA selecionada:', paSelect.value);
      
      // Verificar se a PA está ocupada após clicar no botão de confirmação
      if (isPaOcupada(paSelect)) {
        console.log('PA está ocupada, exibindo modal de confirmação');
        // Obter informações para o modal
        const occupantName = getOccupantName(paSelect);
        const paNumber = getPaNumber(paSelect);
        const paId = paSelect.value;
        
        try {
          // Criar um objeto com as informações para o modal
          const paInfo = {
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
      const formData = new FormData(form);
      
      // Corrigir a URL para corresponder à rota correta no urls.py
      fetch('/ti/auto-atribuicao-pa/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(response => response.json())
      .then(data => {
        const messageContainer = document.getElementById('message-container');
        
        if (data.success) {
          messageContainer.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
              <i class='bx bx-check-circle me-2'></i> ${data.message}
              <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
          `;
          
          // Atualizar a página após 2 segundos
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        } else {
          messageContainer.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
              <i class='bx bx-error-circle me-2'></i> ${data.message}
              <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
          `;
        }
      })
      .catch(error => {
        console.error('Erro:', error);
        const messageContainer = document.getElementById('message-container');
        messageContainer.innerHTML = `
          <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class='bx bx-error-circle me-2'></i> Ocorreu um erro ao processar sua solicitação.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          </div>
        `;
      });
    });
  }
});