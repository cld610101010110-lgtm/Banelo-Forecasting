import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.models import Product, Recipe, RecipeIngredient
import uuid

def create_ingredients():
    """Create ingredient products if they don't exist"""
    print("\n📦 CREATING INGREDIENT PRODUCTS")
    print("=" * 60)
    
    ingredients_data = {
        'Coffee Beans': {'unit': 'g', 'category': 'Ingredients', 'stock': 5000, 'price': 500},
        'Milk': {'unit': 'ml', 'category': 'Ingredients', 'stock': 10000, 'price': 150},
        'Water': {'unit': 'ml', 'category': 'Ingredients', 'stock': 20000, 'price': 0},
        'Sugar': {'unit': 'g', 'category': 'Ingredients', 'stock': 2000, 'price': 50},
        'Chocolate Syrup': {'unit': 'ml', 'category': 'Ingredients', 'stock': 1000, 'price': 200},
        'White Chocolate Syrup': {'unit': 'ml', 'category': 'Ingredients', 'stock': 500, 'price': 250},
        'Vanilla Syrup': {'unit': 'ml', 'category': 'Ingredients', 'stock': 500, 'price': 180},
        'Caramel Syrup': {'unit': 'ml', 'category': 'Ingredients', 'stock': 500, 'price': 180},
        'Whipped Cream': {'unit': 'ml', 'category': 'Ingredients', 'stock': 1000, 'price': 120},
        'Chocolate Powder': {'unit': 'g', 'category': 'Ingredients', 'stock': 1000, 'price': 300},
        'Ice': {'unit': 'g', 'category': 'Ingredients', 'stock': 5000, 'price': 20},
        'Tea Bags': {'unit': 'pcs', 'category': 'Ingredients', 'stock': 200, 'price': 5},
        'Lemon Juice': {'unit': 'ml', 'category': 'Ingredients', 'stock': 500, 'price': 80},
    }
    
    created_ingredients = {}
    
    for name, data in ingredients_data.items():
        ingredient, created = Product.objects.get_or_create(
            name=name,
            defaults={
                'firebase_id': f'ingredient_{uuid.uuid4().hex[:8]}',
                'category': data['category'],
                'unit': data['unit'],
                'stock': data['stock'],
                'price': data['price']
            }
        )
        
        created_ingredients[name] = ingredient
        
        if created:
            print(f"✅ Created: {name} (Stock: {data['stock']}{data['unit']})")
        else:
            # Update stock if exists
            ingredient.stock = data['stock']
            ingredient.save()
            print(f"🔄 Updated: {name} (Stock: {data['stock']}{data['unit']})")
    
    print(f"\n📊 Total ingredients: {len(created_ingredients)}")
    return created_ingredients


def create_recipes():
    """Create recipes for all beverages"""
    print("\n☕ CREATING BEVERAGE RECIPES")
    print("=" * 60)
    
    # Recipe definitions: beverage_name -> [(ingredient_name, quantity, unit), ...]
    recipes_data = {
        'Espresso': [
            ('Coffee Beans', 18, 'g'),
            ('Water', 30, 'ml'),
        ],
        'Cappuccino': [
            ('Coffee Beans', 18, 'g'),
            ('Milk', 200, 'ml'),
        ],
        'Latte': [
            ('Coffee Beans', 18, 'g'),
            ('Milk', 260, 'ml'),
        ],
        'Flat White': [
            ('Coffee Beans', 18, 'g'),
            ('Milk', 190, 'ml'),
        ],
        'Mocha': [
            ('Coffee Beans', 18, 'g'),
            ('Milk', 180, 'ml'),
            ('Chocolate Syrup', 30, 'ml'),
            ('Whipped Cream', 20, 'ml'),
        ],
        'White Mocha': [
            ('Coffee Beans', 18, 'g'),
            ('Milk', 180, 'ml'),
            ('White Chocolate Syrup', 30, 'ml'),
            ('Whipped Cream', 20, 'ml'),
        ],
        'Caramel Macchiato': [
            ('Coffee Beans', 18, 'g'),
            ('Milk', 240, 'ml'),
            ('Vanilla Syrup', 15, 'ml'),
            ('Caramel Syrup', 15, 'ml'),
        ],
        'Hot Chocolate': [
            ('Milk', 240, 'ml'),
            ('Chocolate Powder', 30, 'g'),
            ('Whipped Cream', 20, 'ml'),
        ],
        'Cold Coffee': [
            ('Coffee Beans', 18, 'g'),
            ('Ice', 100, 'g'),
            ('Milk', 200, 'ml'),
            ('Sugar', 10, 'g'),
        ],
        'Cold Mocha': [
            ('Coffee Beans', 18, 'g'),
            ('Ice', 100, 'g'),
            ('Milk', 180, 'ml'),
            ('Chocolate Syrup', 30, 'ml'),
            ('Whipped Cream', 20, 'ml'),
        ],
        'Iced Tea': [
            ('Tea Bags', 1, 'pcs'),
            ('Water', 300, 'ml'),
            ('Sugar', 15, 'g'),
            ('Ice', 50, 'g'),
        ],
        'Lemonade': [
            ('Lemon Juice', 60, 'ml'),
            ('Water', 240, 'ml'),
            ('Sugar', 30, 'g'),
            ('Ice', 50, 'g'),
        ],
    }
    
    # Get all ingredients
    ingredients = {ing.name: ing for ing in Product.objects.filter(category='Ingredients')}
    
    recipes_created = 0
    recipes_updated = 0
    total_ingredients_added = 0
    
    for beverage_name, ingredients_list in recipes_data.items():
        try:
            # Get the beverage product
            try:
                beverage = Product.objects.get(name=beverage_name)
            except Product.DoesNotExist:
                print(f"⚠️  Beverage not found: {beverage_name} - skipping")
                continue
            
            # Create or get recipe
            recipe, created = Recipe.objects.get_or_create(
                product=beverage,
                defaults={
                    'firebase_id': f'recipe_{uuid.uuid4().hex[:8]}',
                    'product_firebase_id': beverage.firebase_id or f'prod_{uuid.uuid4().hex[:8]}',
                    'product_number': 0,
                    'product_name': beverage_name
                }
            )
            
            if created:
                recipes_created += 1
                print(f"\n✅ Created Recipe: {beverage_name}")
            else:
                # Clear existing ingredients
                recipe.ingredients.all().delete()
                recipes_updated += 1
                print(f"\n🔄 Updated Recipe: {beverage_name}")
            
            # Add ingredients
            for ingredient_name, quantity, unit in ingredients_list:
                if ingredient_name in ingredients:
                    ingredient_product = ingredients[ingredient_name]
                    
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient_product,
                        ingredient_firebase_id=ingredient_product.firebase_id or f'ing_{uuid.uuid4().hex[:8]}',
                        ingredient_name=ingredient_name,
                        quantity_needed=quantity,
                        unit=unit,
                        recipe_firebase_id=recipe.firebase_id
                    )
                    
                    total_ingredients_added += 1
                    print(f"   + {quantity}{unit} {ingredient_name}")
                else:
                    print(f"   ⚠️  Ingredient not found: {ingredient_name}")
                    
        except Exception as e:
            print(f"❌ Error creating recipe for {beverage_name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Created: {recipes_created} recipes")
    print(f"   🔄 Updated: {recipes_updated} recipes")
    print(f"   📝 Total ingredients added: {total_ingredients_added}")
    print("=" * 60)
    print("\n✅ ALL RECIPES CREATED!\n")


def main():
    """Main function to create ingredients and recipes"""
    try:
        print("\n" + "="*60)
        print("🍳 BEVERAGE RECIPES SETUP (LOCAL DATABASE)")
        print("="*60)
        
        # Step 1: Create ingredients
        ingredients = create_ingredients()
        
        # Step 2: Create recipes
        create_recipes()
        
        # Step 3: Summary
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   - {Product.objects.filter(category='Ingredients').count()} ingredients in database")
        print(f"   - {Recipe.objects.count()} recipes created")
        print(f"   - {RecipeIngredient.objects.count()} recipe ingredients added")
        print("\n🎯 Next: Train your ML model to see ingredient forecasting!")
        print("   Go to: http://127.0.0.1:8000/dashboard/inventory/forecasting/")
        print("   Click: 'Train Model'\n")
        
    except Exception as e:
        print(f"\n❌ SETUP FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()