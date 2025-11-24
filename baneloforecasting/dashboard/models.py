from django.db import models
from django.utils import timezone


# =====================================================
# MODELS SHARED WITH MOBILE APP (PostgreSQL)
# These tables are created and managed by the mobile Room database
# managed = False means Django won't try to create/modify these tables
# =====================================================

class Product(models.Model):
    """
    Product model - matches SQLite database schema
    """
    # Primary key
    id = models.AutoField(primary_key=True)

    # Firebase reference ID
    firebase_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    # Product details
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    price = models.FloatField(default=0)
    unit = models.CharField(max_length=50, default='pcs')

    # Stock/Quantity fields - use 'stock' as the main stock field since SQLite has 'stock' column
    stock = models.FloatField(default=0)

    # Dual inventory system
    inventory_a = models.FloatField(
        default=0,
        help_text='Main Warehouse Stock'
    )
    inventory_b = models.FloatField(
        default=0,
        help_text='Expendable Stock (used for orders)'
    )
    cost_per_unit = models.FloatField(
        default=0,
        help_text='Cost per unit for ingredients'
    )

    # Image URI - stored in a separate column or as part of product
    image_uri = models.TextField(
        null=True,
        blank=True,
        db_column='image_uri'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True
    )

    # Property to get quantity (alias for stock for backward compatibility)
    @property
    def quantity(self):
        return self.stock

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'products'
        managed = True  # Django will manage this table


class Sale(models.Model):
    """
    Sale model - matches SQLite database schema
    """
    id = models.AutoField(primary_key=True)

    # Product reference
    product_firebase_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    product_name = models.CharField(
        max_length=255
    )

    # Sale details
    category = models.CharField(max_length=100)
    quantity = models.FloatField()
    price = models.FloatField(null=True, blank=True)
    total = models.FloatField(null=True, blank=True)

    # Order date
    order_date = models.DateTimeField()

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.product_name} - {self.quantity} - {self.order_date}"

    class Meta:
        db_table = 'sales'
        managed = True  # Django will manage this table
        ordering = ['-order_date']


class Recipe(models.Model):
    """
    Recipe model - matches SQLite database schema
    """
    id = models.AutoField(primary_key=True)

    # Firebase IDs
    firebase_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    product_firebase_id = models.CharField(
        max_length=255,
        db_index=True
    )

    # Product info
    product_name = models.CharField(
        max_length=255
    )
    product_number = models.IntegerField(
        default=0
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Recipe: {self.product_name}"

    class Meta:
        db_table = 'recipes'
        managed = True  # Django will manage this table


class RecipeIngredient(models.Model):
    """
    RecipeIngredient model - matches SQLite database schema
    """
    id = models.AutoField(primary_key=True)

    # Firebase IDs
    recipe_firebase_id = models.CharField(
        max_length=255,
        db_index=True
    )
    ingredient_firebase_id = models.CharField(
        max_length=255,
        db_index=True
    )

    # Ingredient details
    ingredient_name = models.CharField(
        max_length=255
    )
    quantity_needed = models.FloatField()
    unit = models.CharField(max_length=50, default='g')

    # Recipe foreign key
    recipe_id = models.IntegerField(
        null=True,
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.ingredient_name}: {self.quantity_needed} {self.unit}"

    class Meta:
        db_table = 'recipe_ingredients'
        managed = True  # Django will manage this table


# =====================================================
# MODELS FOR WASTE TRACKING (May be mobile or web-only)
# =====================================================

class WasteLog(models.Model):
    """
    Waste tracking model - for tracking product waste/spoilage
    Set managed = False if mobile app manages this table
    """
    id = models.AutoField(primary_key=True)

    # Product reference
    product_firebase_id = models.CharField(
        max_length=255,
        db_column='productFirebaseId'
    )
    product_name = models.CharField(
        max_length=255,
        db_column='productName'
    )

    # Waste details
    quantity = models.FloatField()
    reason = models.CharField(max_length=255)  # e.g., 'Expired', 'Damaged', 'Spoiled'
    category = models.CharField(max_length=100, null=True, blank=True)

    # Recording info
    waste_date = models.DateTimeField(db_column='wasteDate')
    recorded_by = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column='recordedBy'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        db_column='createdAt'
    )

    def __str__(self):
        return f"{self.product_name} - {self.quantity} - {self.reason}"

    class Meta:
        db_table = 'waste_logs'
        managed = True  # Django will create this table if needed
        ordering = ['-waste_date']


# =====================================================
# MODELS FOR AUDIT TRAIL (Web-only typically)
# =====================================================

class AuditTrail(models.Model):
    """
    Audit trail model - for tracking user actions
    """
    id = models.AutoField(primary_key=True)

    # Action details
    action = models.CharField(max_length=255)  # e.g., 'Product Updated', 'Sale Created'
    details = models.TextField(null=True, blank=True)

    # User info
    user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column='userId'
    )
    user_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_column='userName'
    )

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user_name} at {self.timestamp}"

    class Meta:
        db_table = 'audit_trail'
        managed = True  # Django will create this table
        ordering = ['-timestamp']


# =====================================================
# DJANGO-MANAGED MODELS (For ML/Forecasting)
# These tables are created and managed by Django
# =====================================================

class MLPrediction(models.Model):
    """
    ML Prediction model - stores forecasting predictions
    Managed by Django, not mobile app
    """
    id = models.AutoField(primary_key=True)

    # Product reference (by firebase_id since Product uses managed=False)
    product_firebase_id = models.CharField(
        max_length=255,
        unique=True,
        default='',
        db_column='productFirebaseId'
    )
    product_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default='',
        db_column='productName'
    )

    # Prediction data
    predicted_daily_usage = models.FloatField(db_column='predictedDailyUsage')
    avg_daily_usage = models.FloatField(db_column='avgDailyUsage')
    trend = models.FloatField()
    confidence_score = models.FloatField(db_column='confidenceScore')
    data_points = models.IntegerField(db_column='dataPoints')

    # Timestamps
    last_updated = models.DateTimeField(auto_now=True, db_column='lastUpdated')

    def __str__(self):
        return f"{self.product_name} - Prediction"

    class Meta:
        db_table = 'ml_predictions'
        managed = True  # Django manages this table


class MLModel(models.Model):
    """
    ML Model metadata - tracks training status
    Managed by Django, not mobile app
    """
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=100, unique=True)
    is_trained = models.BooleanField(default=False, db_column='isTrained')
    last_trained = models.DateTimeField(null=True, blank=True, db_column='lastTrained')
    total_records = models.IntegerField(default=0, db_column='totalRecords')
    products_analyzed = models.IntegerField(default=0, db_column='productsAnalyzed')
    predictions_generated = models.IntegerField(default=0, db_column='predictionsGenerated')
    accuracy = models.IntegerField(default=85)
    model_type = models.CharField(
        max_length=200,
        default='Linear Regression (Moving Average)',
        db_column='modelType'
    )
    training_period_days = models.IntegerField(default=90, db_column='trainingPeriodDays')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ml_models'
        managed = True  # Django manages this table
