import os
import django
from django.utils import timezone
import pytz

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.models import Product, Sale
from datetime import datetime, timedelta
import random

def add_test_sales():
    """Add test sales data for ML training"""
    
    print("\n💰 ADDING TEST SALES DATA")
    print("=" * 60)
    
    # Get beverages and other products
    beverages = Product.objects.filter(category__in=['Beverage', 'Beverages'])
    
    if not beverages.exists():
        print("❌ No beverages found in database!")
        return
    
    print(f"📊 Found {beverages.count()} beverages")
    
    # Generate sales for the last 30 days
    local_tz = pytz.timezone('Asia/Manila')
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    sales_created = 0
    
    # Popular beverages with their typical daily sales
    beverage_popularity = {
        'Cappuccino': (8, 15),      # 8-15 sales per day
        'Latte': (6, 12),
        'Espresso': (4, 8),
        'Mocha': (5, 10),
        'Caramel Macchiato': (4, 9),
        'Hot Chocolate': (3, 7),
        'Cold Coffee': (5, 11),
        'Cold Mocha': (4, 8),
        'Iced Tea': (6, 12),
        'Lemonade': (5, 10),
        'Flat White': (3, 6),
        'White Mocha': (3, 6),
    }
    
    current_date = start_date
    
    while current_date <= end_date:
        date_aware = local_tz.localize(current_date.replace(hour=12, minute=0, second=0, microsecond=0))
        
        # Create sales for each beverage
        for beverage in beverages:
            if beverage.name in beverage_popularity:
                min_qty, max_qty = beverage_popularity[beverage.name]
                quantity = random.randint(min_qty, max_qty)
                
                # Check if sale already exists
                if not Sale.objects.filter(
                    product=beverage,
                    order_date=date_aware
                ).exists():
                    Sale.objects.create(
                        product=beverage,
                        product_firebase_id=beverage.firebase_id,
                        product_name=beverage.name,
                        category=beverage.category,
                        quantity=quantity,
                        price=beverage.price,
                        total=beverage.price * quantity,
                        order_date=date_aware
                    )
                    sales_created += 1
                    
                    if sales_created % 50 == 0:
                        print(f"📊 Created {sales_created} sales...")
        
        current_date += timedelta(days=1)
    
    print(f"\n✅ Created {sales_created} test sales")
    print(f"📅 Date range: {start_date.date()} to {end_date.date()}")
    print("\n🎯 Now retrain your ML model to see predictions!")
    print("   Go to: http://127.0.0.1:8000/dashboard/inventory/forecasting/")
    print("   Click: 'Retrain Model'\n")


if __name__ == '__main__':
    try:
        add_test_sales()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()