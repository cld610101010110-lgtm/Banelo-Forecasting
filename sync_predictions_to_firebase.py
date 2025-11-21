"""
Sync ML Predictions to Firebase
=================================

This script syncs ML predictions from the local Django database to Firebase Firestore.
This allows real-time access to predictions across all platforms.

Prerequisites:
- Firebase credentials configured (firebase-credentials.json)
- ML predictions generated in Django database

Usage:
    python sync_predictions_to_firebase.py
"""

import os
import sys
import django
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baneloforecasting.settings')
django.setup()

from dashboard.models import Product, MLPrediction, MLModel
from dashboard.firebase_utils import validate_firebase_credentials

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("❌ Error: firebase-admin package not found!")
    print("\nPlease install:")
    print("  pip install firebase-admin")
    sys.exit(1)


# Configuration
FIREBASE_CREDENTIALS_PATH = 'baneloforecasting/firebase-credentials.json'
COLLECTION_NAME = 'ml_predictions'
MODEL_COLLECTION = 'ml_models'


def initialize_firebase():
    """Initialize Firebase connection"""
    print("\n🔥 Initializing Firebase...")

    # Check if already initialized
    if firebase_admin._apps:
        print("   ✓ Firebase already initialized")
        return firestore.client()

    # Validate credentials
    if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        print(f"❌ Error: Firebase credentials not found at {FIREBASE_CREDENTIALS_PATH}")
        print("\nPlease ensure firebase-credentials.json is in the correct location.")
        sys.exit(1)

    try:
        # Validate credentials first
        is_valid, message = validate_firebase_credentials()
        if not is_valid:
            print(f"❌ Error: {message}")
            sys.exit(1)

        # Initialize Firebase
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        db = firestore.client()

        print("   ✓ Firebase initialized successfully")
        return db

    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def get_ml_predictions():
    """Fetch ML predictions from Django database"""
    print("\n📊 Fetching ML predictions from database...")

    predictions = MLPrediction.objects.select_related('product').all()

    prediction_data = []
    for pred in predictions:
        # Calculate additional metrics
        if pred.product.stock > 0 and pred.predicted_daily_usage > 0:
            days_until_stockout = pred.product.stock / pred.predicted_daily_usage
        else:
            days_until_stockout = 999  # Essentially infinite

        # Determine stock status
        if days_until_stockout <= 3:
            stock_status = 'critical'
        elif days_until_stockout <= 7:
            stock_status = 'low'
        else:
            stock_status = 'healthy'

        # Calculate reorder recommendation (30-day supply)
        recommended_reorder = max(0, (pred.predicted_daily_usage * 30) - pred.product.stock)

        prediction_data.append({
            'product_id': pred.product.id,
            'product_firebase_id': pred.product.firebase_id or '',
            'product_name': pred.product.name,
            'category': pred.product.category,
            'current_stock': float(pred.product.stock),
            'unit': pred.product.unit,
            'predicted_daily_usage': float(pred.predicted_daily_usage),
            'avg_daily_usage': float(pred.avg_daily_usage),
            'trend': float(pred.trend),
            'confidence_score': float(pred.confidence_score),
            'data_points': int(pred.data_points),
            'days_until_stockout': float(days_until_stockout),
            'stock_status': stock_status,
            'recommended_reorder': float(recommended_reorder),
            'last_updated': pred.last_updated,
            'synced_at': datetime.now()
        })

    print(f"   ✓ Fetched {len(prediction_data)} predictions")

    return prediction_data


def get_ml_model_metadata():
    """Fetch ML model metadata"""
    print("\n📋 Fetching ML model metadata...")

    try:
        models = MLModel.objects.all()

        model_data = []
        for model in models:
            model_data.append({
                'name': model.name,
                'is_trained': model.is_trained,
                'last_trained': model.last_trained,
                'total_records': model.total_records,
                'products_analyzed': model.products_analyzed,
                'predictions_generated': model.predictions_generated,
                'accuracy': model.accuracy,
                'model_type': model.model_type,
                'training_period_days': model.training_period_days,
                'synced_at': datetime.now()
            })

        print(f"   ✓ Fetched {len(model_data)} model records")
        return model_data

    except Exception as e:
        print(f"   ⚠ Error fetching model metadata: {e}")
        return []


def sync_predictions_to_firestore(db, predictions):
    """Upload predictions to Firestore"""
    print(f"\n☁️  Syncing predictions to Firebase...")

    collection_ref = db.collection(COLLECTION_NAME)

    success_count = 0
    error_count = 0

    for pred in predictions:
        try:
            # Use product_id as document ID
            doc_id = str(pred['product_id'])

            # Upload to Firestore
            collection_ref.document(doc_id).set(pred)

            success_count += 1

        except Exception as e:
            print(f"   ⚠ Error syncing {pred['product_name']}: {e}")
            error_count += 1

    print(f"   ✓ Successfully synced {success_count} predictions")
    if error_count > 0:
        print(f"   ⚠ Failed to sync {error_count} predictions")

    return success_count, error_count


def sync_model_metadata_to_firestore(db, models):
    """Upload model metadata to Firestore"""
    print(f"\n☁️  Syncing model metadata to Firebase...")

    if len(models) == 0:
        print("   ⚠ No model metadata to sync")
        return 0, 0

    collection_ref = db.collection(MODEL_COLLECTION)

    success_count = 0
    error_count = 0

    for model in models:
        try:
            # Use model name as document ID
            doc_id = model['name'].replace(' ', '_').lower()

            # Upload to Firestore
            collection_ref.document(doc_id).set(model)

            success_count += 1

        except Exception as e:
            print(f"   ⚠ Error syncing model {model['name']}: {e}")
            error_count += 1

    print(f"   ✓ Successfully synced {success_count} model records")
    if error_count > 0:
        print(f"   ⚠ Failed to sync {error_count} model records")

    return success_count, error_count


def verify_sync(db, expected_count):
    """Verify that predictions were synced correctly"""
    print(f"\n✅ Verifying sync...")

    try:
        collection_ref = db.collection(COLLECTION_NAME)
        docs = collection_ref.stream()

        synced_count = sum(1 for _ in docs)

        print(f"   ✓ Found {synced_count} predictions in Firestore")

        if synced_count == expected_count:
            print(f"   ✓ Sync verified! All {expected_count} predictions uploaded.")
            return True
        else:
            print(f"   ⚠ Warning: Expected {expected_count} but found {synced_count}")
            return False

    except Exception as e:
        print(f"   ⚠ Error verifying sync: {e}")
        return False


def display_summary(predictions, models, pred_success, pred_errors, model_success, model_errors):
    """Display sync summary"""
    print("\n" + "=" * 70)
    print("FIREBASE SYNC SUMMARY")
    print("=" * 70)

    print(f"\n📊 Predictions:")
    print(f"   - Total predictions: {len(predictions)}")
    print(f"   - Successfully synced: {pred_success}")
    print(f"   - Errors: {pred_errors}")
    print(f"   - Success rate: {(pred_success / len(predictions) * 100):.1f}%" if len(predictions) > 0 else "   - N/A")

    print(f"\n📋 Model Metadata:")
    print(f"   - Total models: {len(models)}")
    print(f"   - Successfully synced: {model_success}")
    print(f"   - Errors: {model_errors}")

    # Stock status summary
    critical_count = sum(1 for p in predictions if p['stock_status'] == 'critical')
    low_count = sum(1 for p in predictions if p['stock_status'] == 'low')
    healthy_count = sum(1 for p in predictions if p['stock_status'] == 'healthy')

    print(f"\n🏥 Stock Status Distribution:")
    print(f"   - Critical (≤3 days): {critical_count}")
    print(f"   - Low (≤7 days): {low_count}")
    print(f"   - Healthy (>7 days): {healthy_count}")

    # Top critical items
    critical_items = [p for p in predictions if p['stock_status'] == 'critical']
    if critical_items:
        print(f"\n⚠️  Critical Stock Items:")
        critical_items.sort(key=lambda x: x['days_until_stockout'])
        for item in critical_items[:5]:
            print(f"   - {item['product_name'][:30]:<30} | "
                  f"{item['days_until_stockout']:.1f} days | "
                  f"Reorder: {item['recommended_reorder']:.0f} {item['unit']}")

    print("\n" + "=" * 70)
    print("✅ SYNC COMPLETE!")
    print("=" * 70)
    print("\nNext Steps:")
    print("  1. Verify in Firebase Console: https://console.firebase.google.com/")
    print("  2. Check Firestore collections: ml_predictions, ml_models")
    print("  3. View predictions in dashboard: /dashboard/inventory/forecasting/")
    print("=" * 70 + "\n")


def main():
    """Main sync function"""
    print("=" * 70)
    print("SYNC ML PREDICTIONS TO FIREBASE")
    print("=" * 70)

    try:
        # Initialize Firebase
        db = initialize_firebase()

        # Get predictions from Django
        predictions = get_ml_predictions()

        if len(predictions) == 0:
            print("\n⚠ Warning: No predictions found in database!")
            print("   Please run: python integrate_ml_model.py")
            sys.exit(1)

        # Get model metadata
        models = get_ml_model_metadata()

        # Sync predictions to Firestore
        pred_success, pred_errors = sync_predictions_to_firestore(db, predictions)

        # Sync model metadata to Firestore
        model_success, model_errors = sync_model_metadata_to_firestore(db, models)

        # Verify sync
        verify_sync(db, len(predictions))

        # Display summary
        display_summary(predictions, models, pred_success, pred_errors, model_success, model_errors)

    except KeyboardInterrupt:
        print("\n\n⚠ Sync cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
