document.addEventListener('DOMContentLoaded', function() {
    // Função de busca
    function searchTable() {
        const input = document.getElementById('searchInput');
        const filter = input.value.toLowerCase();
        const activeTable = document.querySelector('.sistema-table.active');
        
        if (!activeTable) return;
        
        const rows = activeTable.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            let found = false;
            
            cells.forEach(cell => {
                if (cell.textContent.toLowerCase().includes(filter)) {
                    found = true;
                }
            });
            
            row.style.display = found ? '' : 'none';
        });
    }
    
    // Função para alternar sistema
    function toggleSistema() {
        const select = document.getElementById('sistemaSelect');
        const selectedSistema = select.value;
        const tables = document.querySelectorAll('.sistema-table');
        
        tables.forEach(table => {
            table.classList.remove('active');
        });
        
        if (selectedSistema) {
            const targetTable = document.getElementById(selectedSistema + 'Table');
            if (targetTable) {
                targetTable.classList.add('active');
            }
        }
        
        // Limpar busca ao trocar de sistema
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
            searchTable();
        }
    }
    
    // Event listeners
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', searchTable);
    }
    
    const sistemaSelect = document.getElementById('sistemaSelect');
    if (sistemaSelect) {
        sistemaSelect.addEventListener('change', toggleSistema);
        
        // Ativar primeira opção por padrão
        if (sistemaSelect.options.length > 1) {
            sistemaSelect.selectedIndex = 1;
            toggleSistema();
        }
    }
});