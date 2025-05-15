/**
 * admin.js - Funcionalidades para a página de administração do módulo TI
 * 
 * Este arquivo contém as funções para ajuste de largura de elementos e
 * carregamento dinâmico de ilhas com base na sala selecionada.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Ajustar largura dos elementos
  const adjustWidths = () => {
    const containerWidth = document.querySelector('.container').offsetWidth;
    const maxElementWidth = Math.min(containerWidth - 30, 1140);
    
    // Ajustar largura dos botões
    document.querySelectorAll('.btn-listagem').forEach(btn => {
      btn.style.maxWidth = '100%';
    });
  };
  
  // Executar no carregamento e no redimensionamento
  adjustWidths();
  window.addEventListener('resize', adjustWidths);
  
  // Carregar ilhas com base na sala selecionada
  const salaSelect = document.getElementById('sala');
  const ilhaSelect = document.getElementById('ilha');
  
  if (salaSelect && ilhaSelect) {
    salaSelect.addEventListener('change', function() {
      // Limpar as opções existentes
      ilhaSelect.innerHTML = '<option value="">-- Selecione uma Ilha --</option>';
      
      if (salaSelect.value) {
        // Fazer uma requisição para obter as ilhas da sala selecionada
        fetch(`/ti/api/ilhas-por-sala/${salaSelect.value}/`)
          .then(response => response.json())
          .then(data => {
            // Adicionar as novas opções
            data.forEach(ilha => {
              const option = document.createElement('option');
              option.value = ilha.id;
              option.textContent = ilha.nome;
              ilhaSelect.appendChild(option);
            });
          })
          .catch(error => console.error('Erro ao carregar ilhas:', error));
      }
    });
  }

  // Validação do formulário de ramal
  const formRamal = document.getElementById('form-ramal');
  const ramalInput = document.getElementById('numero_ramal');
  const funcionarioSelect = document.getElementById('funcionario_ramal');
  const ramalFeedback = document.getElementById('ramal-feedback');
  const submitButton = formRamal ? formRamal.querySelector('button[type="submit"]') : null;

  if (formRamal && ramalInput && funcionarioSelect && submitButton) {
    // Função para ativar/desativar o botão de envio
    const toggleSubmitButton = (isValid) => {
      if (isValid) {
        submitButton.disabled = false;
        submitButton.classList.remove('disabled');
      } else {
        submitButton.disabled = true;
        submitButton.classList.add('disabled');
      }
    };

    // Função para verificar se o ramal já existe no sistema
    const verificarRamalExistente = () => {
      const ramal = ramalInput.value.trim();
      const funcionarioId = funcionarioSelect.value;
      
      // Limpar estados anteriores
      ramalInput.classList.remove('is-valid');
      ramalInput.classList.remove('is-invalid');
      ramalFeedback.style.display = 'none';
      
      // Validação básica - se não tiver exatamente 4 dígitos ou funcionário selecionado, não verificar
      if (!ramal || ramal.length !== 4 || !/^\d{4}$/.test(ramal) || !funcionarioId) {
        toggleSubmitButton(false);
        return;
      }

      // Mostrar indicador de carregamento
      ramalInput.classList.add('is-loading');
      toggleSubmitButton(false); // Desabilitar botão durante a verificação
      
      // Verificar se o ramal já existe no sistema
      fetch('/ti/api/verificar-ramal/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
          ramal: ramal,
          funcionario_id: funcionarioId
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Erro na resposta do servidor: ' + response.status);
        }
        return response.json();
      })
      .then(data => {
        // Remover indicador de carregamento
        ramalInput.classList.remove('is-loading');
        
        console.log('Resposta do servidor:', data); // Para depuração
        
        if (data.existe === true) {
          // Ramal já existe - aplicar estilo inválido
          ramalInput.classList.add('is-invalid');
          ramalFeedback.textContent = `Este ramal já está atribuído ao funcionário ${data.funcionario_nome}`;
          ramalFeedback.style.display = 'block';
          toggleSubmitButton(false); // Manter botão desabilitado
        } else {
          // Ramal não existe, está disponível - aplicar estilo válido
          ramalInput.classList.add('is-valid');
          toggleSubmitButton(true); // Habilitar botão
        }
      })
      .catch(error => {
        console.error('Erro ao verificar ramal:', error);
        ramalInput.classList.remove('is-loading');
        toggleSubmitButton(true); // Em caso de erro, habilitar o botão para permitir tentativa
      });
    };

    // Inicialmente, desabilitar o botão
    toggleSubmitButton(false);

    // Validar ramal quando o usuário digitar
    ramalInput.addEventListener('input', function() {
      // Limpar feedback anterior
      ramalFeedback.textContent = '';
      ramalInput.classList.remove('is-invalid');
      ramalInput.classList.remove('is-valid');
      ramalFeedback.style.display = 'none';
      
      const ramal = ramalInput.value.trim();
      
      // Validação básica de formato
      if (ramal.length > 0 && !/^\d+$/.test(ramal)) {
        ramalFeedback.textContent = 'O ramal deve conter apenas dígitos numéricos.';
        ramalInput.classList.add('is-invalid');
        ramalFeedback.style.display = 'block';
        toggleSubmitButton(false);
        return;
      }
      
      // Se o ramal não tiver 4 dígitos, apenas desabilitar o botão
      if (ramal.length !== 4) {
        toggleSubmitButton(false);
        return;
      }
      
      // Verificar apenas quando tiver 4 dígitos exatos
      if (ramal.length === 4 && /^\d{4}$/.test(ramal) && funcionarioSelect.value) {
        // Verificar após um pequeno delay para evitar muitas requisições durante a digitação
        clearTimeout(ramalInput.timeoutId);
        ramalInput.timeoutId = setTimeout(verificarRamalExistente, 500);
      }
    });
    
    // Verificar também quando o select de funcionário mudar
    funcionarioSelect.addEventListener('change', function() {
      if (ramalInput.value.trim().length === 4) {
        verificarRamalExistente();
      } else {
        toggleSubmitButton(false);
      }
    });
    
    // Verificar também quando o campo de ramal perder o foco
    ramalInput.addEventListener('blur', function() {
      const ramal = ramalInput.value.trim();
      if (ramal.length === 4 && /^\d{4}$/.test(ramal)) {
        verificarRamalExistente();
      }
    });

    // Verificar ramal no submit do formulário (garantia extra)
    formRamal.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const ramal = ramalInput.value.trim();
      const funcionarioId = funcionarioSelect.value;
      
      if (!ramal || !funcionarioId) {
        if (!ramal) {
          ramalFeedback.textContent = 'Por favor, digite um ramal.';
          ramalInput.classList.add('is-invalid');
          ramalFeedback.style.display = 'block';
        }
        toggleSubmitButton(false);
        return;
      }
      
      // Validação básica de formato
      if (!/^\d{4}$/.test(ramal)) {
        ramalFeedback.textContent = 'O ramal deve ter exatamente 4 dígitos numéricos.';
        ramalInput.classList.add('is-invalid');
        ramalFeedback.style.display = 'block';
        toggleSubmitButton(false);
        return;
      }

      // Se o campo já estiver marcado como inválido, não submete
      if (ramalInput.classList.contains('is-invalid')) {
        toggleSubmitButton(false);
        return;
      }

      // Verificação final antes do envio
      fetch('/ti/api/verificar-ramal/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
          ramal: ramal,
          funcionario_id: funcionarioId
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.existe) {
          // Ramal já existe
          ramalFeedback.textContent = `Este ramal já está atribuído ao funcionário ${data.funcionario_nome}`;
          ramalInput.classList.add('is-invalid');
          ramalFeedback.style.display = 'block';
          toggleSubmitButton(false);
        } else {
          // Ramal não existe, pode prosseguir
          toggleSubmitButton(true);
          formRamal.submit();
        }
      })
      .catch(error => {
        console.error('Erro ao verificar ramal:', error);
        // Em caso de erro, mostrar alerta mas permitir o envio
        if (confirm('Ocorreu um erro ao verificar o ramal. Deseja continuar mesmo assim?')) {
          toggleSubmitButton(true);
          formRamal.submit();
        }
      });
    });
  }
}); 