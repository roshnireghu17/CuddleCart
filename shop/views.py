import re
import random
import time
from decimal import Decimal
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count, Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    RegisterForm, ProfileForm, AddressForm, ReviewForm, CheckoutForm,
    CategoryForm, ProductForm, ProductImageForm, OrderStatusForm,
    StyledAuthenticationForm
)
from .models import (
    Product, ProductImage, Category, Cart, CartItem, Wishlist, WishlistItem,
    Address, Order, OrderItem, Payment, Review, User, SalesInvoice
)


# ---------------------------------------------------------------------------
# Helper Functions & Decorators
# ---------------------------------------------------------------------------

def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_staff or user.is_superuser)


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _get_or_create_wishlist(user):
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    return wishlist


# ---------------------------------------------------------------------------
# Public & Customer Views
# ---------------------------------------------------------------------------

def home(request):
    """CuddleCart homepage with soft toy theme, hero, featured categories and products."""
    categories = Category.objects.filter(is_active=True).annotate(prod_count=Count('products'))[:6]
    all_products = Product.objects.filter(is_available=True, is_active=True).select_related('category').order_by('-created_at')[:12]
    featured_products = all_products[:8]
    latest_reviews = Review.objects.filter(rating__gte=4).select_related('user', 'product').order_by('-created_at')[:6]

    user_wishlist_ids = set()
    if request.user.is_authenticated and not is_admin(request.user):
        wishlist = getattr(request.user, 'wishlist', None)
        if wishlist:
            user_wishlist_ids = set(wishlist.items.values_list('product_id', flat=True))

    return render(request, 'shop/home.html', {
        'categories': categories,
        'all_products': all_products,
        'featured_products': featured_products,
        'featured': featured_products,  # backwards compatibility
        'latest_reviews': latest_reviews,
        'reviews': latest_reviews,
        'user_wishlist_ids': user_wishlist_ids,
        'login_form': StyledAuthenticationForm(),
        'register_form': RegisterForm(),
    })


def about_view(request):
    """About CuddleCart page describing the website, safety, and handcrafted philosophy."""
    return render(request, 'shop/about.html')


def categories_view(request):
    """Categories overview page showcasing all soft toy categories."""
    categories = Category.objects.filter(is_active=True).annotate(prod_count=Count('products'))
    return render(request, 'shop/categories.html', {'categories': categories})


def product_list(request):
    """Product catalog with search, multi-field filtering, sorting and pagination."""
    products = Product.objects.filter(is_active=True).select_related('category')

    # Search
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Filters
    selected_category = request.GET.get('category', '').strip()
    if selected_category:
        products = products.filter(category_id=selected_category)

    selected_brand = request.GET.get('brand', '').strip()
    if selected_brand:
        products = products.filter(brand__iexact=selected_brand)

    selected_size = request.GET.get('size', '').strip()
    if selected_size:
        products = products.filter(size=selected_size)

    selected_age_group = request.GET.get('age_group', '').strip()
    if selected_age_group:
        products = products.filter(age_group=selected_age_group)

    min_price = request.GET.get('min_price', '').strip()
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass

    max_price = request.GET.get('max_price', '').strip()
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    in_stock_only = request.GET.get('in_stock', '').strip()
    if in_stock_only == '1':
        products = products.filter(stock_quantity__gt=0, is_available=True)

    # Sorting
    sort_by = request.GET.get('sort', 'newest').strip()
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'rating':
        products = products.annotate(avg_rate=Avg('reviews__rating')).order_by('-avg_rate')
    else:  # newest
        products = products.order_by('-created_at')

    # Distinct brands, sizes, age groups for filters
    categories = Category.objects.filter(is_active=True)
    all_brands = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct()
    size_choices = Product.SIZE_CHOICES
    age_group_choices = Product.AGE_GROUP_CHOICES

    # Wishlist IDs
    user_wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist = getattr(request.user, 'wishlist', None)
        if wishlist:
            user_wishlist_ids = set(wishlist.items.values_list('product_id', flat=True))

    # Pagination: 9 products per page
    paginator = Paginator(products, 9)
    page = request.GET.get('page', 1)
    try:
        paginated_products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        paginated_products = paginator.page(1)

    return render(request, 'shop/product_list.html', {
        'products': paginated_products,
        'paginator': paginator,
        'categories': categories,
        'all_brands': sorted(list(set(all_brands))),
        'size_choices': size_choices,
        'age_group_choices': age_group_choices,
        'query': query,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'selected_size': selected_size,
        'selected_age_group': selected_age_group,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock_only': in_stock_only,
        'sort_by': sort_by,
        'user_wishlist_ids': user_wishlist_ids,
        'total_count': paginator.count,
    })


def product_detail(request, pk):
    """Detailed view for a soft toy product, gallery images, reviews, and purchasing check."""
    product = get_object_or_404(Product, pk=pk)
    gallery_images = product.images.all()
    reviews = product.reviews.select_related('user').order_by('-created_at')
    
    # Check if user has purchased this product and has a DELIVERED order
    user_has_purchased_and_delivered = False
    user_existing_review = None
    already_reviewed = False
    
    if request.user.is_authenticated:
        # Check delivered orders containing this product
        user_has_purchased_and_delivered = OrderItem.objects.filter(
            order__user=request.user,
            order__status='delivered',
            product=product
        ).exists()

        user_existing_review = reviews.filter(user=request.user).first()
        if user_existing_review:
            already_reviewed = True

    # Review Submission Handling
    review_form = ReviewForm(instance=user_existing_review if already_reviewed else None)
    if request.method == 'POST' and request.user.is_authenticated:
        if not user_has_purchased_and_delivered:
            messages.error(request, 'Only customers who have purchased and received this product (Delivered status) can write a review.')
            return redirect('shop:product_detail', pk=pk)

        review_form = ReviewForm(request.POST, instance=user_existing_review if already_reviewed else None)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Thank you! Your review has been submitted successfully.')
            return redirect('shop:product_detail', pk=pk)

    # In wishlist check
    in_wishlist = False
    if request.user.is_authenticated:
        wishlist = getattr(request.user, 'wishlist', None)
        if wishlist:
            in_wishlist = wishlist.items.filter(product=product).exists()

    related = Product.objects.filter(
        category=product.category,
        is_available=True,
        is_active=True
    ).exclude(pk=pk)[:4]

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'gallery_images': gallery_images,
        'reviews': reviews,
        'total_reviews': reviews.count(),
        'avg_rating': product.average_rating(),
        'already_reviewed': already_reviewed,
        'user_has_purchased_and_delivered': user_has_purchased_and_delivered,
        'review_form': review_form,
        'in_wishlist': in_wishlist,
        'related': related,
    })


@login_required
@require_POST
def delete_review(request, pk):
    """Customer can delete their own review."""
    review = get_object_or_404(Review, pk=pk, user=request.user)
    product_id = review.product.id
    review.delete()
    messages.info(request, 'Your review has been removed.')
    return redirect('shop:product_detail', pk=product_id)


# ---------------------------------------------------------------------------
# Authentication & User Account
# ---------------------------------------------------------------------------

def register_view(request):
    """Customer registration view."""
    if request.user.is_authenticated:
        return redirect('shop:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Cart.objects.get_or_create(user=user)
            Wishlist.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Welcome to CuddleCart, {user.username}! Your account is ready.')
            return redirect('shop:dashboard')
    else:
        form = RegisterForm()

    return render(request, 'shop/register.html', {'form': form})


class CuddleLoginView(LoginView):
    """Customer & Admin login view supporting email or username."""
    template_name = 'shop/login.html'
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if is_admin(user):
            return reverse_lazy('shop:admin_overview')
        return reverse_lazy('shop:user_dashboard')


def logout_view(request):
    """User logout."""
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('shop:home')


@login_required
def dashboard_redirect(request):
    """Direct user to admin panel or customer dashboard based on role."""
    if is_admin(request.user):
        return redirect('shop:admin_overview')
    return redirect('shop:user_dashboard')


@login_required
def user_dashboard(request):
    """Customer dashboard overview with recent orders, addresses, and wishlist."""
    if is_admin(request.user):
        return redirect('shop:admin_overview')

    user = request.user
    recent_orders = user.orders.order_by('-order_date')[:5]
    total_orders = user.orders.count()
    wishlist_count = user.wishlist.items.count() if hasattr(user, 'wishlist') else 0
    addresses_count = user.addresses.count()

    return render(request, 'shop/user_dashboard.html', {
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'wishlist_count': wishlist_count,
        'addresses_count': addresses_count,
    })


@login_required
def profile_view(request):
    """Customer profile information and address book management."""
    if request.method == 'POST' and 'update_profile' in request.POST:
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile details have been updated.')
            return redirect('shop:profile')
    else:
        form = ProfileForm(instance=request.user)

    addresses = request.user.addresses.all()
    address_form = AddressForm()

    return render(request, 'shop/profile.html', {
        'form': form,
        'addresses': addresses,
        'address_form': address_form,
    })


@login_required
def change_password(request):
    """Change customer password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was changed successfully!')
            return redirect('shop:profile')
        else:
            messages.error(request, 'Please correct the error(s) below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'shop/change_password.html', {'form': form})


# ---------------------------------------------------------------------------
# Address Management
# ---------------------------------------------------------------------------

@login_required
def add_address(request):
    """Add a new delivery address."""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default or not request.user.addresses.exists():
                Address.objects.filter(user=request.user).update(is_default=False)
                address.is_default = True
            address.save()
            request.session['selected_address_id'] = address.id
            messages.success(request, 'Delivery address added successfully.')
        else:
            err_msgs = []
            for field, errs in form.errors.items():
                for err in errs:
                    err_msgs.append(f"{field.replace('_', ' ').capitalize()}: {err}")
            messages.error(request, 'Error adding address: ' + ' | '.join(err_msgs))
    next_url = request.POST.get('next') or request.GET.get('next') or 'shop:profile'
    return redirect(next_url)


@login_required
def edit_address(request, pk):
    """Edit an existing address."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            addr = form.save(commit=False)
            if addr.is_default:
                Address.objects.filter(user=request.user).exclude(pk=pk).update(is_default=False)
            addr.save()
            messages.success(request, 'Address updated.')
            return redirect('shop:profile')
    else:
        form = AddressForm(instance=address)

    return render(request, 'shop/address_form.html', {'form': form, 'address': address})


@login_required
def delete_address(request, pk):
    """Delete a delivery address."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.info(request, 'Delivery address removed.')
    return redirect('shop:profile')


@login_required
def set_default_address(request, pk):
    """Set an address as default."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    Address.objects.filter(user=request.user).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, f'Address set as default.')
    next_url = request.GET.get('next') or 'shop:profile'
    return redirect(next_url)


# ---------------------------------------------------------------------------
# Cart Module
# ---------------------------------------------------------------------------

def cart_view(request):
    """Display customer shopping cart with coupon, delivery fee, and tax calculations."""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please sign in or create an account to view your cuddle bag and start shopping.')
        return redirect('shop:login')

    cart = _get_or_create_cart(request.user)
    items = cart.items.select_related('product').all()

    # Verify inventory warning for any item that exceeds current stock
    has_stock_issue = False
    for item in items:
        if item.quantity > item.product.stock_quantity:
            has_stock_issue = True

    subtotal = cart.get_total()
    coupon_code = request.session.get('coupon_code', '')
    discount = Decimal('0.00')
    if coupon_code:
        discount = round(subtotal * Decimal('0.10'), 2)

    taxable_amount = max(Decimal('0.00'), subtotal - discount)
    tax = round(taxable_amount * Decimal('0.05'), 2)

    # Free delivery on orders >= 600, otherwise delivery fee is 80
    if subtotal == 0:
        shipping_fee = Decimal('0.00')
    elif taxable_amount >= Decimal('600.00'):
        shipping_fee = Decimal('0.00')
    else:
        shipping_fee = Decimal('80.00')

    total_amount = taxable_amount + tax + shipping_fee

    return render(request, 'shop/cart.html', {
        'cart': cart,
        'items': items,
        'has_stock_issue': has_stock_issue,
        'subtotal': subtotal,
        'coupon_code': coupon_code,
        'discount': discount,
        'tax': tax,
        'shipping_fee': shipping_fee,
        'total_amount': total_amount,
        'free_shipping_threshold': Decimal('600.00'),
    })


@require_POST
def apply_coupon(request):
    """Apply CuddleCart Club 10% coupon or promotional code."""
    code = (request.POST.get('coupon_code') or request.POST.get('code') or '').strip().upper()
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'shop:cart_view'

    if not code:
        messages.warning(request, 'Please enter a coupon code.')
        return redirect(next_url)

    if code in ('CLUB10', 'CUDDLECLUB', 'CUDDLE10', 'WELCOME10'):
        request.session['coupon_code'] = code
        messages.success(request, f'🎉 Coupon "{code}" applied! 10% CuddleCart Club discount has been activated.')
    else:
        messages.error(request, f'Invalid coupon code "{code}". Use code "CLUB10" for 10% CuddleCart Club discount.')

    return redirect(next_url)


def remove_coupon(request):
    """Remove active coupon code."""
    request.session.pop('coupon_code', None)
    messages.info(request, 'Coupon code has been removed.')
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'shop:cart_view'
    return redirect(next_url)


@require_POST
def add_to_cart(request, pk):
    """Add a product to customer cart with size selection, stock validation, AJAX & Buy Now support."""
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1'
    is_buy_now = request.POST.get('buy_now') == '1' or request.POST.get('action') == 'buy_now'

    if not request.user.is_authenticated:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'require_login': True,
                'login_url': reverse('shop:login'),
                'message': 'Please sign in or create an account to start shopping and add items to your cart.'
            }, status=401)
        messages.warning(request, 'Please sign in or create an account to start shopping and add items to your cart.')
        return redirect('shop:login')

    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = _get_or_create_cart(request.user)

    if product.stock_quantity <= 0:
        if is_ajax:
            return JsonResponse({'success': False, 'message': f'Sorry, "{product.name}" is currently out of stock.'}, status=400)
        messages.error(request, f'Sorry, "{product.name}" is currently out of stock.')
        return redirect(request.POST.get('next') or 'shop:product_detail', pk=pk)

    try:
        qty = int(request.POST.get('quantity', 1))
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1

    size = product.size or 'Medium'

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        selected_size=size,
        defaults={'quantity': 0}
    )
    new_quantity = item.quantity + qty

    if new_quantity > product.stock_quantity:
        item.quantity = product.stock_quantity
        item.save()
        msg = f'Only {product.stock_quantity} unit(s) of "{product.name}" are in stock. Cart updated to max available.'
        if not is_ajax:
            messages.warning(request, msg)
    else:
        item.quantity = new_quantity
        item.save()
        msg = f'Added {qty} × "{product.name}" ({size}) to your bag.'
        if not is_ajax:
            messages.success(request, msg)

    total_qty = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    total_amt = cart.get_total()

    if is_buy_now:
        if is_ajax:
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('shop:checkout'),
                'cart_count': total_qty,
                'cart_total': f"{total_amt:.2f}",
                'message': 'Directing to checkout...'
            })
        return redirect('shop:checkout')

    if is_ajax:
        drawer_html = render_to_string('shop/partials/cart_drawer_body.html', {
            'nav_cart': cart,
            'nav_cart_total': total_amt,
            'user': request.user,
        }, request=request)

        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_count': total_qty,
            'cart_total': f"{total_amt:.2f}",
            'product_name': product.name,
            'drawer_html': drawer_html,
        })

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('shop:cart_view')


@login_required
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity with real-time recalculation (supports AJAX and direct post)."""
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    cart = item.cart
    try:
        qty = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        qty = 1

    warning_msg = None
    deleted = False
    if qty <= 0:
        item.delete()
        messages.info(request, f'Removed "{item.product.name}" from your cart.')
        deleted = True
    elif qty > item.product.stock_quantity:
        item.quantity = item.product.stock_quantity
        item.save()
        warning_msg = f'Only {item.product.stock_quantity} unit(s) of "{item.product.name}" available in stock.'
        messages.warning(request, warning_msg)
    else:
        item.quantity = qty
        item.save()
        messages.success(request, f'Updated quantity for "{item.product.name}".')

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.headers.get('accept') == 'application/json' or
        'application/json' in request.headers.get('accept', '') or
        request.POST.get('ajax') == '1'
    )

    if is_ajax:
        subtotal = cart.get_total()
        coupon_code = request.session.get('coupon_code', '')
        discount = Decimal('0.00')
        if coupon_code:
            discount = round(subtotal * Decimal('0.10'), 2)

        taxable_amount = max(Decimal('0.00'), subtotal - discount)
        tax = round(taxable_amount * Decimal('0.05'), 2)

        if taxable_amount >= Decimal('600.00'):
            shipping_fee = Decimal('0.00')
        else:
            shipping_fee = Decimal('80.00')

        total_amount = taxable_amount + tax + shipping_fee

        return JsonResponse({
            'success': True,
            'deleted': deleted,
            'item_id': item_id,
            'quantity': 0 if deleted else item.quantity,
            'unit_price': f"{item.get_unit_price():.2f}" if not deleted else "0.00",
            'item_subtotal': f"{item.get_subtotal():.2f}" if not deleted else "0.00",
            'total_items': cart.total_items(),
            'subtotal': f"{subtotal:.2f}",
            'discount': f"{discount:.2f}",
            'tax': f"{tax:.2f}",
            'shipping_fee': 'FREE' if shipping_fee == Decimal('0.00') else f"₹{shipping_fee:.2f}",
            'is_shipping_free': shipping_fee == Decimal('0.00'),
            'total_amount': f"{total_amount:.2f}",
            'warning_msg': warning_msg,
            'qualifies_free_shipping': taxable_amount >= Decimal('600.00'),
            'amount_needed_for_free_shipping': f"{max(Decimal('0.00'), Decimal('600.00') - taxable_amount):.2f}",
            'progress_percent': min(100, int((taxable_amount / Decimal('600.00')) * 100)) if taxable_amount < Decimal('600.00') else 100,
        })

    return redirect('shop:cart_view')


@login_required
def remove_cart_item(request, item_id):
    """Remove item from cart (supports AJAX for slide-over drawer)."""
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    cart = item.cart
    product_name = item.product.name
    item.delete()

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    if is_ajax:
        total_qty = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
        total_amt = cart.get_total()
        drawer_html = render_to_string('shop/partials/cart_drawer_body.html', {
            'nav_cart': cart,
            'nav_cart_total': total_amt,
            'user': request.user,
        }, request=request)
        return JsonResponse({
            'success': True,
            'message': f'Removed "{product_name}" from cart.',
            'cart_count': total_qty,
            'cart_total': f"{total_amt:.2f}",
            'drawer_html': drawer_html,
        })

    messages.info(request, f'Removed "{product_name}" from cart.')
    next_url = request.META.get('HTTP_REFERER') or 'shop:cart_view'
    return redirect(next_url)


@login_required
def clear_cart(request):
    """Empty all items from cart."""
    cart = _get_or_create_cart(request.user)
    cart.items.all().delete()
    messages.info(request, 'Your cart has been cleared.')
    return redirect('shop:cart_view')


# ---------------------------------------------------------------------------
# Wishlist Module
# ---------------------------------------------------------------------------

@login_required
def wishlist_view(request):
    """Display customer wishlist."""
    wishlist = _get_or_create_wishlist(request.user)
    items = wishlist.items.select_related('product', 'product__category').all()
    return render(request, 'shop/wishlist.html', {
        'wishlist': wishlist,
        'items': items,
    })


@require_POST
def add_to_wishlist(request, pk):
    """Add or toggle product in wishlist with AJAX support."""
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1'

    if not request.user.is_authenticated:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'require_login': True,
                'login_url': reverse('shop:login'),
                'message': 'Please sign in or create an account to save companions to your wishlist.'
            }, status=401)
        messages.info(request, 'Please sign in or create an account to save companions to your wishlist.')
        return redirect('shop:login')

    product = get_object_or_404(Product, pk=pk, is_active=True)
    wishlist = _get_or_create_wishlist(request.user)

    existing_item = wishlist.items.filter(product=product).first()
    if existing_item:
        if is_ajax:
            existing_item.delete()
            in_wishlist = False
            msg = f'Removed "{product.name}" from your wishlist.'
        else:
            in_wishlist = True
            msg = f'"{product.name}" is already in your wishlist.'
            messages.info(request, msg)
    else:
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        in_wishlist = True
        msg = f'Added "{product.name}" to your wishlist.'
        if not is_ajax:
            messages.success(request, msg)

    wishlist_count = wishlist.items.count()

    if is_ajax:
        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist,
            'wishlist_count': wishlist_count,
            'message': msg,
            'product_id': product.pk,
        })

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('shop:wishlist_view')


@login_required
def remove_wishlist_item(request, item_id):
    """Remove an item from wishlist."""
    item = get_object_or_404(WishlistItem, pk=item_id, wishlist__user=request.user)
    product_name = item.product.name
    item.delete()
    messages.info(request, f'Removed "{product_name}" from your wishlist.')
    return redirect('shop:wishlist_view')


@login_required
@require_POST
def move_wishlist_to_cart(request, item_id):
    """Move product from wishlist to cart."""
    wishlist_item = get_object_or_404(WishlistItem, pk=item_id, wishlist__user=request.user)
    product = wishlist_item.product

    if product.stock_quantity <= 0:
        messages.error(request, f'Cannot move "{product.name}" to cart because it is currently out of stock.')
        return redirect('shop:wishlist_view')

    cart = _get_or_create_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        selected_size=product.size,
        defaults={'quantity': 1}
    )
    if not created:
        if cart_item.quantity < product.stock_quantity:
            cart_item.quantity += 1
            cart_item.save()

    wishlist_item.delete()
    messages.success(request, f'Moved "{product.name}" to your cart.')
    return redirect('shop:cart_view')


# ---------------------------------------------------------------------------
# Checkout, Mock Payment & Order Processing
# ---------------------------------------------------------------------------

def checkout(request):
    """Multi-step checkout: verify cart & inventory, select address, review summary, proceed."""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please sign in or create an account before checking out.')
        return redirect('shop:login')

    cart = _get_or_create_cart(request.user)
    items = cart.items.select_related('product').all()

    if not items.exists():
        messages.warning(request, 'Your shopping cart is empty. Add some lovely soft toys first!')
        return redirect('shop:product_list')

    # Verify inventory availability before allowing checkout
    for item in items:
        if item.quantity > item.product.stock_quantity:
            messages.error(
                request,
                f'Insufficient stock for "{item.product.name}". Available: {item.product.stock_quantity}. Please adjust your cart.'
            )
            return redirect('shop:cart_view')

    addresses = request.user.addresses.all()
    subtotal = cart.get_total()
    coupon_code = request.session.get('coupon_code', '')
    discount = Decimal('0.00')
    if coupon_code:
        discount = round(subtotal * Decimal('0.10'), 2)

    taxable_amount = max(Decimal('0.00'), subtotal - discount)
    tax = round(taxable_amount * Decimal('0.05'), 2)

    if taxable_amount >= Decimal('600.00'):
        shipping_fee = Decimal('0.00')
    else:
        shipping_fee = Decimal('80.00')

    total_amount = taxable_amount + tax + shipping_fee

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            address = form.cleaned_data['address']
            payment_method = form.cleaned_data['payment_method']

            # Create Order
            order = Order.objects.create(
                user=request.user,
                address=address,
                subtotal=subtotal,
                discount_amount=discount,
                tax_amount=tax,
                shipping_fee=shipping_fee,
                coupon_code=coupon_code,
                total_amount=total_amount,
                status='pending'
            )

            # Create OrderItems and deduct stock
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    selected_size=item.selected_size,
                    quantity=item.quantity,
                    price_at_purchase=item.get_unit_price()
                )
                # Deduct inventory
                item.product.stock_quantity = max(item.product.stock_quantity - item.quantity, 0)
                item.product.check_availability()
                item.product.save()

            # Create SalesInvoice (Table 14)
            invoice_num = f"INV-{order.id:05d}-{timezone.now().strftime('%Y%m%d')}"
            SalesInvoice.objects.get_or_create(
                order=order,
                defaults={
                    'invoice_number': invoice_num,
                    'invoice_date': timezone.now().date(),
                    'subtotal': subtotal,
                    'discount': discount,
                    'tax': tax,
                    'total_amount': total_amount
                }
            )

            # Clear session coupon
            request.session.pop('coupon_code', None)

            if payment_method == 'cod':
                # Cash on delivery order confirmation
                order.status = 'confirmed'
                order.save()
                Payment.objects.create(
                    order=order,
                    payment_method='cod',
                    amount=total_amount,
                    status='pending',
                    transaction_id=f'COD-CC-{order.id}-{int(time.time())}'
                )
                # Clear cart
                cart.items.all().delete()
                messages.success(request, f'Thank you! Your Cash on Delivery order #{order.id} has been placed successfully.')
                return redirect('shop:order_detail', pk=order.id)
            else:
                # Online Payment -> Redirect to Interactive Mock Payment Screen
                Payment.objects.create(
                    order=order,
                    payment_method='online',
                    amount=total_amount,
                    status='pending',
                    transaction_id=''
                )
                return redirect('shop:payment_simulation', order_id=order.id)
    else:
        form = CheckoutForm(user=request.user)
        selected_addr_id = request.session.pop('selected_address_id', None)
        if selected_addr_id and addresses.filter(id=selected_addr_id).exists():
            form.fields['address'].initial = selected_addr_id

    return render(request, 'shop/checkout.html', {
        'form': form,
        'cart': cart,
        'items': items,
        'addresses': addresses,
        'subtotal': subtotal,
        'discount': discount,
        'tax': tax,
        'shipping_fee': shipping_fee,
        'coupon_code': coupon_code,
        'total_amount': total_amount,
        'address_form': AddressForm(),
    })


@login_required
def payment_simulation(request, order_id):
    """Safe Mock Online Payment Gateway simulation for academic demonstration."""
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    payment = get_object_or_404(Payment, order=order)

    if order.status != 'pending' and payment.status == 'success':
        messages.info(request, 'This order payment has already been completed.')
        return redirect('shop:order_detail', pk=order.id)

    if request.method == 'POST':
        action = request.POST.get('simulation_action')
        chosen_submethod = request.POST.get('sub_method', 'card')

        if action == 'success':
            if chosen_submethod == 'card':
                raw_exp = request.POST.get('card_expiry')
                raw_num = request.POST.get('card_number')
                raw_cvv = request.POST.get('card_cvv')

                if raw_exp is not None or raw_num is not None:
                    card_num = re.sub(r'[\s\-]+', '', raw_num or '')
                    card_expiry = (raw_exp or '').strip()
                    card_cvv = (raw_cvv or '').strip()

                    if not card_num or len(card_num) < 15 or not card_num.isdigit():
                        messages.error(request, 'Please enter a valid 16-digit card number.')
                        return redirect('shop:payment_simulation', order_id=order.id)

                    if not card_cvv or len(card_cvv) < 3 or not card_cvv.isdigit():
                        messages.error(request, 'Please enter a valid 3 or 4-digit CVV.')
                        return redirect('shop:payment_simulation', order_id=order.id)

                    # Validate expiry format MM/YY
                    exp_clean = card_expiry.replace('/', '').strip()
                    if len(exp_clean) != 4 or not exp_clean.isdigit():
                        messages.error(request, 'Invalid expiry date format. Please enter MM/YY.')
                        return redirect('shop:payment_simulation', order_id=order.id)

                    exp_month = int(exp_clean[:2])
                    exp_year = 2000 + int(exp_clean[2:])

                    if exp_month < 1 or exp_month > 12:
                        messages.error(request, 'Invalid expiry month. Month must be between 01 and 12.')
                        return redirect('shop:payment_simulation', order_id=order.id)

                    now = timezone.now()
                    if (exp_year < now.year) or (exp_year == now.year and exp_month < now.month):
                        messages.error(request, 'Card expired! The card you entered is expired. Please enter an active card.')
                        return redirect('shop:payment_simulation', order_id=order.id)

            # Generate simulated transaction ID
            txn_id = f"TXN-CC{order.id}-{int(time.time())}-{random.randint(1000, 9999)}"
            payment.payment_method = chosen_submethod
            payment.status = 'success'
            payment.transaction_id = txn_id
            payment.save()

            order.status = 'confirmed'
            order.save()

            # Ensure SalesInvoice exists (Table 14)
            invoice_num = f"INV-{order.id:05d}-{timezone.now().strftime('%Y%m%d')}"
            SalesInvoice.objects.get_or_create(
                order=order,
                defaults={
                    'invoice_number': invoice_num,
                    'invoice_date': timezone.now().date(),
                    'subtotal': order.subtotal or order.total_amount,
                    'discount': order.discount_amount or Decimal('0.00'),
                    'tax': order.tax_amount or Decimal('0.00'),
                    'total_amount': order.total_amount
                }
            )

            # Clear customer cart
            cart = _get_or_create_cart(request.user)
            cart.items.all().delete()

            messages.success(request, f'Payment Simulated Successfully! Transaction ID: {txn_id}')
            return redirect('shop:order_detail', pk=order.id)

        elif action == 'failure':
            payment.status = 'failed'
            payment.save()
            messages.error(request, 'Payment simulation failed. Your card or account was not charged. You may retry payment.')
            return redirect('shop:payment_simulation', order_id=order.id)

    return render(request, 'shop/payment_simulation.html', {
        'order': order,
        'payment': payment,
    })


@login_required
def order_history(request):
    """Customer order history."""
    orders = request.user.orders.select_related('address').prefetch_related('items', 'items__product').order_by('-order_date')
    return render(request, 'shop/order_history.html', {'orders': orders})


@login_required
def order_detail(request, pk):
    """Customer order details, status timeline, item list, payment record and cancellation button."""
    order = get_object_or_404(
        Order.objects.select_related('address', 'payment').prefetch_related('items', 'items__product'),
        pk=pk,
        user=request.user
    )
    return render(request, 'shop/order_detail.html', {'order': order})


@login_required
def order_invoice(request, pk):
    """Customer tax invoice view with printable layout (Table 14: Sales_Invoices)."""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    invoice = getattr(order, 'invoice', None)
    if not invoice:
        invoice_num = f"INV-{order.id:05d}-{order.order_date.strftime('%Y%m%d')}"
        invoice, _ = SalesInvoice.objects.get_or_create(
            order=order,
            defaults={
                'invoice_number': invoice_num,
                'invoice_date': order.order_date.date(),
                'subtotal': order.subtotal or order.calculate_total(),
                'discount': order.discount_amount or Decimal('0.00'),
                'tax': order.tax_amount or Decimal('0.00'),
                'total_amount': order.total_amount
            }
        )
    return render(request, 'shop/order_invoice.html', {
        'order': order,
        'invoice': invoice,
    })


@login_required
@require_POST
def cancel_order(request, pk):
    """Customer can cancel an order only before it is shipped."""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.can_cancel():
        success = order.cancel_order()
        if success:
            messages.info(request, f'Order #{order.id} has been cancelled and stock has been restored.')
        else:
            messages.error(request, 'Unable to cancel this order.')
    else:
        messages.error(request, 'This order cannot be cancelled as it has already been shipped or delivered.')

    return redirect('shop:order_detail', pk=pk)


# ---------------------------------------------------------------------------
# Admin Panel Module (Separate Admin Portal)
# ---------------------------------------------------------------------------

@user_passes_test(is_admin, login_url='shop:login')
def admin_overview(request):
    raw_revenue = Payment.objects.filter(status='success').aggregate(total=Sum('amount'))['total'] or 0
    try:
        total_revenue = round(Decimal(str(raw_revenue)), 2)
    except Exception:
        total_revenue = Decimal('0.00')
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed', 'processing']).count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    total_customers = User.objects.filter(role='customer').count()
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_reviews = Review.objects.count()

    low_stock = Product.objects.filter(stock_quantity__lte=5, is_active=True).select_related('category')
    recent_orders = Order.objects.select_related('user', 'address', 'payment').order_by('-order_date')[:10]

    return render(request, 'shop/admin/overview.html', {
        'total_revenue': total_revenue,
        'total_sales': total_revenue,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'active_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_customers': total_customers,
        'new_customers': total_customers,
        'total_products': total_products,
        'total_categories': total_categories,
        'total_reviews': total_reviews,
        'low_stock': low_stock,
        'low_stock_count': low_stock.count(),
        'recent_orders': recent_orders,
        'active': 'overview',
    })


@user_passes_test(is_admin, login_url='shop:login')
def admin_products(request):
    """Admin product catalog management."""
    products_qs = Product.objects.select_related('category').all().order_by('-created_at')
    
    query = request.GET.get('q', '').strip()
    if query:
        products_qs = products_qs.filter(Q(name__icontains=query) | Q(brand__icontains=query) | Q(category__name__icontains=query))
    
    cat_id = request.GET.get('category', '')
    if cat_id:
        products_qs = products_qs.filter(category_id=cat_id)

    paginator = Paginator(products_qs, 15)
    page = request.GET.get('page', 1)
    products = paginator.get_page(page)
    categories = Category.objects.all()

    return render(request, 'shop/admin/products.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': cat_id,
        'active': 'products',
    })


@user_passes_test(is_admin, login_url='shop:login')
def admin_product_form(request, pk=None):
    """Add or edit a product."""
    product = get_object_or_404(Product, pk=pk) if pk else None
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            prod = form.save()
            messages.success(request, f'Product "{prod.name}" has been saved.')
            return redirect('shop:admin_products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'shop/admin/product_form.html', {
        'form': form,
        'product': product,
        'active': 'products',
    })


@user_passes_test(is_admin, login_url='shop:login')
@require_POST
def admin_product_delete(request, pk):
    """Delete a product."""
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.info(request, f'Product "{name}" has been deleted.')
    return redirect('shop:admin_products')


@user_passes_test(is_admin, login_url='shop:login')
def admin_product_images(request, pk):
    """Manage multiple gallery images for a product."""
    product = get_object_or_404(Product, pk=pk)
    images = product.images.all()
    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.product = product
            img.save()
            messages.success(request, 'Additional image uploaded.')
            return redirect('shop:admin_product_images', pk=pk)
    else:
        form = ProductImageForm()

    return render(request, 'shop/admin/product_images.html', {
        'product': product,
        'images': images,
        'form': form,
        'active': 'products',
    })


@user_passes_test(is_admin, login_url='shop:login')
@require_POST
def admin_product_image_delete(request, image_id):
    """Delete a gallery image."""
    img = get_object_or_404(ProductImage, pk=image_id)
    prod_id = img.product.id
    img.delete()
    messages.info(request, 'Gallery image deleted.')
    return redirect('shop:admin_product_images', pk=prod_id)


@user_passes_test(is_admin, login_url='shop:login')
def admin_categories(request):
    """List categories and add category."""
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'New category created successfully.')
            return redirect('shop:admin_categories')
    else:
        form = CategoryForm()

    return render(request, 'shop/admin/categories.html', {
        'categories': categories,
        'form': form,
        'active': 'categories',
    })


@user_passes_test(is_admin, login_url='shop:login')
def admin_category_form(request, pk=None):
    """Edit category."""
    category = get_object_or_404(Category, pk=pk) if pk else None
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated.')
            return redirect('shop:admin_categories')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'shop/admin/category_form.html', {
        'form': form,
        'category': category,
        'active': 'categories',
    })


@user_passes_test(is_admin, login_url='shop:login')
@require_POST
def admin_category_delete(request, pk):
    """Delete category."""
    category = get_object_or_404(Category, pk=pk)
    name = category.name
    category.delete()
    messages.info(request, f'Category "{name}" deleted.')
    return redirect('shop:admin_categories')


@user_passes_test(is_admin, login_url='shop:login')
def admin_inventory(request):
    """Dedicated inventory management table."""
    products = Product.objects.select_related('category').order_by('stock_quantity')
    return render(request, 'shop/admin/inventory.html', {
        'products': products,
        'active': 'inventory',
    })


@user_passes_test(is_admin, login_url='shop:login')
@require_POST
def admin_inventory_update(request, pk):
    """Quick update product stock from inventory dashboard."""
    product = get_object_or_404(Product, pk=pk)
    try:
        new_stock = int(request.POST.get('stock_quantity', product.stock_quantity))
        if new_stock >= 0:
            product.stock_quantity = new_stock
            product.check_availability()
            product.save()
            messages.success(request, f'Stock for "{product.name}" updated to {new_stock}.')
        else:
            messages.error(request, 'Stock quantity cannot be negative.')
    except (ValueError, TypeError):
        messages.error(request, 'Invalid stock value.')

    return redirect('shop:admin_inventory')


@user_passes_test(is_admin, login_url='shop:login')
def admin_customers(request):
    """View registered customers."""
    customers = User.objects.filter(role='customer').annotate(
        orders_count=Count('orders')
    ).order_by('-created_at')
    return render(request, 'shop/admin/customers.html', {
        'customers': customers,
        'active': 'customers',
    })


@user_passes_test(is_admin, login_url='shop:login')
@require_POST
def admin_customer_toggle_status(request, pk):
    """Activate or deactivate a customer account."""
    customer = get_object_or_404(User, pk=pk, role='customer')
    customer.is_active_customer = not customer.is_active_customer
    customer.is_active = customer.is_active_customer
    customer.save()
    status_str = "activated" if customer.is_active_customer else "deactivated"
    messages.info(request, f'Customer account {customer.username} has been {status_str}.')
    return redirect('shop:admin_customers')


@user_passes_test(is_admin, login_url='shop:login')
def admin_orders(request):
    """Manage customer orders and filter by status."""
    orders_qs = Order.objects.select_related('user', 'address', 'payment').prefetch_related('items').order_by('-order_date')
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    paginator = Paginator(orders_qs, 20)
    page = request.GET.get('page', 1)
    orders = paginator.get_page(page)

    return render(request, 'shop/admin/orders.html', {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
        'active': 'orders',
    })


@user_passes_test(is_admin, login_url='shop:login')
def admin_order_detail(request, pk):
    """View and update order status."""
    order = get_object_or_404(
        Order.objects.select_related('user', 'address', 'payment').prefetch_related('items', 'items__product'),
        pk=pk
    )
    old_status = order.status
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            new_order = form.save()
            if old_status != 'cancelled' and new_order.status == 'cancelled':
                # Restore stock on cancellation
                for item in new_order.items.select_related('product'):
                    item.product.stock_quantity += item.quantity
                    item.product.check_availability()
                    item.product.save()
            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}.')
            return redirect('shop:admin_order_detail', pk=pk)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, 'shop/admin/order_detail.html', {
        'order': order,
        'form': form,
        'active': 'orders',
    })


@user_passes_test(is_admin, login_url='shop:login')
def admin_payments(request):
    """View all payment transactions."""
    payments = Payment.objects.select_related('order', 'order__user').order_by('-payment_date')
    return render(request, 'shop/admin/payments.html', {
        'payments': payments,
        'active': 'payments',
    })


@user_passes_test(is_admin, login_url='shop:login')
def admin_reviews(request):
    """View all customer reviews and moderate/delete."""
    reviews = Review.objects.select_related('product', 'user').order_by('-created_at')
    return render(request, 'shop/admin/reviews.html', {
        'reviews': reviews,
        'active': 'reviews',
    })


@user_passes_test(is_admin, login_url='shop:login')
@require_POST
def admin_review_delete(request, pk):
    """Delete inappropriate review."""
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.info(request, 'Review has been deleted.')
    return redirect('shop:admin_reviews')
