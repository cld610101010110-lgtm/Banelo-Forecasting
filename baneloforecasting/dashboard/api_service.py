"""
API Service Layer - Connects to Node.js API instead of direct PostgreSQL
This allows the website to work on a different machine than the database.
"""

import requests
import os
from datetime import datetime
from functools import lru_cache
import json


class APIService:
    """Service class for making API calls to the Node.js backend"""

    def __init__(self):
        # API Configuration - can be overridden via environment variables
        self.base_url = os.getenv('API_BASE_URL', 'http://localhost:3000')
        self.timeout = int(os.getenv('API_TIMEOUT', '30'))

    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, timeout=self.timeout)
            elif method == 'DELETE':
                response = requests.delete(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            print(f"[API] Connection error: Cannot reach {url}")
            return {'success': False, 'error': 'Cannot connect to API server', 'data': []}
        except requests.exceptions.Timeout:
            print(f"[API] Timeout: Request to {url} timed out")
            return {'success': False, 'error': 'API request timed out', 'data': []}
        except requests.exceptions.RequestException as e:
            print(f"[API] Request error: {e}")
            return {'success': False, 'error': str(e), 'data': []}
        except json.JSONDecodeError:
            print(f"[API] Invalid JSON response from {url}")
            return {'success': False, 'error': 'Invalid API response', 'data': []}

    # ========================================
    # PRODUCTS ENDPOINTS
    # ========================================

    def get_products(self):
        """Get all products from the API"""
        result = self._make_request('GET', '/api/products')
        if result.get('success', True):
            return result.get('data', result.get('products', []))
        return []

    def get_product(self, product_id):
        """Get a single product by ID"""
        result = self._make_request('GET', f'/api/products/{product_id}')
        if result.get('success', True):
            return result.get('data', result.get('product', None))
        return None

    def add_product(self, product_data):
        """Add a new product"""
        return self._make_request('POST', '/api/products', data=product_data)

    def update_product(self, product_id, product_data):
        """Update an existing product"""
        return self._make_request('PUT', f'/api/products/{product_id}', data=product_data)

    def delete_product(self, product_id):
        """Delete a product"""
        return self._make_request('DELETE', f'/api/products/{product_id}')

    # ========================================
    # SALES ENDPOINTS
    # ========================================

    def get_sales(self, limit=1000, date_from=None, date_to=None):
        """Get sales data with optional filters"""
        params = {'limit': limit}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to

        result = self._make_request('GET', '/api/sales', params=params)
        if result.get('success', True):
            return result.get('data', result.get('sales', []))
        return []

    def get_sales_summary(self, period='today'):
        """Get sales summary (today, week, month)"""
        result = self._make_request('GET', f'/api/sales/summary', params={'period': period})
        return result

    # ========================================
    # RECIPES ENDPOINTS
    # ========================================

    def get_recipes(self):
        """Get all recipes with ingredients"""
        result = self._make_request('GET', '/api/recipes')
        if result.get('success', True):
            return result.get('data', result.get('recipes', []))
        return []

    def get_recipe(self, recipe_id):
        """Get a single recipe by ID"""
        result = self._make_request('GET', f'/api/recipes/{recipe_id}')
        if result.get('success', True):
            return result.get('data', result.get('recipe', None))
        return None

    def add_recipe(self, recipe_data):
        """Add a new recipe"""
        return self._make_request('POST', '/api/recipes', data=recipe_data)

    def update_recipe(self, recipe_id, recipe_data):
        """Update an existing recipe"""
        return self._make_request('PUT', f'/api/recipes/{recipe_id}', data=recipe_data)

    def delete_recipe(self, recipe_id):
        """Delete a recipe"""
        return self._make_request('DELETE', f'/api/recipes/{recipe_id}')

    # ========================================
    # RECIPE INGREDIENTS ENDPOINTS
    # ========================================

    def get_recipe_ingredients(self, recipe_id):
        """Get ingredients for a specific recipe"""
        result = self._make_request('GET', f'/api/recipes/{recipe_id}/ingredients')
        if result.get('success', True):
            return result.get('data', result.get('ingredients', []))
        return []

    # ========================================
    # USERS ENDPOINTS
    # ========================================

    def get_users(self):
        """Get all users"""
        result = self._make_request('GET', '/api/users')
        if result.get('success', True):
            return result.get('data', result.get('users', []))
        return []

    def authenticate_user(self, username, password):
        """Authenticate a user"""
        return self._make_request('POST', '/api/auth/login', data={
            'username': username,
            'password': password
        })

    # ========================================
    # AUDIT LOGS ENDPOINTS
    # ========================================

    def get_audit_logs(self, limit=1000, user=None, action=None, date_from=None, date_to=None):
        """Get audit logs with optional filters"""
        params = {'limit': limit}
        if user:
            params['user'] = user
        if action:
            params['action'] = action
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to

        result = self._make_request('GET', '/api/audit-logs', params=params)
        if result.get('success', True):
            return result.get('data', result.get('logs', []))
        return []

    def add_audit_log(self, log_data):
        """Add a new audit log entry"""
        return self._make_request('POST', '/api/audit-logs', data=log_data)

    # ========================================
    # WASTE LOGS ENDPOINTS
    # ========================================

    def get_waste_logs(self, date_from=None, date_to=None):
        """Get waste logs with optional date filters"""
        params = {}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to

        result = self._make_request('GET', '/api/waste-logs', params=params)
        if result.get('success', True):
            return result.get('data', result.get('waste_logs', []))
        return []

    def add_waste_log(self, waste_data):
        """Add a new waste log entry"""
        return self._make_request('POST', '/api/waste-logs', data=waste_data)

    # ========================================
    # INVENTORY ENDPOINTS
    # ========================================

    def transfer_inventory(self, product_id, quantity):
        """Transfer stock from Inventory A to B"""
        return self._make_request('POST', '/api/inventory/transfer', data={
            'product_id': product_id,
            'quantity': quantity
        })

    def update_inventory(self, product_id, inventory_a=None, inventory_b=None):
        """Update product inventory"""
        data = {'product_id': product_id}
        if inventory_a is not None:
            data['inventory_a'] = inventory_a
        if inventory_b is not None:
            data['inventory_b'] = inventory_b
        return self._make_request('PUT', f'/api/products/{product_id}/inventory', data=data)

    # ========================================
    # HEALTH CHECK
    # ========================================

    def health_check(self):
        """Check if the API is reachable"""
        try:
            result = self._make_request('GET', '/api/health')
            return {
                'status': 'healthy',
                'api_url': self.base_url,
                'message': 'API connection successful',
                'data': result
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'api_url': self.base_url,
                'message': str(e)
            }


# Singleton instance
_api_service = None

def get_api_service():
    """Get the singleton API service instance"""
    global _api_service
    if _api_service is None:
        _api_service = APIService()
    return _api_service
