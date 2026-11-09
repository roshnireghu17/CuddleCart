from .models import Category


def cart_wishlist_counts(request):
    """Makes cart_count, cart items, wishlist_count and categories available in every template."""
    cart_count = 0
    wishlist_count = 0
    cart = None
    cart_total = 0

    if request.user.is_authenticated and request.user.role == 'customer':
        cart = getattr(request.user, 'cart', None)
        wishlist = getattr(request.user, 'wishlist', None)
        if cart:
            cart_count = cart.total_items()
            cart_total = cart.get_total()
        if wishlist:
            wishlist_count = wishlist.items.count()

    categories = Category.objects.all()

    return {
        'nav_cart': cart,
        'nav_cart_count': cart_count,
        'nav_cart_total': cart_total,
        'nav_wishlist_count': wishlist_count,
        'nav_categories': categories,
    }

