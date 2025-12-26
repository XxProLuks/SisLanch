/**
 * Charts Manager for Dashboard Visualizations
 */

class ChartsManager {
    constructor() {
        this.charts = {
            sales: null,
            products: null,
            payments: null
        };
        this.primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary').trim();
        this.successColor = getComputedStyle(document.documentElement).getPropertyValue('--success').trim();
        this.warningColor = getComputedStyle(document.documentElement).getPropertyValue('--warning').trim();
    }

    /**
     * Create sales chart
     */
    createSalesChart(data) {
        const ctx = document.getElementById('sales-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.sales) {
            this.charts.sales.destroy();
        }

        this.charts.sales = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Vendas (R$)',
                    data: data.values || [],
                    borderColor: this.primaryColor,
                    backgroundColor: this.primaryColor + '20',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: this.primaryColor
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
                        callbacks: {
                            label: (context) => {
                                return 'R$ ' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => 'R$ ' + value
                        }
                    }
                }
            }
        });
    }

    /**
     * Create products chart
     */
    createProductsChart(data) {
        const ctx = document.getElementById('products-chart');
        if (!ctx) return;

        if (this.charts.products) {
            this.charts.products.destroy();
        }

        this.charts.products = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Quantidade Vendida',
                    data: data.values || [],
                    backgroundColor: [
                        this.primaryColor,
                        this.successColor,
                        this.warningColor,
                        '#8b5cf6',
                        '#ec4899'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    /**
     * Create payment methods chart
     */
    createPaymentChart(data) {
        const ctx = document.getElementById('payment-chart');
        if (!ctx) return;

        if (this.charts.payments) {
            this.charts.payments.destroy();
        }

        this.charts.payments = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: [
                        this.primaryColor,
                        this.successColor,
                        this.warningColor,
                        '#8b5cf6'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
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
                }
            }
        });
    }

    /**
     * Update theme for charts (for dark mode)
     */
    updateTheme(isDark) {
        const textColor = isDark ? '#e2e8f0' : '#334155';
        const gridColor = isDark ? '#334155' : '#e2e8f0';

        Chart.defaults.color = textColor;
        Chart.defaults.borderColor = gridColor;

        // Recreate charts with new theme
        // This would need data to be passed again
    }

    /**
     * Destroy all charts
     */
    destroyAll() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
    }
}

// Create global instance
const chartsManager = new ChartsManager();
