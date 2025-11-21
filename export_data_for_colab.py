"""
Export Data for Google Colab ML Training
=========================================

This script exports data from SQLite database to CSV files for training
machine learning models in Google Colab.

Output Files:
- sales_data.csv: Historical sales transactions
- products_data.csv: Product inventory information
- recipes_data.csv: Beverage recipes
- recipe_ingredients.csv: Recipe ingredient mappings

Usage:
    python export_data_for_colab.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
import csv

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.models import Product, Sale, Recipe, RecipeIngredient

# Create output directory
OUTPUT_DIR = 'exported_data'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def export_sales_data(days=90):
    """Export sales data from last N days"""
    print(f"\n📊 Exporting sales data (last {days} days)...")

    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Query sales
    sales = Sale.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    ).select_related('product').order_by('order_date')

    # Export to CSV
    filepath = os.path.join(OUTPUT_DIR, 'sales_data.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'sale_id',
            'product_id',
            'product_firebase_id',
            'product_name',
            'category',
            'quantity',
            'price',
            'total',
            'order_date',
            'created_at'
        ])

        # Data rows
        count = 0
        for sale in sales:
            writer.writerow([
                sale.id,
                sale.product_id if sale.product else '',
                sale.product_firebase_id or '',
                sale.product_name,
                sale.category,
                sale.quantity,
                sale.price or 0,
                sale.total or 0,
                sale.order_date.strftime('%Y-%m-%d %H:%M:%S'),
                sale.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            count += 1

    print(f"   ✓ Exported {count} sales records to {filepath}")
    return count


def export_products_data():
    """Export product inventory data"""
    print("\n📦 Exporting products data...")

    products = Product.objects.all().order_by('category', 'name')

    filepath = os.path.join(OUTPUT_DIR, 'products_data.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'product_id',
            'firebase_id',
            'name',
            'category',
            'stock',
            'unit',
            'price',
            'created_at',
            'updated_at'
        ])

        # Data rows
        count = 0
        for product in products:
            writer.writerow([
                product.id,
                product.firebase_id or '',
                product.name,
                product.category,
                product.stock,
                product.unit,
                product.price,
                product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                product.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            count += 1

    print(f"   ✓ Exported {count} products to {filepath}")
    return count


def export_recipes_data():
    """Export recipe data"""
    print("\n🧪 Exporting recipes data...")

    recipes = Recipe.objects.all().select_related('product').order_by('product_name')

    filepath = os.path.join(OUTPUT_DIR, 'recipes_data.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'recipe_id',
            'firebase_id',
            'product_id',
            'product_firebase_id',
            'product_number',
            'product_name',
            'created_at',
            'updated_at'
        ])

        # Data rows
        count = 0
        for recipe in recipes:
            writer.writerow([
                recipe.id,
                recipe.firebase_id or '',
                recipe.product_id if recipe.product else '',
                recipe.product_firebase_id or '',
                recipe.product_number,
                recipe.product_name,
                recipe.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                recipe.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            count += 1

    print(f"   ✓ Exported {count} recipes to {filepath}")
    return count


def export_recipe_ingredients_data():
    """Export recipe ingredients data"""
    print("\n🥤 Exporting recipe ingredients data...")

    ingredients = RecipeIngredient.objects.all().select_related(
        'recipe', 'ingredient'
    ).order_by('recipe__product_name', 'ingredient_name')

    filepath = os.path.join(OUTPUT_DIR, 'recipe_ingredients.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'ingredient_id',
            'recipe_id',
            'recipe_firebase_id',
            'ingredient_product_id',
            'ingredient_firebase_id',
            'ingredient_name',
            'quantity_needed',
            'unit',
            'created_at'
        ])

        # Data rows
        count = 0
        for ingredient in ingredients:
            writer.writerow([
                ingredient.id,
                ingredient.recipe_id,
                ingredient.recipe_firebase_id or '',
                ingredient.ingredient_id if ingredient.ingredient else '',
                ingredient.ingredient_firebase_id or '',
                ingredient.ingredient_name,
                ingredient.quantity_needed,
                ingredient.unit,
                ingredient.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            count += 1

    print(f"   ✓ Exported {count} recipe ingredients to {filepath}")
    return count


def export_aggregated_features():
    """Export pre-aggregated features for ML training"""
    print("\n📈 Generating aggregated features...")

    from django.db.models import Sum, Avg, Count, Max, Min
    from django.db.models.functions import TruncDate

    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    # Aggregate daily sales by product
    daily_sales = Sale.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    ).annotate(
        date=TruncDate('order_date')
    ).values(
        'date', 'product_id', 'product_name', 'category'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total'),
        num_transactions=Count('id'),
        avg_price=Avg('price'),
        max_quantity=Max('quantity'),
        min_quantity=Min('quantity')
    ).order_by('date', 'product_name')

    filepath = os.path.join(OUTPUT_DIR, 'daily_sales_aggregated.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'date',
            'product_id',
            'product_name',
            'category',
            'total_quantity',
            'total_revenue',
            'num_transactions',
            'avg_price',
            'max_quantity',
            'min_quantity'
        ])

        # Data rows
        count = 0
        for row in daily_sales:
            writer.writerow([
                row['date'].strftime('%Y-%m-%d'),
                row['product_id'],
                row['product_name'],
                row['category'],
                row['total_quantity'],
                row['total_revenue'] or 0,
                row['num_transactions'],
                row['avg_price'] or 0,
                row['max_quantity'],
                row['min_quantity']
            ])
            count += 1

    print(f"   ✓ Generated {count} daily aggregates to {filepath}")
    return count


def generate_metadata():
    """Generate metadata file with export information"""
    print("\n📝 Generating metadata...")

    filepath = os.path.join(OUTPUT_DIR, 'export_metadata.txt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("DATA EXPORT METADATA\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Export Directory: {OUTPUT_DIR}\n\n")

        f.write("Exported Files:\n")
        f.write("-" * 60 + "\n")

        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.csv'):
                filepath = os.path.join(OUTPUT_DIR, filename)
                size = os.path.getsize(filepath)
                f.write(f"  - {filename} ({size:,} bytes)\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("Next Steps:\n")
        f.write("=" * 60 + "\n")
        f.write("1. Upload CSV files to Google Colab\n")
        f.write("2. Open forecasting_model_training.ipynb\n")
        f.write("3. Train your ML model\n")
        f.write("4. Download forecasting_model.pkl\n")
        f.write("5. Run: python integrate_ml_model.py\n")
        f.write("=" * 60 + "\n")

    print(f"   ✓ Metadata saved to {filepath}")


def main():
    """Main export function"""
    print("=" * 60)
    print("DATA EXPORT FOR GOOGLE COLAB ML TRAINING")
    print("=" * 60)

    try:
        # Export all data
        sales_count = export_sales_data(days=90)
        products_count = export_products_data()
        recipes_count = export_recipes_data()
        ingredients_count = export_recipe_ingredients_data()
        aggregated_count = export_aggregated_features()

        # Generate metadata
        generate_metadata()

        # Summary
        print("\n" + "=" * 60)
        print("EXPORT COMPLETE! 🎉")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   - Sales records: {sales_count}")
        print(f"   - Products: {products_count}")
        print(f"   - Recipes: {recipes_count}")
        print(f"   - Recipe ingredients: {ingredients_count}")
        print(f"   - Daily aggregates: {aggregated_count}")
        print(f"\n📁 Output directory: {OUTPUT_DIR}/")
        print(f"\n✅ Files ready for upload to Google Colab!")
        print(f"\n📖 Next: Open forecasting_model_training.ipynb in Colab")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error during export: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
