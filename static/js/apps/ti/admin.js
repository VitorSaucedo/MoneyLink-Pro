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
        fetch(`/apps/ti/api/ilhas-por-sala/${salaSelect.value}/`)
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
}); 