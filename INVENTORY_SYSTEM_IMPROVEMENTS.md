# Inventory System Improvements Documentation

## Overview
This document describes the comprehensive improvements made to the Banelo Coffee POS inventory management and forecasting system. The system now supports a dual-inventory model (Inventory A and Inventory B), waste management, and enhanced recipe management features.

---

## 🆕 New Features Implemented

### 1. **Dual Inventory System**

#### Inventory A (Main Warehouse)
- Represents the main warehouse stock
- Used for bulk storage and inventory management
- Products are transferred from here to Inventory B

#### Inventory B (Expendable Stock)
- Represents stock available for daily operations
- Used for processing orders in the mobile POS
- Can be transferred to waste when items expire or are damaged

#### Database Changes
- Added `inventory_a` field to Product model (Main Warehouse Stock)
- Added `inventory_b` field to Product model (Expendable Stock)
- Added `cost_per_unit` field for ingredient pricing

**Migration File:** `dashboard/migrations/0004_add_dual_inventory_fields.py`

---

### 2. **Inventory Transfer Feature (A → B)**

Allows administrators to transfer stock from Main Warehouse (Inventory A) to Expendable Stock (Inventory B).

#### How to Use:
1. Navigate to Inventory page
2. Select an ingredient product
3. Click the **"Transfer"** button
4. Enter the quantity to transfer
5. Confirm the transfer

#### API Endpoint:
```
POST /dashboard/api/inventory/transfer/
```

**Request Body:**
```json
{
  "productId": "firebase_product_id",
  "quantity": 100.5
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully transferred 100.5 units to Inventory B",
  "newInventoryA": 400.0,
  "newInventoryB": 150.5
}
```

#### Business Logic:
- Validates sufficient stock in Inventory A before transfer
- Automatically deducts from Inventory A
- Automatically adds to Inventory B
- Updates the legacy `quantity` field to match Inventory B (for mobile POS compatibility)

---

### 3. **Waste Management Feature (B → Waste)**

Allows administrators to record waste from Inventory B and automatically log it to the waste_logs collection.

#### How to Use:
1. Navigate to Inventory page
2. Select an ingredient product
3. Click the **"Waste"** button
4. Enter the quantity to record as waste
5. Select a reason (Expired, Damaged, Spoiled, Contaminated, Other)
6. Confirm the waste record

#### API Endpoint:
```
POST /dashboard/api/waste/add/
```

**Request Body:**
```json
{
  "productId": "firebase_product_id",
  "quantity": 25.0,
  "reason": "Expired"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully recorded 25.0 units as waste",
  "newInventoryB": 125.5
}
```

#### Waste Log Entry:
```json
{
  "productFirebaseId": "abc123",
  "productName": "Sugar",
  "quantity": 25.0,
  "reason": "Expired",
  "wasteDate": "2025-11-22 14:30:00",
  "recordedBy": "admin",
  "category": "Ingredients"
}
```

---

### 4. **Enhanced Recipe Management**

#### Ingredient Details in Recipe View
Each ingredient now displays:
- **Cost per unit** (₱ per gram/ml)
- **Current total stock** (Inventory A + Inventory B)

#### Recipe Card Display:
```
Ingredient Name                    Quantity
  Cost: ₱0.50/g    Stock: 1500g
```

#### Ingredient Dropdown Enhancement:
When adding or editing recipes, the ingredient dropdown shows:
```
Butter - Stock: 1000g - Cost: ₱0.3/g
```

This helps administrators:
- Understand ingredient costs when creating recipes
- Check stock availability before adding ingredients
- Calculate recipe costs more easily

---

### 5. **Available Servings for Beverages**

For recipe-based products (beverages and pastries), the system displays **available servings** instead of raw stock count.

#### How It Works:
- Calculates the maximum number of servings based on ingredient availability
- Takes the bottleneck ingredient (ingredient with lowest possible servings)
- Displays "Stock: X servings" instead of quantity

**Example:**
```
Latte Recipe:
- 20g Coffee Beans (available: 1000g) = 50 servings
- 200ml Milk (available: 5000ml) = 25 servings
→ Max servings: 25 (limited by milk)
```

---

### 6. **Inventory Display Improvements**

#### Product Cards Now Show:
```
┌─────────────────────────┐
│  Product Name           │
│  ₱ 150.00              │
│  Category: Ingredients  │
│                        │
│  🏭 Inv A: 500g        │
│  📦 Inv B: 150g        │
│  💰 Cost: ₱0.50/g      │
│                        │
│  [Transfer] [Waste]    │
└─────────────────────────┘
```

**For Beverages with Recipes:**
```
┌─────────────────────────┐
│  Cappuccino            │
│  ₱ 120.00             │
│  Category: Beverage    │
│                        │
│  🧮 Stock: 45 servings │
└─────────────────────────┘
```

---

## 📊 Firebase Database Structure

### Products Collection
```json
{
  "name": "Sugar",
  "category": "Ingredients",
  "price": 50.0,
  "inventoryA": 500.0,
  "inventoryB": 150.0,
  "costPerUnit": 0.50,
  "quantity": 150.0,  // Legacy field (matches inventoryB)
  "imageUri": "https://...",
  "createdAt": "2025-11-22 10:00:00"
}
```

### Waste Logs Collection
```json
{
  "productFirebaseId": "abc123",
  "productName": "Sugar",
  "quantity": 25.0,
  "reason": "Expired",
  "wasteDate": "2025-11-22 14:30:00",
  "recordedBy": "admin",
  "category": "Ingredients"
}
```

### Recipe Ingredients Collection
```json
{
  "recipeFirebaseId": "recipe_xyz",
  "ingredientFirebaseId": "ingredient_abc",
  "ingredientName": "Coffee Beans",
  "quantityNeeded": 20.0,
  "unit": "g",
  "syncedFromLocal": true
}
```

---

## 🔄 Order Deduction Logic (Mobile POS)

**IMPORTANT:** When processing orders in the mobile POS, always deduct ingredients from **Inventory B** first.

### Recommended Implementation (Mobile POS):
```javascript
async function processOrder(recipeId, quantity) {
    // Get recipe ingredients
    const ingredients = await getRecipeIngredients(recipeId);

    for (const ingredient of ingredients) {
        const needed = ingredient.quantityNeeded * quantity;
        const product = await getProduct(ingredient.ingredientFirebaseId);

        // ALWAYS deduct from Inventory B first
        if (product.inventoryB >= needed) {
            // Sufficient stock in Inventory B
            await updateProduct(product.id, {
                inventoryB: product.inventoryB - needed,
                quantity: product.inventoryB - needed
            });
        } else {
            // Insufficient stock in Inventory B
            // Option 1: Show "Out of Stock" error
            throw new Error(`Insufficient stock in Inventory B for ${ingredient.name}`);

            // Option 2: Fallback to Inventory A (if you want to implement this)
            // const remainingNeeded = needed - product.inventoryB;
            // if (product.inventoryA >= remainingNeeded) {
            //     await updateProduct(product.id, {
            //         inventoryB: 0,
            //         inventoryA: product.inventoryA - remainingNeeded,
            //         quantity: 0
            //     });
            // }
        }
    }
}
```

---

## 🎯 User Workflows

### Workflow 1: Restocking Ingredients
1. Purchase ingredients from supplier
2. Add to **Inventory A** (Main Warehouse) via mobile POS or web interface
3. Transfer needed quantities to **Inventory B** (Expendable Stock) via web interface
4. Mobile POS uses Inventory B for daily operations

### Workflow 2: Processing Daily Orders
1. Customer places order in mobile POS
2. System calculates ingredient requirements from recipe
3. System deducts ingredients from **Inventory B**
4. If Inventory B is low, admin transfers more from Inventory A

### Workflow 3: Managing Waste
1. Admin identifies expired/damaged items in Inventory B
2. Opens waste management modal
3. Enters quantity and selects reason
4. System automatically:
   - Deducts from Inventory B
   - Creates waste log entry
   - Maintains audit trail

### Workflow 4: Recipe Management
1. Admin creates or edits beverage recipe
2. Adds ingredients with quantities
3. System shows real-time:
   - Ingredient costs
   - Current stock levels
   - Available servings calculation

---

## 🔧 Technical Implementation

### Files Modified:
1. **`dashboard/models.py`** - Added inventory_a, inventory_b, cost_per_unit fields
2. **`dashboard/views.py`** - Added transfer and waste API endpoints, updated inventory view
3. **`dashboard/urls.py`** - Added API routes for transfer and waste
4. **`dashboard/templates/dashboard/inventory.html`** - Added dual inventory display, transfer/waste modals
5. **`dashboard/templates/dashboard/recipes.html`** - Enhanced ingredient display with cost and stock
6. **`dashboard/migrations/0004_add_dual_inventory_fields.py`** - Database migration

### New API Endpoints:
- `POST /dashboard/api/inventory/transfer/` - Transfer Inventory A → B
- `POST /dashboard/api/waste/add/` - Record waste from Inventory B

### JavaScript Functions Added:
- `openTransferModal()` - Opens inventory transfer modal
- `closeTransferModal()` - Closes inventory transfer modal
- `openWasteModal()` - Opens waste management modal
- `closeWasteModal()` - Closes waste management modal
- Transfer form submission handler with validation
- Waste form submission handler with validation

---

## 📈 Benefits

### For Administrators:
- ✅ Clear separation of warehouse stock vs operational stock
- ✅ Better inventory tracking and accountability
- ✅ Automatic waste logging with reasons
- ✅ Real-time cost visibility for ingredients
- ✅ More accurate available servings calculation
- ✅ Enhanced recipe management with stock and cost information

### For Business Operations:
- ✅ Prevents stockouts by maintaining buffer in Inventory A
- ✅ Improves waste management and tracking
- ✅ Better cost control and recipe pricing
- ✅ Audit trail for all inventory movements
- ✅ Data-driven decisions for purchasing and inventory planning

---

## 🧪 Testing Recommendations

### Test Cases:
1. **Transfer Inventory:**
   - Transfer valid quantity from A to B
   - Attempt transfer with insufficient stock in A
   - Verify both inventories update correctly

2. **Waste Management:**
   - Record waste with valid quantity
   - Attempt waste with insufficient stock in B
   - Verify waste log entry is created
   - Check all waste reasons work correctly

3. **Recipe Management:**
   - Create recipe with multiple ingredients
   - Edit existing recipe
   - Verify cost and stock display correctly
   - Check available servings calculation

4. **Order Processing (Mobile POS):**
   - Process order with sufficient Inventory B
   - Process order with low Inventory B
   - Verify correct deductions from Inventory B

---

## 🚀 Future Enhancements

### Potential Additions:
1. **Automatic Reorder Alerts:**
   - Notify when Inventory A or B falls below threshold
   - Suggest transfer from A to B when B is low

2. **Waste Analytics Dashboard:**
   - Track waste trends over time
   - Identify products with high waste rates
   - Calculate waste costs

3. **Inventory Audit Trail:**
   - Log all inventory movements
   - Track who performed transfers/waste records
   - Generate audit reports

4. **Batch Transfers:**
   - Transfer multiple products at once
   - Scheduled automatic transfers

5. **Cost Analytics:**
   - Calculate recipe costs automatically
   - Track ingredient price changes over time
   - Profit margin calculations per product

---

## 📞 Support

For questions or issues:
1. Check Firebase console for data integrity
2. Review browser console for JavaScript errors
3. Check Django logs for server-side errors
4. Verify Firebase credentials and permissions

---

**Last Updated:** November 22, 2025
**Version:** 1.0
**Author:** Development Team
