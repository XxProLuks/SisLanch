/**
 * Pagination Component for Tables
 */

class PaginationManager {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.currentPage = 1;
        this.totalPages = 1;
        this.limit = options.limit || 20;
        this.onPageChange = options.onPageChange || (() => { });

        this.render();
    }

    setTotalPages(total) {
        this.totalPages = total;
        this.render();
    }

    setCurrentPage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.render();
        this.onPageChange(page, this.limit);
    }

    nextPage() {
        this.setCurrentPage(this.currentPage + 1);
    }

    prevPage() {
        this.setCurrentPage(this.currentPage - 1);
    }

    goToPage(page) {
        this.setCurrentPage(page);
    }

    render() {
        if (!this.container) return;

        const pagination = [];

        // Previous button
        pagination.push(`
            <button class="pagination-btn ${this.currentPage === 1 ? 'disabled' : ''}" 
                    data-action="prev" 
                    ${this.currentPage === 1 ? 'disabled' : ''}>
                ← Anterior
            </button>
        `);

        // Page numbers
        const pages = this.getPageNumbers();
        pages.forEach(page => {
            if (page === '...') {
                pagination.push(`<span class="pagination-ellipsis">...</span>`);
            } else {
                pagination.push(`
                    <button class="pagination-btn ${page === this.currentPage ? 'active' : ''}" 
                            data-page="${page}">
                        ${page}
                    </button>
                `);
            }
        });

        // Next button
        pagination.push(`
            <button class="pagination-btn ${this.currentPage === this.totalPages ? 'disabled' : ''}" 
                    data-action="next"
                    ${this.currentPage === this.totalPages ? 'disabled' : ''}>
                Próximo →
            </button>
        `);

        this.container.innerHTML = `
            <div class="pagination-controls">
                ${pagination.join('')}
            </div>
            <div class="pagination-info">
                Página ${this.currentPage} de ${this.totalPages}
            </div>
        `;

        this.attachEvents();
    }

    getPageNumbers() {
        const pages = [];
        const { currentPage, totalPages } = this;

        if (totalPages <= 7) {
            // Show all pages if total is 7 or less
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Always show first page
            pages.push(1);

            if (currentPage > 3) {
                pages.push('...');
            }

            // Show pages around current
            const start = Math.max(2, currentPage - 1);
            const end = Math.min(totalPages - 1, currentPage + 1);

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (currentPage < totalPages - 2) {
                pages.push('...');
            }

            // Always show last page
            if (totalPages > 1) {
                pages.push(totalPages);
            }
        }

        return pages;
    }

    attachEvents() {
        if (!this.container) return;

        // Page number clicks
        this.container.querySelectorAll('[data-page]').forEach(btn => {
            btn.addEventListener('click', () => {
                const page = parseInt(btn.dataset.page);
                this.goToPage(page);
            });
        });

        // Previous/Next buttons
        this.container.querySelector('[data-action="prev"]')?.addEventListener('click', () => {
            this.prevPage();
        });

        this.container.querySelector('[data-action="next"]')?.addEventListener('click', () => {
            this.nextPage();
        });
    }

    // Get pagination params for API
    getParams() {
        return {
            page: this.currentPage,
            limit: this.limit
        };
    }

    // Update from API response
    updateFromResponse(response) {
        if (response.total_pages) {
            this.totalPages = response.total_pages;
        }
        if (response.current_page) {
            this.currentPage = response.current_page;
        }
        this.render();
    }
}
