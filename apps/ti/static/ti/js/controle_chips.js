$(document).ready(function() {
    // Busca por ramal, nome do funcionário ou número do chip
    function performSearch() {
        var searchTerm = $('#search-chips').val().toLowerCase();
        $('#chips-table tbody tr').each(function() {
            var $row = $(this);
            var ramal = $row.find('td:nth-child(1)').text().toLowerCase(); // Coluna Ramal
            var numero = $row.find('td:nth-child(2)').text().toLowerCase(); // Coluna Número
            var funcionario = $row.find('td:nth-child(3)').text().toLowerCase(); // Coluna Funcionário
            
            if (ramal.includes(searchTerm) || numero.includes(searchTerm) || funcionario.includes(searchTerm)) {
                $row.show();
            } else {
                $row.hide();
            }
        });
    }
    
    // Executar busca em tempo real
    $('#search-chips').on('input keyup paste', performSearch);
});