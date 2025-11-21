# Quick Start - Machine Learning Setup

This guide will help you quickly set up machine learning forecasting with Google Colab.

---

## 🚀 5-Step Quick Start

### Step 1: Export Your Data (2 minutes)

```bash
python export_data_for_colab.py
```

**Output:** Creates `exported_data/` folder with CSV files

---

### Step 2: Open Google Colab (1 minute)

1. Go to https://colab.research.google.com/
2. Click **File → Upload Notebook**
3. Upload `forecasting_model_training.ipynb`

---

### Step 3: Train Model in Colab (10-15 minutes)

1. **Upload data files:**
   - Click the folder icon 📁 on the left sidebar
   - Click upload button
   - Upload all CSV files from `exported_data/`

2. **Run all cells:**
   - Click **Runtime → Run all**
   - Wait for training to complete
   - Monitor progress in the output

3. **Download model:**
   - The last cell will automatically trigger download
   - Save `forecasting_model.pkl` to your computer

---

### Step 4: Integrate Model (2 minutes)

```bash
# 1. Move downloaded model to ml_models folder
mv ~/Downloads/forecasting_model.pkl ml_models/

# 2. Run integration script
python integrate_ml_model.py
```

**Output:** Updates Django database with predictions

---

### Step 5: Sync to Firebase (2 minutes)

```bash
python sync_predictions_to_firebase.py
```

**Output:** Uploads predictions to Firestore

---

## ✅ Verify Everything Works

### Check Database

```bash
python manage.py shell
```

```python
from dashboard.models import MLPrediction, MLModel

# Check model
model = MLModel.objects.first()
print(f"Model trained: {model.is_trained}")
print(f"Accuracy: {model.accuracy}%")

# Check predictions
predictions = MLPrediction.objects.all()
print(f"Total predictions: {predictions.count()}")

# View sample predictions
for pred in predictions[:5]:
    print(f"{pred.product.name}: {pred.predicted_daily_usage:.2f} units/day")
```

### View in Dashboard

1. Start Django server:
   ```bash
   python manage.py runserver
   ```

2. Open browser: http://localhost:8000/dashboard/inventory/forecasting/

3. You should see:
   - Stock predictions for all products
   - Days until stockout
   - Reorder recommendations
   - Confidence scores

---

## 📊 Understanding Your Results

### Prediction Metrics

- **Predicted Daily Usage**: Expected consumption per day
- **Confidence Score**: 50%-95% (higher = more reliable)
- **Trend**: Growth/decline indicator
- **Days Until Stockout**: Current stock ÷ daily usage

### Stock Status Colors

- 🔴 **Critical**: ≤3 days remaining
- 🟡 **Low**: ≤7 days remaining
- 🟢 **Healthy**: >7 days remaining

### Recommended Actions

**Critical Items:**
- Reorder immediately
- Consider increasing stock levels

**Low Stock Items:**
- Plan reorder for next 2-3 days
- Monitor usage closely

**Healthy Items:**
- Continue normal monitoring
- Review monthly

---

## 🔄 Retraining Your Model

**When to retrain:**
- Monthly (recommended)
- After significant sales pattern changes
- When new products are added
- If predictions become inaccurate

**How to retrain:**

```bash
# 1. Export fresh data
python export_data_for_colab.py

# 2. Upload to Colab and train
# (Use the same notebook)

# 3. Download new model

# 4. Integrate
python integrate_ml_model.py

# 5. Sync to Firebase
python sync_predictions_to_firebase.py
```

---

## 🎯 Tips for Better Predictions

### 1. Data Quality
- Ensure consistent sales recording
- Fix any data entry errors
- Remove test/dummy transactions

### 2. Historical Data
- Minimum: 30 days (basic predictions)
- Recommended: 90 days (good accuracy)
- Optimal: 180+ days (best results)

### 3. Product Categories
- Model works best with regular-use items
- Seasonal items may need special handling
- New products need time to build history

### 4. Model Selection
- **Random Forest**: Best for most cases (recommended)
- **XGBoost**: If you need higher accuracy
- **LSTM**: Only for 6+ months of data

---

## 🐛 Common Issues

### Issue: "No sales data found"

**Solution:**
```bash
# Check if you have sales data
python manage.py shell
```
```python
from dashboard.models import Sale
print(f"Total sales: {Sale.objects.count()}")
```

If count is 0, you need to add sales data or sync from Firebase:
```bash
python sync_firebase_to_local.py
```

---

### Issue: "Model file not found"

**Solution:**
Ensure `forecasting_model.pkl` is in the correct location:
```bash
ls -lh ml_models/forecasting_model.pkl
```

If missing, re-download from Colab or retrain the model.

---

### Issue: "Firebase credentials invalid"

**Solution:**
```bash
python manage.py shell
```
```python
from dashboard.firebase_utils import validate_firebase_credentials
validate_firebase_credentials()
```

If invalid, regenerate credentials from Firebase Console.

---

### Issue: "Low prediction accuracy"

**Causes:**
- Not enough historical data
- Irregular sales patterns
- Data quality issues

**Solutions:**
1. Collect more data (wait longer)
2. Clean up data (remove outliers)
3. Try different models (XGBoost instead of Random Forest)
4. Add more features in Colab notebook

---

## 📚 Additional Resources

- **Full Guide**: See `ML_SETUP_GUIDE.md`
- **Colab Notebook**: `forecasting_model_training.ipynb`
- **Scripts**:
  - `export_data_for_colab.py` - Export data
  - `integrate_ml_model.py` - Integrate model
  - `sync_predictions_to_firebase.py` - Sync to cloud

---

## 💡 Pro Tips

1. **Save Colab Notebooks to Drive**: Never lose your work
2. **Version Your Models**: Keep backups with dates
3. **Monitor Accuracy**: Compare predictions vs actual usage
4. **Automate**: Set up monthly retraining reminders
5. **Document Changes**: Note any customizations you make

---

## 🎓 Learning Resources

- [Google Colab Tutorial](https://colab.research.google.com/notebooks/intro.ipynb)
- [Scikit-learn Documentation](https://scikit-learn.org/)
- [Time Series Forecasting](https://www.tensorflow.org/tutorials/structured_data/time_series)
- [Firebase Firestore Guide](https://firebase.google.com/docs/firestore)

---

## Need Help?

1. Check `ML_SETUP_GUIDE.md` for detailed instructions
2. Review the Troubleshooting section above
3. Ensure all dependencies are installed:
   ```bash
   pip install joblib pandas numpy scikit-learn firebase-admin
   ```

---

**Happy Forecasting! 🚀📊**
