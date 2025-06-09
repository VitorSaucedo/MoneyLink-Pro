/**
 * controle_estoque.js
 * Funcionalidades JavaScript para o Controle de Estoque - TI
 * Convertido para jQuery para padronização com o restante do projeto
 */

$(document).ready(function() {
    console.log('Controle de Estoque - TI carregado com sucesso');
    
    // Configurar o seletor de lojas com loading state
    $('#loja-selector').on('change', function() {
        const lojaId = $(this).val();
        
        // Mostrar loading state
        mostrarLoadingState();
        
        // Salvar o tamanho atual da tabela antes da transição
        salvarTamanhoTabela();
        
        // Pequeno delay para mostrar o loading antes de redirecionar
        setTimeout(() => {
            // Redirecionar para a mesma página com o parâmetro de loja
            window.location.href = `${window.location.pathname}?loja=${lojaId}`;
        }, 200);
    });
    
    // Função para mostrar loading state durante transição
    function mostrarLoadingState() {
        const $cardEstoque = $('#card-estoque');
        const $tableContainer = $cardEstoque.find('.table-responsive');
        
        // Adicionar overlay de loading
        if (!$tableContainer.find('.loading-overlay').length) {
            const loadingHtml = `
                <div class="loading-overlay position-absolute w-100 h-100 d-flex align-items-center justify-content-center">
                    <div class="text-center">
                        <div class="spinner-border text-primary mb-2" role="status">
                            <span class="visually-hidden">Carregando...</span>
                        </div>
                        <p class="mb-0 text-muted">Atualizando dados da loja...</p>
                    </div>
                </div>
            `;
            $tableContainer.css('position', 'relative').append(loadingHtml);
        }
        
        // Adicionar classe de transição
        $cardEstoque.addClass('store-transition');
    }
    
    // Função para salvar o tamanho atual da tabela
    function salvarTamanhoTabela() {
        const $cardEstoque = $('#card-estoque');
        const currentWidth = $cardEstoque.width();
        const currentHeight = $cardEstoque.height();
        
        // Salvar no localStorage para manter consistência
        localStorage.setItem('ti_estoque_width', currentWidth);
        localStorage.setItem('ti_estoque_height', currentHeight);
    }
    
    // Função para restaurar o tamanho da tabela
    function restaurarTamanhoTabela() {
        const savedWidth = localStorage.getItem('ti_estoque_width');
        const savedHeight = localStorage.getItem('ti_estoque_height');
        
        if (savedWidth && savedHeight) {
            const $cardEstoque = $('#card-estoque');
            
            // Aplicar temporariamente o tamanho salvo para evitar "pulo"
            $cardEstoque.css({
                'min-width': Math.max(900, parseInt(savedWidth)) + 'px',
                'min-height': Math.max(400, parseInt(savedHeight)) + 'px'
            });
            
            // Remover as restrições após um tempo para permitir ajuste natural
            setTimeout(() => {
                $cardEstoque.css({
                    'min-height': '400px' // Manter apenas altura mínima
                });
            }, 1000);
        }
    }
    
    // Função para garantir tamanho mínimo consistente
    function garantirTamanhoConsistente() {
        const $cardEstoque = $('#card-estoque');
        const $tableResponsive = $cardEstoque.find('.table-responsive');
        const $table = $cardEstoque.find('.table');
        
        // Garantir largura mínima do card
        if ($cardEstoque.width() < 900) {
            $cardEstoque.css('min-width', '900px');
        }
        
        // Garantir altura mínima da área da tabela
        if ($tableResponsive.height() < 400) {
            $tableResponsive.css('min-height', '400px');
        }
        
        // Garantir largura mínima da tabela
        if ($table.width() < 800) {
            $table.css('min-width', '800px');
        }
    }
    
    // Corrigir a contagem total para não somar duplicado os periféricos associados a PAs
    // Movido para depois da definição da função
    
    // Função para alternar destaque nas linhas da tabela ao passar o mouse
    var configurarDestaqueTabelaEstoque = function() {
        $('#card-estoque table tbody tr').not('.table-success').each(function() {
            $(this).on('mouseenter', function() {
                // Verifica se o tema escuro está ativo
                if ($('html').attr('data-theme') === 'dark') {
                    $(this).css('backgroundColor', 'rgba(110, 66, 193, 0.2)');
                } else {
                    $(this).css('backgroundColor', 'rgba(112, 246, 17, 0.15)');
                }
            });
            
            $(this).on('mouseleave', function() {
                $(this).css('backgroundColor', '');
            });
        });
    }
    
    // Função para adicionar tooltips nas células da tabela
    var configurarTooltips = function() {
        $('#card-estoque table tbody tr:not(.table-success) td:not(:first-child):not(:last-child)').each(function() {
            const valor = parseInt($(this).text().trim(), 10);
            
            if (valor > 0) {
                // Encontra o tipo do periférico (primeira célula da linha)
                const tipoPerifetico = $(this).closest('tr').find('td:first-child').text().trim();
                
                // Encontra o local (cabeçalho da coluna)
                const indiceColuna = $(this).index();
                const local = $('#card-estoque table thead tr th').eq(indiceColuna).text().trim();
                
                // $(this).attr('title', `${valor} ${tipoPerifetico}(s) em ${local}`);
                // $(this).css('cursor', 'help');
            }
        });
    }

    // Função para adicionar classe de destaque para células sem estoque
    var destacarCelulasVazias = function() {
        $('#card-estoque table tbody tr:not(.table-success) td:not(:first-child):not(:last-child)').each(function() {
            const valor = parseInt($(this).text().trim(), 10);
            
            if (valor === 0) {
                $(this).addClass('text-muted');
            } else if (valor <= 1) {
                $(this).addClass('text-warning');
            }
        });
    }
    
    // Função para reagir a mudanças de tema
    var observarMudancaDeTema = function() {
        // Usa MutationObserver para detectar mudanças no tema
        var observer = new MutationObserver(function(mutations) {
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
        observer.observe($('html')[0], {
            attributes: true,
            attributeFilter: ['data-theme']
        });
    }
    
    // Funções para manipulação do seletor de lojas
    var atualizarTabelaPorLoja = function(lojaId) {
        // Esta função é chamada quando o usuário seleciona uma loja
        // Nesta implementação, a atualização é feita via redirecionamento da página
        // com parâmetro de loja, por isso o código específico está no handler do evento change acima
        console.log(`Atualizando tabela para loja ID: ${lojaId}`);
    }

    // Função para corrigir a contagem total de periféricos no estoque
    var fixTotalInventoryCount = function() {
        // Seleciona a linha de total (última linha com classe table-success)
        const $totalRow = $('#card-estoque table tbody tr.table-success');
        if ($totalRow.length === 0) return;

        // Para cada célula da linha total (exceto a primeira que é o rótulo e a última que é o total)
        const $cells = $totalRow.find('td:not(:first-child)');
        const $lastCell = $cells.last(); // A última célula é o total global
        
        if ($lastCell.length === 0) return;
        
        // Recalcular o total correto somando apenas os periféricos (não somando computadores)
        let newTotal = 0;
        
        // Pegar apenas as linhas de periféricos (excluindo as linhas de computadores e a linha de total)
        $('#card-estoque table tbody tr:not(.table-success)').each(function() {
            // Verificar se a linha atual é de computadores (contém o texto "Computadores")
            var $firstCell = $(this).find('td:first-child');
            var isComputerRow = $firstCell.length > 0 && $firstCell.text().includes('Computadores');
            
            // Processar apenas se não for uma linha de computadores
            if (!isComputerRow) {
                // Pegar a célula de estoque (segunda célula)
                var $stockCell = $(this).find('td:nth-child(2)');
                if ($stockCell.length > 0) {
                    // Adicionar o valor do estoque ao total
                    var stockValue = parseInt($stockCell.text().trim(), 10) || 0;
                    newTotal += stockValue;
                }
            }
        });
        
        // Atualizar o total global
        $lastCell.text(newTotal);
    }
    
    // Inicializa as funcionalidades
    restaurarTamanhoTabela();
    garantirTamanhoConsistente();
    configurarDestaqueTabelaEstoque();
    configurarTooltips();
    destacarCelulasVazias();
    fixTotalInventoryCount();
    observarMudancaDeTema();
    
    // Garantir tamanho após carregamento completo
    $(window).on('load', function() {
        setTimeout(() => {
            garantirTamanhoConsistente();
        }, 500);
    });
    
    // Ajustar tamanho quando a janela for redimensionada
    $(window).on('resize', function() {
        garantirTamanhoConsistente();
    });
}); 