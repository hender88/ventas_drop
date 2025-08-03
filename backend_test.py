import requests
import sys
from datetime import datetime, date
import json

class ControlGastosAPITester:
    def __init__(self, base_url="https://ee0ade8f-ba28-4446-b75e-f095aaecddbf.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'List with ' + str(len(response_data)) + ' items'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            self.test_results.append({
                'name': name,
                'method': method,
                'endpoint': endpoint,
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'success': success,
                'response_size': len(response.text) if response.text else 0
            })

            return success, response.json() if success and response.text else {}

        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED - Network Error: {str(e)}")
            self.test_results.append({
                'name': name,
                'method': method,
                'endpoint': endpoint,
                'expected_status': expected_status,
                'actual_status': 'ERROR',
                'success': False,
                'error': str(e)
            })
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.test_results.append({
                'name': name,
                'method': method,
                'endpoint': endpoint,
                'expected_status': expected_status,
                'actual_status': 'ERROR',
                'success': False,
                'error': str(e)
            })
            return False, {}

    def test_root_endpoint(self):
        """Test root endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_dashboard_endpoint(self):
        """Test dashboard statistics endpoint"""
        success, response = self.run_test("Dashboard Statistics", "GET", "api/dashboard", 200)
        
        if success:
            # Verify required fields in dashboard response
            required_fields = [
                'ganancias_totales', 'perdidas_totales', 'inversion_publicidad',
                'productos_vendidos', 'productos_devueltos', 'ventas_por_dia', 'ganancias_por_producto'
            ]
            
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"⚠️  WARNING - Missing dashboard fields: {missing_fields}")
            else:
                print(f"✅ All required dashboard fields present")
                
            # Print some statistics
            print(f"   📊 Ganancias Totales: ${response.get('ganancias_totales', 0):,.2f}")
            print(f"   📊 Pérdidas Totales: ${response.get('perdidas_totales', 0):,.2f}")
            print(f"   📊 Inversión Publicidad: ${response.get('inversion_publicidad', 0):,.2f}")
            print(f"   📊 Productos Vendidos: {response.get('productos_vendidos', 0)}")
            print(f"   📊 Productos Devueltos: {response.get('productos_devueltos', 0)}")
            print(f"   📊 Ventas por día: {len(response.get('ventas_por_dia', []))} días")
            print(f"   📊 Ganancias por producto: {len(response.get('ganancias_por_producto', []))} productos")
        
        return success, response

    def test_clientes_endpoints(self):
        """Test clientes GET and POST endpoints"""
        # Test GET clientes
        success_get, clientes = self.run_test("Get Clientes List", "GET", "api/clientes", 200)
        
        if success_get:
            print(f"   📋 Found {len(clientes)} clientes")
            if clientes:
                print(f"   📋 Sample cliente: {clientes[0].get('nombre', 'N/A')} {clientes[0].get('apellidos', 'N/A')}")
        
        # Test POST cliente
        test_cliente = {
            "nombre": "Test",
            "apellidos": "Usuario",
            "telefono": "3001234567"
        }
        
        success_post, response = self.run_test("Create Cliente", "POST", "api/clientes", 200, test_cliente)
        
        return success_get and success_post, clientes

    def test_ventas_endpoints(self):
        """Test ventas GET and POST endpoints"""
        # Test GET ventas
        success_get, ventas = self.run_test("Get Ventas List", "GET", "api/ventas", 200)
        
        if success_get:
            print(f"   📋 Found {len(ventas)} ventas")
            if ventas:
                sample_venta = ventas[0]
                print(f"   📋 Sample venta: {sample_venta.get('producto', 'N/A')} - ${sample_venta.get('valor_venta', 0):,.2f}")
        
        # Get a cliente_id for testing venta creation
        success_clientes, clientes = self.run_test("Get Clientes for Venta Test", "GET", "api/clientes", 200)
        
        if success_clientes and clientes:
            cliente_id = clientes[0]['id']
            
            # Test POST venta
            test_venta = {
                "cliente_id": cliente_id,
                "producto": "Producto Test",
                "fecha_venta": date.today().isoformat(),
                "fecha_entrega": date.today().isoformat(),
                "valor_venta": 100000,
                "ganancia": 30000,
                "entregado": True,
                "valor_perdida": 0
            }
            
            success_post, response = self.run_test("Create Venta", "POST", "api/ventas", 200, test_venta)
            return success_get and success_post, ventas
        else:
            print("⚠️  Cannot test venta creation - no clientes available")
            return success_get, ventas

    def test_gastos_endpoints(self):
        """Test gastos GET and POST endpoints"""
        # Test GET gastos
        success_get, gastos = self.run_test("Get Gastos List", "GET", "api/gastos", 200)
        
        if success_get:
            print(f"   📋 Found {len(gastos)} gastos")
            if gastos:
                sample_gasto = gastos[0]
                print(f"   📋 Sample gasto: {sample_gasto.get('concepto', 'N/A')} - ${sample_gasto.get('valor', 0):,.2f}")
        
        # Test POST gasto
        test_gasto = {
            "concepto": "Test Publicidad",
            "valor": 50000,
            "fecha_inicio": date.today().isoformat(),
            "fecha_final": date.today().isoformat()
        }
        
        success_post, response = self.run_test("Create Gasto", "POST", "api/gastos", 200, test_gasto)
        
        return success_get and success_post, gastos

    def print_summary(self):
        """Print test summary"""
        print(f"\n" + "="*60)
        print(f"📊 TEST SUMMARY")
        print(f"="*60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {status} - {result['name']} ({result['method']} {result['endpoint']})")
            if not result['success'] and 'error' in result:
                print(f"    Error: {result['error']}")
        
        return self.tests_passed == self.tests_run

def main():
    print("🚀 Starting Control de Gastos y Ganancias API Tests")
    print("="*60)
    
    tester = ControlGastosAPITester()
    
    # Run all tests
    print("\n1️⃣ Testing Root Endpoint...")
    tester.test_root_endpoint()
    
    print("\n2️⃣ Testing Dashboard Endpoint...")
    tester.test_dashboard_endpoint()
    
    print("\n3️⃣ Testing Clientes Endpoints...")
    tester.test_clientes_endpoints()
    
    print("\n4️⃣ Testing Ventas Endpoints...")
    tester.test_ventas_endpoints()
    
    print("\n5️⃣ Testing Gastos Endpoints...")
    tester.test_gastos_endpoints()
    
    # Print summary
    all_passed = tester.print_summary()
    
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED! Backend API is working correctly.")
        return 0
    else:
        print(f"\n⚠️  SOME TESTS FAILED! Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())