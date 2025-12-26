/**
 * LANCH - Main Application
 * Hospital Cafeteria Management System
 */

class LanchApp {
    constructor() {
        this.currentUser = null;
        this.currentPage = 'dashboard';
        this.products = [];
        this.categories = [];
        this.orderItems = [];
        this.selectedEmployee = null;
        this.orderType = null;
        this.lastMaxOrderId = 0;

        this.init();
    }

    async init() {
        this.bindEvents();

        // Initialize keyboard shortcuts
        if (typeof ShortcutManager !== 'undefined') {
            this.shortcuts = new ShortcutManager(this);
        }

        // Check if user is logged in
        if (api.token) {
            try {
                this.currentUser = await api.getCurrentUser();
                this.showApp();
            } catch (error) {
                this.showLogin();
            }
        } else {
            this.showLogin();
        }
    }

    // ==================== Event Bindings ====================

    bindEvents() {
        // Login form
        document.getElementById('login-form').addEventListener('submit', (e) => this.handleLogin(e));

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => this.handleLogout());

        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });

        // Customer type selection
        document.querySelectorAll('.customer-type-btn').forEach(btn => {
            btn.addEventListener('click', () => this.selectCustomerType(btn.dataset.type));
        });

        // Employee search
        document.getElementById('btn-buscar-func').addEventListener('click', () => this.searchEmployee());
        document.getElementById('funcionario-busca').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchEmployee();
        });
        document.getElementById('btn-confirmar-func').addEventListener('click', () => this.confirmEmployee());

        // Back buttons
        document.querySelectorAll('.btn-back').forEach(btn => {
            btn.addEventListener('click', () => this.orderGoBack());
        });

        // Finalize order
        document.getElementById('btn-finalizar').addEventListener('click', () => this.finalizeOrder());

        // New order button
        document.getElementById('btn-novo-pedido').addEventListener('click', () => this.resetOrder());

        // Kitchen refresh
        document.getElementById('btn-refresh-kitchen').addEventListener('click', () => this.loadKitchenOrders());

        // Admin buttons
        document.getElementById('btn-novo-produto')?.addEventListener('click', () => this.showProductModal());
        document.getElementById('btn-novo-funcionario')?.addEventListener('click', () => this.showEmployeeModal());

        // Report cards
        document.querySelectorAll('.report-card').forEach(card => {
            card.addEventListener('click', () => this.loadReport(card.dataset.report));
        });
        document.getElementById('btn-close-report')?.addEventListener('click', () => {
            document.getElementById('report-content').classList.add('hidden');
        });

        // Modal close
        document.querySelector('.modal-close')?.addEventListener('click', () => this.closeModal());
        document.querySelector('.modal-overlay')?.addEventListener('click', () => this.closeModal());
    }

    // ==================== Authentication ====================

    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('login-error');

        try {
            await api.login(username, password);

            // Try to get current user info, but don't block login if it fails
            try {
                this.currentUser = await api.getCurrentUser();
            } catch (userError) {
                console.error('Failed to get user info:', userError);
                // Set minimal user info from token if available
                this.currentUser = {
                    nome: username,
                    perfil: 'ADMIN',  // Default, will be corrected if /auth/me works later
                    username: username
                };
            }

            this.showApp();
        } catch (error) {
            console.error('Login error:', error);
            errorDiv.textContent = error.message;
            errorDiv.classList.remove('hidden');
        }
    }

    async showChangePasswordModal() {
        const html = `
            <form id="change-pass-form">
                <div class="form-group">
                    <label>Senha Atual</label>
                    <input type="password" name="current_password" required>
                </div>
                <div class="form-group">
                    <label>Nova Senha</label>
                    <input type="password" name="new_password" required>
                </div>
                <div class="form-group">
                    <label>Confirmar Nova Senha</label>
                    <input type="password" name="confirm_password" required>
                </div>
            </form>
        `;

        this.showModal('Alterar Senha', html, [
            { text: 'Cancelar', class: 'btn-outline', action: () => this.closeModal() },
            { text: 'Salvar', class: 'btn-primary', action: () => this.handleChangePassword() }
        ]);
    }

    async handleChangePassword() {
        const form = document.getElementById('change-pass-form');
        const formData = new FormData(form);
        const current = formData.get('current_password');
        const newPass = formData.get('new_password');
        const confirm = formData.get('confirm_password');

        if (newPass !== confirm) {
            this.showToast('A nova senha e a confirmação não conferem', 'error');
            return;
        }

        try {
            await api.changePassword(current, newPass);
            this.closeModal();
            this.showToast('Senha alterada com sucesso!', 'success');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    async handleBackup() {
        if (!confirm('Deseja criar um backup imediato do banco de dados?')) return;

        try {
            const result = await api.backupDatabase();
            this.showToast(`Backup criado: ${result.filename}`, 'success');
        } catch (error) {
            this.showToast('Erro ao criar backup: ' + error.message, 'error');
        }
    }

    handleLogout() {
        api.logout();
        this.currentUser = null;
        this.showLogin();
    }

    showLogin() {
        document.getElementById('login-screen').classList.add('active');
        document.getElementById('app').classList.add('hidden');
        document.getElementById('login-error').classList.add('hidden');
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
    }

    showApp() {
        document.getElementById('login-screen').classList.remove('active');
        document.getElementById('app').classList.remove('hidden');

        // Update user info
        document.getElementById('user-name').textContent = this.currentUser.nome;
        document.getElementById('user-role').textContent = this.currentUser.perfil;

        // Show/hide admin menu items
        const isAdmin = this.currentUser.perfil === 'ADMIN';
        document.querySelectorAll('.admin-only').forEach(el => {
            el.style.display = isAdmin ? 'flex' : 'none';
        });

        // Setup User Menu Actions
        const userInfo = document.querySelector('.user-info');

        // Change Password Button
        if (!document.getElementById('btn-change-pass')) {
            const btnChange = document.createElement('button');
            btnChange.id = 'btn-change-pass';
            btnChange.className = 'btn btn-outline btn-sm';
            btnChange.textContent = 'Alterar Senha';
            btnChange.style.marginTop = '0.5rem';
            btnChange.addEventListener('click', () => this.showChangePasswordModal());
            userInfo.appendChild(btnChange);
        }

        // Add Backup Button for Admin
        if (isAdmin && !document.getElementById('btn-backup')) {
            const btnBackup = document.createElement('button');
            btnBackup.id = 'btn-backup';
            btnBackup.className = 'btn btn-outline btn-sm';
            btnBackup.textContent = 'Backup DB 💾';
            btnBackup.style.marginTop = '0.5rem';
            btnBackup.addEventListener('click', () => this.handleBackup());
            userInfo.appendChild(btnBackup);
        }

        // Navigate to appropriate page
        if (this.currentUser.perfil === 'COZINHA') {
            this.navigateTo('cozinha');
        } else {
            this.navigateTo('dashboard');
        }
    }

    // ==================== Navigation ====================

    navigateTo(page) {
        this.currentPage = page;

        // Update nav active state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        // Show page
        document.querySelectorAll('.page').forEach(p => {
            p.classList.toggle('active', p.id === `page-${page}`);
        });

        // Load page data
        this.loadPageData(page);
    }

    async loadPageData(page) {
        switch (page) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'pedidos':
                await this.loadProducts();
                this.resetOrder();
                break;
            case 'cozinha':
                await this.loadKitchenOrders();
                break;
            case 'produtos':
                await this.loadProductsTable();
                break;
            case 'funcionarios':
                await this.loadEmployeesTable();
                break;
            case 'competencias':
                await this.loadCompetencies();
                break;
        }
    }

    // ==================== Dashboard ====================

    async loadDashboard() {
        try {
            const data = await api.getDashboard();

            document.getElementById('current-date').textContent = this.formatDate(data.data);
            document.getElementById('stat-pedidos').textContent = data.pedidos.total;
            document.getElementById('stat-pendentes').textContent = data.pedidos.pendentes;
            document.getElementById('stat-faturamento').textContent = this.formatCurrency(data.faturamento.total);
            document.getElementById('stat-funcionarios').textContent = this.formatCurrency(data.faturamento.funcionarios);

            // Load recent orders
            const orders = await api.getOrders({ limit: 5 });
            const tbody = document.querySelector('#ultimos-pedidos tbody');
            tbody.innerHTML = orders.map(order => `
                <tr>
                    <td><strong>${order.numero}</strong></td>
                    <td>${order.tipo_cliente === 'FUNCIONARIO' ? '🏥 Funcionário' : '👤 Paciente'}</td>
                    <td>${this.formatCurrency(order.valor_total)}</td>
                    <td><span class="badge badge-${this.getStatusClass(order.status)}">${order.status}</span></td>
                </tr>
            `).join('');

        } catch (error) {
            this.showToast('Erro ao carregar dashboard', 'error');
        }

        // Load charts
        try {
            const chartData = await api.request('GET', '/relatorios/dashboard/charts');

            if (typeof chartsManager !== 'undefined') {
                chartsManager.createSalesChart(chartData.sales);
                chartsManager.createProductsChart(chartData.products);
                chartsManager.createPaymentChart(chartData.payments);
            }
        } catch (error) {
            console.error('Erro ao carregar gráficos:', error);
        }
    }

    // ==================== Order Flow ====================

    async loadProducts() {
        try {
            this.categories = await api.getCategories(true);
            this.products = await api.getProducts(true);

            // Render categories filter
            const filterContainer = document.getElementById('categories-filter');
            filterContainer.innerHTML = `
                <button class="category-btn active" data-category="all">Todos</button>
                ${this.categories.map(c => `
                    <button class="category-btn" data-category="${c.id}">${c.nome}</button>
                `).join('')}
            `;

            // Bind category filter events
            filterContainer.querySelectorAll('.category-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    filterContainer.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    this.filterProducts(btn.dataset.category);
                });
            });

            this.renderProducts(this.products);

        } catch (error) {
            this.showToast('Erro ao carregar produtos', 'error');
        }
    }

    filterProducts(categoryId) {
        if (categoryId === 'all') {
            this.renderProducts(this.products);
        } else {
            const filtered = this.products.filter(p => p.categoria_id === parseInt(categoryId));
            this.renderProducts(filtered);
        }
    }

    renderProducts(products) {
        const container = document.getElementById('products-list');
        container.innerHTML = products.map(p => `
            <div class="product-card ${p.controlar_estoque && p.estoque_atual <= 0 ? 'disabled' : ''}" data-id="${p.id}">
                <div class="product-name">${p.nome}</div>
                <div class="product-info">
                    <span class="product-price">${this.formatCurrency(p.preco)}</span>
                    ${p.controlar_estoque ? `<span class="product-stock ${p.estoque_atual < 5 ? 'low' : ''}">Estoque: ${p.estoque_atual}</span>` : ''}
                </div>
            </div>
        `).join('');

        // Bind click events
        container.querySelectorAll('.product-card').forEach(card => {
            card.addEventListener('click', () => this.addToOrder(parseInt(card.dataset.id)));
        });
    }

    selectCustomerType(type) {
        this.orderType = type;

        if (type === 'FUNCIONARIO') {
            document.getElementById('step-cliente').classList.add('hidden');
            document.getElementById('step-funcionario').classList.remove('hidden');
            document.getElementById('payment-section').classList.add('hidden');
        } else {
            document.getElementById('step-cliente').classList.add('hidden');
            document.getElementById('step-produtos').classList.remove('hidden');
            document.getElementById('payment-section').classList.remove('hidden');
            document.getElementById('order-customer').innerHTML = '<strong>Cliente:</strong> Paciente / Visitante';
        }
    }

    async searchEmployee() {
        const query = document.getElementById('funcionario-busca').value.trim();
        const errorDiv = document.getElementById('funcionario-error');
        const infoDiv = document.getElementById('funcionario-info');

        if (!query) {
            errorDiv.textContent = 'Digite a matrícula ou CPF';
            errorDiv.classList.remove('hidden');
            return;
        }

        try {
            const employee = await api.searchEmployee(query);
            this.selectedEmployee = employee;

            document.getElementById('func-nome').textContent = employee.nome;
            document.getElementById('func-matricula').textContent = `Matrícula: ${employee.matricula}`;
            document.getElementById('func-setor').textContent = employee.setor;
            document.getElementById('func-saldo').textContent = this.formatCurrency(employee.saldo_disponivel);

            if (employee.saldo_disponivel <= 0) {
                document.getElementById('func-saldo').style.color = '#ef4444';
            } else {
                document.getElementById('func-saldo').style.color = '#10b981';
            }

            infoDiv.classList.remove('hidden');
            errorDiv.classList.add('hidden');

        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.classList.remove('hidden');
            infoDiv.classList.add('hidden');
        }
    }

    confirmEmployee() {
        if (!this.selectedEmployee) return;

        document.getElementById('step-funcionario').classList.add('hidden');
        document.getElementById('step-produtos').classList.remove('hidden');
        document.getElementById('order-customer').innerHTML = `
            <strong>Funcionário:</strong> ${this.selectedEmployee.nome}<br>
            <small>Matrícula: ${this.selectedEmployee.matricula} | Saldo: ${this.formatCurrency(this.selectedEmployee.saldo_disponivel)}</small>
        `;
    }

    orderGoBack() {
        const currentStep = document.querySelector('.order-step:not(.hidden)');

        if (currentStep.id === 'step-funcionario') {
            currentStep.classList.add('hidden');
            document.getElementById('step-cliente').classList.remove('hidden');
            this.selectedEmployee = null;
            document.getElementById('funcionario-busca').value = '';
            document.getElementById('funcionario-info').classList.add('hidden');
            document.getElementById('funcionario-error').classList.add('hidden');
        } else if (currentStep.id === 'step-produtos') {
            currentStep.classList.add('hidden');
            if (this.orderType === 'FUNCIONARIO') {
                document.getElementById('step-funcionario').classList.remove('hidden');
            } else {
                document.getElementById('step-cliente').classList.remove('hidden');
            }
            this.orderItems = [];
            this.updateOrderSummary();
        }
    }

    addToOrder(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        if (product.controlar_estoque && product.estoque_atual <= 0) {
            this.showToast('Produto sem estoque', 'warning');
            return;
        }

        const existingItem = this.orderItems.find(item => item.produto_id === productId);

        if (existingItem) {
            if (product.controlar_estoque && existingItem.quantidade >= product.estoque_atual) {
                this.showToast(`Estoque insuficiente. Máximo: ${product.estoque_atual}`, 'warning');
                return;
            }
            existingItem.quantidade++;
            existingItem.subtotal = existingItem.quantidade * product.preco;
        } else {
            this.orderItems.push({
                produto_id: productId,
                nome: product.nome,
                preco: product.preco,
                quantidade: 1,
                subtotal: product.preco
            });
        }

        this.updateOrderSummary();
    }

    removeFromOrder(productId) {
        this.orderItems = this.orderItems.filter(item => item.produto_id !== productId);
        this.updateOrderSummary();
    }

    updateOrderSummary() {
        const container = document.getElementById('order-items');
        const total = this.orderItems.reduce((sum, item) => sum + item.subtotal, 0);

        if (this.orderItems.length === 0) {
            container.innerHTML = '<p class="empty-cart">Nenhum item adicionado</p>';
        } else {
            container.innerHTML = this.orderItems.map(item => `
                <div class="order-item">
                    <div class="item-info">
                        <span class="item-qty">${item.quantidade}</span>
                        <span>${item.nome}</span>
                    </div>
                    <div>
                        <span>${this.formatCurrency(item.subtotal)}</span>
                        <button class="item-remove" data-id="${item.produto_id}">&times;</button>
                    </div>
                </div>
            `).join('');

            container.querySelectorAll('.item-remove').forEach(btn => {
                btn.addEventListener('click', () => this.removeFromOrder(parseInt(btn.dataset.id)));
            });
        }

        document.getElementById('order-total').textContent = this.formatCurrency(total);

        // Validate order can be finalized
        const hasItems = this.orderItems.length > 0;
        const hasPayment = this.orderType === 'FUNCIONARIO' || document.querySelector('input[name="forma_pagamento"]:checked');

        // Check employee limit
        if (this.orderType === 'FUNCIONARIO' && this.selectedEmployee) {
            if (total > this.selectedEmployee.saldo_disponivel) {
                document.getElementById('btn-finalizar').disabled = true;
                this.showToast('Valor excede o saldo disponível', 'warning');
                return;
            }
        }

        document.getElementById('btn-finalizar').disabled = !hasItems;
    }

    async finalizeOrder() {
        if (this.orderItems.length === 0) return;

        const formaPagamento = this.orderType === 'FUNCIONARIO'
            ? 'CONVENIO'
            : document.querySelector('input[name="forma_pagamento"]:checked')?.value;

        if (!formaPagamento && this.orderType === 'PACIENTE') {
            this.showToast('Selecione uma forma de pagamento', 'warning');
            return;
        }

        const orderData = {
            tipo_cliente: this.orderType,
            funcionario_id: this.selectedEmployee?.id || null,
            forma_pagamento: formaPagamento,
            observacao: document.getElementById('order-obs').value || null,
            itens: this.orderItems.map(item => ({
                produto_id: item.produto_id,
                quantidade: item.quantidade
            }))
        };

        try {
            const result = await api.createOrder(orderData);

            document.getElementById('step-produtos').classList.add('hidden');
            document.getElementById('step-confirmacao').classList.remove('hidden');
            document.getElementById('confirm-numero').textContent = result.numero;

            // Setup print button
            const btnPrint = document.getElementById('btn-print-receipt');
            btnPrint.replaceWith(btnPrint.cloneNode(true)); // Remove old listeners
            document.getElementById('btn-print-receipt').addEventListener('click', () => this.printReceipt(result));

            const message = this.orderType === 'FUNCIONARIO'
                ? `Valor de ${this.formatCurrency(result.valor_total)} será descontado em folha.`
                : `Pagamento de ${this.formatCurrency(result.valor_total)} via ${formaPagamento}.`;
            document.getElementById('confirm-message').textContent = message;

            this.showToast('Pedido realizado com sucesso!', 'success');

        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    updateOrderSummary() {
        const container = document.getElementById('order-items');
        const total = this.orderItems.reduce((sum, item) => sum + item.subtotal, 0);
        // ... (existing updateOrderSummary code is mostly fine, but I need to make sure I don't break indentation context)
        // Actually, I am appending a new method. I'll add it before resetOrder or after.
        // Let's add it at the end of Order Flow section, before resetOrder is safer if I can find resetOrder.
        // Step 285 showed resetOrder starts at line 474.

        // I will use `resetOrder` as anchor and insert BEFORE it.
    }

    printReceipt(order) {
        const container = document.getElementById('receipt-area');
        const date = new Date().toLocaleString('pt-BR');

        container.innerHTML = `
            <div class="receipt-header">
                <div class="receipt-title">HOSPITAL LANCH</div>
                <div class="receipt-info">CNPJ: 00.000.000/0001-00</div>
                <div class="receipt-info">${date}</div>
                <div class="receipt-info">Pedido: <strong>#${order.numero}</strong></div>
            </div>
            <div class="receipt-body">
                ${order.itens.map(item => `
                    <div class="receipt-item">
                        <span>${item.quantidade}x ${item.produto.nome || item.produto?.nome || 'Item'}</span>
                        <span>${this.formatCurrency(item.subtotal || item.product?.preco * item.quantidade)}</span>
                    </div>
                `).join('')}
            </div>
            <div class="receipt-total">
                <span>TOTAL</span>
                <span>${this.formatCurrency(order.valor_total)}</span>
            </div>
            <div class="receipt-footer">
                <p>Cliente: ${order.tipo_cliente === 'FUNCIONARIO' ? 'Funcionário' : 'Paciente/Visitante'}</p>
                <p>Pagamento: ${order.forma_pagamento}</p>
                <br>
                <p>Obrigado pela preferência!</p>
            </div>
        `;

        window.print();
    }

    resetOrder() {
        this.orderType = null;
        this.orderItems = [];
        this.selectedEmployee = null;

        document.querySelectorAll('.order-step').forEach(step => step.classList.add('hidden'));
        document.getElementById('step-cliente').classList.remove('hidden');
        document.getElementById('funcionario-busca').value = '';
        document.getElementById('funcionario-info').classList.add('hidden');
        document.getElementById('funcionario-error').classList.add('hidden');
        document.getElementById('order-obs').value = '';
        document.querySelectorAll('input[name="forma_pagamento"]').forEach(r => r.checked = false);

        this.updateOrderSummary();
    }

    // ==================== Kitchen ====================

    async loadKitchenOrders() {
        try {
            const orders = await api.getKitchenOrders();
            const container = document.getElementById('kitchen-orders');

            // Check for new orders (Audio Alert)
            if (this.lastMaxOrderId && orders.length > 0) {
                const currentMaxId = Math.max(...orders.map(o => o.id));
                if (currentMaxId > this.lastMaxOrderId) {
                    this.playBeep();
                    this.showToast('Novo pedido na cozinha!', 'info');
                }
                this.lastMaxOrderId = currentMaxId;
            } else if (orders.length > 0) {
                this.lastMaxOrderId = Math.max(...orders.map(o => o.id));
            }

            if (orders.length === 0) {
                container.innerHTML = '<p class="text-center" style="padding: 2rem; color: var(--gray-500);">Nenhum pedido pendente</p>';
                return;
            }

            container.innerHTML = orders.map(order => {
                // Determine alert class based on wait time
                let alertClass = '';
                if (order.status !== 'PRONTO') {
                    if (order.tempo_espera >= 20) alertClass = 'wait-critical';
                    else if (order.tempo_espera >= 10) alertClass = 'wait-warning';
                }

                return `
                <div class="kitchen-card ${alertClass}">
                    <div class="kitchen-card-header ${order.status.toLowerCase()}">
                        <span class="order-number-kitchen">#${order.numero}</span>
                        <span class="badge badge-${this.getStatusClass(order.status)}">${order.status}</span>
                    </div>
                    <div class="kitchen-card-body">
                        <div class="kitchen-client">
                            ${order.tipo_cliente === 'FUNCIONARIO' ? '🏥' : '👤'} ${order.cliente}
                        </div>
                        <div class="kitchen-items">${order.itens}</div>
                        ${order.observacao ? `<div class="kitchen-obs"><em>${order.observacao}</em></div>` : ''}
                        <div class="kitchen-time">
                            ⏱️ ${order.tempo_espera} min
                        </div>
                        <div class="kitchen-actions">
                            ${this.getKitchenActions(order)}
                        </div>
                    </div>
                </div>
            `}).join('');

            // Bind action buttons
            container.querySelectorAll('[data-action]').forEach(btn => {
                btn.addEventListener('click', () => this.updateOrderStatus(
                    parseInt(btn.dataset.order),
                    btn.dataset.action
                ));
            });

        } catch (error) {
            this.showToast('Erro ao carregar pedidos', 'error');
        }
    }

    playBeep() {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.type = 'sine';
        osc.frequency.setValueAtTime(500, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(1000, ctx.currentTime + 0.1);

        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);

        osc.start();
        osc.stop(ctx.currentTime + 0.5);
    }

    getKitchenActions(order) {
        switch (order.status) {
            case 'PENDENTE':
                return `<button class="btn btn-primary" data-order="${order.id}" data-action="PREPARANDO">Iniciar Preparo</button>`;
            case 'PREPARANDO':
                return `<button class="btn btn-success" data-order="${order.id}" data-action="PRONTO">Marcar Pronto</button>`;
            case 'PRONTO':
                return `<button class="btn btn-outline" data-order="${order.id}" data-action="ENTREGUE">Entregar</button>`;
            default:
                return '';
        }
    }

    async updateOrderStatus(orderId, status) {
        try {
            await api.updateOrderStatus(orderId, status);
            this.showToast('Status atualizado!', 'success');
            this.loadKitchenOrders();
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    // ==================== Products Management ====================

    async loadProductsTable() {
        try {
            const products = await api.getProducts();
            const tbody = document.querySelector('#produtos-table tbody');

            tbody.innerHTML = products.map(p => `
                <tr>
                    <td>${p.nome}</td>
                    <td>${p.categoria_nome}</td>
                    <td>${this.formatCurrency(p.preco)}</td>
                    <td>${p.controlar_estoque ? p.estoque_atual : '-'}</td>
                    <td><span class="badge badge-${p.ativo ? 'success' : 'gray'}">${p.ativo ? 'Ativo' : 'Inativo'}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="app.editProduct(${p.id})">Editar</button>
                        ${p.ativo ? `<button class="btn btn-sm btn-danger" onclick="app.deleteProduct(${p.id})">Desativar</button>` : ''}
                    </td>
                </tr>
            `).join('');

        } catch (error) {
            this.showToast('Erro ao carregar produtos', 'error');
        }
    }

    async showProductModal(product = null) {
        const categories = await api.getCategories();

        const html = `
            <form id="product-form">
                <div class="form-group">
                    <label>Nome</label>
                    <input type="text" name="nome" value="${product?.nome || ''}" required>
                </div>
                <div class="form-group">
                    <label>Categoria</label>
                    <select name="categoria_id" required>
                        ${categories.map(c => `
                            <option value="${c.id}" ${product?.categoria_id === c.id ? 'selected' : ''}>${c.nome}</option>
                        `).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Preço (R$)</label>
                    <input type="number" name="preco" step="0.01" min="0" value="${product?.preco || ''}" required>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="controlar_estoque" ${product?.controlar_estoque ? 'checked' : ''}>
                            Controlar Estoque
                        </label>
                    </div>
                    <div class="form-group">
                        <label>Estoque Atual</label>
                        <input type="number" name="estoque_atual" min="0" value="${product?.estoque_atual || 0}">
                    </div>
                </div>
            </form>
        `;

        this.showModal(product ? 'Editar Produto' : 'Novo Produto', html, [
            { text: 'Cancelar', class: 'btn-outline', action: () => this.closeModal() },
            { text: 'Salvar', class: 'btn-primary', action: () => this.saveProduct(product?.id) }
        ]);
    }

    async saveProduct(id = null) {
        const form = document.getElementById('product-form');
        const formData = new FormData(form);
        const data = {
            nome: formData.get('nome'),
            categoria_id: parseInt(formData.get('categoria_id')),
            preco: parseFloat(formData.get('preco')),
            controlar_estoque: formData.get('controlar_estoque') === 'on',
            estoque_atual: parseInt(formData.get('estoque_atual') || 0)
        };

        try {
            if (id) {
                await api.updateProduct(id, data);
            } else {
                await api.createProduct(data);
            }
            this.closeModal();
            this.showToast('Produto salvo com sucesso!', 'success');
            this.loadProductsTable();
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    async editProduct(id) {
        const product = await api.getProduct(id);
        this.showProductModal(product);
    }

    async deleteProduct(id) {
        if (confirm('Deseja desativar este produto?')) {
            try {
                await api.deleteProduct(id);
                this.showToast('Produto desativado', 'success');
                this.loadProductsTable();
            } catch (error) {
                this.showToast(error.message, 'error');
            }
        }
    }

    // ==================== Employees Management ====================

    async loadEmployeesTable() {
        try {
            const employees = await api.getEmployees();
            const tbody = document.querySelector('#funcionarios-table tbody');

            tbody.innerHTML = employees.map(f => `
                <tr>
                    <td>${f.matricula}</td>
                    <td>${f.nome}</td>
                    <td>${f.setor}</td>
                    <td>${this.formatCurrency(f.limite_mensal)}</td>
                    <td><span class="badge badge-${f.ativo ? 'success' : 'gray'}">${f.ativo ? 'Ativo' : 'Inativo'}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="app.editEmployee(${f.id})">Editar</button>
                        ${f.ativo ? `<button class="btn btn-sm btn-danger" onclick="app.deleteEmployee(${f.id})">Desativar</button>` : ''}
                    </td>
                </tr>
            `).join('');

        } catch (error) {
            this.showToast('Erro ao carregar funcionários', 'error');
        }
    }

    async showEmployeeModal(employee = null) {
        const html = `
            <form id="employee-form">
                <div class="form-group">
                    <label>Matrícula</label>
                    <input type="text" name="matricula" value="${employee?.matricula || ''}" ${employee ? 'readonly' : 'required'}>
                </div>
                <div class="form-group">
                    <label>CPF</label>
                    <input type="text" name="cpf" value="${employee?.cpf || ''}" ${employee ? 'readonly' : 'required'}>
                </div>
                <div class="form-group">
                    <label>Nome</label>
                    <input type="text" name="nome" value="${employee?.nome || ''}" required>
                </div>
                <div class="form-group">
                    <label>Setor</label>
                    <input type="text" name="setor" value="${employee?.setor || ''}" required>
                </div>
                <div class="form-group">
                    <label>Centro de Custo</label>
                    <input type="text" name="centro_custo" value="${employee?.centro_custo || ''}" required>
                </div>
                <div class="form-group">
                    <label>Limite Mensal (R$)</label>
                    <input type="number" name="limite_mensal" step="0.01" min="0" value="${employee?.limite_mensal || 500}" required>
                </div>
            </form>
        `;

        this.showModal(employee ? 'Editar Funcionário' : 'Novo Funcionário', html, [
            { text: 'Cancelar', class: 'btn-outline', action: () => this.closeModal() },
            { text: 'Salvar', class: 'btn-primary', action: () => this.saveEmployee(employee?.id) }
        ]);
    }

    async saveEmployee(id = null) {
        const form = document.getElementById('employee-form');
        const formData = new FormData(form);
        const data = {
            matricula: formData.get('matricula'),
            cpf: formData.get('cpf'),
            nome: formData.get('nome'),
            setor: formData.get('setor'),
            centro_custo: formData.get('centro_custo'),
            limite_mensal: parseFloat(formData.get('limite_mensal'))
        };

        try {
            if (id) {
                await api.updateEmployee(id, {
                    nome: data.nome,
                    setor: data.setor,
                    centro_custo: data.centro_custo,
                    limite_mensal: data.limite_mensal
                });
            } else {
                await api.createEmployee(data);
            }
            this.closeModal();
            this.showToast('Funcionário salvo com sucesso!', 'success');
            this.loadEmployeesTable();
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    async editEmployee(id) {
        const employee = await api.getEmployee(id);
        this.showEmployeeModal(employee);
    }

    async deleteEmployee(id) {
        if (confirm('Deseja desativar este funcionário?')) {
            try {
                await api.deleteEmployee(id);
                this.showToast('Funcionário desativado', 'success');
                this.loadEmployeesTable();
            } catch (error) {
                this.showToast(error.message, 'error');
            }
        }
    }

    // ==================== Competencies ====================

    async loadCompetencies() {
        try {
            const current = await api.getCurrentCompetency();
            const all = await api.getCompetencies();

            // Current competency info
            const currentDiv = document.querySelector('#competencia-atual .competencia-info');
            currentDiv.innerHTML = `
                <div class="competencia-stat">
                    <div class="competencia-stat-value">${current.referencia}</div>
                    <div class="competencia-stat-label">Competência Atual</div>
                </div>
                <div class="competencia-stat">
                    <div class="competencia-stat-value">${current.total_funcionarios}</div>
                    <div class="competencia-stat-label">Funcionários</div>
                </div>
                <div class="competencia-stat">
                    <div class="competencia-stat-value">${this.formatCurrency(current.valor_total)}</div>
                    <div class="competencia-stat-label">Valor Total</div>
                </div>
                <div>
                    <button class="btn btn-danger" onclick="app.closeCompetency(${current.id})">Fechar Competência</button>
                </div>
            `;

            // Competencies table
            const tbody = document.querySelector('#competencias-table tbody');
            tbody.innerHTML = all.map(c => `
                <tr>
                    <td><strong>${c.referencia}</strong></td>
                    <td>${c.total_funcionarios}</td>
                    <td>${this.formatCurrency(c.valor_total)}</td>
                    <td><span class="badge badge-${c.status === 'ABERTA' ? 'success' : 'gray'}">${c.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="app.viewCompetencyDetails(${c.id})">Ver Detalhes</button>
                        ${c.status === 'FECHADA' ? `
                            <a href="${api.getExcelExportUrl(c.id)}" class="btn btn-sm btn-primary" target="_blank">Excel</a>
                            <a href="${api.getCsvExportUrl(c.id)}" class="btn btn-sm btn-outline" target="_blank">CSV</a>
                        ` : ''}
                    </td>
                </tr>
            `).join('');

        } catch (error) {
            this.showToast('Erro ao carregar competências', 'error');
        }
    }

    async closeCompetency(id) {
        if (!confirm('Tem certeza que deseja fechar esta competência? Esta ação não pode ser desfeita.')) {
            return;
        }

        try {
            await api.closeCompetency(id);
            this.showToast('Competência fechada com sucesso!', 'success');
            this.loadCompetencies();
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    async viewCompetencyDetails(id) {
        try {
            const data = await api.getCompetencyConsumption(id);

            const html = `
                <div style="max-height: 400px; overflow-y: auto;">
                    <p><strong>Total:</strong> ${this.formatCurrency(data.total_geral)}</p>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Matrícula</th>
                                <th>Nome</th>
                                <th>Setor</th>
                                <th>Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.consumos.map(c => `
                                <tr>
                                    <td>${c.matricula}</td>
                                    <td>${c.nome}</td>
                                    <td>${c.setor}</td>
                                    <td>${this.formatCurrency(c.valor_total)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;

            this.showModal(`Consumos - ${data.competencia.referencia}`, html, [
                { text: 'Fechar', class: 'btn-outline', action: () => this.closeModal() }
            ]);

        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    // ==================== Reports ====================

    async loadReport(reportType) {
        const reportContent = document.getElementById('report-content');
        const reportTitle = document.getElementById('report-title');
        const reportData = document.getElementById('report-data');

        try {
            let html = '';

            switch (reportType) {
                case 'vendas-diarias':
                    reportTitle.textContent = 'Vendas Diárias';
                    const sales = await api.getDailySales();
                    html = `
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Data</th>
                                    <th>Pedidos</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${sales.map(s => `
                                    <tr>
                                        <td>${this.formatDate(s.data)}</td>
                                        <td>${s.total_pedidos}</td>
                                        <td>${this.formatCurrency(s.valor_total)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    break;

                case 'formas-pagamento':
                    reportTitle.textContent = 'Formas de Pagamento';
                    const payments = await api.getPaymentMethods();
                    html = `
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                            ${Object.entries(payments.formas).map(([forma, data]) => `
                                <div class="stat-card">
                                    <div class="stat-info">
                                        <span class="stat-value">${this.formatCurrency(data.valor)}</span>
                                        <span class="stat-label">${forma} (${data.quantidade})</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <p style="margin-top: 1rem;"><strong>Total:</strong> ${this.formatCurrency(payments.total)}</p>
                    `;
                    break;

                case 'produtos-vendidos':
                    reportTitle.textContent = 'Produtos Mais Vendidos';
                    const products = await api.getTopProducts();
                    html = `
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Produto</th>
                                    <th>Categoria</th>
                                    <th>Quantidade</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${products.produtos.map(p => `
                                    <tr>
                                        <td>${p.nome}</td>
                                        <td>${p.categoria}</td>
                                        <td>${p.quantidade_vendida}</td>
                                        <td>${this.formatCurrency(p.valor_total)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    break;

                case 'consumo-funcionarios':
                    reportTitle.textContent = 'Consumo de Funcionários';
                    const consumption = await api.getEmployeeConsumptionReport();
                    html = `
                        <p><strong>Competência:</strong> ${consumption.competencia.referencia}</p>
                        <p><strong>Total:</strong> ${this.formatCurrency(consumption.total_geral)}</p>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Matrícula</th>
                                    <th>Nome</th>
                                    <th>Setor</th>
                                    <th>Consumo</th>
                                    <th>Saldo</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${consumption.funcionarios.map(f => `
                                    <tr>
                                        <td>${f.matricula}</td>
                                        <td>${f.nome}</td>
                                        <td>${f.setor}</td>
                                        <td>${this.formatCurrency(f.valor_consumido)}</td>
                                        <td class="${f.saldo < 100 ? 'text-danger' : 'text-success'}">${this.formatCurrency(f.saldo)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    break;
            }

            reportData.innerHTML = html;
            reportContent.classList.remove('hidden');

        } catch (error) {
            this.showToast('Erro ao carregar relatório', 'error');
        }
    }

    // ==================== Modal ====================

    showModal(title, content, buttons = []) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = content;

        const footer = document.getElementById('modal-footer');
        footer.innerHTML = buttons.map(btn =>
            `<button class="btn ${btn.class}" data-action="${btn.text}">${btn.text}</button>`
        ).join('');

        buttons.forEach(btn => {
            footer.querySelector(`[data-action="${btn.text}"]`).addEventListener('click', btn.action);
        });

        document.getElementById('modal').classList.remove('hidden');
    }

    closeModal() {
        document.getElementById('modal').classList.add('hidden');
    }

    // ==================== Toast Notifications ====================

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : '⚠️'}</span>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 4000);
    }

    // ==================== Utility Functions ====================

    formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value || 0);
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('pt-BR');
    }

    getStatusClass(status) {
        switch (status) {
            case 'PENDENTE': return 'warning';
            case 'PREPARANDO': return 'info';
            case 'PRONTO': return 'success';
            case 'ENTREGUE': return 'gray';
            case 'CANCELADO': return 'danger';
            default: return 'gray';
        }
    }
}

// Initialize app
const app = new LanchApp();
