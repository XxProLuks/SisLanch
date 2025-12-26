/**
 * Loading states and spinner utility
 */

class LoadingManager {
    constructor() {
        this.activeLoads = 0;
        this.createSpinner();
    }

    createSpinner() {
        const spinner = document.createElement('div');
        spinner.id = 'global-loading';
        spinner.className = 'loading-overlay hidden';
        spinner.innerHTML = `
            <div class="spinner-container">
                <div class="spinner"></div>
                <p class="loading-text">Carregando...</p>
            </div>
        `;
        document.body.appendChild(spinner);
    }

    show(message = 'Carregando...') {
        this.activeLoads++;
        const overlay = document.getElementById('global-loading');
        const text = overlay.querySelector('.loading-text');
        if (text) text.textContent = message;
        overlay.classList.remove('hidden');
    }

    hide() {
        this.activeLoads = Math.max(0, this.activeLoads - 1);
        if (this.activeLoads === 0) {
            const overlay = document.getElementById('global-loading');
            overlay.classList.add('hidden');
        }
    }

    showButton(button) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="btn-spinner"></span> Processando...';
    }

    hideButton(button) {
        button.disabled = false;
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    }
}

// Create global instance
const loading = new LoadingManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LoadingManager, loading };
}
