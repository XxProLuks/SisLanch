/**
 * Charts Manager for Dashboard Visualizations
 * Enhanced with Hospital Modern Theme
 */

class ChartsManager {
    constructor() {
        this.charts = {
            sales: null,
            products: null,
            payments: null
        };
        this.updateColors();
        this.setupThemeListener();
    }

    /**
     * Update colors from CSS variables
     */
    updateColors() {
        const root = getComputedStyle(document.documentElement);
        this.colors = {
            primary: root.getPropertyValue('--primary').trim() || '#0d9488',
            secondary: root.getPropertyValue('--secondary').trim() || '#0ea5e9',
            accent: root.getPropertyValue('--accent').trim() || '#8b5cf6',
            success: root.getPropertyValue('--success').trim() || '#10b981',
            warning: root.getPropertyValue('--warning').trim() || '#f59e0b',
            danger: root.getPropertyValue('--danger').trim() || '#ef4444',
            text: root.getPropertyValue('--gray-700').trim() || '#334155',
            grid: root.getPropertyValue('--gray-200').trim() || '#e2e8f0'
        };

        // Gradient colors for charts
        this.gradients = {
            primary: ['#0d9488', '#0ea5e9'],
            success: ['#10b981', '#06b6d4'],
            purple: ['#8b5cf6', '#ec4899'],
            warm: ['#f59e0b', '#ef4444']
        };
    }

    /**
     * Listen for theme changes
     */
    setupThemeListener() {
        const observer = new MutationObserver(() => {
            this.updateColors();
            this.updateChartsTheme();
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme']
        });
    }

    /**
     * Update chart theme colors
     */
    updateChartsTheme() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#e2e8f0' : '#334155';
        const gridColor = isDark ? '#374151' : '#e2e8f0';

        Chart.defaults.color = textColor;
        Chart.defaults.borderColor = gridColor;

        // Update existing charts
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.options.scales?.x && (chart.options.scales.x.ticks.color = textColor);
                chart.options.scales?.y && (chart.options.scales.y.ticks.color = textColor);
                chart.options.scales?.x && (chart.options.scales.x.grid.color = gridColor);
                chart.options.scales?.y && (chart.options.scales.y.grid.color = gridColor);
                chart.update();
            }
        });
    }

    /**
     * Create gradient for canvas
     */
    createGradient(ctx, colors) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, colors[0] + 'aa');
        gradient.addColorStop(1, colors[0] + '11');
        return gradient;
    }

    /**
     * Create sales chart with gradient
     */
    createSalesChart(data) {
        const canvas = document.getElementById('sales-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart
        if (this.charts.sales) {
            this.charts.sales.destroy();
        }

        const gradient = this.createGradient(ctx, this.gradients.primary);

        this.charts.sales = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Vendas (R$)',
                    data: data.values || [],
                    borderColor: this.colors.primary,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: this.colors.primary,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#e2e8f0',
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: (context) => {
                                return 'R$ ' + context.parsed.y.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: { family: 'Inter', size: 12 }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: this.colors.grid + '50'
                        },
                        ticks: {
                            font: { family: 'Inter', size: 12 },
                            callback: (value) => 'R$ ' + value.toLocaleString('pt-BR')
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    /**
     * Create products chart with rounded bars
     */
    createProductsChart(data) {
        const canvas = document.getElementById('products-chart');
        if (!canvas) return;

        if (this.charts.products) {
            this.charts.products.destroy();
        }

        this.charts.products = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Quantidade Vendida',
                    data: data.values || [],
                    backgroundColor: [
                        this.colors.primary,
                        this.colors.secondary,
                        this.colors.accent,
                        this.colors.success,
                        this.colors.warning
                    ],
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        padding: 12,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            font: { family: 'Inter', size: 11 },
                            maxRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: this.colors.grid + '50' },
                        ticks: {
                            font: { family: 'Inter', size: 12 },
                            stepSize: 1
                        }
                    }
                },
                animation: {
                    duration: 800,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    /**
     * Create payment methods doughnut chart
     */
    createPaymentChart(data) {
        const canvas = document.getElementById('payment-chart');
        if (!canvas) return;

        if (this.charts.payments) {
            this.charts.payments.destroy();
        }

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

        this.charts.payments = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: [
                        this.colors.primary,
                        this.colors.success,
                        this.colors.warning,
                        this.colors.accent
                    ],
                    borderWidth: 3,
                    borderColor: isDark ? '#111827' : '#ffffff',
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 16,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            font: { family: 'Inter', size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    /**
     * Destroy all charts
     */
    destroyAll() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = { sales: null, products: null, payments: null };
    }

    /**
     * Refresh all charts with new data
     */
    async refreshCharts() {
        try {
            // Fetch data from API
            const [salesRes, productsRes, paymentsRes] = await Promise.all([
                fetch('/relatorios/vendas-diarias?dias=7'),
                fetch('/relatorios/produtos-vendidos?limit=5'),
                fetch('/relatorios/formas-pagamento')
            ]);

            if (salesRes.ok) {
                const salesData = await salesRes.json();
                this.createSalesChart({
                    labels: salesData.map(d => d.data),
                    values: salesData.map(d => d.total)
                });
            }

            if (productsRes.ok) {
                const productsData = await productsRes.json();
                this.createProductsChart({
                    labels: productsData.map(p => p.nome?.substring(0, 15) || ''),
                    values: productsData.map(p => p.quantidade)
                });
            }

            if (paymentsRes.ok) {
                const paymentsData = await paymentsRes.json();
                this.createPaymentChart({
                    labels: Object.keys(paymentsData),
                    values: Object.values(paymentsData)
                });
            }
        } catch (error) {
            console.warn('Could not refresh charts:', error);
        }
    }
}

// Create global instance
const chartsManager = new ChartsManager();

// Initialize charts when Chart.js is available
if (typeof Chart !== 'undefined') {
    // Set global defaults
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
    Chart.defaults.animation.duration = 800;
    Chart.defaults.animation.easing = 'easeOutQuart';
}
