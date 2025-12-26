/**
 * Dark Mode Theme Manager
 */

class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || this.getSystemTheme();
        this.applyTheme(this.currentTheme);
        this.createToggle();
        this.setupSystemListener();
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        localStorage.setItem('theme', theme);
        this.updateToggleIcon();
    }

    toggle() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
    }

    createToggle() {
        // Criar botão de toggle no sidebar
        const sidebar = document.querySelector('.sidebar-footer');
        if (!sidebar) return;

        const toggle = document.createElement('button');
        toggle.id = 'theme-toggle';
        toggle.className = 'btn btn-outline btn-sm';
        toggle.style.marginTop = '0.5rem';
        toggle.setAttribute('data-tooltip', 'Alternar tema escuro/claro');
        toggle.addEventListener('click', () => this.toggle());

        sidebar.appendChild(toggle);
        this.updateToggleIcon();
    }

    updateToggleIcon() {
        const toggle = document.getElementById('theme-toggle');
        if (!toggle) return;

        toggle.innerHTML = this.currentTheme === 'dark' ? '☀️ Modo Claro' : '🌙 Modo Escuro';
    }

    setupSystemListener() {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!this.getStoredTheme()) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
    });
} else {
    window.themeManager = new ThemeManager();
}
