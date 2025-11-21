"""
Integrate ML Model with Django
================================

This script loads the trained ML model from Google Colab and integrates it
with the Django application by generating predictions and updating the database.

Prerequisites:
- forecasting_model.pkl must be in ml_models/ directory
- Django models must be properly configured

Usage:
    python integrate_ml_model.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.models import Product, Sale, MLModel, MLPrediction, Recipe, RecipeIngredient
from django.db.models import Sum, Avg, Count, Max, Min, StdDev
from django.db.models.functions import TruncDate

try:
    import joblib
    import pandas as pd
    import numpy as np
except ImportError:
    print("❌ Error: Required packages not found!")
    print("\nPlease install:")
    print("  pip install joblib pandas numpy scikit-learn")
    sys.exit(1)


# Configuration
MODEL_PATH = 'ml_models/forecasting_model.pkl'
TRAINING_PERIOD_DAYS = 90
MIN_DATA_POINTS = 7  # Minimum sales records required


def load_model():
    """Load the trained ML model"""
    print("\n📦 Loading ML model...")

    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Model file not found at {MODEL_PATH}")
        print("\nPlease:")
        print("  1. Train model in Google Colab")
        print("  2. Download forecasting_model.pkl")
        print("  3. Place it in ml_models/ directory")
        sys.exit(1)

    try:
        model_package = joblib.load(MODEL_PATH)
        print(f"   ✓ Model loaded successfully!")

        # Extract components
        model = model_package['model']
        metadata = model_package['metadata']
        label_encoder = model_package['label_encoder']
        feature_columns = model_package['feature_columns']

        print(f"\n📊 Model Information:")
        print(f"   - Type: {metadata['model_type']}")
        print(f"   - Trained: {metadata['trained_date']}")
        print(f"   - R² Score: {metadata['metrics']['r2_score']:.4f}")
        print(f"   - RMSE: {metadata['metrics']['rmse']:.4f}")
        print(f"   - MAE: {metadata['metrics']['mae']:.4f}")

        return model, metadata, label_encoder, feature_columns

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def get_sales_data():
    """Fetch sales data for prediction"""
    print("\n📊 Fetching sales data...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=TRAINING_PERIOD_DAYS)

    sales = Sale.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    ).select_related('product')

    # Convert to dataframe
    sales_data = []
    for sale in sales:
        sales_data.append({
            'product_id': sale.product_id if sale.product else None,
            'product_name': sale.product_name,
            'category': sale.category,
            'quantity': sale.quantity,
            'price': sale.price or 0,
            'total': sale.total or 0,
            'order_date': sale.order_date
        })

    df = pd.DataFrame(sales_data)
    print(f"   ✓ Loaded {len(df)} sales records")

    return df


def aggregate_daily_sales(sales_df):
    """Aggregate sales data by day and product"""
    print("\n🔄 Aggregating daily sales...")

    if len(sales_df) == 0:
        return pd.DataFrame()

    # Group by date and product
    sales_df['date'] = pd.to_datetime(sales_df['order_date']).dt.date

    daily_agg = sales_df.groupby(['date', 'product_id', 'product_name', 'category']).agg({
        'quantity': ['sum', 'count'],
        'price': 'mean',
        'total': 'sum'
    }).reset_index()

    # Flatten column names
    daily_agg.columns = [
        'date', 'product_id', 'product_name', 'category',
        'total_quantity', 'num_transactions', 'avg_price', 'total_revenue'
    ]

    print(f"   ✓ Created {len(daily_agg)} daily aggregates")

    return daily_agg


def engineer_features(daily_df, label_encoder):
    """Create features for prediction"""
    print("\n🔧 Engineering features...")

    if len(daily_df) == 0:
        return pd.DataFrame()

    df = daily_df.copy()
    df = df.sort_values(['product_id', 'date'])

    # Time-based features
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_of_month'] = df['date'].dt.day
    df['month'] = df['date'].dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['week_of_year'] = df['date'].dt.isocalendar().week

    # Rolling statistics (7-day)
    df['rolling_mean_7d'] = df.groupby('product_id')['total_quantity'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    df['rolling_std_7d'] = df.groupby('product_id')['total_quantity'].transform(
        lambda x: x.rolling(window=7, min_periods=1).std().fillna(0)
    )
    df['rolling_max_7d'] = df.groupby('product_id')['total_quantity'].transform(
        lambda x: x.rolling(window=7, min_periods=1).max()
    )
    df['rolling_min_7d'] = df.groupby('product_id')['total_quantity'].transform(
        lambda x: x.rolling(window=7, min_periods=1).min()
    )

    # Rolling statistics (30-day)
    df['rolling_mean_30d'] = df.groupby('product_id')['total_quantity'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )
    df['rolling_std_30d'] = df.groupby('product_id')['total_quantity'].transform(
        lambda x: x.rolling(window=30, min_periods=1).std().fillna(0)
    )

    # Lag features
    df['lag_1d'] = df.groupby('product_id')['total_quantity'].shift(1).fillna(0)
    df['lag_7d'] = df.groupby('product_id')['total_quantity'].shift(7).fillna(0)
    df['lag_14d'] = df.groupby('product_id')['total_quantity'].shift(14).fillna(0)

    # Trend features
    df['days_since_start'] = (df['date'] - df['date'].min()).dt.days

    # Category encoding (handle new categories)
    try:
        df['category_encoded'] = label_encoder.transform(df['category'])
    except:
        # If category not in label encoder, use default
        df['category_encoded'] = 0

    print(f"   ✓ Created features for {len(df)} records")

    return df


def calculate_confidence_score(data_points, std_dev, mean_val):
    """Calculate confidence score based on data quality"""
    if data_points < MIN_DATA_POINTS:
        return 0.5

    # Base confidence from data points
    data_confidence = min(data_points / 30, 1.0)  # Max at 30 data points

    # Penalty for high variability
    if mean_val > 0:
        cv = std_dev / mean_val  # Coefficient of variation
        variability_penalty = max(0, 1 - cv)
    else:
        variability_penalty = 0.5

    # Combined confidence
    confidence = (data_confidence * 0.6 + variability_penalty * 0.4)

    # Scale to 0.5 - 0.95 range
    return max(0.5, min(0.95, confidence))


def generate_predictions(model, featured_df, feature_columns):
    """Generate predictions for all products"""
    print("\n🔮 Generating predictions...")

    predictions = []
    unique_products = featured_df.groupby('product_id').tail(1)

    for _, row in unique_products.iterrows():
        try:
            product_id = row['product_id']
            if pd.isna(product_id):
                continue

            # Prepare features
            X = row[feature_columns].values.reshape(1, -1)
            X = np.nan_to_num(X, 0)

            # Make prediction
            predicted_quantity = model.predict(X)[0]
            predicted_quantity = max(0, predicted_quantity)  # No negative predictions

            # Calculate statistics
            product_data = featured_df[featured_df['product_id'] == product_id]
            avg_daily = product_data['rolling_mean_7d'].iloc[-1]
            std_daily = product_data['rolling_std_7d'].iloc[-1]
            data_points = len(product_data)

            # Calculate trend
            if len(product_data) >= 2:
                recent_avg = product_data['total_quantity'].tail(7).mean()
                older_avg = product_data['total_quantity'].head(7).mean()
                if older_avg > 0:
                    trend = (recent_avg - older_avg) / older_avg
                else:
                    trend = 0
            else:
                trend = 0

            # Confidence score
            confidence = calculate_confidence_score(data_points, std_daily, avg_daily)

            predictions.append({
                'product_id': int(product_id),
                'product_name': row['product_name'],
                'predicted_daily_usage': float(predicted_quantity),
                'avg_daily_usage': float(avg_daily),
                'trend': float(trend),
                'confidence_score': float(confidence),
                'data_points': int(data_points)
            })

        except Exception as e:
            print(f"   ⚠ Error predicting for product {row.get('product_name', 'unknown')}: {e}")
            continue

    print(f"   ✓ Generated {len(predictions)} predictions")

    return predictions


def update_database(predictions, metadata):
    """Update Django database with predictions"""
    print("\n💾 Updating database...")

    # Create or update MLModel record
    ml_model, created = MLModel.objects.update_or_create(
        name=metadata['model_name'],
        defaults={
            'is_trained': True,
            'last_trained': datetime.now(),
            'total_records': metadata['training_samples'] + metadata['test_samples'],
            'products_analyzed': len(predictions),
            'predictions_generated': len(predictions),
            'accuracy': int(metadata['metrics']['r2_score'] * 100),
            'model_type': metadata['model_type'],
            'training_period_days': TRAINING_PERIOD_DAYS
        }
    )

    action = "Created" if created else "Updated"
    print(f"   ✓ {action} MLModel record: {ml_model.name}")

    # Update predictions
    updated_count = 0
    created_count = 0

    for pred in predictions:
        try:
            product = Product.objects.get(id=pred['product_id'])

            ml_pred, created = MLPrediction.objects.update_or_create(
                product=product,
                defaults={
                    'predicted_daily_usage': pred['predicted_daily_usage'],
                    'avg_daily_usage': pred['avg_daily_usage'],
                    'trend': pred['trend'],
                    'confidence_score': pred['confidence_score'],
                    'data_points': pred['data_points']
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        except Product.DoesNotExist:
            print(f"   ⚠ Product {pred['product_id']} not found, skipping...")
            continue
        except Exception as e:
            print(f"   ⚠ Error updating prediction for {pred['product_name']}: {e}")
            continue

    print(f"   ✓ Created {created_count} new predictions")
    print(f"   ✓ Updated {updated_count} existing predictions")

    return ml_model, created_count, updated_count


def display_summary(ml_model, predictions):
    """Display summary of predictions"""
    print("\n" + "=" * 70)
    print("INTEGRATION SUMMARY")
    print("=" * 70)

    print(f"\n📊 Model Information:")
    print(f"   - Name: {ml_model.name}")
    print(f"   - Type: {ml_model.model_type}")
    print(f"   - Accuracy: {ml_model.accuracy}%")
    print(f"   - Last Trained: {ml_model.last_trained.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   - Products Analyzed: {ml_model.products_analyzed}")

    print(f"\n🔮 Top 10 Predictions:")
    print("-" * 70)

    # Sort by predicted usage
    sorted_preds = sorted(predictions, key=lambda x: x['predicted_daily_usage'], reverse=True)[:10]

    for pred in sorted_preds:
        print(f"   {pred['product_name'][:30]:<30} | "
              f"{pred['predicted_daily_usage']:>8.2f} units/day | "
              f"Confidence: {pred['confidence_score']:.2%}")

    print("\n" + "=" * 70)
    print("✅ INTEGRATION COMPLETE!")
    print("=" * 70)
    print("\nNext Steps:")
    print("  1. View predictions: http://localhost:8000/dashboard/inventory/forecasting/")
    print("  2. Sync to Firebase: python sync_predictions_to_firebase.py")
    print("  3. Monitor performance and retrain monthly")
    print("=" * 70 + "\n")


def main():
    """Main integration function"""
    print("=" * 70)
    print("ML MODEL INTEGRATION - DJANGO")
    print("=" * 70)

    try:
        # Load model
        model, metadata, label_encoder, feature_columns = load_model()

        # Get sales data
        sales_df = get_sales_data()

        if len(sales_df) == 0:
            print("\n⚠ Warning: No sales data found!")
            print("   Please ensure you have sales records in the database.")
            sys.exit(1)

        # Aggregate daily sales
        daily_df = aggregate_daily_sales(sales_df)

        # Engineer features
        featured_df = engineer_features(daily_df, label_encoder)

        # Generate predictions
        predictions = generate_predictions(model, featured_df, feature_columns)

        if len(predictions) == 0:
            print("\n⚠ Warning: No predictions generated!")
            print("   Please check your data quality.")
            sys.exit(1)

        # Update database
        ml_model, created_count, updated_count = update_database(predictions, metadata)

        # Display summary
        display_summary(ml_model, predictions)

    except Exception as e:
        print(f"\n❌ Error during integration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
