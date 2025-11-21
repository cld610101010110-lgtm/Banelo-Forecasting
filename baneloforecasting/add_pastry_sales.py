import os
import django
from django.utils import timezone
import pytz

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.models import Product, Sale
from datetime import datetime, timedelta
import random

def add_pastry_sales():
    """Add sales for new pastries"""
    
    print("\n🥐 ADDING PASTRY SALES DATA")
    print("=" * 60)
    
    # Get the new pastries by name
    pastry_names = [
        'Croissant',
        'Blueberry Muffin', 
        'Chocolate Chip Cookie',
        'Cinnamon Roll',
        'Banana Bread'
    ]
    
    pastries = Product.objects.filter(name__in=pastry_names)
    
    print(f"📦 Found {pastries.count()} pastries to add sales for:")
    for p in pastries:
        print(f"   - {p.name} (Category: {p.category})")
    
    if pastries.count() == 0:
        print("\n⚠️  No pastries found! Make sure they were created first.")
        return
    
    local_tz = pytz.timezone('Asia/Manila')
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # 30 days of data
    
    sales_created = 0
    current_date = start_date
    
    print(f"\n🗓️  Generating sales from {start_date.date()} to {end_date.date()}")
    print("=" * 60)
    
    while current_date <= end_date:
        for product in pastries:
            # 80% chance of sales on any given day
            if random.random() < 0.8:
                # Random time during business hours (8 AM - 8 PM)
                hour = random.randint(8, 20)
                minute = random.randint(0, 59)
                
                date_aware = local_tz.localize(
                    current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                )
                
                # 3-8 pastries sold per day
                quantity = random.randint(3, 8)
                
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
                
                if sales_created % 20 == 0:
                    print(f"   Created {sales_created} sales...")
        
        current_date += timedelta(days=1)
    
    print(f"\n✅ COMPLETED!")
    print(f"📊 Total sales created: {sales_created}")
    
    # Show summary
    print(f"\n📈 Sales Summary:")
    print("=" * 60)
    for product in pastries:
        product_sales = Sale.objects.filter(
            product=product,
            order_date__gte=start_date
        )
        total_qty = sum([s.quantity for s in product_sales])
        days_with_sales = product_sales.values('order_date__date').distinct().count()
        
        print(f"   {product.name}: {total_qty} units over {days_with_sales} days")
    
    print(f"\n💡 Next: Click 'Train Model' to update forecasts!")

if __name__ == '__main__':
    try:
        add_pastry_sales()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()