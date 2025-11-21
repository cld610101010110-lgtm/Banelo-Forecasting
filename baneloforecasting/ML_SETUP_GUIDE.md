# Machine Learning Setup Guide - Google Colab Integration

## Overview

This guide walks you through setting up a machine learning forecasting system using Google Colab for training and integrating the trained model back into your Django application.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ML Training Workflow                        │
└─────────────────────────────────────────────────────────────────┘

Step 1: Export Data (Local SQLite)
   ↓
   └─→ Run: python export_data_for_colab.py
       Output: sales_data.csv, products_data.csv, recipes_data.csv

Step 2: Upload to Google Colab
   ↓
   └─→ Upload CSV files to Colab session
       Open: forecasting_model_training.ipynb

Step 3: Train ML Model (Google Colab)
   ↓
   └─→ Train Random Forest / XGBoost / LSTM models
       Validate: Cross-validation & metrics
       Export: forecasting_model.pkl

Step 4: Download & Integrate (Django)
   ↓
   └─→ Download: forecasting_model.pkl
       Place in: ml_models/forecasting_model.pkl
       Run: python integrate_ml_model.py

Step 5: Sync to Firebase
   ↓
   └─→ Run: python sync_predictions_to_firebase.py
       Upload predictions to Firestore
```

---

## Prerequisites

### Local Environment
- Python 3.8+
- Django 5.2+ (already installed)
- SQLite database (db.sqlite3)
- Firebase credentials (firebase-credentials.json)

### Google Colab
- Google account
- Google Drive for file storage (optional)
- Internet connection

### Python Packages (will be installed in Colab)
```python
pandas
numpy
scikit-learn
xgboost
matplotlib
seaborn
joblib
```

---

## Step 1: Export Dataset from SQLite

### 1.1 Run the Export Script

```bash
# Navigate to project root
cd /home/user/Banelo-Forecasting

# Run the export script
python export_data_for_colab.py
```

### 1.2 Expected Output Files

```
exported_data/
├── sales_data.csv           # All sales transactions (90 days)
├── products_data.csv        # Product inventory with stock levels
├── recipes_data.csv         # Beverage recipes
└── recipe_ingredients.csv   # Recipe ingredients mapping
```

### 1.3 Data Schema

**sales_data.csv:**
- `sale_id`, `product_id`, `product_name`, `category`
- `quantity`, `price`, `total`, `order_date`

**products_data.csv:**
- `product_id`, `firebase_id`, `name`, `category`
- `stock`, `unit`, `price`, `created_at`

**recipes_data.csv:**
- `recipe_id`, `product_id`, `product_name`, `firebase_id`

**recipe_ingredients.csv:**
- `recipe_id`, `ingredient_id`, `ingredient_name`
- `quantity_needed`, `unit`

---

## Step 2: Upload to Google Colab

### 2.1 Open Google Colab

1. Go to https://colab.research.google.com/
2. Click **File → Upload Notebook**
3. Upload `forecasting_model_training.ipynb`

### 2.2 Upload Data Files

In Colab, run:
```python
from google.colab import files
uploaded = files.upload()
```

Or mount Google Drive:
```python
from google.colab import drive
drive.mount('/content/drive')
```

### 2.3 Verify Files

```python
import os
print(os.listdir())  # Should show your CSV files
```

---

## Step 3: Train ML Model in Google Colab

### 3.1 Model Options

The Colab notebook provides 3 ML models:

1. **Random Forest** (Recommended)
   - Handles non-linear patterns
   - Feature importance analysis
   - Good for small-medium datasets

2. **XGBoost**
   - High accuracy
   - Handles missing data well
   - Suitable for time series

3. **LSTM (Deep Learning)**
   - Best for complex temporal patterns
   - Requires more data (3+ months)
   - Longer training time

### 3.2 Training Process

```python
# Load data
sales_df = pd.read_csv('sales_data.csv')
products_df = pd.read_csv('products_data.csv')

# Feature engineering
features = engineer_features(sales_df, products_df)

# Train model
model = train_random_forest(features)

# Evaluate
metrics = evaluate_model(model, X_test, y_test)
print(f"RMSE: {metrics['rmse']}")
print(f"MAE: {metrics['mae']}")
print(f"R²: {metrics['r2']}")

# Save model
import joblib
joblib.dump(model, 'forecasting_model.pkl')
```

### 3.3 Download Trained Model

```python
from google.colab import files
files.download('forecasting_model.pkl')
```

---

## Step 4: Integrate Model into Django

### 4.1 Create Model Directory

```bash
mkdir -p ml_models
```

### 4.2 Place Downloaded Model

```bash
# Move downloaded model to project
mv ~/Downloads/forecasting_model.pkl ml_models/forecasting_model.pkl
```

### 4.3 Run Integration Script

```bash
python integrate_ml_model.py
```

This script will:
- Load the trained model
- Generate predictions for all products
- Update `ml_predictions` table in SQLite
- Create/update `MLModel` metadata

### 4.4 Verify Integration

```bash
python manage.py shell
```

```python
from dashboard.models import MLPrediction, MLModel

# Check model metadata
model = MLModel.objects.get(name='Random Forest Forecasting')
print(f"Trained: {model.is_trained}")
print(f"Accuracy: {model.accuracy}%")
print(f"Products: {model.products_analyzed}")

# Check predictions
predictions = MLPrediction.objects.all()
for pred in predictions[:5]:
    print(f"{pred.product.name}: {pred.predicted_daily_usage:.2f} units/day")
```

---

## Step 5: Sync Predictions to Firebase

### 5.1 Run Firebase Sync

```bash
python sync_predictions_to_firebase.py
```

This will:
- Upload all ML predictions to Firestore
- Create `ml_predictions` collection
- Include metadata (confidence, trend, etc.)

### 5.2 Verify Firebase Upload

Check Firestore console:
- Collection: `ml_predictions`
- Documents: One per product
- Fields: `predicted_daily_usage`, `confidence_score`, etc.

---

## Step 6: Use Predictions in Dashboard

### 6.1 Access Forecasting Page

Navigate to: `http://localhost:8000/dashboard/inventory/forecasting/`

### 6.2 Features Available

- **Stock Depletion Predictions**: Days until stockout
- **Reorder Recommendations**: Suggested order quantities
- **Trend Analysis**: Growth/decline indicators
- **Confidence Scores**: Prediction reliability
- **Visual Charts**: Usage trends over time

### 6.3 Retrain Model

Click **"Train ML Model"** button to retrain with latest data.

---

## Workflow Automation

### Option 1: Manual Retraining (Monthly)

```bash
# Every month
python export_data_for_colab.py
# Upload to Colab, train, download
python integrate_ml_model.py
python sync_predictions_to_firebase.py
```

### Option 2: Scheduled Retraining (Advanced)

Create a cron job:
```bash
# Edit crontab
crontab -e

# Add monthly retraining (1st of month, 2am)
0 2 1 * * cd /home/user/Banelo-Forecasting && python export_data_for_colab.py
```

### Option 3: Cloud Training (Future)

- Deploy Colab notebook to Cloud Functions
- Trigger via Cloud Scheduler
- Auto-download and integrate model

---

## Troubleshooting

### Issue: Model file too large

**Solution:** Use model compression
```python
# In Colab
import joblib
joblib.dump(model, 'model.pkl', compress=3)
```

### Issue: Firebase upload fails

**Solution:** Check credentials
```bash
python manage.py shell
```
```python
from dashboard.firebase_utils import validate_firebase_credentials
validate_firebase_credentials()
```

### Issue: Low prediction accuracy

**Solution:**
1. Increase training data (collect 3+ months)
2. Try different models (XGBoost, LSTM)
3. Add more features (day of week, seasonality)

### Issue: Colab session timeout

**Solution:** Use Google Drive
```python
# Save checkpoints to Drive
from google.colab import drive
drive.mount('/content/drive')
joblib.dump(model, '/content/drive/MyDrive/model.pkl')
```

---

## Best Practices

### Data Quality
- Ensure at least 90 days of historical data
- Clean outliers (abnormal spikes/drops)
- Handle missing values appropriately

### Model Selection
- Start with Random Forest (simplest)
- Use XGBoost for better accuracy
- Try LSTM only if you have 6+ months data

### Retraining Frequency
- Monthly: For stable inventory
- Weekly: For high-turnover items
- Daily: Not recommended (overfitting risk)

### Version Control
- Save model versions with timestamps
- Keep metadata (accuracy, training date)
- Compare performance before replacing

### Security
- Never commit `.pkl` files to Git (add to .gitignore)
- Never upload Firebase credentials to Colab
- Use environment variables for sensitive data

---

## Advanced Features

### Feature Engineering Ideas

```python
# Seasonality
features['day_of_week'] = pd.to_datetime(df['order_date']).dt.dayofweek
features['month'] = pd.to_datetime(df['order_date']).dt.month
features['is_weekend'] = features['day_of_week'] >= 5

# Rolling statistics
features['7day_rolling_avg'] = df.groupby('product_id')['quantity'].rolling(7).mean()
features['30day_rolling_std'] = df.groupby('product_id')['quantity'].rolling(30).std()

# Lag features
features['lag_1day'] = df.groupby('product_id')['quantity'].shift(1)
features['lag_7day'] = df.groupby('product_id')['quantity'].shift(7)
```

### Ensemble Models

```python
from sklearn.ensemble import VotingRegressor

ensemble = VotingRegressor([
    ('rf', RandomForestRegressor()),
    ('xgb', XGBRegressor()),
    ('lr', LinearRegression())
])
```

### Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 20, 30],
    'min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(RandomForestRegressor(), param_grid, cv=5)
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
```

---

## Next Steps

1. ✅ Export your data using `export_data_for_colab.py`
2. ✅ Open the Colab notebook `forecasting_model_training.ipynb`
3. ✅ Train your first model
4. ✅ Integrate and test predictions
5. ✅ Sync to Firebase
6. ✅ Monitor performance and iterate

---

## Resources

- [Google Colab Documentation](https://colab.research.google.com/)
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Time Series Forecasting Guide](https://www.tensorflow.org/tutorials/structured_data/time_series)

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Colab notebook comments
3. Verify Firebase connectivity: `python dashboard/firebase_utils.py`
4. Check Django logs: `python manage.py runserver` (console output)

Good luck with your ML implementation! 🚀
