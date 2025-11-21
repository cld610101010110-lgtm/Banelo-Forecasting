import os
import django
from django.utils import timezone
import pytz

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.models import Product, Sale
from datetime import datetime, timedelta
import random

def add_nonbeverage_sales():
    """Add 200-300 sales for non-beverage products (Pastries, Sandwiches, etc.)"""
    
    print("\n💰 ADDING NON-BEVERAGE SALES DATA")
    print("=" * 60)
    
    # Get non-beverage products (exclude suka, sdfsdfg, datu puti)
    excluded_names = ['suka', 'sdfsdfg', 'datu puti vinegar', 'datu puti']
    
    all_products = Product.objects.exclude(
        name__icontains='suka'
    ).exclude(
        name__icontains='datu'
    ).exclude(
        name__icontains='sdfsdfg'
    )
    
    # Filter for non-beverage categories
    non_beverage_products = all_products.filter(
        category__in=['Pastries', 'Sandwiches', 'Snacks', 'Desserts', 'Food']
    )
    
    print(f"📦 Found {non_beverage_products.count()} non-beverage products (excluding suka, sdfsdfg, datu puti)")
    
    if non_beverage_products.count() == 0:
        print("\n⚠️  No non-beverage products found!")
        print("Available products:")
        for p in Product.objects.all():
            print(f"   - {p.name} ({p.category})")
        return
    
    # Display products that will get sales
    print("\n📋 Products that will receive sales data:")
    for product in non_beverage_products:
        print(f"   ✓ {product.name} ({product.category})")
    
    local_tz = pytz.timezone('Asia/Manila')
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # 30 days of data
    
    # Sales patterns for different product types
    # Format: (min_sales_per_day, max_sales_per_day)
    product_patterns = {
        'pastries': (3, 8),      # Croissants, Muffins, etc.
        'sandwiches': (5, 12),   # Ham & Cheese, etc.
        'snacks': (2, 6),        # Chips, cookies, etc.
        'desserts': (4, 10),     # Cakes, brownies, etc.
        'default': (3, 7)        # Any other product
    }
    
    sales_created = 0
    current_date = start_date
    
    print(f"\n🗓️  Generating sales from {start_date.date()} to {end_date.date()}")
    print("=" * 60)
    
    while current_date <= end_date:
        # Random time during business hours (8 AM - 8 PM)
        hour = random.randint(8, 20)
        minute = random.randint(0, 59)
        
        date_aware = local_tz.localize(
            current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        )
        
        for product in non_beverage_products:
            # Determine sales pattern based on category
            category_lower = product.category.lower()
            
            if 'pastry' in category_lower or 'pastries' in category_lower:
                min_qty, max_qty = product_patterns['pastries']
            elif 'sandwich' in category_lower or 'sandwiches' in category_lower:
                min_qty, max_qty = product_patterns['sandwiches']
            elif 'snack' in category_lower or 'snacks' in category_lower:
                min_qty, max_qty = product_patterns['snacks']
            elif 'dessert' in category_lower or 'desserts' in category_lower:
                min_qty, max_qty = product_patterns['desserts']
            else:
                min_qty, max_qty = product_patterns['default']
            
            # 80% chance of sales on any given day (some days no sales)
            if random.random() < 0.8:
                quantity = random.randint(min_qty, max_qty)
                
                # Create sale
                Sale.objects.create(
                    product=product,
                    product_firebase_id=product.firebase_id or f"local_{product.id}",
                    product_name=product.name,
                    category=product.category,
                    quantity=quantity,
                    price=product.price,
                    total=product.price * quantity,
                    order_date=date_aware
                )
                
                sales_created += 1
                
                if sales_created % 50 == 0:
                    print(f"   Created {sales_created} sales...")
        
        current_date += timedelta(days=1)
    
    print(f"\n✅ COMPLETED!")
    print(f"📊 Total sales created: {sales_created}")
    print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
    print(f"📦 Products with sales: {non_beverage_products.count()}")
    
    # Show summary by product
    print(f"\n📈 Sales Summary by Product:")
    print("=" * 60)
    for product in non_beverage_products:
        product_sales = Sale.objects.filter(
            product=product,
            order_date__gte=start_date
        )
        total_qty = sum([s.quantity for s in product_sales])
        days_with_sales = product_sales.values('order_date__date').distinct().count()
        
        if total_qty > 0:
            print(f"   {product.name}: {total_qty} units sold over {days_with_sales} days")
    
    print(f"\n💡 Next Step: Click 'Retrain Model' in the dashboard!")

if __name__ == '__main__':
    try:
        add_nonbeverage_sales()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()