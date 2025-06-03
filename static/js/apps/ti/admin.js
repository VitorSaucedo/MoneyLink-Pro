/**
 * admin.js - Funcionalidades para a página de administração do módulo TI
 * 
 * Este arquivo contém as funções para ajuste de largura de elementos,
 * carregamento dinâmico de ilhas com base na sala selecionada,
 * e suporte ao modo escuro.
 * 
 * Convertido para jQuery para padronização com o restante do projeto
 */

$(document).ready(function() {
  // Ajustar largura dos elementos
  var adjustWidths = function() {
    var containerWidth = $('.container').width();
    var maxElementWidth = Math.min(containerWidth - 30, 1140);
    
    // Ajustar largura dos botões
    $('.btn-listagem').each(function() {
      $(this).css('maxWidth', '100%');
    });
  };
  
  // Executar no carregamento e no redimensionamento
  adjustWidths();
  $(window).on('resize', adjustWidths);
  
  // Carregar ilhas com base na sala selecionada
  var $salaSelect = $('#sala');
  var $ilhaSelect = $('#ilha');
  var $quantidadePasInput = $('#quantidade_pas');
  
  // Objeto para armazenar informações das ilhas
  var ilhasInfo = {};
  
  if ($salaSelect.length && $ilhaSelect.length) {
    $salaSelect.on('change', function() {
      // Limpar as opções existentes
      $ilhaSelect.html('<option value="">-- Selecione uma Ilha --</option>');
      
      if ($(this).val()) {
        // Fazer uma requisição para obter as ilhas da sala selecionada
        $.ajax({
          url: '/ti/api/ilhas-por-sala/' + $(this).val() + '/',
          type: 'GET',
          dataType: 'json',
          success: function(data) {
            // Adicionar as novas opções
            if (data.ilhas && Array.isArray(data.ilhas)) {
              $.each(data.ilhas, function(index, ilha) {
                var $option = $('<option></option>');
                $option.val(ilha.id);
                $option.text(ilha.nome);
                $ilhaSelect.append($option);
                
                // Armazenar a quantidade de PAs para cada ilha
                if (ilha.quantidade_pas) {
                  ilhasInfo[ilha.id] = ilha.quantidade_pas;
                }
              });
            }
          },
          error: function(error) {
            console.error('Erro ao carregar ilhas:', error);
          }
        });
      }
    });
    
    // Atualizar o valor máximo do campo quantidade com base na ilha selecionada
    if ($ilhaSelect.length && $quantidadePasInput.length) {
      $ilhaSelect.on('change', function() {
        const ilhaId = $(this).val();
        if (ilhaId && ilhasInfo[ilhaId]) {
          // Obter informações detalhadas sobre a ilha selecionada
          $.ajax({
            url: '/ti/api/ilha-info/' + ilhaId + '/',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
              if (data.success && data.ilha) {
                var capacidadeDisponivel = data.ilha.pas_disponiveis || 1;
                $quantidadePasInput.attr('max', capacidadeDisponivel);
                $quantidadePasInput.val(Math.min($quantidadePasInput.val(), capacidadeDisponivel));
                
                // Atualizar texto informativo
                var $infoText = $('#quantidade-pas-info');
                if ($infoText.length) {
                  $infoText.text('Máximo disponível: ' + capacidadeDisponivel + ' PAs');
                }
              }
            },
            error: function(error) {
              console.error('Erro ao obter informações da ilha:', error);
              $quantidadePasInput.attr('max', 1);
              $quantidadePasInput.val(1);
            }
          });
        } else {
          // Se nenhuma ilha estiver selecionada, limitar para 1
          $quantidadePasInput.attr('max', 1);
          $quantidadePasInput.val(1);
        }
      });
    }
  }

  // Validação do formulário de ramal
  var $formRamal = $('#form-ramal');
  var $ramalInput = $('#numero_ramal');
  var $funcionarioSelect = $('#funcionario_ramal');
  var $ramalFeedback = $('#ramal-feedback');
  var $submitButton = $formRamal.length ? $formRamal.find('button[type="submit"]') : null;

  if ($formRamal.length && $ramalInput.length && $funcionarioSelect.length && $submitButton && $submitButton.length) {
    // Função para ativar/desativar o botão de envio
    var toggleSubmitButton = function(isValid) {
      if (isValid) {
        $submitButton.prop('disabled', false);
        $submitButton.removeClass('btn-secondary').addClass('btn-primary');
      } else {
        $submitButton.prop('disabled', true);
        $submitButton.removeClass('btn-primary').addClass('btn-secondary');
      }
    };

    // Função para verificar se o ramal já existe no sistema
    var verificarRamalExistente = function() {
      var ramal = $ramalInput.val().trim();
      var funcionarioId = $funcionarioSelect.val();
      
      // Limpar estados anteriores
      $ramalInput.removeClass('is-invalid is-valid');
      $ramalFeedback.hide().text('');
      
      // Validação básica - se não tiver exatamente 4 dígitos ou funcionário selecionado, não verificar
      if (!ramal || ramal.length !== 4 || !/^\d{4}$/.test(ramal) || !funcionarioId) {
        toggleSubmitButton(false);
        return;
      }

      // Mostrar indicador de carregamento
      $ramalInput.addClass('is-loading');
      toggleSubmitButton(false); // Desabilitar botão durante a verificação
      
      // Verificar se o ramal já existe no sistema
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
          // Remover indicador de carregamento
          $ramalInput.removeClass('is-loading');
          
          console.log('Resposta do servidor:', data); // Para depuração
          
          if (data.existe === true) {
            // Ramal já existe - aplicar estilo inválido
            $ramalInput.addClass('is-invalid');
            $ramalFeedback.text('Este ramal já está atribuído ao funcionário ' + data.funcionario_nome);
            $ramalFeedback.show();
            toggleSubmitButton(false); // Manter botão desabilitado
          } else {
            // Ramal não existe, está disponível - aplicar estilo válido
            $ramalInput.addClass('is-valid');
            toggleSubmitButton(true); // Habilitar botão
          }
        },
        error: function(xhr, status, error) {
          console.error('Erro ao verificar ramal:', error);
          $ramalInput.removeClass('is-loading');
          toggleSubmitButton(true); // Em caso de erro, habilitar o botão para permitir tentativa
        }
      });
    };

    // Inicialmente, desabilitar o botão
    toggleSubmitButton(false);

    // Validar ramal quando o usuário digitar
    $ramalInput.on('input', function() {
      // Limpar feedback anterior
      $ramalFeedback.text('');
      $ramalInput.removeClass('is-invalid is-valid');
      $ramalFeedback.hide();
      
      const ramal = $(this).val().trim();
      
      // Validação básica de formato
      if (ramal.length > 0 && !/^\d+$/.test(ramal)) {
        $ramalFeedback.text('O ramal deve conter apenas dígitos numéricos.');
        $ramalInput.addClass('is-invalid');
        $ramalFeedback.show();
        toggleSubmitButton(false);
        return;
      }
      
      // Se o ramal não tiver 4 dígitos, apenas desabilitar o botão
      if (ramal.length !== 4) {
        toggleSubmitButton(false);
        return;
      }
      
      // Verificar apenas quando tiver 4 dígitos exatos
      if (ramal.length === 4 && /^\d{4}$/.test(ramal) && $funcionarioSelect.val()) {
        // Verificar após um pequeno delay para evitar muitas requisições durante a digitação
        if (window.ramalTimeoutId) {
          clearTimeout(window.ramalTimeoutId);
        }
        window.ramalTimeoutId = setTimeout(function() {
          verificarRamalExistente();
        }, 500);
      }
    });
    
    // Verificar também quando o select de funcionário mudar
    $funcionarioSelect.on('change', function() {
      if ($ramalInput.val().trim().length === 4) {
        verificarRamalExistente();
      } else {
        toggleSubmitButton(false);
      }
    });
    
    // Verificar também quando o campo de ramal perder o foco
    $ramalInput.on('blur', function() {
      const ramal = $(this).val().trim();
      if (ramal.length === 4 && /^\d{4}$/.test(ramal)) {
        verificarRamalExistente();
      }
    });

    // Verificar ramal no submit do formulário (garantia extra)
    $formRamal.on('submit', function(e) {
      e.preventDefault();
      
      const ramal = $ramalInput.val().trim();
      const funcionarioId = $funcionarioSelect.val();
      
      if (!ramal || !funcionarioId) {
        if (!ramal) {
          $ramalFeedback.text('Por favor, digite um ramal.');
          $ramalInput.addClass('is-invalid');
          $ramalFeedback.show();
        }
        toggleSubmitButton(false);
        return;
      }
      
      // Validação básica de formato
      if (!/^\d{4}$/.test(ramal)) {
        $ramalFeedback.text('O ramal deve ter exatamente 4 dígitos numéricos.');
        $ramalInput.addClass('is-invalid');
        toggleSubmitButton(false);
        return;
      }

      // Se o campo já estiver marcado como inválido, não submete
      if ($ramalInput.hasClass('is-invalid')) {
        toggleSubmitButton(false);
        return;
      }

      // Verificação final antes do envio
      $.ajax({
        url: '/ti/api/verificar-ramal/',
        type: 'POST',
        dataType: 'json',
        headers: {
          'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
        },
        data: JSON.stringify({
          ramal: ramal,
          funcionario_id: funcionarioId
        }),
        contentType: 'application/json',
        success: function(data) {
          if (data.existe) {
            // Ramal já existe
            $ramalFeedback.text('Este ramal já está atribuído ao funcionário ' + data.funcionario_nome);
            $ramalInput.addClass('is-invalid');
            $ramalFeedback.show();
            toggleSubmitButton(false);
          } else {
            // Ramal não existe, pode prosseguir
            toggleSubmitButton(true);
            $formRamal.off('submit').submit();
          }
        },
        error: function(error) {
          console.error('Erro ao verificar ramal:', error);
          // Em caso de erro, mostrar alerta mas permitir o envio
          if (confirm('Ocorreu um erro ao verificar o ramal. Deseja continuar mesmo assim?')) {
            toggleSubmitButton(true);
            $formRamal.off('submit').submit();
          }
        }
      });
      return false;
    });
  }
});