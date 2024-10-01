from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove-all/<int:product_id>/', views.remove_all_from_cart, name='remove_all_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/complete/', views.checkout_complete, name='checkout_complete'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('export/sales/<str:report_type>/', views.export_sales_report, name='export_sales_report'),
    path('download-report/', views.download_report, name='download_report'),
]