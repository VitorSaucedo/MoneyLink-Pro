$(document).ready(function() {
    // Busca por ramal, e-mail ou nome do funcionário
    function performSearch() {
        var searchTerm = $('#search-emails').val().toLowerCase();
        $('#emails-table tbody tr').each(function() {
            var $row = $(this);
            var ramal = $row.find('td:nth-child(1)').text().toLowerCase(); // Coluna Ramal
            var email = $row.find('td:nth-child(2)').text().toLowerCase(); // Coluna E-mail
            var funcionario = $row.find('td:nth-child(3)').text().toLowerCase(); // Coluna Funcionário
            
            if (ramal.includes(searchTerm) || email.includes(searchTerm) || funcionario.includes(searchTerm)) {
                $row.show();
            } else {
                $row.hide();
            }
        });
    }
    
    // Executar busca em tempo real
    $('#search-emails').on('input keyup paste', performSearch);
});