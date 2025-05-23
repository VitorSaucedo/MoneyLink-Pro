/**
 * controle_estoque.js
 * Funcionalidades JavaScript para o Controle de Estoque - TI
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Controle de Estoque - TI carregado com sucesso');
    
    // Configurar o seletor de lojas
    const lojaSeletor = document.getElementById('loja-selector');
    if (lojaSeletor) {
        lojaSeletor.addEventListener('change', function() {
            const lojaId = this.value;
            // Redirecionar para a mesma página com o parâmetro de loja
            window.location.href = `${window.location.pathname}?loja=${lojaId}`;
        });
    }
    
    // Corrigir a contagem total para não somar duplicado os periféricos associados a PAs
    fixTotalInventoryCount();
    
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
    
    // Funções para manipulação do seletor de lojas
    function atualizarTabelaPorLoja(lojaId) {
        // Esta função é chamada quando o usuário seleciona uma loja
        // Nesta implementação, a atualização é feita via redirecionamento da página
        // com parâmetro de loja, por isso o código específico está no handler do evento change acima
        console.log(`Atualizando tabela para loja ID: ${lojaId}`);
    }

    // Função para corrigir a contagem total de periféricos no estoque
    function fixTotalInventoryCount() {
        // Seleciona a linha de total (última linha com classe table-success)
        const totalRow = document.querySelector('#card-estoque table tbody tr.table-success');
        if (!totalRow) return;

        // Para cada célula da linha total (exceto a primeira que é o rótulo e a última que é o total)
        const cells = totalRow.querySelectorAll('td:not(:first-child)');
        const lastCell = cells[cells.length - 1]; // A última célula é o total global
        
        if (!lastCell) return;
        
        // Recalcular o total correto somando apenas os periféricos (não somando computadores)
        let newTotal = 0;
        
        // Pegar apenas as linhas de periféricos (excluindo as linhas de computadores e a linha de total)
        const rows = document.querySelectorAll('#card-estoque table tbody tr:not(.table-success)');
        
        // Para cada linha da tabela
        rows.forEach(row => {
            // Verificar se a linha atual é de computadores (contém o texto "Computadores")
            const firstCell = row.querySelector('td:first-child');
            const isComputerRow = firstCell && firstCell.textContent.includes('Computadores');
            
            // Processar apenas se não for uma linha de computadores
            if (!isComputerRow) {
                // Pegar a célula de estoque (segunda célula)
                const stockCell = row.querySelector('td:nth-child(2)');
                if (stockCell) {
                    // Adicionar o valor do estoque ao total
                    const stockValue = parseInt(stockCell.textContent.trim(), 10) || 0;
                    newTotal += stockValue;
                }
            }
        });
        
        // Atualizar o total global
        lastCell.textContent = newTotal;
    }
    
    // Inicializa as funcionalidades
    configurarDestaqueTabelaEstoque();
    configurarTooltips();
    destacarCelulasVazias();
    observarMudancaDeTema();
}); 