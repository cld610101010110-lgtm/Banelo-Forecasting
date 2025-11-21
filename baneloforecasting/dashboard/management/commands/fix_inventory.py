# dashboard/management/commands/fix_inventory.py
# Create this file in: dashboard/management/commands/fix_inventory.py
# Run with: python manage.py fix_inventory

from django.core.management.base import BaseCommand
from dashboard.models import Product, Recipe, RecipeIngredient
from django.db import transaction

class Command(BaseCommand):
    help = 'Fix pastries stock and update beverage recipes (remove water, tea bags, ice)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting inventory fix...'))
        
        # ===== STEP 1: Add stock to pastries =====
        self.stdout.write('\n1. Adding stock to pastries...')
        
        pastries_to_update = [
            {'name': 'Sandwich Ham&Cheese', 'stock': 50, 'unit': 'pcs'},
            {'name': 'Sandwich Salami&Mozzarella', 'stock': 50, 'unit': 'pcs'},
        ]
        
        for pastry_data in pastries_to_update:
            try:
                pastry = Product.objects.get(name=pastry_data['name'])
                pastry.stock = pastry_data['stock']
                pastry.unit = pastry_data['unit']
                pastry.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Updated {pastry.name}: {pastry.stock} {pastry.unit}"
                    )
                )
            except Product.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"  ! Pastry '{pastry_data['name']}' not found")
                )
        
        # ===== STEP 2: Remove easy-to-acquire ingredients from recipes =====
        self.stdout.write('\n2. Removing easy-to-acquire ingredients from beverage recipes...')
        
        # Ingredients to remove: water, tea bags, ice, etc.
        ingredients_to_remove = [
            'water',
            'tea bag',
            'ice',
            'tea bags',
            'iced',
            'cold water',
            'hot water',
        ]
        
        # Get all beverage products
        beverages = Product.objects.filter(category__iexact='beverages')
        
        removed_count = 0
        for beverage in beverages:
            try:
                # Get recipe for this beverage
                recipe = Recipe.objects.filter(product=beverage).first()
                
                if recipe:
                    # Get recipe ingredients
                    recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
                    
                    for recipe_ing in recipe_ingredients:
                        ingredient_name = recipe_ing.ingredient.name.lower()
                        
                        # Check if this ingredient should be removed
                        should_remove = any(
                            remove_word in ingredient_name 
                            for remove_word in ingredients_to_remove
                        )
                        
                        if should_remove:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ✗ Removing '{recipe_ing.ingredient.name}' from {beverage.name}"
                                )
                            )
                            recipe_ing.delete()
                            removed_count += 1
                            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ! Error processing {beverage.name}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\n  ✓ Removed {removed_count} easy-to-acquire ingredients")
        )
        
        # ===== STEP 3: Display updated beverage recipes =====
        self.stdout.write('\n3. Current beverage recipes:')
        
        for beverage in beverages:
            recipe = Recipe.objects.filter(product=beverage).first()
            
            if recipe:
                ingredients = RecipeIngredient.objects.filter(recipe=recipe)
                
                self.stdout.write(f"\n  📋 {beverage.name}:")
                
                if ingredients.exists():
                    for ing in ingredients:
                        self.stdout.write(
                            f"     - {ing.ingredient.name}: {ing.quantity} {ing.ingredient.unit}"
                        )
                else:
                    self.stdout.write(self.style.WARNING("     (No ingredients)"))
        
        # ===== STEP 4: Verify pastries have stock =====
        self.stdout.write('\n4. Verifying pastries stock:')
        
        pastries = Product.objects.filter(category__iexact='pastries')
        
        for pastry in pastries:
            status = "✓" if pastry.stock > 0 else "✗"
            style = self.style.SUCCESS if pastry.stock > 0 else self.style.ERROR
            
            self.stdout.write(
                style(f"  {status} {pastry.name}: {pastry.stock} {pastry.unit}")
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Inventory fix completed!')
        )