from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'shop'

urlpatterns = [
    # Public browsing
    path('', views.home, name='home'),
    path('about/', views.about_view, name='about'),
    path('categories/', views.categories_view, name='categories'),
    path('categories/overview/', views.categories_view, name='categories_overview'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # Coupons
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),

    # Reviews
    path('reviews/<int:pk>/delete/', views.delete_review, name='delete_review'),

    # Auth & Account
    path('register/', views.register_view, name='register'),
    path('login/', views.CuddleLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),

    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='shop/password_reset.html',
        email_template_name='shop/password_reset_email.html',
        subject_template_name='shop/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='shop/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='shop/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='shop/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Customer Dashboard, Profile & Addresses
    path('my/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('my/profile/', views.profile_view, name='profile'),
    path('my/profile/change-password/', views.change_password, name='change_password'),
    path('my/address/add/', views.add_address, name='add_address'),
    path('my/address/<int:pk>/edit/', views.edit_address, name='edit_address'),
    path('my/address/<int:pk>/delete/', views.delete_address, name='delete_address'),
    path('my/address/<int:pk>/default/', views.set_default_address, name='set_default_address'),

    # Cart
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist_view'),
    path('wishlist/add/<int:pk>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_wishlist_item, name='remove_wishlist_item'),
    path('wishlist/move/<int:item_id>/', views.move_wishlist_to_cart, name='move_wishlist_to_cart'),

    # Checkout, Payment & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('payment/simulate/<int:order_id>/', views.payment_simulation, name='payment_simulation'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/invoice/', views.order_invoice, name='order_invoice'),
    path('orders/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),

    # Admin Panel (Dedicated Custom Portal)
    path('admin-panel/', views.admin_overview, name='admin_overview'),
    
    # Admin Products & Gallery
    path('admin-panel/products/', views.admin_products, name='admin_products'),
    path('admin-panel/products/add/', views.admin_product_form, name='admin_product_add'),
    path('admin-panel/products/<int:pk>/edit/', views.admin_product_form, name='admin_product_edit'),
    path('admin-panel/products/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/products/<int:pk>/images/', views.admin_product_images, name='admin_product_images'),
    path('admin-panel/products/images/<int:image_id>/delete/', views.admin_product_image_delete, name='admin_product_image_delete'),

    # Admin Categories
    path('admin-panel/categories/', views.admin_categories, name='admin_categories'),
    path('admin-panel/categories/add/', views.admin_category_form, name='admin_category_add'),
    path('admin-panel/categories/<int:pk>/edit/', views.admin_category_form, name='admin_category_edit'),
    path('admin-panel/categories/<int:pk>/delete/', views.admin_category_delete, name='admin_category_delete'),

    # Admin Inventory
    path('admin-panel/inventory/', views.admin_inventory, name='admin_inventory'),
    path('admin-panel/inventory/update/<int:pk>/', views.admin_inventory_update, name='admin_inventory_update'),

    # Admin Orders
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),

    # Admin Customers
    path('admin-panel/customers/', views.admin_customers, name='admin_customers'),
    path('admin-panel/customers/<int:pk>/toggle-status/', views.admin_customer_toggle_status, name='admin_customer_toggle_status'),

    # Admin Payments
    path('admin-panel/payments/', views.admin_payments, name='admin_payments'),

    # Admin Reviews
    path('admin-panel/reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin-panel/reviews/<int:pk>/delete/', views.admin_review_delete, name='admin_review_delete'),
]
