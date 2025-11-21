"""
Sync Local Database → Firebase
================================

This script syncs data FROM your local SQLite database TO Firebase Firestore.
It carefully avoids duplicates by matching existing records.

Usage:
    python sync_local_to_firebase.py
"""

import os
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.firebase_service import FirebaseService
from dashboard.models import Product, Sale, Recipe, RecipeIngredient

# Initialize Firebase
firebase_service = FirebaseService()
db = firebase_service.db


def sync_products_to_firebase():
    """Sync products from local DB to Firebase (avoiding duplicates)"""
    print("\n📦 SYNCING PRODUCTS: LOCAL DB → FIREBASE")
    print("=" * 70)

    products = Product.objects.all()
    print(f"📊 Found {products.count()} products in local database\n")

    created = 0
    updated = 0
    skipped = 0

    for product in products:
        try:
            # Prepare product data
            product_data = {
                'name': product.name,
                'category': product.category,
                'stock': float(product.stock),
                'unit': product.unit,
                'price': float(product.price),
                'updatedAt': datetime.now(),
                'syncedFromLocal': True
            }

            # Check if product already exists in Firebase
            if product.firebase_id:
                # Product has Firebase ID - check if it exists
                try:
                    doc_ref = db.collection('products').document(product.firebase_id)
                    doc = doc_ref.get()

                    if doc.exists:
                        # Update existing document
                        doc_ref.update(product_data)
                        print(f"🔄 Updated: {product.name} (ID: {product.firebase_id})")
                        updated += 1
                    else:
                        # Firebase ID doesn't exist anymore, create new
                        doc_ref.set(product_data)
                        print(f"✅ Created: {product.name} (ID: {product.firebase_id})")
                        created += 1
                except Exception as e:
                    print(f"   ⚠️  Error checking {product.name}: {e}")
                    skipped += 1
            else:
                # No Firebase ID - check for duplicate by name
                existing = db.collection('products').where('name', '==', product.name).limit(1).get()

                if existing:
                    # Duplicate found - update it and save the ID locally
                    existing_doc = list(existing)[0]
                    firebase_id = existing_doc.id

                    db.collection('products').document(firebase_id).update(product_data)

                    # Update local product with Firebase ID
                    product.firebase_id = firebase_id
                    product.save()

                    print(f"🔄 Updated existing: {product.name} (linked ID: {firebase_id})")
                    updated += 1
                else:
                    # No duplicate - create new
                    doc_ref = db.collection('products').add(product_data)
                    firebase_id = doc_ref[1].id

                    # Save Firebase ID to local product
                    product.firebase_id = firebase_id
                    product.save()

                    print(f"✅ Created new: {product.name} (new ID: {firebase_id})")
                    created += 1

        except Exception as e:
            print(f"❌ Error syncing {product.name}: {e}")
            skipped += 1

    print(f"\n{'='*70}")
    print(f"✅ PRODUCTS SYNC COMPLETE!")
    print(f"   Created: {created}")
    print(f"   Updated: {updated}")
    print(f"   Skipped: {skipped}")
    print(f"   Total: {products.count()}")
    print(f"{'='*70}\n")


def sync_sales_to_firebase():
    """Sync sales from local DB to Firebase (avoiding duplicates)"""
    print("\n💰 SYNCING SALES: LOCAL DB → FIREBASE")
    print("=" * 70)

    sales = Sale.objects.all().order_by('-order_date')
    print(f"📊 Found {sales.count()} sales in local database\n")

    # Ask for confirmation if large dataset
    if sales.count() > 500:
        confirm = input(f"⚠️  You have {sales.count()} sales records. Sync all? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Sync cancelled")
            return

    created = 0
    updated = 0
    skipped = 0

    for sale in sales:
        try:
            # Prepare sale data
            sale_data = {
                'productName': sale.product_name,
                'category': sale.category,
                'quantity': float(sale.quantity),
                'price': float(sale.price) if sale.price else 0,
                'total': float(sale.total) if sale.total else 0,
                'orderDate': sale.order_date,
                'createdAt': sale.created_at,
                'syncedFromLocal': True
            }

            # Add product reference if available
            if sale.product and sale.product.firebase_id:
                sale_data['productFirebaseId'] = sale.product.firebase_id
            elif sale.product_firebase_id:
                sale_data['productFirebaseId'] = sale.product_firebase_id

            # Check for duplicate by matching product + date + quantity
            # (Sales rarely have unique IDs, so we check for exact matches)
            existing = db.collection('sales').where('productName', '==', sale.product_name)\
                                             .where('orderDate', '==', sale.order_date)\
                                             .where('quantity', '==', float(sale.quantity))\
                                             .limit(1).get()

            if existing:
                # Possible duplicate found - skip to avoid duplication
                skipped += 1
                if skipped <= 5:  # Only show first 5 to avoid spam
                    print(f"⏭️  Skipped (duplicate): {sale.product_name} on {sale.order_date.strftime('%Y-%m-%d')}")
            else:
                # No duplicate - create new
                db.collection('sales').add(sale_data)
                created += 1
                if created <= 10:  # Show first 10
                    print(f"✅ Created: {sale.product_name} - {sale.quantity} units on {sale.order_date.strftime('%Y-%m-%d')}")

        except Exception as e:
            if skipped + created < 10:  # Only show errors for first few
                print(f"❌ Error syncing sale {sale.id}: {e}")
            skipped += 1

    print(f"\n{'='*70}")
    print(f"✅ SALES SYNC COMPLETE!")
    print(f"   Created: {created}")
    print(f"   Skipped (duplicates): {skipped}")
    print(f"   Total processed: {sales.count()}")
    print(f"{'='*70}\n")


def sync_recipes_to_firebase():
    """Sync recipes and ingredients from local DB to Firebase"""
    print("\n🍳 SYNCING RECIPES: LOCAL DB → FIREBASE")
    print("=" * 70)

    recipes = Recipe.objects.all()
    print(f"📊 Found {recipes.count()} recipes in local database\n")

    recipes_created = 0
    recipes_updated = 0
    ingredients_synced = 0

    for recipe in recipes:
        try:
            # Prepare recipe data
            recipe_data = {
                'productName': recipe.product_name,
                'productNumber': recipe.product_number,
                'updatedAt': datetime.now(),
                'syncedFromLocal': True
            }

            # Add product reference if available
            if recipe.product and recipe.product.firebase_id:
                recipe_data['productFirebaseId'] = recipe.product.firebase_id
            elif recipe.product_firebase_id:
                recipe_data['productFirebaseId'] = recipe.product_firebase_id

            # Check if recipe already exists
            if recipe.firebase_id:
                # Has Firebase ID - update
                doc_ref = db.collection('recipes').document(recipe.firebase_id)
                doc = doc_ref.get()

                if doc.exists:
                    doc_ref.update(recipe_data)
                    print(f"🔄 Updated recipe: {recipe.product_name}")
                    recipes_updated += 1
                else:
                    doc_ref.set(recipe_data)
                    print(f"✅ Created recipe: {recipe.product_name}")
                    recipes_created += 1

                recipe_firebase_id = recipe.firebase_id
            else:
                # No Firebase ID - check for duplicate by product name
                existing = db.collection('recipes').where('productName', '==', recipe.product_name).limit(1).get()

                if existing:
                    # Duplicate found
                    existing_doc = list(existing)[0]
                    recipe_firebase_id = existing_doc.id

                    db.collection('recipes').document(recipe_firebase_id).update(recipe_data)
                    recipe.firebase_id = recipe_firebase_id
                    recipe.save()

                    print(f"🔄 Updated existing recipe: {recipe.product_name}")
                    recipes_updated += 1
                else:
                    # Create new
                    doc_ref = db.collection('recipes').add(recipe_data)
                    recipe_firebase_id = doc_ref[1].id

                    recipe.firebase_id = recipe_firebase_id
                    recipe.save()

                    print(f"✅ Created new recipe: {recipe.product_name}")
                    recipes_created += 1

            # Sync recipe ingredients
            ingredients = RecipeIngredient.objects.filter(recipe=recipe)

            for ingredient in ingredients:
                try:
                    ingredient_data = {
                        'recipeFirebaseId': recipe_firebase_id,
                        'ingredientName': ingredient.ingredient_name,
                        'quantityNeeded': float(ingredient.quantity_needed),
                        'unit': ingredient.unit,
                        'syncedFromLocal': True
                    }

                    # Add ingredient reference if available
                    if ingredient.ingredient and ingredient.ingredient.firebase_id:
                        ingredient_data['ingredientFirebaseId'] = ingredient.ingredient.firebase_id
                    elif ingredient.ingredient_firebase_id:
                        ingredient_data['ingredientFirebaseId'] = ingredient.ingredient_firebase_id

                    # Check for duplicate ingredient
                    existing_ing = db.collection('recipe_ingredients')\
                                     .where('recipeFirebaseId', '==', recipe_firebase_id)\
                                     .where('ingredientName', '==', ingredient.ingredient_name)\
                                     .limit(1).get()

                    if existing_ing:
                        # Update existing
                        existing_doc = list(existing_ing)[0]
                        db.collection('recipe_ingredients').document(existing_doc.id).update(ingredient_data)
                    else:
                        # Create new
                        db.collection('recipe_ingredients').add(ingredient_data)

                    ingredients_synced += 1

                except Exception as e:
                    print(f"   ⚠️  Error syncing ingredient {ingredient.ingredient_name}: {e}")

        except Exception as e:
            print(f"❌ Error syncing recipe {recipe.product_name}: {e}")

    print(f"\n{'='*70}")
    print(f"✅ RECIPES SYNC COMPLETE!")
    print(f"   Recipes created: {recipes_created}")
    print(f"   Recipes updated: {recipes_updated}")
    print(f"   Ingredients synced: {ingredients_synced}")
    print(f"{'='*70}\n")


def main():
    """Main sync function"""
    print("=" * 70)
    print("SYNC LOCAL DATABASE → FIREBASE")
    print("Carefully avoiding duplicates")
    print("=" * 70)

    try:
        # Show what we're about to sync
        products_count = Product.objects.count()
        sales_count = Sale.objects.count()
        recipes_count = Recipe.objects.count()

        print(f"\n📊 LOCAL DATABASE STATUS:")
        print(f"   Products: {products_count}")
        print(f"   Sales: {sales_count}")
        print(f"   Recipes: {recipes_count}")

        # Ask for confirmation
        print(f"\n⚠️  This will sync your local data to Firebase.")
        print(f"   Existing Firebase records will be UPDATED if matches found.")
        print(f"   New records will be CREATED if no duplicates exist.")

        confirm = input(f"\n   Proceed? (y/n): ")

        if confirm.lower() != 'y':
            print("\n❌ Sync cancelled by user")
            return

        # Sync in order
        print("\n🚀 Starting sync...\n")

        # 1. Sync products first (needed for references)
        sync_products_to_firebase()

        # 2. Sync recipes (needs products)
        sync_recipes_to_firebase()

        # 3. Sync sales (can be large)
        sync_sales_to_firebase()

        print("\n" + "=" * 70)
        print("🎉 ALL SYNC OPERATIONS COMPLETE!")
        print("=" * 70)
        print("\n✅ Your Firebase database is now up to date with local data!")
        print("✅ No duplicates were created (checked before inserting)")
        print("\n📱 You can now:")
        print("   - Check Firebase Console to verify")
        print("   - Use your mobile app with latest data")
        print("   - Continue using the system normally")
        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Sync interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
