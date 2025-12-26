/**
 * LANCH - API Client
 * Handles all communication with the backend
 */

const API_BASE_URL = 'http://localhost:8000';

class LanchAPI {
    constructor() {
        this.token = localStorage.getItem('token');
    }

    // ==================== Auth ====================

    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('token');
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async request(method, endpoint, data = null) {
        const options = {
            method,
            headers: this.getHeaders()
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

            if (response.status === 401) {
                this.clearToken();
                window.location.reload();
                throw new Error('Sua sessão expirou. Por favor, faça login novamente.');
            }

            const result = await response.json();

            if (!response.ok) {
                // Mensagens de erro mais amigáveis
                const errorMessages = {
                    400: 'Dados inválidos. Verifique as informações e tente novamente.',
                    403: 'Você não tem permissão para realizar esta ação.',
                    404: 'Recurso não encontrado.',
                    409: 'Conflito: esse registro já existe.',
                    422: 'Dados inválidos. Verifique os campos e tente novamente.',
                    429: 'Muitas tentativas. Aguarde um momento e tente novamente.',
                    500: 'Erro no servidor. Tente novamente em alguns instantes.',
                    503: 'Serviço temporariamente indisponível.'
                };

                const statusMessage = errorMessages[response.status] || 'Erro na requisição';
                const detailMessage = result.detail || statusMessage;

                throw new Error(detailMessage);
            }

            return result;
        } catch (error) {
            // Melhorar mensagens de erro de rede
            if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
                console.error(`API Error [${method} ${endpoint}]: Não foi possível conectar ao servidor`);
                throw new Error('Não foi possível conectar ao servidor. Verifique sua conexão com a internet.');
            }

            console.error(`API Error [${method} ${endpoint}]:`, error);
            throw error;
        }
    }

    // ==================== Authentication ====================

    async login(username, password) {
        const response = await this.request('POST', '/auth/login', { username, password });
        this.setToken(response.access_token);
        return response;
    }

    async getCurrentUser() {
        return this.request('GET', '/auth/me');
    }

    async changePassword(currentPassword, newPassword) {
        return this.request('POST', '/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword
        });
    }

    // ==================== Admin ====================

    async backupDatabase() {
        return this.request('POST', '/admin/backup');
    }

    logout() {
        this.clearToken();
    }

    // ==================== Dashboard ====================

    async getDashboard() {
        return this.request('GET', '/relatorios/dashboard');
    }

    // ==================== Products ====================

    async getCategories(ativo = true) {
        return this.request('GET', `/produtos/categorias?ativo=${ativo}`);
    }

    async createCategory(data) {
        return this.request('POST', '/produtos/categorias', data);
    }

    async getProducts(ativo = null, categoriaId = null) {
        let url = '/produtos?';
        if (ativo !== null) url += `ativo=${ativo}&`;
        if (categoriaId) url += `categoria_id=${categoriaId}`;
        return this.request('GET', url);
    }

    async getProduct(id) {
        return this.request('GET', `/produtos/${id}`);
    }

    async createProduct(data) {
        return this.request('POST', '/produtos', data);
    }

    async updateProduct(id, data) {
        return this.request('PUT', `/produtos/${id}`, data);
    }

    async deleteProduct(id) {
        return this.request('DELETE', `/produtos/${id}`);
    }

    // ==================== Employees ====================

    async getEmployees(ativo = null) {
        let url = '/funcionarios';
        if (ativo !== null) url += `?ativo=${ativo}`;
        return this.request('GET', url);
    }

    async searchEmployee(matriculaOrCpf) {
        const isMatricula = /^\d+$/.test(matriculaOrCpf) && matriculaOrCpf.length < 11;
        const param = isMatricula ? 'matricula' : 'cpf';
        return this.request('GET', `/funcionarios/buscar?${param}=${matriculaOrCpf}`);
    }

    async getEmployee(id) {
        return this.request('GET', `/funcionarios/${id}`);
    }

    async createEmployee(data) {
        return this.request('POST', '/funcionarios', data);
    }

    async updateEmployee(id, data) {
        return this.request('PUT', `/funcionarios/${id}`, data);
    }

    async deleteEmployee(id) {
        return this.request('DELETE', `/funcionarios/${id}`);
    }

    async getEmployeeConsumption(id) {
        return this.request('GET', `/funcionarios/${id}/consumo`);
    }

    // ==================== Orders ====================

    async getOrders(filters = {}) {
        let url = '/pedidos?';
        if (filters.status) url += `status=${filters.status}&`;
        if (filters.tipo_cliente) url += `tipo_cliente=${filters.tipo_cliente}&`;
        if (filters.limit) url += `limit=${filters.limit}`;
        return this.request('GET', url);
    }

    async getKitchenOrders() {
        return this.request('GET', '/pedidos/cozinha');
    }

    async getTodayOrders() {
        return this.request('GET', '/pedidos/hoje');
    }

    async getOrder(id) {
        return this.request('GET', `/pedidos/${id}`);
    }

    async createOrder(data) {
        return this.request('POST', '/pedidos', data);
    }

    async updateOrderStatus(id, status) {
        return this.request('PUT', `/pedidos/${id}/status?novo_status=${status}`);
    }

    async cancelOrder(id) {
        return this.request('DELETE', `/pedidos/${id}`);
    }

    // ==================== Competencies ====================

    async getCompetencies() {
        return this.request('GET', '/competencias');
    }

    async getCurrentCompetency() {
        return this.request('GET', '/competencias/atual');
    }

    async getCompetencyConsumption(id) {
        return this.request('GET', `/competencias/${id}/consumos`);
    }

    async createCompetency() {
        return this.request('POST', '/competencias/nova');
    }

    async closeCompetency(id) {
        return this.request('POST', `/competencias/${id}/fechar`);
    }

    getExcelExportUrl(competenciaId) {
        return `${API_BASE_URL}/competencias/${competenciaId}/export/excel`;
    }

    getCsvExportUrl(competenciaId) {
        return `${API_BASE_URL}/competencias/${competenciaId}/export/csv`;
    }

    // ==================== Reports ====================

    async getDailySales(dataInicio, dataFim) {
        let url = '/relatorios/vendas-diarias?';
        if (dataInicio) url += `data_inicio=${dataInicio}&`;
        if (dataFim) url += `data_fim=${dataFim}`;
        return this.request('GET', url);
    }

    async getPaymentMethods(dataInicio, dataFim) {
        let url = '/relatorios/formas-pagamento?';
        if (dataInicio) url += `data_inicio=${dataInicio}&`;
        if (dataFim) url += `data_fim=${dataFim}`;
        return this.request('GET', url);
    }

    async getTopProducts(dataInicio, dataFim, limit = 20) {
        let url = `/relatorios/produtos-vendidos?limit=${limit}&`;
        if (dataInicio) url += `data_inicio=${dataInicio}&`;
        if (dataFim) url += `data_fim=${dataFim}`;
        return this.request('GET', url);
    }

    async getEmployeeConsumptionReport(competenciaId = null) {
        let url = '/relatorios/funcionarios-consumo';
        if (competenciaId) url += `?competencia_id=${competenciaId}`;
        return this.request('GET', url);
    }

    async getAuditLog(filters = {}) {
        let url = '/relatorios/audit-log?';
        if (filters.tabela) url += `tabela=${filters.tabela}&`;
        if (filters.limit) url += `limit=${filters.limit}`;
        return this.request('GET', url);
    }
}

// Create global instance
const api = new LanchAPI();
