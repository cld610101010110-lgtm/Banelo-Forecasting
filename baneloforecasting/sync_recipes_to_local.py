import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.firebase_service import FirebaseService
from dashboard.models import Product, Recipe, RecipeIngredient

# Initialize Firebase
db = FirebaseService().db

def sync_recipes():
    """Sync recipes and recipe ingredients from Firebase to local DB"""
    
    print("\n🍳 SYNCING RECIPES FROM FIREBASE TO LOCAL DB")
    print("=" * 60)
    
    # Get all recipes from Firebase
    recipes_ref = db.collection('recipes')
    recipes_docs = list(recipes_ref.stream())
    
    print(f"📊 Found {len(recipes_docs)} recipes in Firebase")
    
    recipes_synced = 0
    recipes_updated = 0
    
    for doc in recipes_docs:
        try:
            recipe_data = doc.to_dict()
            recipe_firebase_id = doc.id
            
            print(f"\n📝 Processing: {recipe_data.get('productName', 'Unknown')}")
            
            # Get or create local product reference
            product_firebase_id = recipe_data.get('productFirebaseId', '')
            product = None
            
            if product_firebase_id:
                try:
                    product = Product.objects.get(firebase_id=product_firebase_id)
                    print(f"   ✅ Found product: {product.name}")
                except Product.DoesNotExist:
                    print(f"   ⚠️  Product not found in local DB: {recipe_data.get('productName')}")
            
            # Create or update recipe
            recipe, created = Recipe.objects.update_or_create(
                firebase_id=recipe_firebase_id,
                defaults={
                    'product': product,
                    'product_firebase_id': product_firebase_id,
                    'product_number': recipe_data.get('productId', 0),
                    'product_name': recipe_data.get('productName', 'Unknown'),
                }
            )
            
            if created:
                recipes_synced += 1
                print(f"   ✅ Created recipe")
            else:
                recipes_updated += 1
                print(f"   🔄 Updated recipe")
            
        except Exception as e:
            print(f"   ❌ Error processing recipe: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n📊 Recipes: {recipes_synced} created, {recipes_updated} updated")
    
    # Now sync recipe ingredients
    print("\n🥤 SYNCING RECIPE INGREDIENTS FROM FIREBASE")
    print("=" * 60)
    
    ingredients_ref = db.collection('recipe_ingredients')
    ingredients_docs = list(ingredients_ref.stream())
    
    print(f"📊 Found {len(ingredients_docs)} recipe ingredients in Firebase")
    
    ingredients_synced = 0
    ingredients_updated = 0
    ingredients_skipped = 0
    
    for doc in ingredients_docs:
        try:
            ingredient_data = doc.to_dict()
            ingredient_doc_id = doc.id
            
            # Get recipe
            recipe_firebase_id = ingredient_data.get('recipeFirebaseId', '')
            
            if not recipe_firebase_id:
                print(f"   ⚠️  No recipeFirebaseId in ingredient")
                ingredients_skipped += 1
                continue
            
            try:
                recipe = Recipe.objects.get(firebase_id=recipe_firebase_id)
            except Recipe.DoesNotExist:
                print(f"   ⚠️  Recipe not found: {recipe_firebase_id}")
                ingredients_skipped += 1
                continue
            
            # Get ingredient product
            ingredient_firebase_id = ingredient_data.get('ingredientFirebaseId', '')
            ingredient_product = None
            
            if ingredient_firebase_id:
                try:
                    ingredient_product = Product.objects.get(firebase_id=ingredient_firebase_id)
                except Product.DoesNotExist:
                    print(f"   ⚠️  Ingredient not found: {ingredient_data.get('ingredientName')}")
            
            # Create or update recipe ingredient
            recipe_ingredient, created = RecipeIngredient.objects.update_or_create(
                recipe=recipe,
                ingredient_firebase_id=ingredient_firebase_id,
                defaults={
                    'ingredient': ingredient_product,
                    'ingredient_name': ingredient_data.get('ingredientName', 'Unknown'),
                    'quantity_needed': float(ingredient_data.get('quantityNeeded', 0)),
                    'unit': ingredient_data.get('unit', 'g'),
                    'recipe_firebase_id': recipe_firebase_id,
                }
            )
            
            if created:
                ingredients_synced += 1
                print(f"   ✅ {ingredient_data.get('ingredientName')} - {ingredient_data.get('quantityNeeded')}{ingredient_data.get('unit')}")
            else:
                ingredients_updated += 1
                print(f"   🔄 {ingredient_data.get('ingredientName')} - {ingredient_data.get('quantityNeeded')}{ingredient_data.get('unit')}")
            
        except Exception as e:
            print(f"   ❌ Error processing ingredient: {str(e)}")
            import traceback
            traceback.print_exc()
            ingredients_skipped += 1
            continue
    
    print(f"\n📊 Recipe Ingredients:")
    print(f"   ✅ Created: {ingredients_synced}")
    print(f"   🔄 Updated: {ingredients_updated}")
    print(f"   ⏭️  Skipped: {ingredients_skipped}")
    print("\n✅ RECIPE SYNC COMPLETE!\n")


if __name__ == '__main__':
    try:
        sync_recipes()
    except Exception as e:
        print(f"\n❌ SYNC FAILED: {str(e)}")
        import traceback
        traceback.print_exc()