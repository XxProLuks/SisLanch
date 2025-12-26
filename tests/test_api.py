"""
LANCH - Sistema de Lanchonete Hospitalar
Test Suite - API e Fluxos de Negócio
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class LanchTester:
    def __init__(self):
        self.token = None
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def log(self, test_name, success, message=""):
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append(f"{status} | {test_name} | {message}")
        if success:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
        print(f"{status} | {test_name}")
        if message and not success:
            print(f"         └── {message}")
    
    def headers(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h
    
    # ==================== Testes ====================
    
    def test_health_check(self):
        """Testa se a API está respondendo"""
        try:
            r = requests.get(f"{BASE_URL}/")
            self.log("Health Check", r.status_code == 200, r.text[:50])
            return r.status_code == 200
        except Exception as e:
            self.log("Health Check", False, str(e))
            return False
    
    def test_login_admin(self):
        """Testa login do administrador"""
        try:
            r = requests.post(
                f"{BASE_URL}/auth/login",
                headers={"Content-Type": "application/json"},
                json={"username": "admin", "password": "admin123"}
            )
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                self.log("Login Admin", True, "Token obtido")
                return True
            else:
                self.log("Login Admin", False, r.text)
                return False
        except Exception as e:
            self.log("Login Admin", False, str(e))
            return False
    
    def test_login_invalid(self):
        """Testa login com credenciais inválidas"""
        try:
            r = requests.post(
                f"{BASE_URL}/auth/login",
                headers={"Content-Type": "application/json"},
                json={"username": "admin", "password": "wrongpassword"}
            )
            self.log("Login Inválido (deve falhar)", r.status_code == 401)
            return r.status_code == 401
        except Exception as e:
            self.log("Login Inválido", False, str(e))
            return False
    
    def test_get_current_user(self):
        """Testa obtenção do usuário atual"""
        try:
            r = requests.get(f"{BASE_URL}/auth/me", headers=self.headers())
            success = r.status_code == 200 and r.json()["username"] == "admin"
            self.log("Obter Usuário Atual", success)
            return success
        except Exception as e:
            self.log("Obter Usuário Atual", False, str(e))
            return False
    
    def test_list_categories(self):
        """Testa listagem de categorias"""
        try:
            r = requests.get(f"{BASE_URL}/produtos/categorias", headers=self.headers())
            categories = r.json()
            success = r.status_code == 200 and len(categories) >= 5
            self.log("Listar Categorias", success, f"{len(categories)} categorias encontradas")
            return success
        except Exception as e:
            self.log("Listar Categorias", False, str(e))
            return False
    
    def test_create_product(self):
        """Testa criação de produto"""
        try:
            product_data = {
                "nome": "X-Burger Test",
                "categoria_id": 1,
                "preco": 18.90
            }
            r = requests.post(f"{BASE_URL}/produtos", headers=self.headers(), json=product_data)
            if r.status_code == 201:
                self.product_id = r.json()["id"]
                self.log("Criar Produto", True, f"ID: {self.product_id}")
                return True
            else:
                self.log("Criar Produto", False, r.text)
                return False
        except Exception as e:
            self.log("Criar Produto", False, str(e))
            return False
    
    def test_list_products(self):
        """Testa listagem de produtos"""
        try:
            r = requests.get(f"{BASE_URL}/produtos", headers=self.headers())
            products = r.json()
            success = r.status_code == 200 and len(products) >= 1
            self.log("Listar Produtos", success, f"{len(products)} produtos encontrados")
            return success
        except Exception as e:
            self.log("Listar Produtos", False, str(e))
            return False
    
    def test_create_employee(self):
        """Testa criação de funcionário"""
        try:
            employee_data = {
                "matricula": "12345",
                "cpf": "12345678901",
                "nome": "João da Silva Test",
                "setor": "Enfermagem",
                "centro_custo": "CC001",
                "limite_mensal": 500.00
            }
            r = requests.post(f"{BASE_URL}/funcionarios", headers=self.headers(), json=employee_data)
            if r.status_code == 201:
                self.employee_id = r.json()["id"]
                self.log("Criar Funcionário", True, f"ID: {self.employee_id}")
                return True
            else:
                self.log("Criar Funcionário", False, r.text)
                return False
        except Exception as e:
            self.log("Criar Funcionário", False, str(e))
            return False
    
    def test_search_employee(self):
        """Testa busca de funcionário por matrícula"""
        try:
            r = requests.get(f"{BASE_URL}/funcionarios/buscar?matricula=12345", headers=self.headers())
            if r.status_code == 200:
                emp = r.json()
                success = emp["matricula"] == "12345" and emp["saldo_disponivel"] == 500.00
                self.log("Buscar Funcionário", success, f"Saldo: R$ {emp['saldo_disponivel']}")
                return success
            else:
                self.log("Buscar Funcionário", False, r.text)
                return False
        except Exception as e:
            self.log("Buscar Funcionário", False, str(e))
            return False
    
    def test_get_current_competency(self):
        """Testa obtenção da competência atual"""
        try:
            r = requests.get(f"{BASE_URL}/competencias/atual", headers=self.headers())
            if r.status_code == 200:
                comp = r.json()
                self.competency_id = comp["id"]
                self.log("Competência Atual", True, f"{comp['referencia']} - {comp['status']}")
                return True
            else:
                self.log("Competência Atual", False, r.text)
                return False
        except Exception as e:
            self.log("Competência Atual", False, str(e))
            return False
    
    def test_create_employee_order(self):
        """Testa criação de pedido para funcionário"""
        try:
            order_data = {
                "tipo_cliente": "FUNCIONARIO",
                "funcionario_id": self.employee_id,
                "forma_pagamento": "CONVENIO",
                "observacao": "Pedido de teste",
                "itens": [
                    {"produto_id": self.product_id, "quantidade": 2}
                ]
            }
            r = requests.post(f"{BASE_URL}/pedidos", headers=self.headers(), json=order_data)
            if r.status_code == 201:
                order = r.json()
                self.order_id = order["id"]
                expected_total = 18.90 * 2
                success = order["tipo_cliente"] == "FUNCIONARIO" and abs(order["valor_total"] - expected_total) < 0.01
                self.log("Criar Pedido Funcionário", success, f"#{order['numero']} - R$ {order['valor_total']}")
                return success
            else:
                self.log("Criar Pedido Funcionário", False, r.text)
                return False
        except Exception as e:
            self.log("Criar Pedido Funcionário", False, str(e))
            return False
    
    def test_verify_consumption_updated(self):
        """Verifica se o consumo do funcionário foi atualizado"""
        try:
            r = requests.get(f"{BASE_URL}/funcionarios/buscar?matricula=12345", headers=self.headers())
            if r.status_code == 200:
                emp = r.json()
                expected_consumed = 18.90 * 2
                expected_balance = 500.00 - expected_consumed
                success = abs(emp["valor_consumido"] - expected_consumed) < 0.01
                self.log("Consumo Atualizado", success, f"Consumido: R$ {emp['valor_consumido']:.2f}")
                return success
            else:
                self.log("Consumo Atualizado", False, r.text)
                return False
        except Exception as e:
            self.log("Consumo Atualizado", False, str(e))
            return False
    
    def test_create_patient_order(self):
        """Testa criação de pedido para paciente"""
        try:
            order_data = {
                "tipo_cliente": "PACIENTE",
                "forma_pagamento": "PIX",
                "itens": [
                    {"produto_id": self.product_id, "quantidade": 1}
                ]
            }
            r = requests.post(f"{BASE_URL}/pedidos", headers=self.headers(), json=order_data)
            if r.status_code == 201:
                order = r.json()
                success = order["tipo_cliente"] == "PACIENTE" and order["forma_pagamento"] == "PIX"
                self.log("Criar Pedido Paciente", success, f"#{order['numero']} - {order['forma_pagamento']}")
                return success
            else:
                self.log("Criar Pedido Paciente", False, r.text)
                return False
        except Exception as e:
            self.log("Criar Pedido Paciente", False, str(e))
            return False
    
    def test_kitchen_orders(self):
        """Testa listagem de pedidos da cozinha"""
        try:
            r = requests.get(f"{BASE_URL}/pedidos/cozinha", headers=self.headers())
            if r.status_code == 200:
                orders = r.json()
                success = len(orders) >= 2  # Os dois pedidos criados
                self.log("Pedidos Cozinha", success, f"{len(orders)} pedidos pendentes")
                return success
            else:
                self.log("Pedidos Cozinha", False, r.text)
                return False
        except Exception as e:
            self.log("Pedidos Cozinha", False, str(e))
            return False
    
    def test_update_order_status(self):
        """Testa atualização de status do pedido"""
        try:
            r = requests.put(
                f"{BASE_URL}/pedidos/{self.order_id}/status?novo_status=PREPARANDO",
                headers=self.headers()
            )
            success = r.status_code == 200
            self.log("Atualizar Status Pedido", success, "PENDENTE → PREPARANDO")
            
            # Atualiza para PRONTO
            r2 = requests.put(
                f"{BASE_URL}/pedidos/{self.order_id}/status?novo_status=PRONTO",
                headers=self.headers()
            )
            success2 = r2.status_code == 200
            self.log("Atualizar Status Pedido", success2, "PREPARANDO → PRONTO")
            
            return success and success2
        except Exception as e:
            self.log("Atualizar Status Pedido", False, str(e))
            return False
    
    def test_employee_limit_exceeded(self):
        """Testa bloqueio quando limite é excedido"""
        try:
            # Tenta criar pedido que excede o limite
            order_data = {
                "tipo_cliente": "FUNCIONARIO",
                "funcionario_id": self.employee_id,
                "forma_pagamento": "CONVENIO",
                "itens": [
                    {"produto_id": self.product_id, "quantidade": 100}  # Vai exceder
                ]
            }
            r = requests.post(f"{BASE_URL}/pedidos", headers=self.headers(), json=order_data)
            success = r.status_code == 403  # Deve ser bloqueado
            self.log("Bloqueio Limite Excedido", success, "Pedido bloqueado corretamente" if success else r.text[:50])
            return success
        except Exception as e:
            self.log("Bloqueio Limite Excedido", False, str(e))
            return False
    
    def test_dashboard(self):
        """Testa dashboard"""
        try:
            r = requests.get(f"{BASE_URL}/relatorios/dashboard", headers=self.headers())
            if r.status_code == 200:
                data = r.json()
                success = "pedidos" in data and "faturamento" in data
                self.log("Dashboard", success, f"Pedidos: {data['pedidos']['total']}")
                return success
            else:
                self.log("Dashboard", False, r.text)
                return False
        except Exception as e:
            self.log("Dashboard", False, str(e))
            return False
    
    def test_competency_consumption(self):
        """Testa relatório de consumo da competência"""
        try:
            r = requests.get(f"{BASE_URL}/competencias/{self.competency_id}/consumos", headers=self.headers())
            if r.status_code == 200:
                data = r.json()
                success = len(data["consumos"]) >= 1
                self.log("Consumo Competência", success, f"Total: R$ {data['total_geral']:.2f}")
                return success
            else:
                self.log("Consumo Competência", False, r.text)
                return False
        except Exception as e:
            self.log("Consumo Competência", False, str(e))
            return False
    
    def test_audit_log(self):
        """Testa log de auditoria"""
        try:
            r = requests.get(f"{BASE_URL}/relatorios/audit-log?limit=10", headers=self.headers())
            if r.status_code == 200:
                logs = r.json()
                success = len(logs) >= 1
                self.log("Audit Log", success, f"{len(logs)} registros")
                return success
            else:
                self.log("Audit Log", False, r.text)
                return False
        except Exception as e:
            self.log("Audit Log", False, str(e))
            return False
    
    def run_all(self):
        """Executa todos os testes"""
        print("=" * 60)
        print("LANCH - Suite de Testes")
        print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        # Testes de Autenticação
        print("🔐 AUTENTICAÇÃO")
        print("-" * 40)
        self.test_health_check()
        self.test_login_admin()
        self.test_login_invalid()
        self.test_get_current_user()
        print()
        
        # Testes de Produtos
        print("🍔 PRODUTOS")
        print("-" * 40)
        self.test_list_categories()
        self.test_create_product()
        self.test_list_products()
        print()
        
        # Testes de Funcionários
        print("👥 FUNCIONÁRIOS")
        print("-" * 40)
        self.test_create_employee()
        self.test_search_employee()
        print()
        
        # Testes de Competência
        print("📅 COMPETÊNCIAS")
        print("-" * 40)
        self.test_get_current_competency()
        print()
        
        # Testes de Pedidos
        print("🛒 PEDIDOS")
        print("-" * 40)
        self.test_create_employee_order()
        self.test_verify_consumption_updated()
        self.test_create_patient_order()
        self.test_kitchen_orders()
        self.test_update_order_status()
        self.test_employee_limit_exceeded()
        print()
        
        # Testes de Relatórios
        print("📊 RELATÓRIOS")
        print("-" * 40)
        self.test_dashboard()
        self.test_competency_consumption()
        self.test_audit_log()
        print()
        
        # Resultado Final
        print("=" * 60)
        print("RESULTADO FINAL")
        print("=" * 60)
        total = self.tests_passed + self.tests_failed
        print(f"✅ Passou: {self.tests_passed}/{total}")
        print(f"❌ Falhou: {self.tests_failed}/{total}")
        print(f"📊 Taxa de Sucesso: {(self.tests_passed/total)*100:.1f}%")
        print("=" * 60)
        
        return self.tests_failed == 0


if __name__ == "__main__":
    tester = LanchTester()
    success = tester.run_all()
    exit(0 if success else 1)
