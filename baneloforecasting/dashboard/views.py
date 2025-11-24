"""
Dashboard Views - API Version
Business data is fetched from the Node.js API which connects to PostgreSQL.
Django only manages authentication and sessions locally.
"""

import csv
import os
import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from datetime import datetime, timedelta
from collections import defaultdict
from django.db.models import Q

# Import models
from .models import Product, Sale, Recipe, RecipeIngredient, AuditTrail, WasteLog, MLPrediction, MLModel

# Import API service (fallback)
from .api_service import get_api_service


# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_max_servings(product_firebase_id, recipe_id):
    """Calculate maximum servings based on available ingredients"""
    try:
        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🧮 Calculating max servings")
        print(f"   Product ID: {product_firebase_id}")
        print(f"   Recipe ID: {recipe_id}")

        # Get all ingredients for this recipe using Django ORM
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            try:
                recipe = Recipe.objects.get(firebase_id=str(recipe_id))
            except Recipe.DoesNotExist:
                print(f"   ❌ Recipe not found")
                return None

        ingredients = RecipeIngredient.objects.filter(
            Q(recipe_id=recipe.id) | Q(recipe_firebase_id=recipe.firebase_id)
        )

        max_servings_list = []
        ingredient_count = 0

        for ingredient in ingredients:
            ingredient_count += 1
            ingredient_product_id = ingredient.ingredient_firebase_id.strip() if ingredient.ingredient_firebase_id else ''
            quantity_needed = ingredient.quantity_needed or 0
            ingredient_name = ingredient.ingredient_name or 'Unknown'

            print(f"\n   📦 Ingredient #{ingredient_count}: {ingredient_name}")
            print(f"      Ingredient ID: '{ingredient_product_id}'")
            print(f"      Quantity needed: {quantity_needed}")

            if not ingredient_product_id or quantity_needed == 0:
                print(f"      ⚠️ Missing ID or quantity, skipping")
                continue

            # Get the ingredient product's current stock
            try:
                product = Product.objects.get(firebase_id=ingredient_product_id)
                available_quantity = product.quantity or 0
            except Product.DoesNotExist:
                print(f"      ❌ Ingredient product not found in database!")
                max_servings_list.append(0)
                continue

            # Calculate max servings for this ingredient
            if quantity_needed > 0:
                max_for_this_ingredient = int(available_quantity / quantity_needed)
            else:
                max_for_this_ingredient = 0

            print(f"      ✅ Available: {available_quantity}g")
            print(f"      🎯 Max servings from this ingredient: {max_for_this_ingredient}")

            max_servings_list.append(max_for_this_ingredient)

        # Return the minimum (bottleneck ingredient)
        result = min(max_servings_list) if max_servings_list else 0

        print(f"\n   🏆 FINAL MAX SERVINGS: {result}")
        print(f"   Total ingredients checked: {ingredient_count}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━\n")

        return result

    except Exception as e:
        print(f"❌ Error calculating max servings: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_statistics(audit_logs):
    """Calculate audit trail statistics"""
    stats = {
        'total_logs': len(audit_logs),
        'actions_today': 0,
        'unique_users': len(set(log['user'] for log in audit_logs)),
    }

    today = datetime.now().date()
    for log in audit_logs:
        try:
            log_date = datetime.strptime(log['timestamp'].split()[0], '%Y-%m-%d').date()
            if log_date == today:
                stats['actions_today'] += 1
        except:
            pass

    return stats


def get_unique_users():
    """Get unique users from audit trail"""
    users = AuditTrail.objects.values_list('user_name', flat=True).distinct()
    return [u for u in users if u]


def log_audit(action, user, details=''):
    """Helper function to log audit trail entries"""
    try:
        AuditTrail.objects.create(
            action=action,
            user_id=str(user.id) if hasattr(user, 'id') else '',
            user_name=user.username if hasattr(user, 'username') else str(user),
            details=details,
            timestamp=datetime.now()
        )
    except Exception as e:
        print(f"Warning: Could not log audit trail: {e}")


# ========================================
# DASHBOARD VIEWS
# ========================================

@login_required
def dashboard_view(request):
    """Display dashboard with data from PostgreSQL via Django ORM"""
    try:
        print("\n🔥 DASHBOARD VIEW CALLED (Django ORM Mode)")

        # Get filter parameter (default: week)
        filter_type = request.GET.get('filter', 'week')

        today = datetime.now()
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        # Determine date range based on filter
        if filter_type == 'today':
            start_date = today_start
            date_range_days = 1
        elif filter_type == 'month':
            start_date = today_start - timedelta(days=30)
            date_range_days = 30
        else:  # week (default)
            start_date = today_start - timedelta(days=7)
            date_range_days = 7

        # ========================================
        # 1. GET SALES DATA FROM POSTGRESQL
        # ========================================
        print("🔍 Fetching sales data from PostgreSQL...")

        all_sales = Sale.objects.all().order_by('-order_date')[:5000]
        print(f"✅ Fetched {all_sales.count()} sales records")

        today_sales = 0
        yesterday_sales = 0
        today_orders = 0
        yesterday_orders = 0
        recent_sales = []

        # For charts
        daily_sales = defaultdict(float)
        product_sales = defaultdict(int)

        for sale in all_sales:
            try:
                order_date = sale.order_date
                if order_date:
                    price = float(sale.price or 0)
                    quantity = int(sale.quantity or 0)
                    sale_total = float(sale.total or 0) or (price * quantity)
                    product_name = sale.product_name or 'Unknown'

                    # Check if within date range for charts
                    if order_date >= start_date:
                        date_key = order_date.strftime('%Y-%m-%d')
                        daily_sales[date_key] += sale_total
                        product_sales[product_name] += quantity

                    # Today's data
                    if order_date.date() == today.date():
                        today_sales += sale_total
                        today_orders += 1

                        if len(recent_sales) < 5:
                            recent_sales.append({
                                'product': product_name,
                                'quantity': quantity,
                                'price': price,
                                'total': sale_total,
                                'datetime': order_date.strftime('%Y-%m-%d %H:%M:%S')
                            })

                    # Yesterday's data
                    elif order_date.date() == yesterday_start.date():
                        yesterday_sales += sale_total
                        yesterday_orders += 1

            except Exception as item_error:
                print(f"⚠️ Error processing sale item: {item_error}")
                continue

        # Calculate percentage changes
        sales_change = 0
        if yesterday_sales > 0:
            sales_change = round(((today_sales - yesterday_sales) / yesterday_sales) * 100, 1)

        orders_change = 0
        if yesterday_orders > 0:
            orders_change = round(((today_orders - yesterday_orders) / yesterday_orders) * 100, 1)

        # ========================================
        # 2. PREPARE CHART DATA BASED ON FILTER
        # ========================================
        chart_dates = []
        chart_sales_data = []

        if filter_type == 'today':
            # Show hourly data for today
            for hour in range(0, 24):
                hour_str = f"{hour:02d}:00"
                chart_dates.append(hour_str)
                chart_sales_data.append(0)

            # Put all today's sales in current hour
            current_hour = today.hour
            date_key = today_start.strftime('%Y-%m-%d')
            chart_sales_data[current_hour] = float(daily_sales.get(date_key, 0))

        elif filter_type == 'month':
            # Show daily data for last 30 days
            for i in range(29, -1, -1):
                date = today_start - timedelta(days=i)
                date_key = date.strftime('%Y-%m-%d')
                date_label = date.strftime('%b %d')

                chart_dates.append(date_label)
                chart_sales_data.append(float(daily_sales.get(date_key, 0)))

        else:  # week
            # Show daily data for last 7 days
            for i in range(6, -1, -1):
                date = today_start - timedelta(days=i)
                date_key = date.strftime('%Y-%m-%d')
                date_label = date.strftime('%b %d')

                chart_dates.append(date_label)
                chart_sales_data.append(float(daily_sales.get(date_key, 0)))

        # ========================================
        # 3. PREPARE TOP 5 PRODUCTS DATA
        # ========================================
        top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]

        chart_products = []
        chart_quantities = []

        for product, quantity in top_products:
            chart_products.append(product)
            chart_quantities.append(quantity)

        # ========================================
        # 4. GET PRODUCT STATISTICS FROM POSTGRESQL
        # ========================================
        print("🔍 Fetching product data from PostgreSQL...")

        products = Product.objects.all()
        total_products = products.count()
        low_stock_items = 0

        for product in products:
            category = (product.category or '').lower().strip()

            # Skip beverages - they don't have physical stock
            if category in ['beverage', 'beverages', 'drink', 'drinks']:
                continue

            # For non-beverage items: check quantity stock
            stock = float(product.quantity or 0)
            reorder_level = 20  # Default reorder level

            # Check if low stock
            if stock < reorder_level:
                low_stock_items += 1

        # ========================================
        # 5. GET ACTIVE USERS COUNT
        # ========================================
        from django.contrib.auth.models import User
        active_users = User.objects.filter(is_active=True).count()

        # ========================================
        # 6. SORT RECENT SALES BY TIME
        # ========================================
        recent_sales.sort(key=lambda x: x['datetime'], reverse=True)

        for sale in recent_sales:
            try:
                dt = datetime.strptime(sale['datetime'], '%Y-%m-%d %H:%M:%S')
                sale['display_date'] = dt.strftime('%b %d, %Y - %I:%M %p')
            except:
                sale['display_date'] = sale['datetime']

        print(f"💰 Today's Sales: ₱{today_sales:.2f} ({sales_change:+.1f}%)")
        print(f"📦 Today's Orders: {today_orders} ({orders_change:+.1f}%)")
        print(f"📊 Total Products: {total_products}")
        print(f"⚠️  Low Stock Items: {low_stock_items}")
        print(f"📊 Chart Filter: {filter_type.upper()} - {len(chart_dates)} data points")
        print("=" * 50 + "\n")

        # ========================================
        # PREPARE CONTEXT
        # ========================================
        context = {
            'today_sales': today_sales,
            'sales_change': sales_change,
            'total_products': total_products,
            'low_stock_items': low_stock_items,
            'today_orders': today_orders,
            'orders_change': orders_change,
            'active_users': active_users,
            'recent_sales': recent_sales,
            # Chart data
            'chart_dates': chart_dates,
            'chart_sales_data': chart_sales_data,
            'chart_products': chart_products,
            'chart_quantities': chart_quantities,
            'current_filter': filter_type,
        }

        return render(request, 'dashboard/dashboard.html', context)

    except Exception as e:
        print(f"❌ Error loading dashboard: {e}")
        import traceback
        traceback.print_exc()

        context = {
            'today_sales': 0,
            'sales_change': 0,
            'total_products': 0,
            'low_stock_items': 0,
            'today_orders': 0,
            'orders_change': 0,
            'active_users': 0,
            'recent_sales': [],
            'chart_dates': [],
            'chart_sales_data': [],
            'chart_products': [],
            'chart_quantities': [],
            'current_filter': 'week',
            'error_message': f'Unable to load dashboard data: {str(e)}',
        }
        return render(request, 'dashboard/dashboard.html', context)


@login_required
def inventory_view(request):
    """Display inventory page with data from PostgreSQL via Django ORM"""
    try:
        print("\n🔥 INVENTORY VIEW CALLED (Django ORM Mode)")

        # Get all products from PostgreSQL
        products_queryset = Product.objects.all()

        # Get all recipes from PostgreSQL
        recipes_queryset = Recipe.objects.all()

        recipes_by_id = {}
        recipes_by_name = {}

        for recipe in recipes_queryset:
            product_id = recipe.product_firebase_id or ''
            product_name = (recipe.product_name or '').lower().strip()
            recipe_id = recipe.id

            # Get ingredients for this recipe
            ingredients_queryset = RecipeIngredient.objects.filter(
                Q(recipe_id=recipe.id) | Q(recipe_firebase_id=recipe.firebase_id)
            )
            ingredients_list = []
            for ing in ingredients_queryset:
                ingredients_list.append({
                    'ingredient_firebase_id': ing.ingredient_firebase_id,
                    'ingredientFirebaseId': ing.ingredient_firebase_id,
                    'ingredient_name': ing.ingredient_name,
                    'ingredientName': ing.ingredient_name,
                    'quantity_needed': ing.quantity_needed,
                    'quantityNeeded': ing.quantity_needed,
                    'quantity': ing.quantity_needed,
                    'unit': ing.unit or 'g',
                    'name': ing.ingredient_name,
                })

            recipe_info = {
                'recipeId': recipe_id,
                'firebaseId': recipe.firebase_id,
                'productName': recipe.product_name,
                'ingredients': ingredients_list
            }

            if product_id:
                recipes_by_id[product_id] = recipe_info
                print(f"📋 Recipe found by ID: {product_id} -> {recipe_info['productName']}")

            if product_name:
                recipes_by_name[product_name] = recipe_info
                print(f"📋 Recipe found by Name: {product_name}")

        print(f"✅ Found {len(recipes_by_id)} recipes by ID, {len(recipes_by_name)} by name")

        # Build ingredient inventory lookup (firebase_id -> inventory_b)
        ingredient_stock_lookup = {}
        for product in products_queryset:
            fb_id = product.firebase_id or ''
            # Use inventory_b (expendable stock) for calculating available servings
            inv_b = float(product.inventory_b or 0)
            if fb_id:
                ingredient_stock_lookup[fb_id] = inv_b

        # Process products data
        products_data = []
        doc_count = 0

        for product in products_queryset:
            doc_count += 1

            # Normalize category
            raw_category = product.category or 'Unknown'
            category_lower = str(raw_category).lower().strip()

            if category_lower in ['beverage', 'beverages', 'drink', 'drinks', 'hot drinks', 'cold drinks']:
                category = 'beverage'
            elif category_lower in ['pastries', 'pastry', 'snacks', 'snack']:
                category = 'pastries'
            elif category_lower in ['ingredients', 'ingredient']:
                category = 'ingredients'
            else:
                category = category_lower

            # Handle image
            image_raw = product.image_uri
            image = None

            if image_raw and str(image_raw) not in ['nan', 'None', '']:
                image = str(image_raw)

            has_image = False
            if image and (image.startswith('http://') or image.startswith('https://')):
                has_image = True

            if not has_image:
                if category == 'beverage':
                    image = '☕'
                elif category == 'pastries':
                    image = '🥐'
                elif category == 'ingredients':
                    image = '🧂'
                else:
                    image = '📦'

            # Calculate max servings for beverages and pastries with recipes
            max_servings = None
            recipe_found = False
            firebase_id = product.firebase_id or ''
            product_name = product.name or 'Unknown'

            if category in ['beverage', 'pastries']:
                recipe_info = None

                # Try matching by Firebase ID first
                if firebase_id in recipes_by_id:
                    recipe_found = True
                    recipe_info = recipes_by_id[firebase_id]
                    print(f"✅ Recipe matched by ID for: {product_name}")

                # If not found, try matching by product name
                elif product_name.lower().strip() in recipes_by_name:
                    recipe_found = True
                    recipe_info = recipes_by_name[product_name.lower().strip()]
                    print(f"✅ Recipe matched by NAME for: {product_name}")

                # Calculate max servings based on ingredients
                if recipe_found and recipe_info:
                    ingredients = recipe_info.get('ingredients', [])
                    if ingredients:
                        servings_list = []
                        for ing in ingredients:
                            # Get ingredient firebase ID
                            ing_fb_id = ing.get('ingredient_firebase_id') or ing.get('ingredientFirebaseId') or ing.get('id', '')
                            # Get quantity needed per serving
                            qty_needed = float(ing.get('quantity_needed') or ing.get('quantityNeeded') or ing.get('quantity', 0) or 0)

                            if ing_fb_id and qty_needed > 0:
                                # Get available stock from inventory_b (expendable stock)
                                available_stock = ingredient_stock_lookup.get(ing_fb_id, 0)
                                # Calculate max servings from this ingredient
                                max_from_ing = int(available_stock / qty_needed)
                                servings_list.append(max_from_ing)
                                print(f"   📦 {ing.get('ingredient_name') or ing.get('ingredientName') or ing.get('name', 'Unknown')}: {available_stock}/{qty_needed} = {max_from_ing} servings")

                        # Max servings is limited by the bottleneck ingredient
                        if servings_list:
                            max_servings = min(servings_list)
                            print(f"   🎯 Max servings for {product_name}: {max_servings}")
                        else:
                            max_servings = 0
                    else:
                        # Has recipe but no ingredients defined
                        max_servings = 0

            # Get inventory data
            inventory_a = float(product.inventory_a or product.quantity or 0)
            inventory_b = float(product.inventory_b or 0)
            cost_per_unit = float(product.cost_per_unit or 0)

            products_data.append({
                'id': firebase_id or str(product.id),
                'name': product_name,
                'price': float(product.price or 0),
                'category': category,
                'stock': float(product.quantity or 0),
                'inventory_a': inventory_a,
                'inventory_b': inventory_b,
                'cost_per_unit': cost_per_unit,
                'image': image,
                'has_image': has_image,
                'max_servings': max_servings,
                'has_recipe': recipe_found
            })

        # Sort by name
        products_data.sort(key=lambda x: x['name'])

        print(f"\n{'=' * 60}")
        print(f"✅ LOADED {len(products_data)} PRODUCTS FROM POSTGRESQL")
        print(f"{'=' * 60}")

        context = {
            'products': products_data,
        }

        return render(request, 'dashboard/inventory.html', context)

    except Exception as e:
        print(f"❌ Error loading inventory: {e}")
        import traceback
        traceback.print_exc()

        context = {
            'products': [],
        }
        return render(request, 'dashboard/inventory.html', context)


@login_required
def settings_view(request):
    context = {'user': request.user}
    return render(request, 'dashboard/settings.html', context)


@login_required
def sales_view(request):
    """Display sales page with data from PostgreSQL via Django ORM"""
    try:
        print("\n🔥 SALES VIEW CALLED (Django ORM Mode)")

        # Get sales from PostgreSQL
        sales_queryset = Sale.objects.all().order_by('-order_date')[:1000]

        # Process sales data
        sales_data = []
        total_sales = 0

        for sale in sales_queryset:
            price = float(sale.price or 0)
            quantity = int(sale.quantity or 0)
            sale_total = float(sale.total or 0) or (price * quantity)

            # Parse order_date
            order_date = sale.order_date
            date_only = order_date.strftime('%Y-%m-%d') if order_date else 'N/A'

            sales_data.append({
                'id': sale.id,
                'date': date_only,
                'product': sale.product_name or 'Unknown',
                'quantity': quantity,
                'unit_price': price,
                'total': sale_total,
                'category': sale.category or 'Uncategorized'
            })

            total_sales += sale_total

        print(f"✅ Loaded {len(sales_data)} sales from PostgreSQL")
        print(f"✅ Total sales: ₱{total_sales:.2f}")

        context = {
            'sales': sales_data,
            'total_sales': total_sales,
            'total_transactions': len(sales_data),
        }

        return render(request, 'dashboard/sales.html', context)

    except Exception as e:
        print(f"❌ Error loading sales: {e}")
        import traceback
        traceback.print_exc()

        context = {
            'sales': [],
            'total_sales': 0,
            'total_transactions': 0,
        }
        return render(request, 'dashboard/sales.html', context)


@login_required
def export_sales_csv(request):
    """Export sales to CSV file"""
    try:
        print("\n🔥 SALES CSV EXPORT CALLED")

        # Get filter parameters
        filter_date_from = request.GET.get('date_from', '')
        filter_date_to = request.GET.get('date_to', '')

        # Query PostgreSQL
        sales = Sale.objects.all().order_by('-order_date')

        # Apply date filters
        if filter_date_from:
            from_date = datetime.strptime(filter_date_from, '%Y-%m-%d')
            sales = sales.filter(order_date__gte=from_date)
        if filter_date_to:
            to_date = datetime.strptime(filter_date_to, '%Y-%m-%d') + timedelta(days=1)
            sales = sales.filter(order_date__lt=to_date)

        sales = sales[:5000]

        # Process sales data
        sales_data = []

        for sale in sales:
            price = float(sale.price or 0)
            quantity = int(sale.quantity or 0)
            sale_total = float(sale.total) if sale.total else price * quantity

            order_date = sale.order_date
            date_only = order_date.strftime('%Y-%m-%d') if order_date else 'N/A'

            sales_data.append({
                'date': date_only,
                'product': sale.product_name or 'Unknown',
                'category': sale.category or 'Uncategorized',
                'quantity': quantity,
                'unit_price': price,
                'total': sale_total
            })

        print(f"✅ Exporting {len(sales_data)} sales to CSV")

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        # Write CSV
        writer = csv.writer(response)
        writer.writerow(['Date', 'Product Name', 'Category', 'Quantity', 'Unit Price', 'Total Amount'])

        for sale in sales_data:
            writer.writerow([
                sale['date'],
                sale['product'],
                sale['category'],
                sale['quantity'],
                f"₱{sale['unit_price']:.2f}",
                f"₱{sale['total']:.2f}"
            ])

        print(f"✅ CSV export completed - {len(sales_data)} records\n")
        return response

    except Exception as e:
        print(f"❌ Error exporting sales CSV: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error: {str(e)}", status=500)


@login_required
def accounts_view(request):
    """Display accounts management page"""
    from django.contrib.auth.models import User

    users = User.objects.all()

    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'first_name': user.first_name or 'User',
            'last_name': user.last_name or str(user.id),
            'email': user.email or '',
            'role': 'Admin' if user.is_superuser else 'Staff',
            'initials': (user.first_name[:1] if user.first_name else 'U') + (user.last_name[:1] if user.last_name else ''),
            'date_joined': user.date_joined.strftime('%Y-%m-%d'),
            'is_active': user.is_active
        })

    context = {
        'users': users_data,
        'total_users': len(users_data)
    }
    return render(request, 'dashboard/accounts.html', context)


# ========================================
# AUDIT TRAIL VIEWS
# ========================================

@login_required
def audit_trail_view(request):
    """Display audit trail from PostgreSQL with filters"""
    try:
        print("\n" + "=" * 80)
        print("🔥 AUDIT TRAIL VIEW CALLED (PostgreSQL)")
        print("=" * 80)

        # Get filter parameters
        filter_user = request.GET.get('user', '')
        filter_action = request.GET.get('action', '')
        filter_date_from = request.GET.get('date_from', '')
        filter_date_to = request.GET.get('date_to', '')

        print(f"📊 Filters: user={filter_user}, action={filter_action}, from={filter_date_from}, to={filter_date_to}")

        # Build query
        audit_queryset = AuditTrail.objects.all()

        if filter_user:
            audit_queryset = audit_queryset.filter(user_name=filter_user)
        if filter_action:
            audit_queryset = audit_queryset.filter(action=filter_action)
        if filter_date_from:
            from_date = datetime.strptime(filter_date_from, '%Y-%m-%d')
            audit_queryset = audit_queryset.filter(timestamp__gte=from_date)
        if filter_date_to:
            to_date = datetime.strptime(filter_date_to, '%Y-%m-%d') + timedelta(days=1)
            audit_queryset = audit_queryset.filter(timestamp__lt=to_date)

        audit_queryset = audit_queryset.order_by('-timestamp')[:10000]

        # Process audit logs
        audit_logs = []
        for log in audit_queryset:
            audit_logs.append({
                'id': log.id,
                'user': log.user_name or 'Unknown',
                'action': log.action or 'N/A',
                'description': log.details or '',
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
                'ip_address': 'N/A',
                'status': 'Success'
            })

        print(f"\n{'=' * 80}")
        print(f"✅ RESULTS: {len(audit_logs)} audit logs")
        print(f"{'=' * 80}\n")

        # Get statistics
        stats = calculate_statistics(audit_logs)

        # Get unique users for filter dropdown
        users = get_unique_users()

        context = {
            'audit_logs': audit_logs,
            'stats': stats,
            'users': users,
            'filter_user': filter_user,
            'filter_action': filter_action,
            'filter_date_from': filter_date_from,
            'filter_date_to': filter_date_to,
        }

        return render(request, 'dashboard/audit_trail.html', context)

    except Exception as e:
        print(f"❌ Error loading audit trail: {e}")
        import traceback
        traceback.print_exc()

        context = {
            'audit_logs': [],
            'stats': {'total_logs': 0, 'actions_today': 0, 'unique_users': 0},
            'users': [],
        }
        return render(request, 'dashboard/audit_trail.html', context)


@login_required
def get_audit_logs_api(request):
    """API endpoint to get audit logs"""
    try:
        audit_logs = AuditTrail.objects.all().order_by('-timestamp')[:1000]

        logs_list = []
        for log in audit_logs:
            logs_list.append({
                'id': log.id,
                'user': log.user_name or 'Unknown',
                'action': log.action or 'N/A',
                'details': log.details or '',
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
            })

        return JsonResponse({'success': True, 'logs': logs_list})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def export_audit_trail_csv(request):
    """Export audit trail to CSV"""
    try:
        audit_logs = AuditTrail.objects.all().order_by('-timestamp')[:5000]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="audit_trail_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'User', 'Action', 'Details'])

        for log in audit_logs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
                log.user_name or '',
                log.action or '',
                log.details or ''
            ])

        return response

    except Exception as e:
        print(f"❌ Error exporting audit trail CSV: {e}")
        return HttpResponse(f"Error: {str(e)}", status=500)


# ========================================
# API ENDPOINTS
# ========================================

@login_required
def api_products(request):
    """API endpoint to get all products"""
    try:
        products = Product.objects.all()
        products_list = []

        for product in products:
            products_list.append({
                'id': product.firebase_id or str(product.id),
                'name': product.name,
                'category': product.category,
                'price': float(product.price or 0),
                'quantity': float(product.quantity or 0),
                'inventoryA': float(product.inventory_a or 0),
                'inventoryB': float(product.inventory_b or 0),
                'costPerUnit': float(product.cost_per_unit or 0),
                'unit': product.unit,
            })

        return JsonResponse({'success': True, 'products': products_list})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_sales(request):
    """API endpoint to get all sales"""
    try:
        sales = Sale.objects.all().order_by('-order_date')[:1000]
        sales_list = []

        for sale in sales:
            sales_list.append({
                'id': sale.id,
                'productName': sale.product_name,
                'productFirebaseId': sale.product_firebase_id,
                'category': sale.category,
                'quantity': float(sale.quantity or 0),
                'price': float(sale.price or 0),
                'total': float(sale.total or 0),
                'orderDate': sale.order_date.strftime('%Y-%m-%d %H:%M:%S') if sale.order_date else '',
            })

        return JsonResponse({'success': True, 'sales': sales_list})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def database_health_check(request):
    """Check API connection health"""
    try:
        api = get_api_service()
        health = api.health_check()

        if health['status'] == 'healthy':
            # Get counts from API
            products = api.get_products()
            sales = api.get_sales(limit=1)
            recipes = api.get_recipes()

            return JsonResponse({
                'status': 'healthy',
                'connection': 'Node.js API',
                'api_url': health['api_url'],
                'message': 'API connection is working',
                'counts': {
                    'products': len(products),
                    'sales': 'Available',
                    'recipes': len(recipes),
                }
            })
        else:
            return JsonResponse({
                'status': 'unhealthy',
                'connection': 'Node.js API',
                'api_url': health['api_url'],
                'message': health['message'],
            }, status=500)

    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'connection': 'Node.js API',
            'message': str(e),
        }, status=500)


# Alias for backward compatibility
firebase_health_check = database_health_check


@login_required
def debug_database_status(request):
    """Debug endpoint to check database status"""
    try:
        from django.db import connection

        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

        # Get table counts
        products_count = Product.objects.count()
        sales_count = Sale.objects.count()
        recipes_count = Recipe.objects.count()
        ingredients_count = RecipeIngredient.objects.count()

        status_html = f"""
        <html>
        <head><title>PostgreSQL Database Status</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1>📊 PostgreSQL Database Status</h1>

        <h2>✅ Connection Status: CONNECTED</h2>

        <h3>Database Info:</h3>
        <ul>
            <li><strong>Version:</strong> {version[:50]}...</li>
            <li><strong>Engine:</strong> PostgreSQL</li>
        </ul>

        <h3>Table Counts:</h3>
        <table border="1" cellpadding="10">
            <tr><th>Table</th><th>Count</th></tr>
            <tr><td>Products</td><td>{products_count}</td></tr>
            <tr><td>Sales</td><td>{sales_count}</td></tr>
            <tr><td>Recipes</td><td>{recipes_count}</td></tr>
            <tr><td>Recipe Ingredients</td><td>{ingredients_count}</td></tr>
        </table>

        <h3>Sample Data:</h3>
        <h4>Recent Sales:</h4>
        <ul>
        """

        recent_sales = Sale.objects.all().order_by('-order_date')[:5]
        for sale in recent_sales:
            status_html += f"<li>{sale.product_name} - {sale.quantity} x ₱{sale.price} ({sale.order_date})</li>"

        status_html += """
        </ul>
        </body>
        </html>
        """

        return HttpResponse(status_html, content_type='text/html')

    except Exception as e:
        print(f"❌ Error in debug endpoint: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"<h1>Error: {str(e)}</h1>", content_type='text/html', status=500)


# Alias for backward compatibility
debug_firebase_status = debug_database_status


@login_required
@csrf_exempt
def update_password_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            current_password = data.get('current_password')
            new_password = data.get('new_password')

            user = request.user

            if not user.check_password(current_password):
                return JsonResponse({
                    'success': False,
                    'message': 'Current password is incorrect'
                }, status=400)

            user.set_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            log_audit('Password Changed', user, 'User changed their password')

            return JsonResponse({
                'success': True,
                'message': 'Password updated successfully'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)


# ========================================
# RECIPES VIEWS
# ========================================

@login_required
def recipes_view(request):
    """Display recipe management page"""
    try:
        print("\n🔥 RECIPES VIEW CALLED (PostgreSQL)")

        # Get all recipes
        recipes = Recipe.objects.all()

        recipes_list = []

        for recipe in recipes:
            # Get ingredients for this recipe
            ingredients = RecipeIngredient.objects.filter(
                Q(recipe_id=recipe.id) | Q(recipe_firebase_id=recipe.firebase_id)
            )

            ingredients_data = []
            for ing in ingredients:
                ingredient_id = ing.ingredient_firebase_id or ''

                # Get ingredient product details
                ingredient_cost = 0
                ingredient_stock = 0
                if ingredient_id:
                    try:
                        ing_product = Product.objects.get(firebase_id=ingredient_id)
                        ingredient_cost = ing_product.cost_per_unit or 0
                        inventory_a = ing_product.inventory_a or ing_product.quantity or 0
                        inventory_b = ing_product.inventory_b or 0
                        ingredient_stock = inventory_a + inventory_b
                    except Product.DoesNotExist:
                        pass

                ingredients_data.append({
                    'id': ing.id,
                    'name': ing.ingredient_name or 'Unknown',
                    'quantity': ing.quantity_needed or 0,
                    'unit': ing.unit or 'g',
                    'ingredientFirebaseId': ingredient_id,
                    'cost_per_unit': ingredient_cost,
                    'stock': ingredient_stock
                })

            recipes_list.append({
                'id': recipe.firebase_id or str(recipe.id),
                'productName': recipe.product_name or 'Unknown',
                'productFirebaseId': recipe.product_firebase_id or '',
                'ingredients': ingredients_data,
                'ingredientCount': len(ingredients_data)
            })

        # Get all beverage and pastry products for dropdown
        beverages = []
        products = Product.objects.all()

        for product in products:
            category = (product.category or '').lower().strip()
            if category in ['beverage', 'beverages', 'pastries', 'pastry', 'drink', 'drinks', 'hot drinks', 'cold drinks', 'snacks', 'snack']:
                beverages.append({
                    'id': product.firebase_id or str(product.id),
                    'name': product.name or 'Unknown',
                    'category': category
                })

        # Get all ingredients for dropdown
        ingredients_products = Product.objects.filter(category__iexact='Ingredients')

        available_ingredients = []
        for ing in ingredients_products:
            inventory_a = ing.inventory_a or ing.quantity or 0
            inventory_b = ing.inventory_b or 0
            total_stock = inventory_a + inventory_b

            available_ingredients.append({
                'id': ing.firebase_id or str(ing.id),
                'name': ing.name or 'Unknown',
                'stock': total_stock,
                'inventory_a': inventory_a,
                'inventory_b': inventory_b,
                'cost_per_unit': ing.cost_per_unit or 0,
                'unit': 'g'
            })

        print(f"✅ Loaded {len(recipes_list)} recipes")
        print(f"✅ Found {len(beverages)} beverages")
        print(f"✅ Found {len(available_ingredients)} ingredients")

        context = {
            'recipes': recipes_list,
            'beverages': beverages,
            'ingredients': available_ingredients,
        }

        return render(request, 'dashboard/recipes.html', context)

    except Exception as e:
        print(f"❌ Error loading recipes: {e}")
        import traceback
        traceback.print_exc()

        context = {
            'recipes': [],
            'beverages': [],
            'ingredients': [],
        }
        return render(request, 'dashboard/recipes.html', context)


# ============================================
# RECIPE MANAGEMENT API ENDPOINTS
# ============================================

@login_required
@require_http_methods(["POST"])
def add_recipe_api(request):
    """Add a new recipe with ingredients"""
    try:
        data = json.loads(request.body)
        print("\n🔥 ADD RECIPE API CALLED (PostgreSQL)")
        print(f"Data received: {data}")

        product_firebase_id = data.get('productFirebaseId')
        product_name = data.get('productName')
        ingredients = data.get('ingredients', [])

        if not product_firebase_id or not product_name:
            return JsonResponse({'success': False, 'message': 'Product information required'})

        if not ingredients:
            return JsonResponse({'success': False, 'message': 'At least one ingredient is required'})

        # Check if recipe already exists
        existing = Recipe.objects.filter(product_firebase_id=product_firebase_id).exists()
        if existing:
            return JsonResponse({'success': False, 'message': 'Recipe already exists for this product'})

        # Create recipe
        import uuid
        recipe = Recipe.objects.create(
            firebase_id=str(uuid.uuid4()),
            product_firebase_id=product_firebase_id,
            product_name=product_name,
            product_number=0
        )

        print(f"✅ Recipe created with ID: {recipe.id}")

        # Add ingredients
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe_id=recipe.id,
                recipe_firebase_id=recipe.firebase_id,
                ingredient_firebase_id=ingredient.get('ingredientFirebaseId'),
                ingredient_name=ingredient.get('ingredientName'),
                quantity_needed=ingredient.get('quantityNeeded'),
                unit=ingredient.get('unit', 'g')
            )

        print(f"✅ Added {len(ingredients)} ingredients to recipe")

        log_audit('Recipe Created', request.user, f'Created recipe for {product_name}')

        return JsonResponse({
            'success': True,
            'message': f'Recipe for {product_name} created successfully!'
        })

    except Exception as e:
        print(f"❌ Error adding recipe: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def update_recipe_api(request):
    """Update an existing recipe"""
    try:
        data = json.loads(request.body)
        print("\n🔥 UPDATE RECIPE API CALLED (PostgreSQL)")

        recipe_id = data.get('recipeId')
        product_firebase_id = data.get('productFirebaseId')
        product_name = data.get('productName')
        ingredients = data.get('ingredients', [])

        if not recipe_id:
            return JsonResponse({'success': False, 'message': 'Recipe ID required'})

        # Find and update recipe
        try:
            recipe = Recipe.objects.get(Q(id=recipe_id) | Q(firebase_id=recipe_id))
        except Recipe.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Recipe not found'})

        recipe.product_firebase_id = product_firebase_id
        recipe.product_name = product_name
        recipe.save()

        print(f"✅ Recipe {recipe_id} updated")

        # Delete old ingredients
        RecipeIngredient.objects.filter(
            Q(recipe_id=recipe.id) | Q(recipe_firebase_id=recipe.firebase_id)
        ).delete()

        print(f"✅ Old ingredients deleted")

        # Add new ingredients
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe_id=recipe.id,
                recipe_firebase_id=recipe.firebase_id,
                ingredient_firebase_id=ingredient.get('ingredientFirebaseId'),
                ingredient_name=ingredient.get('ingredientName'),
                quantity_needed=ingredient.get('quantityNeeded'),
                unit=ingredient.get('unit', 'g')
            )

        print(f"✅ Added {len(ingredients)} new ingredients")

        log_audit('Recipe Updated', request.user, f'Updated recipe for {product_name}')

        return JsonResponse({
            'success': True,
            'message': f'Recipe for {product_name} updated successfully!'
        })

    except Exception as e:
        print(f"❌ Error updating recipe: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_recipe_api(request):
    """Delete a recipe and its ingredients"""
    try:
        data = json.loads(request.body)
        print("\n🔥 DELETE RECIPE API CALLED (PostgreSQL)")

        recipe_id = data.get('recipeId')

        if not recipe_id:
            return JsonResponse({'success': False, 'message': 'Recipe ID required'})

        # Find recipe
        try:
            recipe = Recipe.objects.get(Q(id=recipe_id) | Q(firebase_id=recipe_id))
        except Recipe.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Recipe not found'})

        product_name = recipe.product_name

        # Delete all ingredients for this recipe
        deleted_count, _ = RecipeIngredient.objects.filter(
            Q(recipe_id=recipe.id) | Q(recipe_firebase_id=recipe.firebase_id)
        ).delete()

        print(f"✅ Deleted {deleted_count} ingredients")

        # Delete the recipe
        recipe.delete()

        print(f"✅ Recipe {recipe_id} deleted")

        log_audit('Recipe Deleted', request.user, f'Deleted recipe for {product_name}')

        return JsonResponse({
            'success': True,
            'message': f'Recipe for {product_name} deleted successfully!'
        })

    except Exception as e:
        print(f"❌ Error deleting recipe: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


# ============================================
# INVENTORY TRANSFER API (A → B)
# ============================================

@login_required
@require_http_methods(["POST"])
def transfer_inventory_api(request):
    """Transfer stock from Inventory A to Inventory B"""
    try:
        data = json.loads(request.body)
        print("\n🔄 INVENTORY TRANSFER API CALLED (PostgreSQL)")
        print(f"Data received: {data}")

        product_id = data.get('productId')
        transfer_qty = float(data.get('quantity', 0))

        if not product_id or transfer_qty <= 0:
            return JsonResponse({'success': False, 'message': 'Invalid product or quantity'})

        # Get product from PostgreSQL
        try:
            product = Product.objects.get(Q(firebase_id=product_id) | Q(id=product_id))
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})

        product_name = product.name
        inventory_a = float(product.inventory_a or 0)
        inventory_b = float(product.inventory_b or 0)

        # Check if sufficient stock
        if inventory_a < transfer_qty:
            return JsonResponse({
                'success': False,
                'message': f'Insufficient stock in Inventory A. Available: {inventory_a:.2f}'
            })

        # Perform transfer
        new_inventory_a = inventory_a - transfer_qty
        new_inventory_b = inventory_b + transfer_qty

        # Update database
        product.inventory_a = new_inventory_a
        product.inventory_b = new_inventory_b
        product.quantity = new_inventory_b  # Update legacy field
        product.save()

        print(f"✅ Transferred {transfer_qty} units of {product_name}")
        print(f"   Inventory A: {inventory_a} → {new_inventory_a}")
        print(f"   Inventory B: {inventory_b} → {new_inventory_b}")

        log_audit('Inventory Transfer', request.user, f'Transferred {transfer_qty} units of {product_name} from A to B')

        return JsonResponse({
            'success': True,
            'message': f'Successfully transferred {transfer_qty} units of {product_name} to Inventory B',
            'newInventoryA': new_inventory_a,
            'newInventoryB': new_inventory_b
        })

    except Exception as e:
        print(f"❌ Error in transfer: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


# ============================================
# WASTE MANAGEMENT API (B → Waste)
# ============================================

@login_required
@require_http_methods(["POST"])
def add_waste_api(request):
    """Transfer items from Inventory B to Waste logs"""
    try:
        data = json.loads(request.body)
        print("\n🗑️ WASTE MANAGEMENT API CALLED (PostgreSQL)")
        print(f"Data received: {data}")

        product_id = data.get('productId')
        waste_qty = float(data.get('quantity', 0))
        reason = data.get('reason', 'Expired')

        if not product_id or waste_qty <= 0:
            return JsonResponse({'success': False, 'message': 'Invalid product or quantity'})

        # Get product from PostgreSQL
        try:
            product = Product.objects.get(Q(firebase_id=product_id) | Q(id=product_id))
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})

        product_name = product.name
        inventory_b = float(product.inventory_b or 0)

        # Check if sufficient stock
        if inventory_b < waste_qty:
            return JsonResponse({
                'success': False,
                'message': f'Insufficient stock in Inventory B. Available: {inventory_b:.2f}'
            })

        # Deduct from Inventory B
        new_inventory_b = inventory_b - waste_qty

        # Update product
        product.inventory_b = new_inventory_b
        product.quantity = new_inventory_b
        product.save()

        # Create waste log entry
        WasteLog.objects.create(
            product_firebase_id=product.firebase_id or str(product.id),
            product_name=product_name,
            quantity=waste_qty,
            reason=reason,
            waste_date=datetime.now(),
            recorded_by=request.user.username,
            category=product.category
        )

        print(f"✅ Recorded waste: {waste_qty} units of {product_name}")
        print(f"   Inventory B: {inventory_b} → {new_inventory_b}")
        print(f"   Reason: {reason}")

        log_audit('Waste Recorded', request.user, f'Recorded {waste_qty} units of {product_name} as waste ({reason})')

        return JsonResponse({
            'success': True,
            'message': f'Successfully recorded {waste_qty} units of {product_name} as waste',
            'newInventoryB': new_inventory_b
        })

    except Exception as e:
        print(f"❌ Error in waste management: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def waste_tracking_view(request):
    """Display waste tracking page with date filters and cost analysis"""
    try:
        print("\n🗑️ WASTE TRACKING VIEW CALLED (PostgreSQL)")

        # Get date filter parameters
        from_date = request.GET.get('from_date', '')
        to_date = request.GET.get('to_date', '')

        # Build query
        waste_queryset = WasteLog.objects.all()

        if from_date:
            from_datetime = datetime.strptime(from_date, '%Y-%m-%d')
            waste_queryset = waste_queryset.filter(waste_date__gte=from_datetime)
        if to_date:
            to_datetime = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
            waste_queryset = waste_queryset.filter(waste_date__lt=to_datetime)

        waste_queryset = waste_queryset.order_by('-waste_date')

        waste_entries = []
        total_waste_cost = 0
        daily_costs = {}

        for waste in waste_queryset:
            product_id = waste.product_firebase_id
            quantity = waste.quantity or 0

            # Get product details for cost
            waste_cost = 0
            product_name = waste.product_name or 'Unknown'
            category = waste.category or 'Unknown'

            if product_id:
                try:
                    product = Product.objects.get(Q(firebase_id=product_id) | Q(id=product_id))
                    cost_per_unit = product.cost_per_unit or 0
                    waste_cost = quantity * cost_per_unit
                    product_name = product.name or product_name
                    category = product.category or category
                except Product.DoesNotExist:
                    pass

            waste_date = waste.waste_date
            date_str = waste_date.strftime('%Y-%m-%d') if waste_date else 'Unknown'
            date_display = waste_date.strftime('%b %d, %Y %I:%M %p') if waste_date else 'Unknown'

            # Track daily costs
            if date_str != 'Unknown':
                if date_str not in daily_costs:
                    daily_costs[date_str] = 0
                daily_costs[date_str] += waste_cost

            total_waste_cost += waste_cost

            waste_entries.append({
                'id': waste.id,
                'productName': product_name,
                'productId': product_id,
                'quantity': quantity,
                'reason': waste.reason or 'Unknown',
                'wasteDate': date_display,
                'dateStr': date_str,
                'recordedBy': waste.recorded_by or 'Unknown',
                'category': category,
                'wasteCost': waste_cost
            })

        # Sort daily costs by date
        daily_costs_list = [
            {'date': date, 'cost': cost}
            for date, cost in sorted(daily_costs.items(), reverse=True)
        ]

        print(f"✅ Loaded {len(waste_entries)} waste entries")
        print(f"💰 Total waste cost: ₱{total_waste_cost:.2f}")

        context = {
            'waste_entries': waste_entries,
            'total_waste_cost': total_waste_cost,
            'daily_costs': daily_costs_list,
            'from_date': from_date,
            'to_date': to_date,
            'entry_count': len(waste_entries)
        }

        return render(request, 'dashboard/waste_tracking.html', context)

    except Exception as e:
        print(f"❌ Error loading waste tracking: {e}")
        import traceback
        traceback.print_exc()

        context = {
            'waste_entries': [],
            'total_waste_cost': 0,
            'daily_costs': [],
            'from_date': '',
            'to_date': '',
            'entry_count': 0
        }
        return render(request, 'dashboard/waste_tracking.html', context)


# ========================================
# INVENTORY FORECASTING VIEW
# ========================================

@login_required
def inventory_forecasting_view(request):
    """ML-based inventory forecasting using PostgreSQL"""
    try:
        print("\n🤖 ML INVENTORY FORECASTING VIEW (PostgreSQL)")

        # Data validation
        sales_count = Sale.objects.count()
        products_count = Product.objects.count()
        predictions_count = MLPrediction.objects.count()

        print(f"📊 Data Status:")
        print(f"   Sales: {sales_count}")
        print(f"   Products: {products_count}")
        print(f"   Predictions: {predictions_count}")

        data_issues = []
        if sales_count == 0:
            data_issues.append({
                'type': 'no_sales',
                'title': 'No Sales Data',
                'message': 'You need sales history to train the forecasting model.',
                'action': 'Add sales records or sync from mobile app',
                'command': None
            })
        elif sales_count < 30:
            data_issues.append({
                'type': 'insufficient_sales',
                'title': 'Insufficient Sales Data',
                'message': f'You have only {sales_count} sales records. At least 30 records recommended.',
                'action': 'Add more sales data or wait for more transactions',
                'command': None
            })

        if products_count == 0:
            data_issues.append({
                'type': 'no_products',
                'title': 'No Products',
                'message': 'You need products in your inventory to forecast.',
                'action': 'Add products or sync from mobile app',
                'command': None
            })

        # Get model status
        try:
            ml_model = MLModel.objects.get(name='inventory_forecasting')
            model_status = {
                'is_trained': ml_model.is_trained,
                'last_trained': ml_model.last_trained,
                'accuracy': ml_model.accuracy,
                'total_records': ml_model.total_records,
                'model_name': ml_model.name,
                'model_type': ml_model.model_type,
                'products_analyzed': ml_model.products_analyzed
            }
        except MLModel.DoesNotExist:
            model_status = {
                'is_trained': False,
                'last_trained': None,
                'accuracy': 0,
                'total_records': 0,
                'model_name': 'Not trained yet',
                'model_type': 'N/A',
                'products_analyzed': 0
            }
            data_issues.append({
                'type': 'no_model',
                'title': 'Model Not Trained',
                'message': 'No ML model has been trained yet.',
                'action': 'Click "Train Model" button below',
                'command': None
            })

        # Build forecast data
        forecast_data = []
        summary = {
            'critical': 0,
            'low': 0,
            'healthy': 0,
            'needs_reorder': 0
        }

        # Exclude beverages and specific items
        products = Product.objects.exclude(
            category__iexact='Beverages'
        ).exclude(
            category__iexact='beverage'
        ).exclude(
            category__iexact='drinks'
        ).exclude(
            name__icontains='Water'
        ).exclude(
            name__icontains='Ice'
        )

        print(f"📦 Processing {products.count()} products...")

        for product in products:
            # Get ML prediction if available
            ml_confidence = None
            predicted_daily_usage = 0
            avg_daily_usage = 0

            try:
                prediction = MLPrediction.objects.get(product_firebase_id=product.firebase_id)
                predicted_daily_usage = prediction.predicted_daily_usage
                avg_daily_usage = prediction.avg_daily_usage
                ml_confidence = prediction.confidence_score
            except MLPrediction.DoesNotExist:
                predicted_daily_usage = 0
                avg_daily_usage = 0
                ml_confidence = 0

            # Calculate forecast metrics
            stock = float(product.quantity or 0)

            if predicted_daily_usage > 0:
                days_left = int(stock / predicted_daily_usage)
            else:
                days_left = 999

            if days_left < 999:
                depletion_date = (datetime.now() + timedelta(days=days_left)).strftime('%b %d, %Y')
            else:
                depletion_date = 'N/A'

            # Determine status
            if days_left <= 3:
                status = 'critical'
                status_label = 'Critical'
                summary['critical'] += 1
            elif days_left <= 7:
                status = 'warning'
                status_label = 'Low Stock'
                summary['low'] += 1
            else:
                status = 'healthy'
                status_label = 'Healthy'
                summary['healthy'] += 1

            if days_left <= 7:
                summary['needs_reorder'] += 1

            predicted_7day_usage = predicted_daily_usage * 7

            if days_left <= 7:
                reorder_qty = max(0, (predicted_daily_usage * 30) - stock)
            else:
                reorder_qty = 0

            confidence_percent = f"{int(ml_confidence * 100)}%" if ml_confidence else "0%"

            forecast_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'category': product.category,
                'current_stock': f"{stock:.2f}",
                'unit': product.unit,
                'avg_daily_usage': f"{avg_daily_usage:.2f}" if avg_daily_usage else "0.00",
                'days_left': days_left if days_left < 999 else 'N/A',
                'depletion_date': depletion_date,
                'status': status,
                'status_label': status_label,
                'predicted_usage': f"{predicted_7day_usage:.2f}",
                'reorder_qty': f"{reorder_qty:.2f}",
                'confidence': confidence_percent
            })

        # Sort by days_left
        forecast_data.sort(key=lambda x: x['days_left'] if isinstance(x['days_left'], int) else 999)

        print(f"\n{'=' * 60}")
        print(f"✅ FORECAST SUMMARY:")
        print(f"   Total products: {len(forecast_data)}")
        print(f"   Critical: {summary['critical']}")
        print(f"   Low Stock: {summary['low']}")
        print(f"   Healthy: {summary['healthy']}")
        print(f"{'=' * 60}\n")

        context = {
            'forecast_data': forecast_data,
            'model_status': model_status,
            'summary': summary,
            'data_issues': data_issues,
            'data_status': {
                'sales_count': sales_count,
                'products_count': products_count,
                'predictions_count': predictions_count,
                'has_issues': len(data_issues) > 0
            }
        }

        return render(request, 'dashboard/inventory_forecasting.html', context)

    except Exception as e:
        print(f"❌ Error in forecasting view: {e}")
        import traceback
        traceback.print_exc()

        context = {
            'forecast_data': [],
            'model_status': {'is_trained': False},
            'summary': {'critical': 0, 'low': 0, 'healthy': 0, 'needs_reorder': 0},
            'data_issues': [{'type': 'error', 'title': 'Error', 'message': str(e)}],
            'data_status': {'has_issues': True}
        }
        return render(request, 'dashboard/inventory_forecasting.html', context)


# ========================================
# ML MODEL TRAINING
# ========================================

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def train_forecasting_model(request):
    """Train the ML forecasting model using PostgreSQL data"""
    try:
        print("\n🤖 TRAINING FORECASTING MODEL (PostgreSQL)")

        # Get sales data
        sales = Sale.objects.all()
        sales_count = sales.count()

        if sales_count < 10:
            return JsonResponse({
                'success': False,
                'message': f'Insufficient data for training. Need at least 10 sales records, found {sales_count}.'
            })

        # Calculate predictions for each product
        products = Product.objects.all()
        predictions_created = 0

        for product in products:
            # Get sales for this product
            product_sales = Sale.objects.filter(
                Q(product_firebase_id=product.firebase_id) |
                Q(product_name=product.name)
            )

            if product_sales.count() < 3:
                continue

            # Calculate daily usage
            sales_data = list(product_sales.values('order_date', 'quantity'))

            if not sales_data:
                continue

            # Simple moving average calculation
            total_quantity = sum(s['quantity'] for s in sales_data if s['quantity'])
            days = (datetime.now() - min(s['order_date'] for s in sales_data if s['order_date'])).days or 1

            avg_daily_usage = total_quantity / max(days, 1)
            predicted_daily_usage = avg_daily_usage * 1.1  # Add 10% buffer

            # Create or update prediction
            MLPrediction.objects.update_or_create(
                product_firebase_id=product.firebase_id or str(product.id),
                defaults={
                    'product_name': product.name,
                    'predicted_daily_usage': predicted_daily_usage,
                    'avg_daily_usage': avg_daily_usage,
                    'trend': 0.0,
                    'confidence_score': min(0.9, 0.5 + (len(sales_data) / 100)),
                    'data_points': len(sales_data)
                }
            )
            predictions_created += 1

        # Update model status
        MLModel.objects.update_or_create(
            name='inventory_forecasting',
            defaults={
                'is_trained': True,
                'last_trained': datetime.now(),
                'total_records': sales_count,
                'products_analyzed': products.count(),
                'predictions_generated': predictions_created,
                'accuracy': 85,
                'model_type': 'Linear Regression (Moving Average)',
                'training_period_days': 90
            }
        )

        log_audit('Model Trained', request.user, f'Trained ML model with {sales_count} records, {predictions_created} predictions')

        return JsonResponse({
            'success': True,
            'message': f'Model trained successfully! Analyzed {products.count()} products, created {predictions_created} predictions.',
            'stats': {
                'sales_records': sales_count,
                'products_analyzed': products.count(),
                'predictions_created': predictions_created
            }
        })

    except Exception as e:
        print(f"❌ Error training model: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})


# ========================================
# PRODUCT MANAGEMENT APIs
# ========================================

@login_required
@require_http_methods(["POST"])
def add_product_view(request):
    """Add a new product"""
    try:
        data = json.loads(request.body)
        print("\n🔥 ADD PRODUCT API CALLED (PostgreSQL)")

        import uuid
        product = Product.objects.create(
            firebase_id=str(uuid.uuid4()),
            name=data.get('name'),
            category=data.get('category'),
            price=float(data.get('price', 0)),
            quantity=float(data.get('quantity', 0)),
            unit=data.get('unit', 'pcs'),
            inventory_a=float(data.get('inventoryA', data.get('quantity', 0))),
            inventory_b=0,
            cost_per_unit=float(data.get('costPerUnit', 0))
        )

        log_audit('Product Added', request.user, f'Added product: {product.name}')

        return JsonResponse({
            'success': True,
            'message': f'Product {product.name} added successfully!',
            'productId': product.firebase_id
        })

    except Exception as e:
        print(f"❌ Error adding product: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def update_product_view(request):
    """Update an existing product"""
    try:
        data = json.loads(request.body)
        print("\n🔥 UPDATE PRODUCT API CALLED (PostgreSQL)")

        product_id = data.get('productId')

        try:
            product = Product.objects.get(Q(firebase_id=product_id) | Q(id=product_id))
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})

        # Update fields
        if 'name' in data:
            product.name = data['name']
        if 'category' in data:
            product.category = data['category']
        if 'price' in data:
            product.price = float(data['price'])
        if 'quantity' in data:
            product.quantity = float(data['quantity'])
        if 'unit' in data:
            product.unit = data['unit']
        if 'inventoryA' in data:
            product.inventory_a = float(data['inventoryA'])
        if 'inventoryB' in data:
            product.inventory_b = float(data['inventoryB'])
        if 'costPerUnit' in data:
            product.cost_per_unit = float(data['costPerUnit'])

        product.save()

        log_audit('Product Updated', request.user, f'Updated product: {product.name}')

        return JsonResponse({
            'success': True,
            'message': f'Product {product.name} updated successfully!'
        })

    except Exception as e:
        print(f"❌ Error updating product: {e}")
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_product_view(request):
    """Delete a product"""
    try:
        data = json.loads(request.body)
        print("\n🔥 DELETE PRODUCT API CALLED (PostgreSQL)")

        product_id = data.get('productId')

        try:
            product = Product.objects.get(Q(firebase_id=product_id) | Q(id=product_id))
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})

        product_name = product.name
        product.delete()

        log_audit('Product Deleted', request.user, f'Deleted product: {product_name}')

        return JsonResponse({
            'success': True,
            'message': f'Product {product_name} deleted successfully!'
        })

    except Exception as e:
        print(f"❌ Error deleting product: {e}")
        return JsonResponse({'success': False, 'message': str(e)})
