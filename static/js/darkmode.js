// darkmode.js - Arquivo principal para gerenciar o dark mode
document.addEventListener('DOMContentLoaded', function() {
    const checkbox = document.getElementById('checkbox');
    const containers = document.querySelectorAll('.container, .box, div, section');
    const mainElement = document.querySelector('main');
    const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');
    const body = document.body;
    const html = document.documentElement;

    // Função para aplicar o tema
    function applyTheme(isDark) {
        if (isDark) {
            html.setAttribute('data-theme', 'dark');
            body.classList.add('dark-mode');
            containers.forEach(container => container.classList.add('darkmode'));
            mainElement?.classList.add('darkmode');
            if (toggleSwitch) toggleSwitch.checked = true;
            if (checkbox) checkbox.checked = true;
            
            // Aplicar classes específicas para módulo TI
            const tiElements = document.querySelectorAll('.app-ti');
            tiElements.forEach(element => {
                element.classList.add('dark-mode');
            });
        } else {
            html.setAttribute('data-theme', 'light');
            body.classList.remove('dark-mode');
            containers.forEach(container => container.classList.remove('darkmode'));
            mainElement?.classList.remove('darkmode');
            if (toggleSwitch) toggleSwitch.checked = false;
            if (checkbox) checkbox.checked = false;
            
            // Remover classes específicas para módulo TI
            const tiElements = document.querySelectorAll('.app-ti');
            tiElements.forEach(element => {
                element.classList.remove('dark-mode');
            });
        }
    }

    // Função para alternar o tema
    function switchTheme(e) {
        const isDark = e.target.checked;
        html.setAttribute('data-theme', isDark ? 'dark' : 'light');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        applyTheme(isDark);
    }

    // Verifica preferência salva
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme) {
        html.setAttribute('data-theme', currentTheme);
        applyTheme(currentTheme === 'dark');
    } else {
        // Verifica preferência do sistema
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
        if (prefersDarkScheme.matches) {
            html.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            applyTheme(true);
        }
    }

    // Listeners para mudança do tema
    if (toggleSwitch) {
        toggleSwitch.addEventListener('change', switchTheme);
    }

    if (checkbox) {
        checkbox.addEventListener('change', function() {
            body.classList.add('transition');
            containers.forEach(container => container.classList.add('transition'));

            switchTheme({ target: { checked: this.checked } });

            // Remove a classe de transição após a animação
            setTimeout(() => {
                body.classList.remove('transition');
                containers.forEach(container => container.classList.remove('transition'));
            }, 300);
        });
    }

    // Listener para mudanças no localStorage de outras abas
    window.addEventListener('storage', function(e) {
        if (e.key === 'theme') {
            applyTheme(e.newValue === 'dark');
        }
    });
});
