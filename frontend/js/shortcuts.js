/**
 * Keyboard Shortcuts Manager
 */

class ShortcutManager {
    constructor(app) {
        this.app = app;
        this.shortcuts = {
            // Navigation
            'ctrl+n': () => this.app.navigateTo('pedidos'),
            'ctrl+d': () => this.app.navigateTo('dashboard'),
            'ctrl+k': () => this.focusSearch(),

            // Actions
            'ctrl+s': (e) => this.saveForm(e),
            'escape': () => this.closeModal(),
            'f5': (e) => this.refreshCurrentPage(e),

            // Quick access
            'alt+1': () => this.app.navigateTo('dashboard'),
            'alt+2': () => this.app.navigateTo('pedidos'),
            'alt+3': () => this.app.navigateTo('cozinha'),
            'alt+4': () => this.app.navigateTo('produtos'),
            'alt+5': () => this.app.navigateTo('funcionarios'),
        };

        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        this.createShortcutsHelp();
    }

    handleKeyPress(e) {
        // Don't trigger if user is typing in input
        if (e.target.matches('input, textarea, select')) {
            // Except for ESC
            if (e.key === 'Escape') {
                e.target.blur();
                this.closeModal();
            }
            return;
        }

        const key = this.getKeyCombo(e);
        const handler = this.shortcuts[key];

        if (handler) {
            e.preventDefault();
            handler(e);
        }

        // Help menu
        if (e.key === '?' || (e.shiftKey && e.key === '/')) {
            e.preventDefault();
            this.showShortcutsHelp();
        }
    }

    getKeyCombo(e) {
        const keys = [];
        if (e.ctrlKey) keys.push('ctrl');
        if (e.altKey) keys.push('alt');
        if (e.shiftKey && e.key !== 'Shift') keys.push('shift');

        const key = e.key.toLowerCase();
        if (key !== 'control' && key !== 'alt' && key !== 'shift') {
            keys.push(key);
        }

        return keys.join('+');
    }

    focusSearch() {
        const searchInputs = document.querySelectorAll('input[type="text"]:not([disabled])');
        if (searchInputs.length > 0) {
            searchInputs[0].focus();
        }
    }

    saveForm(e) {
        e.preventDefault();
        const activeForm = document.querySelector('form:not(.hidden)');
        if (activeForm) {
            const submitButton = activeForm.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                submitButton.click();
            }
        }
    }

    closeModal() {
        const modal = document.getElementById('modal');
        if (modal && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
        }
    }

    refreshCurrentPage(e) {
        e.preventDefault();
        if (this.app && typeof this.app.loadPageData === 'function') {
            this.app.loadPageData(this.app.currentPage);
        }
    }

    createShortcutsHelp() {
        const helpDiv = document.createElement('div');
        helpDiv.id = 'shortcuts-help';
        helpDiv.className = 'modal hidden';
        helpDiv.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h3>Atalhos de Teclado</h3>
                    <button class="modal-close" onclick="this.closest('.modal').classList.add('hidden')">×</button>
                </div>
                <div class="modal-body">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Atalho</th>
                                <th>Ação</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td><kbd>Ctrl + N</kbd></td><td>Novo Pedido</td></tr>
                            <tr><td><kbd>Ctrl + D</kbd></td><td>Dashboard</td></tr>
                            <tr><td><kbd>Ctrl + K</kbd></td><td>Buscar</td></tr>
                            <tr><td><kbd>Ctrl + S</kbd></td><td>Salvar</td></tr>
                            <tr><td><kbd>F5</kbd></td><td>Atualizar</td></tr>
                            <tr><td><kbd>ESC</kbd></td><td>Fechar Modal</td></tr>
                            <tr><td><kbd>Alt + 1-5</kbd></td><td>Navegar entre páginas</td></tr>
                            <tr><td><kbd>?</kbd></td><td>Mostrar esta ajuda</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        document.body.appendChild(helpDiv);
    }

    showShortcutsHelp() {
        const help = document.getElementById('shortcuts-help');
        if (help) {
            help.classList.remove('hidden');
        }
    }
}

// Will be initialized by app.js with app instance
