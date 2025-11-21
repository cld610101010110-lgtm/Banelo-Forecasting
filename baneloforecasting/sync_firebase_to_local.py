import os
import django
from django.utils import timezone
import pytz

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.firebase_service import FirebaseService
from dashboard.models import Product, Sale
from datetime import datetime

# Initialize Firebase
db = FirebaseService().db

def sync_products():
    """Sync products from Firebase to local database"""
    print("\n📦 SYNCING PRODUCTS FROM FIREBASE TO LOCAL DB")
    print("=" * 60)
    
    products_ref = db.collection('products')
    products_docs = products_ref.stream()
    
    synced = 0
    updated = 0
    
    for doc in products_docs:
        try:
            data = doc.to_dict()
            firebase_id = doc.id
            
            # Create or update product
            product, created = Product.objects.update_or_create(
                firebase_id=firebase_id,
                defaults={
                    'name': data.get('name', 'Unknown'),
                    'category': data.get('category', 'Unknown'),
                    'stock': float(data.get('stock', 0)),
                    'unit': data.get('unit', 'pcs'),
                    'price': float(data.get('price', 0)),
                }
            )
            
            if created:
                synced += 1
                print(f"✅ Created: {product.name}")
            else:
                updated += 1
                print(f"🔄 Updated: {product.name}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print(f"\n📊 Products: {synced} created, {updated} updated")


def sync_sales():
    """Sync sales from Firebase to local database"""
    print("\n💰 SYNCING SALES FROM FIREBASE TO LOCAL DB")
    print("=" * 60)
    
    sales_ref = db.collection('sales')
    sales_docs = sales_ref.stream()
    
    synced = 0
    skipped = 0
    
    # Set timezone
    local_tz = pytz.timezone('Asia/Manila')  # Use your timezone
    
    for doc in sales_docs:
        try:
            data = doc.to_dict()
            
            # Parse order date
            order_date_str = data.get('orderDate', '')
            if not order_date_str:
                skipped += 1
                continue
            
            try:
                # Try to parse date
                date_part = order_date_str.split()[0] if ' ' in order_date_str else order_date_str
                order_date = datetime.strptime(date_part, '%Y-%m-%d')
                
                # Make timezone aware
                order_date = local_tz.localize(order_date)
                
            except Exception as e:
                print(f"⚠️ Date parse error: {order_date_str} - {str(e)}")
                skipped += 1
                continue
            
            # Get product
            product_firebase_id = data.get('productFirebaseId')
            product = None
            
            if product_firebase_id:
                try:
                    product = Product.objects.get(firebase_id=product_firebase_id)
                except Product.DoesNotExist:
                    pass
            
            # Get price (handle missing price)
            price = data.get('price')
            if price is not None:
                try:
                    price = float(price)
                except:
                    price = 0.0
            else:
                price = 0.0
            
            # Check if sale already exists (avoid duplicates)
            product_name = data.get('productName', 'Unknown')
            quantity = float(data.get('quantity', 0))
            
            if not Sale.objects.filter(
                product_name=product_name,
                order_date=order_date,
                quantity=quantity
            ).exists():
                
                Sale.objects.create(
                    product=product,
                    product_firebase_id=product_firebase_id,
                    product_name=product_name,
                    category=data.get('category', 'Unknown'),
                    quantity=quantity,
                    price=price,
                    total=float(data.get('total', 0)) if data.get('total') else None,
                    order_date=order_date
                )
                
                synced += 1
                if synced % 50 == 0:
                    print(f"📊 Synced {synced} sales...")
            else:
                skipped += 1
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            skipped += 1
    
    print(f"\n📊 Sales: {synced} created, {skipped} skipped (duplicates or errors)")


if __name__ == '__main__':
    try:
        sync_products()
        sync_sales()
        print("\n✅ SYNC COMPLETE!\n")
    except Exception as e:
        print(f"\n❌ SYNC FAILED: {str(e)}")
        import traceback
        traceback.print_exc()