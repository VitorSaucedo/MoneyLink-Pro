/**
 * controle_estoque.js
 * Funcionalidades JavaScript para o Controle de Estoque - TI
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Controle de Estoque - TI carregado com sucesso');
    
    // Função para alternar destaque nas linhas da tabela ao passar o mouse
    function configurarDestaqueTabelaEstoque() {
        const linhasTabela = document.querySelectorAll('#card-estoque table tbody tr');
        
        linhasTabela.forEach(linha => {
            // Ignora a linha de total (última linha com classe table-success)
            if (!linha.classList.contains('table-success')) {
                linha.addEventListener('mouseenter', function() {
                    // Verifica se o tema escuro está ativo
                    if (document.documentElement.getAttribute('data-theme') === 'dark') {
                        this.style.backgroundColor = 'rgba(110, 66, 193, 0.2)';
                    } else {
                        this.style.backgroundColor = 'rgba(112, 246, 17, 0.15)';
                    }
                });
                
                linha.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = '';
                });
            }
        });
    }
    
    // Função para adicionar tooltips nas células da tabela
    function configurarTooltips() {
        const celulasTabela = document.querySelectorAll('#card-estoque table tbody tr:not(.table-success) td:not(:first-child):not(:last-child)');
        
        celulasTabela.forEach(celula => {
            const valor = parseInt(celula.textContent.trim(), 10);
            
            if (valor > 0) {
                // Encontra o tipo do periférico (primeira célula da linha)
                const tipoPerifetico = celula.closest('tr').querySelector('td:first-child').textContent.trim();
                
                // Encontra o local (cabeçalho da coluna)
                const indiceColuna = Array.from(celula.parentNode.children).indexOf(celula);
                const local = document.querySelector('#card-estoque table thead tr th:nth-child(' + (indiceColuna + 1) + ')').textContent.trim();
                
                // celula.title = `${valor} ${tipoPerifetico}(s) em ${local}`;
                // celula.style.cursor = 'help';
            }
        });
    }

    // Função para adicionar classe de destaque para células sem estoque
    function destacarCelulasVazias() {
        const celulasTabela = document.querySelectorAll('#card-estoque table tbody tr:not(.table-success) td:not(:first-child):not(:last-child)');
        
        celulasTabela.forEach(celula => {
            const valor = parseInt(celula.textContent.trim(), 10);
            
            if (valor === 0) {
                celula.classList.add('text-muted');
            } else if (valor <= 1) {
                celula.classList.add('text-warning');
            }
        });
    }
    
    // Função para reagir a mudanças de tema
    function observarMudancaDeTema() {
        // Observa mudanças no tema e atualiza as configurações
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'data-theme') {
                    // Reaplica as configurações quando o tema mudar
                    configurarDestaqueTabelaEstoque();
                    configurarTooltips();
                    destacarCelulasVazias();
                }
            });
        });
        
        // Observa mudanças no atributo data-theme do documento
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme']
        });
    }
    
    // Inicializa as funcionalidades
    configurarDestaqueTabelaEstoque();
    configurarTooltips();
    destacarCelulasVazias();
    observarMudancaDeTema();
}); 