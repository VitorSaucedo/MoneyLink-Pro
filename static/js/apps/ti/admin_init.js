/**
 * admin_init.js - Arquivo de inicialização das funcionalidades de administração do TI
 * 
 * Este arquivo deve ser carregado após todos os outros módulos admin e é responsável por:
 * - Inicializar os módulos de admin na ordem correta
 * - Configurar eventos específicos de administração
 * - Garantir que todas as dependências de admin estejam disponíveis
 */

$(document).ready(function() {
  console.log('🚀 Iniciando módulos de administração do TI...');
  
  // Verificar se os módulos de admin foram carregados
  const adminModulesStatus = {
    utils: !!window.TIAdminUtils,
    notifications: !!window.TIAdminNotifications,
    dropdowns: !!window.TIAdminDropdowns
  };
  
  console.log('📦 Status dos módulos de admin:', adminModulesStatus);
  
  // Configurações específicas de admin
  if (window.TIAdminUtils) {
    // Configurar ajustes responsivos para páginas de admin
    window.TIAdminUtils.adjustAdminWidths();
    $(window).on('resize', window.TIAdminUtils.adjustAdminWidths);
    
    // Inicializar comportamentos específicos de admin
    window.TIAdminUtils.initAdminBehaviors();
  }
  
  // Inicializar dropdowns de admin se necessário
  if (window.TIAdminDropdowns && window.TIAdminUtils) {
    // Carregar dropdowns iniciais se houver uma loja selecionada
    const lojaId = window.TIAdminUtils.getSelectedLojaAdmin();
    if (lojaId) {
      console.log('🔄 Carregando dropdowns de admin para loja:', lojaId);
      window.TIAdminDropdowns.updateAdminDropdowns();
    }
  }
  
  // Configurar eventos específicos de administração
  setupAdminEvents();
  
  // Configurar campos condicionais
  setupConditionalFields();
  
  // Configurar interceptação de formulários
  setupFormInterception();
  
  // Configurar comportamentos de formulários AJAX
  setupAjaxFormBehaviors();
  
  // Mostrar notificação de inicialização apenas em desenvolvimento
  if (window.TIAdminNotifications && (window.location.hostname === 'localhost' || window.location.hostname.includes('127.0.0.1'))) {
    setTimeout(() => {
      window.TIAdminNotifications.showAdminNotification('success', 'Módulos de administração carregados!');
    }, 1500);
  }
  
  console.log('✅ Módulos de administração do TI inicializados');
});

// Função para configurar eventos específicos de administração
function setupAdminEvents() {
  // Evento para atualizar dropdowns quando a loja for alterada
  $(document).on('change', 'select[name="loja"]', function() {
    const lojaId = $(this).val();
    console.log('🏪 Loja alterada para:', lojaId);
    
    if (window.TIAdminDropdowns && lojaId) {
      window.TIAdminDropdowns.updateAdminDropdowns();
    }
  });
  
  // Evento para validação de formulários de admin antes do envio
  $(document).on('submit', 'form.ajax-form, form[data-ajax="true"]', function(e) {
    const $form = $(this);
    const formId = $form.attr('id') || '';
    
    console.log('📝 Validando formulário de admin:', formId);
    
    // Validações específicas para cada tipo de formulário de admin
    if (formId.includes('ramal')) {
      return validateAdminRamalForm($form, e);
    } else if (formId.includes('computador')) {
      return validateAdminComputadorForm($form, e);
    }
    
    return true;
  });
  
  // Evento para fechar modais automaticamente após sucesso
  $(document).on('hidden.bs.modal', '.modal', function() {
    const $modal = $(this);
    
    // Limpar formulários dentro do modal
    $modal.find('form').each(function() {
      this.reset();
      $(this).find('.is-invalid, .is-valid').removeClass('is-invalid is-valid');
      $(this).find('.admin-validation-feedback').remove();
    });
  });
}

// Função para validar formulários de ramal (específico de admin)
function validateAdminRamalForm($form, event) {
  const $ramalInput = $form.find('#numero_ramal, input[name="numero_ramal"]');
  const $funcionarioSelect = $form.find('#funcionario_ramal, select[name="funcionario_ramal"]');
  
  if ($ramalInput.length && $funcionarioSelect.length) {
    const ramal = $ramalInput.val().trim();
    const funcionarioId = $funcionarioSelect.val();
    
    if (!ramal || !funcionarioId) {
      event.preventDefault();
      
      if (window.TIAdminNotifications) {
        window.TIAdminNotifications.showAdminNotification('error', 'Preencha todos os campos obrigatórios');
      }
      
      return false;
    }
    
    if (!/^\d{4}$/.test(ramal)) {
      event.preventDefault();
      
      if (window.TIAdminNotifications) {
        window.TIAdminNotifications.showAdminValidationNotification('numero_ramal', 'O ramal deve ter exatamente 4 dígitos numéricos');
      }
      
      return false;
    }
  }
  
  return true;
}

// Função para validar formulários de computador (específico de admin)
function validateAdminComputadorForm($form, event) {
  const $statusSelect = $form.find('#status_computador, select[name="status_computador"]');
  
  if ($statusSelect.length) {
    const status = $statusSelect.val();
    
    if (status === 'em_uso') {
      const $paSelect = $form.find('#pa_em_uso, select[name="pa_em_uso"]');
      
      if ($paSelect.length && !$paSelect.val()) {
        event.preventDefault();
        
        if (window.TIAdminNotifications) {
          window.TIAdminNotifications.showAdminNotification('error', 'Selecione uma Posição de Atendimento para computadores em uso');
        }
        
        return false;
      }
    } else if (status === 'manutencao') {
      const $obsTextarea = $form.find('#observacoes_manutencao, textarea[name="observacoes_manutencao"]');
      
      if ($obsTextarea.length && !$obsTextarea.val().trim()) {
        event.preventDefault();
        
        if (window.TIAdminNotifications) {
          window.TIAdminNotifications.showAdminNotification('error', 'Informe o motivo da manutenção');
        }
        
        return false;
      }
    }
  }
  
  return true;
}

// Função para verificar se ramal já existe (movida do admin.js)
function verificarRamalExistente(ramal, funcionarioId, callback) {
  if (!ramal || !funcionarioId) {
    if (callback) callback(null);
    return;
  }
  
  $.ajax({
    url: '/ti/api/verificar-ramal/',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
    },
    data: JSON.stringify({
      ramal: ramal,
      funcionario_id: funcionarioId
    }),
    dataType: 'json',
    success: function(data) {
      if (callback) callback(data);
    },
    error: function(xhr, status, error) {
      console.error('Erro ao verificar ramal:', error);
      if (callback) callback(null);
    }
  });
}

// Função para configurar eventos de campos condicionais
function setupConditionalFields() {
  // Configurar campos condicionais do status do computador
  const $statusComputador = $('#status_computador');
  const $camposEmUso = $('#campos_em_uso');
  const $camposManutencao = $('#campos_manutencao');
  
  if ($statusComputador.length) {
    function atualizarCamposCondicionais() {
      const status = $statusComputador.val();
      
      // Esconder todos os campos condicionais primeiro
      $('.campos-condicionais').hide();
      
      // Resetar validação visual
      $('#pa_em_uso, #observacoes_manutencao').removeClass('is-invalid');
      
      if (status === 'em_uso') {
        $camposEmUso.show();
        $('#pa_em_uso').prop('required', true);
        $('#observacoes_manutencao').prop('required', false);
      } else if (status === 'manutencao') {
        $camposManutencao.show();
        $('#observacoes_manutencao').prop('required', true);
        $('#pa_em_uso').prop('required', false);
      } else {
        $('#pa_em_uso, #observacoes_manutencao').prop('required', false);
      }
    }
    
    // Atualizar ao carregar a página
    atualizarCamposCondicionais();
    
         // Atualizar quando o status mudar
     $statusComputador.on('change', atualizarCamposCondicionais);
   }
}

// Função para configurar interceptação de formulários (movida do admin.js)
function setupFormInterception() {
  // Interceptar submits de formulários principais  
  $(document).on('submit', 'form[data-ajax="true"], form.ajax-form, #form-periferico, #form-computador, #form-sala, #form-ilha, #form-pa, #form-tipo-periferico, #form-monitor, form[id*="form_"], form[id*="form-"]', function(e) {
    e.preventDefault();
    
    const form = this;
    const $form = $(form);
    const formId = $form.attr('id') || '';
    
    console.log('🔄 Interceptando formulário:', formId);
    
    // Marcar como processado para evitar dupla interceptação
    $form.addClass('ajax-processed').attr('data-ajax-processed', 'true');
    
    // Obter URL AJAX e mensagem de sucesso usando módulo utilitário
    const ajaxUrl = window.TIAdminUtils ? window.TIAdminUtils.getFormAjaxUrl(formId) : null;
    const successMessage = window.TIAdminUtils ? window.TIAdminUtils.getSuccessMessage(formId) : 'Salvo com sucesso!';
    
    console.log('🎯 URL AJAX encontrada:', ajaxUrl);
    
    if (ajaxUrl && window.submitFormAjaxCustom) {
      // Usar URL AJAX específica
      window.submitFormAjaxCustom(form, ajaxUrl, successMessage);
    } else if (window.submitFormAjax) {
      // Fallback para método original
      window.submitFormAjax(form, successMessage);
    }
  });
  
  // Interceptar submits de formulários de atribuição
  $(document).on('submit', 'form[data-ajax-atribuicao="true"], #form-atribuicao-funcionario, #form-atribuicao-periferico, #form-atribuicao-computador, #form-atribuicao-monitor', function(e) {
    e.preventDefault();
    
    const form = this;
    const $form = $(form);
    
    // Marcar como processado
    $form.addClass('ajax-processed').attr('data-ajax-processed', 'true');
    
    if (window.submitFormAjax) {
      window.submitFormAjax(form, 'Atribuição realizada com sucesso!');
    }
  });
  
  // Interceptador geral para qualquer formulário que não foi capturado acima
  $(document).on('submit', 'form', function(e) {
    const $form = $(this);
    const formId = $form.attr('id') || '';
    
    // Verificar se o formulário já foi processado pelos interceptadores acima
    if ($form.hasClass('ajax-processed') || 
        $form.attr('data-ajax-processed') === 'true') {
      return; // Deixar o comportamento normal
    }
    
    // Verificar se deveria usar AJAX usando módulo utilitário
    const shouldUseAjax = window.TIAdminUtils ? window.TIAdminUtils.shouldUseAjax(this) : false;
    
    if (shouldUseAjax) {
      e.preventDefault();
      
      console.log('🔄 Formulário capturado pelo interceptador geral:', formId);
      
      // Marcar como processado
      $form.addClass('ajax-processed').attr('data-ajax-processed', 'true');
      
      // Determinar URL AJAX
      const ajaxUrl = window.TIAdminUtils ? window.TIAdminUtils.getFormAjaxUrl(formId) : null;
      
      if (ajaxUrl && window.submitFormAjaxCustom) {
        window.submitFormAjaxCustom(this, ajaxUrl, 'Cadastrado com sucesso!');
      } else if (window.submitFormAjax) {
        window.submitFormAjax(this, 'Cadastrado com sucesso!');
      }
    }
  });
}

// Função para configurar comportamentos de formulários AJAX
function setupAjaxFormBehaviors() {
  // Inicializar comportamentos de admin se o módulo estiver disponível
  if (window.TIAdminUtils) {
    window.TIAdminUtils.initAdminBehaviors();
  } else {
    // Fallback - identificar formulários que devem usar AJAX
    $('form').each(function() {
      const $form = $(this);
      const shouldUse = window.TIAdminUtils ? window.TIAdminUtils.shouldUseAjax(this) : false;
      
      if (shouldUse) {
        $form.addClass('ajax-form');
        $form.attr('data-ajax', 'true');
      }
    });
    
    // Marcar formulários específicos por ID
    $('#form-periferico, #form-computador, #form-sala, #form-ilha, #form-pa, #form-tipo-periferico, #form-monitor').each(function() {
      $(this).addClass('ajax-form').attr('data-ajax', 'true');
    });
  }
}  