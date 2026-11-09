from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Address, Category, Product, ProductImage, Cart, CartItem,
    Wishlist, WishlistItem, Order, OrderItem, Payment, Review
)


@admin.register(User)
class CuddleUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'is_active_customer', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active_customer', 'is_staff')
    search_fields = ('username', 'email', 'phone')
    fieldsets = UserAdmin.fieldsets + (
        ('CuddleCart Details', {'fields': ('role', 'phone', 'is_active_customer')}),
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'size', 'age_group', 'price', 'stock_quantity', 'is_available', 'is_active')
    list_filter = ('category', 'brand', 'size', 'age_group', 'is_available', 'is_active')
    search_fields = ('name', 'description', 'brand')
    inlines = [ProductImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'city', 'state', 'pincode', 'address_type', 'is_default')
    list_filter = ('address_type', 'is_default', 'state')
    search_fields = ('user__username', 'full_name', 'phone', 'city', 'pincode')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'quantity', 'price_at_purchase')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'order_date')
    list_filter = ('status', 'order_date')
    search_fields = ('id', 'user__username', 'user__email')
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'payment_method', 'status', 'transaction_id', 'payment_date')
    list_filter = ('payment_method', 'status', 'payment_date')
    search_fields = ('transaction_id', 'order__id', 'order__user__username')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'get_total', 'created_at')
    inlines = [CartItemInline]


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user',)
    inlines = [WishlistItemInline]


admin.site.register(ProductImage)
