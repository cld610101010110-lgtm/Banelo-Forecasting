from django.db import models
from django.utils import timezone

class Product(models.Model):
    firebase_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    stock = models.FloatField(default=0)  # Legacy field - now using inventoryA and inventoryB
    unit = models.CharField(max_length=50, default='pcs')
    price = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # New inventory fields for dual inventory system
    inventory_a = models.FloatField(default=0, help_text='Main Warehouse Stock')
    inventory_b = models.FloatField(default=0, help_text='Expendable Stock (used for orders)')
    cost_per_unit = models.FloatField(default=0, help_text='Cost per unit for ingredients')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'products'


class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales', null=True)
    product_firebase_id = models.CharField(max_length=100, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    quantity = models.FloatField()
    price = models.FloatField(null=True, blank=True)  # ← ADD null=True, blank=True
    total = models.FloatField(null=True, blank=True)
    order_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product_name} - {self.quantity} - {self.order_date}"
    
    class Meta:
        db_table = 'sales'
        ordering = ['-order_date']


class MLPrediction(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='ml_prediction')
    predicted_daily_usage = models.FloatField()
    avg_daily_usage = models.FloatField()
    trend = models.FloatField()
    confidence_score = models.FloatField()
    data_points = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - Prediction"
    
    class Meta:
        db_table = 'ml_predictions'

class MLModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_trained = models.BooleanField(default=False)
    last_trained = models.DateTimeField(null=True, blank=True)
    total_records = models.IntegerField(default=0)
    products_analyzed = models.IntegerField(default=0)
    predictions_generated = models.IntegerField(default=0)
    accuracy = models.IntegerField(default=85)
    model_type = models.CharField(max_length=200, default='Linear Regression (Moving Average)')
    training_period_days = models.IntegerField(default=90)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'ml_models'


class Recipe(models.Model):
    # Match Firebase structure
    firebase_id = models.CharField(max_length=100, unique=True, db_index=True)  # Recipe's own Firebase ID
    product_firebase_id = models.CharField(max_length=100, db_index=True)  # Reference to product
    product_number = models.IntegerField(default=0)  # ← CHANGED from product_id to product_number
    product_name = models.CharField(max_length=200)
    
    # Local fields
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recipes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Recipe: {self.product_name}"
    
    class Meta:
        db_table = 'recipes'


class RecipeIngredient(models.Model):
    # Match Firebase structure
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    ingredient_firebase_id = models.CharField(max_length=100, db_index=True)
    ingredient_name = models.CharField(max_length=200)
    quantity_needed = models.FloatField()
    unit = models.CharField(max_length=50, default='g')
    recipe_firebase_id = models.CharField(max_length=100, db_index=True)
    
    # Local fields
    ingredient = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='used_in_recipes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.recipe.product_name} - {self.ingredient_name}: {self.quantity_needed} {self.unit}"
    
    class Meta:
        db_table = 'recipe_ingredients'