// Arquivo JS para a página de Controle de Manutenção - TI
// Pode ser usado para adicionar interatividade no futuro, se necessário.
// Convertido para jQuery para padronização com o restante do projeto

$(document).ready(function() {
    // Exemplo: console.log("Controle de Manutenção JS carregado.");
    
    // Adicionar evento de clique em todos os botões de excluir
    $('.btn-excluir').on('click', function() {
        // Obter o formulário pai do botão
        var $form = $(this).closest('.form-excluir');
        
        // Mostrar confirmação
        var confirmacao = confirm('Tem certeza que deseja excluir este periférico permanentemente? Esta ação não pode ser desfeita.');
        
        // Se confirmar, enviar o formulário
        if (confirmacao) {
            $form.submit();
        }
    });
}); 