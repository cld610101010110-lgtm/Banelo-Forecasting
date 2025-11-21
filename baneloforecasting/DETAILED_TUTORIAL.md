# 📚 Detailed Tutorial: ML Forecasting Setup

A complete step-by-step guide to set up machine learning forecasting for your Banelo inventory system.

**⏱️ Estimated Time:** 30-45 minutes (first time)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Export Your Data](#step-1-export-your-data)
3. [Step 2: Train Model in Google Colab](#step-2-train-model-in-google-colab)
4. [Step 3: Place Model in Project](#step-3-place-model-in-project)
5. [Step 4: Integrate with Django](#step-4-integrate-with-django)
6. [Step 5: Sync to Firebase](#step-5-sync-to-firebase)
7. [Step 6: View Results](#step-6-view-results)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

---

## Prerequisites

### ✅ Before You Start

Make sure you have:

1. **Django Application Running**
   ```bash
   python manage.py runserver
   # Should start without errors
   ```

2. **Sales Data Available**
   ```bash
   python manage.py shell
   ```
   ```python
   from dashboard.models import Sale
   print(f"Total sales: {Sale.objects.count()}")
   # Should show at least 100+ sales records
   exit()
   ```

3. **Python Packages Installed**
   ```bash
   pip install joblib pandas numpy scikit-learn firebase-admin
   ```

4. **Google Account**
   - For accessing Google Colab
   - Free account works fine!

5. **Internet Connection**
   - Needed for Google Colab training

---

## Step 1: Export Your Data

### 🎯 Goal
Export sales, products, and recipe data from your SQLite database to CSV files that Google Colab can read.

### 📍 Current Location
Make sure you're in your project root:
```bash
cd /home/user/Banelo-Forecasting
pwd
# Should show: /home/user/Banelo-Forecasting
```

### ▶️ Run the Export Script

```bash
python export_data_for_colab.py
```

### 📊 Expected Output

You should see:
```
============================================================
DATA EXPORT FOR GOOGLE COLAB ML TRAINING
============================================================

📊 Exporting sales data (last 90 days)...
   ✓ Exported 1523 sales records to exported_data/sales_data.csv

📦 Exporting products data...
   ✓ Exported 45 products to exported_data/products_data.csv

🧪 Exporting recipes data...
   ✓ Exported 12 recipes to exported_data/recipes_data.csv

🥤 Exporting recipe ingredients data...
   ✓ Exported 48 recipe ingredients to exported_data/recipe_ingredients.csv

📈 Generating aggregated features...
   ✓ Generated 892 daily aggregates to exported_data/daily_sales_aggregated.csv

📝 Generating metadata...
   ✓ Metadata saved to exported_data/export_metadata.txt

============================================================
EXPORT COMPLETE! 🎉
============================================================

📊 Summary:
   - Sales records: 1523
   - Products: 45
   - Recipes: 12
   - Recipe ingredients: 48
   - Daily aggregates: 892

📁 Output directory: exported_data/

✅ Files ready for upload to Google Colab!

📖 Next: Open forecasting_model_training.ipynb in Colab
============================================================
```

### ✅ Verify Files Created

```bash
ls -lh exported_data/
```

You should see:
```
total 256K
-rw-r--r-- 1 user user  45K Nov 21 10:30 daily_sales_aggregated.csv
-rw-r--r-- 1 user user  892 Nov 21 10:30 export_metadata.txt
-rw-r--r-- 1 user user  12K Nov 21 10:30 products_data.csv
-rw-r--r-- 1 user user  8.5K Nov 21 10:30 recipe_ingredients.csv
-rw-r--r-- 1 user user  5.2K Nov 21 10:30 recipes_data.csv
-rw-r--r-- 1 user user 180K Nov 21 10:30 sales_data.csv
```

### 🔍 Preview Your Data (Optional)

```bash
# Look at first few lines of sales data
head -5 exported_data/sales_data.csv
```

### ❌ Common Errors

**Error: "No sales data found"**
- **Cause:** Your database doesn't have enough sales records
- **Fix:**
  ```bash
  # Import from Firebase first
  python sync_firebase_to_local.py
  # Or add test data
  python add_test_sales.py
  # Then run export again
  python export_data_for_colab.py
  ```

**Error: "ModuleNotFoundError: No module named 'dashboard'"**
- **Cause:** Not running from project root
- **Fix:**
  ```bash
  cd /home/user/Banelo-Forecasting
  python export_data_for_colab.py
  ```

### ✅ Step 1 Complete!
You should now have a folder called `exported_data/` with 5 CSV files inside.

---

## Step 2: Train Model in Google Colab

### 🎯 Goal
Upload your data to Google Colab, train a machine learning model, and download the trained model file.

### Part A: Open Google Colab

1. **Open your web browser** (Chrome, Firefox, Safari, etc.)

2. **Go to Google Colab**
   - URL: https://colab.research.google.com/
   - Sign in with your Google account if prompted

3. **You should see the Colab welcome screen**
   - Orange/yellow Colab logo at top
   - Examples and recent notebooks

### Part B: Upload Your Notebook

1. **Click "File" in the top menu**

2. **Click "Upload notebook"**

3. **Click "Choose File" button**

4. **Navigate to your project folder**
   - Go to: `/home/user/Banelo-Forecasting/`
   - Select: `forecasting_model_training.ipynb`
   - Click "Open"

5. **Wait for upload** (5-10 seconds)

6. **You should now see the notebook open** with:
   - Title: "Banelo Forecasting - ML Model Training"
   - Multiple sections with code cells

### Part C: Upload Your Data Files

1. **Look at the left sidebar** in Colab
   - You should see a 📁 folder icon
   - Click it to open the "Files" panel

2. **Click the Upload button** (looks like a document with an up arrow)

3. **Select ALL CSV files to upload:**
   - Navigate to: `/home/user/Banelo-Forecasting/exported_data/`
   - Select these files (hold Ctrl/Cmd to select multiple):
     - `sales_data.csv`
     - `products_data.csv`
     - `recipes_data.csv`
     - `recipe_ingredients.csv`
     - `daily_sales_aggregated.csv`
   - Click "Open"

4. **Wait for uploads to complete**
   - You'll see progress bars for each file
   - Total time: 10-30 seconds depending on data size

5. **Verify files are uploaded**
   - In the Files panel, you should see all 5 CSV files listed
   - Click the refresh button if you don't see them

### Part D: Run the Notebook

1. **Read the introduction** (optional but recommended)
   - The first cell explains what the notebook does

2. **Run the notebook cells sequentially**

   **Option 1: Run All Cells at Once (Recommended for First Time)**
   - Click **"Runtime"** in the top menu
   - Click **"Run all"**
   - Colab will execute all cells from top to bottom
   - ⏱️ This takes about 10-15 minutes

   **Option 2: Run Cells One by One**
   - Click on the first code cell
   - Press **Shift + Enter** to run it
   - Wait for it to complete (you'll see a green checkmark ✓)
   - Move to next cell and repeat

3. **What You'll See During Training:**

   **Cell 1: Install Dependencies**
   ```
   Installing pandas numpy scikit-learn...
   ✅ Libraries imported successfully!
   ```

   **Cell 2: Upload Files** (you already did this)

   **Cell 3: Load Data**
   ```
   📊 Loading data...
   ✅ Data loaded successfully!
      - Sales records: 1,523
      - Products: 45
      - Daily aggregates: 892
   ```

   **Cell 4-6: Data Visualization**
   - You'll see charts and graphs
   - Sales over time
   - Top products
   - Category breakdown

   **Cell 7: Feature Engineering**
   ```
   🔧 Engineering features...
      ✓ Created 24 features
   ✅ Feature engineering complete!
   ```

   **Cell 8: Train Linear Regression**
   ```
   🤖 Training Linear Regression...
   ✅ Linear Regression Results:
      RMSE: 3.2451
      MAE: 2.1234
      R² Score: 0.7234
   ```

   **Cell 9: Train Random Forest** ⭐ (Best Model)
   ```
   🌲 Training Random Forest...
   [Parallel(n_jobs=-1)]: Done 200 out of 200 | elapsed: 12.3s finished

   ✅ Random Forest Results:
      RMSE: 2.1234
      MAE: 1.5678
      R² Score: 0.8567

   📊 Top 10 Important Features:
      rolling_mean_7d       0.2145
      lag_1d               0.1834
      rolling_mean_30d     0.1523
      ...
   ```

   **Cell 10: Train XGBoost**
   ```
   🚀 Training XGBoost...
   ✅ XGBoost Results:
      RMSE: 2.0123
      MAE: 1.4567
      R² Score: 0.8723
   ```

   **Cell 11: Model Comparison**
   - You'll see a table comparing all models
   - And bar charts showing performance

   **Cell 12: Export Model**
   ```
   ✅ Model saved successfully!
   📦 Model: forecasting_model.pkl
      - Model Type: Random Forest
      - Training Samples: 892
      - Test Samples: 223
      - RMSE: 2.1234
      - MAE: 1.5678
      - R² Score: 0.8567

   📥 Download this file and place it in: ml_models/forecasting_model.pkl
   ✅ Then run: python integrate_ml_model.py
   ```

4. **Wait for All Cells to Complete**
   - Green checkmarks ✓ appear when done
   - Total time: 10-15 minutes
   - Don't close the browser tab!

### Part E: Download the Trained Model

1. **Find the last cell** in the notebook
   - Should say "Download the model"

2. **Run the download cell** if it hasn't run yet
   ```python
   from google.colab import files
   files.download('forecasting_model.pkl')
   ```

3. **The download should start automatically**
   - Look for download notification in your browser
   - File name: `forecasting_model.pkl`
   - File size: ~5-50 MB (varies by model complexity)

4. **Check your Downloads folder**
   ```bash
   ls -lh ~/Downloads/forecasting_model.pkl
   # Should show the file with size
   ```

### ✅ Understanding Your Results

Look for these key metrics in the output:

**R² Score (Coefficient of Determination)**
- 0.85-0.95 = Excellent ⭐⭐⭐
- 0.75-0.85 = Good ⭐⭐
- 0.60-0.75 = Acceptable ⭐
- <0.60 = Needs more data

**RMSE (Root Mean Squared Error)**
- Lower is better
- Compare to your typical daily sales
- If RMSE is 2.5 and you sell ~20 units/day, that's 12.5% error

**MAE (Mean Absolute Error)**
- Average prediction error
- In same units as your data
- If MAE is 1.5, predictions are off by ±1.5 units on average

### ❌ Common Errors

**Error: "No backend available" or "Runtime disconnected"**
- **Cause:** Colab session timeout or no GPU needed
- **Fix:** Click "Runtime → Restart runtime" and run again

**Error: "FileNotFoundError: sales_data.csv"**
- **Cause:** CSV files not uploaded
- **Fix:** Upload files again (Part C above)

**Error: "ValueError: not enough values to unpack"**
- **Cause:** CSV file might be empty or corrupted
- **Fix:** Re-export data (Step 1) and upload again

**Warning: "Low R² score (0.45)"**
- **Cause:** Not enough data or irregular patterns
- **Fix:**
  - Collect more sales data (wait 1-2 weeks)
  - Try XGBoost model instead
  - Still works, but predictions less accurate

### 💾 Save Your Work (Optional but Recommended)

1. **Click "File → Save a copy in Drive"**
   - Saves notebook to your Google Drive
   - You can reuse it next month for retraining

2. **Rename the notebook** (optional)
   - Click the title at top
   - Rename to: "Banelo_Forecasting_Nov_2025"

### ✅ Step 2 Complete!
You should now have `forecasting_model.pkl` in your Downloads folder.

---

## Step 3: Place Model in Project

### 🎯 Goal
Move the downloaded model file to the correct location in your Django project.

### 📍 Check Current Location of Model

```bash
# Check Downloads folder
ls -lh ~/Downloads/forecasting_model.pkl
```

Expected output:
```
-rw-r--r-- 1 user user 8.5M Nov 21 11:15 /home/user/Downloads/forecasting_model.pkl
```

### ▶️ Move Model to Project

**Method 1: Using Command Line (Recommended)**

```bash
# Move file from Downloads to ml_models directory
mv ~/Downloads/forecasting_model.pkl /home/user/Banelo-Forecasting/ml_models/

# Verify it's in the right place
ls -lh /home/user/Banelo-Forecasting/ml_models/
```

Expected output:
```
total 8.5M
-rw-r--r-- 1 user user 8.5M Nov 21 11:15 forecasting_model.pkl
-rw-r--r-- 1 user user 1.2K Nov 21 10:00 README.md
```

**Method 2: Using File Manager (GUI)**

1. Open your file manager
2. Navigate to Downloads folder
3. Find `forecasting_model.pkl`
4. Cut the file (Ctrl+X)
5. Navigate to `/home/user/Banelo-Forecasting/ml_models/`
6. Paste the file (Ctrl+V)

### ✅ Verify Model is Loadable

```bash
cd /home/user/Banelo-Forecasting
python -c "import joblib; model = joblib.load('ml_models/forecasting_model.pkl'); print('✅ Model loaded successfully!')"
```

Expected output:
```
✅ Model loaded successfully!
```

### ❌ Common Errors

**Error: "No such file or directory"**
- **Cause:** File not downloaded or wrong location
- **Fix:**
  ```bash
  # Find the file
  find ~ -name "forecasting_model.pkl" 2>/dev/null
  # Move it to correct location
  mv /path/to/found/file /home/user/Banelo-Forecasting/ml_models/
  ```

**Error: "Permission denied"**
- **Cause:** File permissions issue
- **Fix:**
  ```bash
  chmod 644 /home/user/Banelo-Forecasting/ml_models/forecasting_model.pkl
  ```

### ✅ Step 3 Complete!
Your model is now in the correct location: `ml_models/forecasting_model.pkl`

---

## Step 4: Integrate with Django

### 🎯 Goal
Load the trained model and generate predictions for all products in your database.

### 📍 Make Sure You're in Project Root

```bash
cd /home/user/Banelo-Forecasting
pwd
# Should show: /home/user/Banelo-Forecasting
```

### ▶️ Run Integration Script

```bash
python integrate_ml_model.py
```

### 📊 Expected Output (Detailed Walkthrough)

**Phase 1: Loading Model**
```
======================================================================
ML MODEL INTEGRATION - DJANGO
======================================================================

📦 Loading ML model...
   ✓ Model loaded successfully!

📊 Model Information:
   - Type: RandomForestRegressor
   - Trained: 2025-11-21 11:15:23
   - R² Score: 0.8567
   - RMSE: 2.1234
   - MAE: 1.5678
```

**Phase 2: Fetching Data**
```
📊 Fetching sales data...
   ✓ Loaded 1523 sales records

🔄 Aggregating daily sales...
   ✓ Created 892 daily aggregates
```

**Phase 3: Feature Engineering**
```
🔧 Engineering features...
   ✓ Created features for 892 records
```

**Phase 4: Generating Predictions**
```
🔮 Generating predictions...
   ✓ Generated 45 predictions
```

**Phase 5: Updating Database**
```
💾 Updating database...
   ✓ Updated MLModel record: Random Forest
   ✓ Created 23 new predictions
   ✓ Updated 22 existing predictions
```

**Phase 6: Summary**
```
======================================================================
INTEGRATION SUMMARY
======================================================================

📊 Model Information:
   - Name: Random Forest
   - Type: RandomForestRegressor
   - Accuracy: 85%
   - Last Trained: 2025-11-21 11:15:23
   - Products Analyzed: 45

🔮 Top 10 Predictions:
----------------------------------------------------------------------
   Espresso                       |    25.34 units/day | Confidence: 92%
   Americano                      |    18.67 units/day | Confidence: 89%
   Cappuccino                     |    16.23 units/day | Confidence: 88%
   Coffee Beans (Dark Roast)      |    12.45 units/day | Confidence: 85%
   Milk (2% Reduced Fat)          |    10.89 units/day | Confidence: 87%
   Sugar Packets                  |     9.56 units/day | Confidence: 83%
   Croissant                      |     8.34 units/day | Confidence: 81%
   Chocolate Chip Cookie          |     7.12 units/day | Confidence: 79%
   Blueberry Muffin              |     6.45 units/day | Confidence: 78%
   Iced Latte                    |     5.89 units/day | Confidence: 76%

======================================================================
✅ INTEGRATION COMPLETE!
======================================================================

Next Steps:
  1. View predictions: http://localhost:8000/dashboard/inventory/forecasting/
  2. Sync to Firebase: python sync_predictions_to_firebase.py
  3. Monitor performance and retrain monthly
======================================================================
```

### 🔍 What Just Happened?

The script:
1. ✅ Loaded your trained ML model
2. ✅ Fetched 90 days of sales history from database
3. ✅ Calculated rolling averages, trends, and patterns
4. ✅ Generated daily usage predictions for each product
5. ✅ Calculated confidence scores (how reliable predictions are)
6. ✅ Updated `ml_predictions` table in database
7. ✅ Created/updated `ml_models` metadata record

### ✅ Verify in Database

```bash
python manage.py shell
```

```python
from dashboard.models import MLPrediction, MLModel

# Check model record
model = MLModel.objects.first()
print(f"Model: {model.name}")
print(f"Trained: {model.is_trained}")
print(f"Accuracy: {model.accuracy}%")
print(f"Products analyzed: {model.products_analyzed}")
print()

# Check predictions
predictions = MLPrediction.objects.all().order_by('-predicted_daily_usage')[:10]
print("Top 10 Predicted Products:")
print("-" * 60)
for pred in predictions:
    print(f"{pred.product.name[:30]:30} {pred.predicted_daily_usage:>8.2f} units/day")

# Exit shell
exit()
```

Expected output:
```
Model: Random Forest
Trained: True
Accuracy: 85%
Products analyzed: 45

Top 10 Predicted Products:
------------------------------------------------------------
Espresso                         25.34 units/day
Americano                        18.67 units/day
Cappuccino                       16.23 units/day
...
```

### ❌ Common Errors

**Error: "ModuleNotFoundError: No module named 'joblib'"**
- **Cause:** Missing dependency
- **Fix:**
  ```bash
  pip install joblib pandas numpy scikit-learn
  python integrate_ml_model.py
  ```

**Error: "Model file not found"**
- **Cause:** Model not in correct location
- **Fix:**
  ```bash
  # Check if file exists
  ls -lh ml_models/forecasting_model.pkl
  # If not found, go back to Step 3
  ```

**Error: "No sales data found"**
- **Cause:** Empty database
- **Fix:**
  ```bash
  # Import from Firebase
  python sync_firebase_to_local.py
  # Then try again
  python integrate_ml_model.py
  ```

**Warning: "Generated 0 predictions"**
- **Cause:** Data quality issues or product ID mismatches
- **Fix:**
  - Check that products have sales records
  - Verify product IDs are consistent
  - Check Django admin: http://localhost:8000/admin/

### 💡 Understanding Confidence Scores

- **90-95%**: Excellent data, very reliable predictions
- **80-90%**: Good data, reliable predictions
- **70-80%**: Decent data, moderately reliable
- **50-70%**: Limited data, less reliable but still useful

Low confidence scores mean:
- Not enough historical sales data
- Irregular sales patterns
- Product is seasonal or sporadic

### ✅ Step 4 Complete!
Your database now contains ML predictions for all products!

---

## Step 5: Sync to Firebase

### 🎯 Goal
Upload your ML predictions to Firebase Firestore so they're accessible from cloud/mobile apps.

### 📍 Prerequisites Check

```bash
# Verify Firebase credentials exist
ls -lh baneloforecasting/firebase-credentials.json
```

Expected output:
```
-rw-r--r-- 1 user user 2.3K Oct 15 09:30 baneloforecasting/firebase-credentials.json
```

If file doesn't exist:
- Download from Firebase Console
- Place in `baneloforecasting/` folder
- Rename to `firebase-credentials.json`

### ▶️ Run Sync Script

```bash
python sync_predictions_to_firebase.py
```

### 📊 Expected Output

**Phase 1: Initialize Firebase**
```
======================================================================
SYNC ML PREDICTIONS TO FIREBASE
======================================================================

🔥 Initializing Firebase...
   ✓ Firebase initialized successfully
```

**Phase 2: Fetch Data**
```
📊 Fetching ML predictions from database...
   ✓ Fetched 45 predictions

📋 Fetching ML model metadata...
   ✓ Fetched 1 model records
```

**Phase 3: Sync Predictions**
```
☁️  Syncing predictions to Firebase...
   ✓ Successfully synced 45 predictions
```

**Phase 4: Sync Metadata**
```
☁️  Syncing model metadata to Firebase...
   ✓ Successfully synced 1 model records
```

**Phase 5: Verification**
```
✅ Verifying sync...
   ✓ Found 45 predictions in Firestore
   ✓ Sync verified! All 45 predictions uploaded.
```

**Phase 6: Summary**
```
======================================================================
FIREBASE SYNC SUMMARY
======================================================================

📊 Predictions:
   - Total predictions: 45
   - Successfully synced: 45
   - Errors: 0
   - Success rate: 100.0%

📋 Model Metadata:
   - Total models: 1
   - Successfully synced: 1
   - Errors: 0

🏥 Stock Status Distribution:
   - Critical (≤3 days): 3
   - Low (≤7 days): 8
   - Healthy (>7 days): 34

⚠️  Critical Stock Items:
   - Sugar Packets                  | 2.3 days | Reorder: 720 g
   - Coffee Beans (Dark Roast)      | 2.8 days | Reorder: 5000 g
   - Milk (2% Reduced Fat)          | 1.5 days | Reorder: 8500 ml

======================================================================
✅ SYNC COMPLETE!
======================================================================

Next Steps:
  1. Verify in Firebase Console: https://console.firebase.google.com/
  2. Check Firestore collections: ml_predictions, ml_models
  3. View predictions in dashboard: /dashboard/inventory/forecasting/
======================================================================
```

### 🔍 What Was Synced?

For each product, Firebase now has:
- Product name and category
- Current stock level
- Predicted daily usage
- Average daily usage
- Trend (growing/declining)
- Confidence score
- Days until stockout
- Stock status (critical/low/healthy)
- Recommended reorder quantity
- Last update timestamp

### ✅ Verify in Firebase Console

1. **Open Firebase Console**
   - Go to: https://console.firebase.google.com/
   - Sign in with your Google account

2. **Select Your Project**
   - Click on your project name

3. **Open Firestore Database**
   - Click "Firestore Database" in left sidebar
   - You should see your collections

4. **Check `ml_predictions` Collection**
   - Click on `ml_predictions`
   - You should see 45 documents (one per product)
   - Click on any document to see the data

5. **Check `ml_models` Collection**
   - Click on `ml_models`
   - You should see 1 document with model metadata

### ❌ Common Errors

**Error: "Firebase credentials not found"**
- **Cause:** Missing `firebase-credentials.json`
- **Fix:**
  1. Go to Firebase Console → Project Settings → Service Accounts
  2. Click "Generate new private key"
  3. Download the JSON file
  4. Rename to `firebase-credentials.json`
  5. Place in `baneloforecasting/` folder

**Error: "Permission denied" or "Insufficient permissions"**
- **Cause:** Service account doesn't have Firestore permissions
- **Fix:**
  1. Go to Firebase Console → Firestore Database → Rules
  2. Temporarily set rules to allow writes (for testing):
     ```
     rules_version = '2';
     service cloud.firestore {
       match /databases/{database}/documents {
         match /{document=**} {
           allow read, write: if true;  // DEVELOPMENT ONLY
         }
       }
     }
     ```
  3. Click "Publish"
  4. Run sync again
  5. Set proper security rules after testing

**Error: "Connection timeout"**
- **Cause:** Network issues or firewall
- **Fix:**
  - Check internet connection
  - Try again in a few minutes
  - Check if Firebase is accessible: `ping firestore.googleapis.com`

**Warning: "Failed to sync 5 predictions"**
- **Cause:** Individual sync errors (usually data validation)
- **Fix:**
  - Check the error messages for specific products
  - Usually safe to ignore if most synced successfully

### ✅ Step 5 Complete!
Your predictions are now in Firebase Firestore and accessible from anywhere!

---

## Step 6: View Results

### 🎯 Goal
See your ML predictions in action through the Django dashboard.

### ▶️ Start Django Server

```bash
cd /home/user/Banelo-Forecasting
python manage.py runserver
```

Expected output:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
November 21, 2025 - 11:45:30
Django version 5.2, using settings 'baneloforecasting.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### 🌐 Open Dashboard in Browser

1. **Open your web browser**

2. **Go to the dashboard**
   - URL: http://localhost:8000/dashboard/

3. **Log in** (if not already logged in)
   - Use your admin credentials

### 📊 Navigate to Forecasting Page

1. **Click on "Inventory" in the sidebar** (or top menu)

2. **Click on "Forecasting"** sub-menu

   Or directly visit: http://localhost:8000/dashboard/inventory/forecasting/

### 🎨 What You Should See

**Page Title:** "Inventory Forecasting"

**Model Information Card:**
```
┌─────────────────────────────────────────┐
│ ML Model: Random Forest                │
│ Last Trained: Nov 21, 2025 11:15 AM   │
│ Accuracy: 85%                          │
│ Products Analyzed: 45                  │
│                                        │
│ [Train New Model]                      │
└─────────────────────────────────────────┘
```

**Stock Status Summary:**
```
┌──────────────┬──────────────┬──────────────┐
│   Critical   │     Low      │   Healthy    │
│   (≤3 days)  │  (≤7 days)   │  (>7 days)   │
│      3       │      8       │      34      │
│     🔴       │     🟡       │     🟢       │
└──────────────┴──────────────┴──────────────┘
```

**Predictions Table:**
```
┌────────────────────────────────────────────────────────────────────────────────┐
│ Product         │ Current  │ Daily    │ Days   │ Status   │ Reorder │ Conf.  │
│                 │ Stock    │ Usage    │ Left   │          │ Qty     │ Score  │
├────────────────────────────────────────────────────────────────────────────────┤
│ Milk (2%)      │ 15 L     │ 10.89 L  │ 1.4    │ 🔴 Crit. │ 255 L   │ 87%    │
│ Sugar Packets  │ 500 g    │ 220 g    │ 2.3    │ 🔴 Crit. │ 6100 g  │ 83%    │
│ Coffee Beans   │ 2000 g   │ 710 g    │ 2.8    │ 🔴 Crit. │ 19300g  │ 85%    │
│ Espresso       │ 450 pc   │ 25.34 pc │ 17.8   │ 🟢 Good  │ 310 pc  │ 92%    │
│ Americano      │ 380 pc   │ 18.67 pc │ 20.4   │ 🟢 Good  │ 180 pc  │ 89%    │
│ ...            │ ...      │ ...      │ ...    │ ...      │ ...     │ ...    │
└────────────────────────────────────────────────────────────────────────────────┘
```

**Trend Indicators:**
- 📈 = Growing demand
- 📉 = Declining demand
- ➡️ = Stable

### 🎯 How to Use the Predictions

**For Critical Items (🔴):**
1. **Order immediately!**
   - Click product name to see details
   - Note the recommended reorder quantity
   - Add to shopping list

2. **Monitor closely**
   - These items will run out in 1-3 days
   - May need emergency orders

**For Low Stock Items (🟡):**
1. **Plan reorder for next 2-3 days**
   - Add to weekly order
   - Watch for usage changes

2. **Review trends**
   - If trending up 📈, order extra
   - If trending down 📉, order less

**For Healthy Items (🟢):**
1. **Normal monitoring**
   - Review weekly
   - No immediate action needed

2. **Plan ahead**
   - Note when they'll become "Low"
   - Schedule regular reorders

### 💡 Understanding the Metrics

**Current Stock**
- Your inventory right now
- Updated from products table

**Daily Usage**
- ML prediction of units consumed per day
- Based on 90 days of history

**Days Left**
- Current Stock ÷ Daily Usage
- How long until stockout

**Status**
- 🔴 Critical: ≤3 days
- 🟡 Low: 4-7 days
- 🟢 Healthy: >7 days

**Reorder Qty**
- Suggested amount to order
- Calculated for 30-day supply
- Adjustable based on your needs

**Confidence Score**
- How reliable the prediction is
- 90%+ = Very reliable
- 70-90% = Reliable
- 50-70% = Use with caution

### 📈 View Charts (if available)

Some implementations include:
- **Usage Trends Chart**: Shows past 30 days actual usage
- **Prediction Accuracy**: Compares predictions vs actuals
- **Stock Timeline**: When each item will run out

### 🔄 Retrain Model from Dashboard

If you want to retrain with new data:

1. **Click "Train New Model" button** on the forecasting page

2. **Wait for training** (2-5 minutes)
   - Progress indicator should appear
   - Don't close the page

3. **See updated predictions**
   - Page will refresh automatically
   - New accuracy score shown

Note: This uses the existing Linear Regression model in Django. For best results, retrain in Google Colab monthly.

### ✅ Step 6 Complete!
You can now view and use your ML predictions in the dashboard!

---

## Troubleshooting

### General Issues

**Q: Predictions seem inaccurate**

A: Several possible causes:
1. **Not enough data**
   - Need at least 30 days of consistent sales
   - 90+ days is ideal
   - Solution: Wait and collect more data

2. **Irregular sales patterns**
   - Seasonal items
   - New products
   - Solution: Wait for patterns to stabilize

3. **Data quality issues**
   - Test sales not removed
   - Duplicate entries
   - Solution: Clean up sales data

4. **Model needs updating**
   - Sales patterns changed
   - Solution: Retrain monthly

**Q: Some products missing from predictions**

A: Check these:
1. Product has no sales history
   - Solution: Wait until product has sales

2. Product excluded by category
   - Beverages, water, etc. may be filtered
   - Solution: Modify filter in integration script

3. Database sync issues
   - Solution: Run `python sync_firebase_to_local.py`

**Q: Forecasting page blank/empty**

A: Troubleshoot:
```bash
# Check if predictions exist
python manage.py shell
```
```python
from dashboard.models import MLPrediction
print(f"Predictions: {MLPrediction.objects.count()}")
exit()
```

If 0, run:
```bash
python integrate_ml_model.py
```

**Q: "Days left" shows very high numbers (999+)**

A: This means:
- Product has no usage prediction (predicted_daily_usage = 0)
- Or current stock is very high
- Usually happens with:
  - New products with no sales
  - Inactive products
  - One-time items

**Q: Want to exclude certain products from forecasting**

A: Edit `integrate_ml_model.py`:
```python
# Around line 180, add filter:
products = Product.objects.exclude(
    category__in=['Beverage', 'Water', 'Ice']
).exclude(
    name__icontains='test'  # Exclude test products
)
```

### Performance Issues

**Q: Colab training takes too long (>30 minutes)**

A: Try these:
1. **Use smaller dataset**
   - Reduce to 60 days instead of 90
   - Edit `export_data_for_colab.py` line 32

2. **Reduce model complexity**
   - In Colab, change `n_estimators=100` instead of 200
   - Use Linear Regression only

3. **Check Colab resources**
   - Click Runtime → View resources
   - If RAM full, restart runtime

**Q: Integration script slow**

A: Normal if you have:
- Thousands of sales records
- Dozens of products
- Should complete in 2-5 minutes max

If >10 minutes:
- Check database isn't corrupted
- Restart Django
- Check system resources

### Firebase Issues

**Q: Sync fails intermittently**

A: Could be:
1. **Network timeout**
   - Retry in a few minutes
   - Check internet speed

2. **Firebase quota exceeded**
   - Free tier: 50K reads/day, 20K writes/day
   - Check quota in Firebase Console

3. **Rate limiting**
   - Too many requests too fast
   - Wait 5 minutes and retry

**Q: Can't access Firebase Console**

A: Verify:
- Correct Google account
- Project exists and not deleted
- Invited as owner/editor

### Data Issues

**Q: Negative predictions**

A: Shouldn't happen (code has safeguards)
If it does:
- Check for data corruption
- Re-export and retrain

**Q: All predictions same value**

A: Model didn't train properly:
- Retrain in Colab
- Try different model (XGBoost)
- Check feature engineering worked

**Q: Confidence scores all 50%**

A: Not enough data per product:
- Each product needs 7+ sales records
- Collect more data
- Or acceptable - predictions still useful

---

## Next Steps

### 🎯 Immediate Actions

1. **✅ Review Critical Items**
   - Check red/critical stock items
   - Place orders for items <3 days

2. **✅ Set Up Monitoring**
   - Check dashboard daily
   - Review predictions weekly

3. **✅ Validate Predictions**
   - Compare predictions to actual usage
   - Note any discrepancies
   - Adjust orders accordingly

### 📅 Regular Maintenance

**Daily:**
- Check critical stock items
- Update inventory levels
- Record sales

**Weekly:**
- Review prediction accuracy
- Adjust stock levels
- Plan next week's orders

**Monthly:**
- Retrain ML model in Google Colab
- Export fresh data
- Run full integration
- Analyze trends and patterns

### 🚀 Advanced Features (Optional)

**1. Automate Data Export**
```bash
# Create cron job (Linux/Mac)
crontab -e

# Add line (runs 1st of each month at 2 AM):
0 2 1 * * cd /home/user/Banelo-Forecasting && python export_data_for_colab.py
```

**2. Email Alerts for Critical Stock**
- Set up in Django settings
- Email when items <3 days
- Daily digest of low stock

**3. Custom Dashboards**
- Create category-specific views
- Supplier-based ordering
- Cost analysis

**4. API Integration**
- Access predictions via REST API
- Mobile app integration
- Third-party ordering systems

**5. Advanced Models**
- LSTM for seasonal patterns
- Prophet for holidays
- Ensemble methods

### 📚 Learning More

**Improve Predictions:**
- Add weather data (for seasonal items)
- Include day-of-week patterns
- Account for holidays/events
- Track promotions impact

**Understand ML Better:**
- [Scikit-learn tutorials](https://scikit-learn.org/stable/tutorial/index.html)
- [Random Forest explained](https://www.youtube.com/watch?v=J4Wdy0Wc_xQ)
- [Time series forecasting](https://otexts.com/fpp3/)

**Django Optimization:**
- Database indexing
- Caching predictions
- Background tasks (Celery)

### 🎓 Monthly Retraining Checklist

- [ ] Export fresh data: `python export_data_for_colab.py`
- [ ] Upload to Google Colab
- [ ] Train new model
- [ ] Download model file
- [ ] Place in `ml_models/` (backup old one)
- [ ] Run integration: `python integrate_ml_model.py`
- [ ] Sync to Firebase: `python sync_predictions_to_firebase.py`
- [ ] Verify in dashboard
- [ ] Compare accuracy to last month
- [ ] Document any changes

---

## 🎉 Congratulations!

You've successfully set up machine learning forecasting for your inventory system!

### What You've Accomplished:

✅ Exported 90 days of sales data
✅ Trained a Random Forest ML model
✅ Generated predictions for all products
✅ Integrated with Django database
✅ Synced to Firebase Firestore
✅ Enabled real-time forecasting dashboard

### Results You Can Expect:

📊 **Better Inventory Management**
- Know exactly when to reorder
- Avoid stockouts
- Reduce over-ordering

💰 **Cost Savings**
- Less waste from overstocking
- Fewer emergency orders
- Better supplier negotiations

⏰ **Time Savings**
- Automated predictions
- No manual calculations
- Focus on strategy, not counting

📈 **Business Insights**
- Understand sales trends
- Identify top products
- Plan for growth

---

## Need Help?

**Documentation:**
- This guide (DETAILED_TUTORIAL.md)
- Quick start (QUICK_START.md)
- Full guide (ML_SETUP_GUIDE.md)

**Common Issues:**
- See Troubleshooting section above
- Check error messages carefully
- Verify each step completed

**Questions?**
- Review the guides
- Check Django documentation
- Google Colab documentation
- Firebase documentation

---

**Happy Forecasting! 🚀📊**

*Last updated: November 21, 2025*
