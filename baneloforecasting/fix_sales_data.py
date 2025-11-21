import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.firebase_service import FirebaseService
from datetime import datetime

# Initialize Firebase
db = FirebaseService().db

def fix_sales_data():
    """Add productFirebaseId to existing sales"""
    
    print("\n🔧 FIXING SALES DATA - ADDING FIREBASE IDs")
    print("=" * 60)
    
    # Get all products
    print("\n📦 Loading products from Firebase...")
    products_ref = db.collection('products')
    products = {}
    
    product_count = 0
    for doc in products_ref.stream():
        data = doc.to_dict()
        product_name = data.get('name', '').strip().lower()
        products[product_name] = {
            'id': doc.id,
            'name': data.get('name', ''),
            'category': data.get('category', '')
        }
        product_count += 1
        print(f"  ✅ {data.get('name')} → {doc.id}")
    
    print(f"\n📊 Loaded {product_count} products")
    
    # Get all sales
    print("\n📦 Loading sales from Firebase...")
    sales_ref = db.collection('sales')
    sales_docs = list(sales_ref.stream())
    
    print(f"📊 Found {len(sales_docs)} sales records")
    
    updated_count = 0
    skipped_count = 0
    no_match_count = 0
    error_count = 0
    
    print("\n🔄 Processing sales...")
    print("-" * 60)
    
    for sale_doc in sales_docs:
        try:
            sale_data = sale_doc.to_dict()
            sale_id = sale_doc.id
            
            # Skip if already has productFirebaseId
            if 'productFirebaseId' in sale_data and sale_data['productFirebaseId']:
                skipped_count += 1
                continue
            
            # Get product name - handle different types
            product_name_original = sale_data.get('productName', '')
            
            # Convert to string if it's not
            if not isinstance(product_name_original, str):
                # If it's a number or other type, convert to string
                product_name_original = str(product_name_original)
                print(f"⚠️  Converted non-string productName: {product_name_original} (type: {type(sale_data.get('productName')).__name__})")
            
            # Clean the product name
            product_name = product_name_original.strip().lower()
            
            # Skip if empty
            if not product_name:
                error_count += 1
                print(f"❌ Empty product name in sale {sale_id}")
                continue
            
            if product_name in products:
                firebase_id = products[product_name]['id']
                
                # Update with Firebase ID
                db.collection('sales').document(sale_id).update({
                    'productFirebaseId': firebase_id
                })
                
                updated_count += 1
                print(f"✅ Updated: {product_name_original} → {firebase_id}")
            else:
                no_match_count += 1
                print(f"⚠️  No match: {product_name_original}")
        
        except Exception as e:
            error_count += 1
            print(f"❌ Error processing sale {sale_doc.id}: {str(e)}")
            continue
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY:")
    print("=" * 60)
    print(f"  ✅ Updated:     {updated_count} sales")
    print(f"  ⏭️  Skipped:     {skipped_count} sales (already had IDs)")
    print(f"  ⚠️  No match:    {no_match_count} sales")
    print(f"  ❌ Errors:      {error_count} sales")
    print(f"  📦 Total:       {len(sales_docs)} sales")
    print("=" * 60)
    
    # Show percentage
    success_rate = (updated_count / len(sales_docs)) * 100 if len(sales_docs) > 0 else 0
    print(f"\n✨ Success Rate: {success_rate:.1f}%")
    print(f"✨ {updated_count} sales now have Firebase IDs!")
    print("\n🎯 Next step: Go to ML Forecasting page and click 'Retrain Model'\n")

if __name__ == '__main__':
    try:
        fix_sales_data()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()