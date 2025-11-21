import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

class FirebaseService:
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Load environment variables from .env file
            load_dotenv()
            
            if not firebase_admin._apps:
                # Get credentials path from environment or use default
                cred_path = os.getenv('FIREBASE_CREDENTIALS', 'firebase-credentials.json')
                
                # Debug: Print the path being used
                print(f"🔍 Looking for Firebase credentials at: {cred_path}")
                print(f"🔍 File exists: {os.path.exists(cred_path)}")
                print(f"🔍 Current working directory: {os.getcwd()}")
                
                # Check if file exists
                if not os.path.exists(cred_path):
                    raise FileNotFoundError(f"Firebase credentials file not found at: {cred_path}")
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase initialized successfully!")
            
            self._db = firestore.client()
            print(f"✅ Firestore client created: {self._db}")
            
        except Exception as e:
            print(f"❌ Error initializing Firebase: {e}")
            import traceback
            traceback.print_exc()
            self._db = None
    
    @property
    def db(self):
        return self._db
    
    def get_all_products(self):
        """Get all products from Firestore"""
        try:
            if self._db is None:
                raise Exception("Firebase is not initialized. Check your credentials.")
            
            # Use 'products' collection
            products_ref = self._db.collection('products')
            docs = products_ref.stream()
            
            products = []
            for doc in docs:
                product_data = doc.to_dict()
                product_data['id'] = doc.id
                products.append(product_data)
            
            print(f"🔍 Found {len(products)} products in Firebase")
            return products
        except Exception as e:
            print(f"❌ Error getting products: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_all_sales(self):
        """Get all sales from Firestore"""
        try:
            if self._db is None:
                raise Exception("Firebase is not initialized. Check your credentials.")
            
            sales_ref = self._db.collection('sales_report')
            docs = sales_ref.order_by('orderDate', direction=firestore.Query.DESCENDING).stream()
            
            sales = []
            for doc in docs:
                sale_data = doc.to_dict()
                sale_data['id'] = doc.id
                sales.append(sale_data)
            
            return sales
        except Exception as e:
            print(f"❌ Error getting sales: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # ✅ NEW CRUD METHODS BELOW
    
    def add_product(self, product_data):
        """Add a new product to Firestore"""
        try:
            if self._db is None:
                raise Exception("Firebase is not initialized.")
            
            products_ref = self._db.collection('products')
            
            # Add timestamp
            from datetime import datetime
            product_data['createdAt'] = datetime.now()
            product_data['updatedAt'] = datetime.now()
            
            # Add document and get reference
            doc_ref = products_ref.add(product_data)
            
            print(f"✅ Product added with ID: {doc_ref[1].id}")
            return {'success': True, 'id': doc_ref[1].id}
        except Exception as e:
            print(f"❌ Error adding product: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def update_product(self, product_id, product_data):
        """Update an existing product in Firestore"""
        try:
            if self._db is None:
                raise Exception("Firebase is not initialized.")
            
            # Add timestamp
            from datetime import datetime
            product_data['updatedAt'] = datetime.now()
            
            # Update document
            product_ref = self._db.collection('products').document(product_id)
            product_ref.update(product_data)
            
            print(f"✅ Product updated: {product_id}")
            return {'success': True, 'id': product_id}
        except Exception as e:
            print(f"❌ Error updating product: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def delete_product(self, product_id):
        """Delete a product from Firestore"""
        try:
            if self._db is None:
                raise Exception("Firebase is not initialized.")
            
            # Delete document
            self._db.collection('products').document(product_id).delete()
            
            print(f"✅ Product deleted: {product_id}")
            return {'success': True}
        except Exception as e:
            print(f"❌ Error deleting product: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def get_product_by_id(self, product_id):
        """Get a single product by ID"""
        try:
            if self._db is None:
                raise Exception("Firebase is not initialized.")
            
            doc = self._db.collection('products').document(product_id).get()
            
            if doc.exists:
                product_data = doc.to_dict()
                product_data['id'] = doc.id
                return product_data
            else:
                return None
        except Exception as e:
            print(f"❌ Error getting product: {e}")
            return None