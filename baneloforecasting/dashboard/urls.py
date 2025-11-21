from django.urls import path
from . import views


urlpatterns = [
    

    path('', views.dashboard_view, name='dashboard'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('inventory/recipes/', views.recipes_view, name='recipes'),
    path('settings/', views.settings_view, name='settings'),
    path('sales/', views.sales_view, name='sales'),
    path('sales/export/', views.export_sales_csv, name='export_sales_csv'),
    path('accounts/', views.accounts_view, name='accounts'),
    path('audit-trail/', views.audit_trail_view, name='audit_trail'),
    
    # API endpoints for Firebase
    path('api/products/', views.api_products, name='api_products'),
    path('api/sales/', views.api_sales, name='api_sales'),

    # Firebase Health Check endpoints
    path('api/health/', views.firebase_health_check, name='firebase_health_check'),
    path('api/debug/firebase/', views.debug_firebase_status, name='debug_firebase_status'),
    
    # CRUD endpoints for products (ADD, EDIT, DELETE)
    path('api/products/add/', views.add_product_view, name='add_product'),
    path('api/products/update/', views.update_product_view, name='update_product'),
    path('api/products/delete/', views.delete_product_view, name='delete_product'),
    # API endpoint for updating user password (admin)
    path('api/update-password/', views.update_password_api, name='update_password_api'),

    # Audit Trail URLs
    path('audit-trail/', views.audit_trail_view, name='audit_trail'),
    path('audit-trail/api/', views.get_audit_logs_api, name='audit_logs_api'),
    path('audit-trail/export/', views.export_audit_trail_csv, name='export_audit_trail_csv'),  # ← ADD THIS LINE

    # Recipe API endpoints
    path('api/recipes/add/', views.add_recipe_api, name='add_recipe_api'),
    path('api/recipes/update/', views.update_recipe_api, name='update_recipe_api'),
    path('api/recipes/delete/', views.delete_recipe_api, name='delete_recipe_api'),

    path('inventory/forecasting/', views.inventory_forecasting_view, name='inventory_forecasting'),
    path('api/train-forecasting/', views.train_forecasting_model, name='train_forecasting_model'),

   

]