from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils import timezone


class User(AbstractUser):
    """Custom user model for CuddleCart (Customer & Admin roles)."""
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    is_active_customer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_admin_role(self):
        return self.role == 'admin' or self.is_staff or self.is_superuser

    def __str__(self):
        return self.username


class Address(models.Model):
    """Customer delivery addresses."""
    ADDRESS_TYPE_CHOICES = (
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100, default='', blank=True)
    phone = models.CharField(max_length=15, default='', blank=True)
    house_building = models.CharField(max_length=150, blank=True, default='')
    street = models.CharField(max_length=150, blank=True, default='')
    address_line = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=50, default='India', blank=True)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default='home')
    is_default = models.BooleanField(default=False)

    def get_full_address(self):
        parts = []
        if self.house_building:
            parts.append(self.house_building)
        if self.street:
            parts.append(self.street)
        elif self.address_line:
            parts.append(self.address_line)
        parts.extend([self.city, self.state, self.pincode, self.country])
        return ", ".join(parts)

    def save(self, *args, **kwargs):
        if not self.country:
            self.country = 'India'
        if not self.address_line:
            parts = [p for p in [self.house_building, self.street] if p]
            self.address_line = ", ".join(parts) if parts else f"{self.city}, {self.state}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name or self.user.username} - {self.city}, {self.state}"


class Category(models.Model):
    """Soft toy product categories."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)


    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return ''


class Product(models.Model):
    """Soft toy product details."""
    SIZE_CHOICES = (
        ('Small', 'Small'),
        ('Medium', 'Medium'),
        ('Large', 'Large'),
        ('Extra Large', 'Extra Large'),
    )
    AGE_GROUP_CHOICES = (
        ('0–3 years', '0–3 years'),
        ('3–6 years', '3–6 years'),
        ('6–12 years', '6–12 years'),
        ('12+ years', '12+ years'),
    )

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    brand = models.CharField(max_length=100, default='CuddleCart')
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='Medium')
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, default='3–6 years')
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, help_text="Optional fallback image URL")
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return ''

    def average_rating(self):
        agg = self.reviews.aggregate(models.Avg('rating'))
        return round(agg['rating__avg'] or 0, 1)

    def total_reviews(self):
        return self.reviews.count()

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.pk])

    def check_availability(self):
        self.is_available = self.stock_quantity > 0 and self.is_active
        return self.is_available

    def get_price_for_size(self, size_choice=None):
        return self.price

    def save(self, *args, **kwargs):
        self.is_available = self.stock_quantity > 0 and self.is_active
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """Additional gallery images for products."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    alt_text = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(default=timezone.now)


    def get_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return ''

    def __str__(self):
        return f"Image for {self.product.name}"


class Cart(models.Model):
    """Customer shopping cart."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Cart({self.user.username})"


class CartItem(models.Model):
    """Item inside shopping cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    selected_size = models.CharField(max_length=20, default='Medium')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product', 'selected_size')

    def get_unit_price(self):
        return self.product.get_price_for_size(self.selected_size)

    def get_subtotal(self):
        return self.get_unit_price() * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.selected_size})"


class Wishlist(models.Model):
    """Customer wishlist."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')

    def __str__(self):
        return f"Wishlist({self.user.username})"


class WishlistItem(models.Model):
    """Item inside wishlist."""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product')

    def __str__(self):
        return f"{self.product.name} in wishlist"


class Order(models.Model):
    """Customer placed order."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=50, blank=True, default='')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    def calculate_total(self):
        self.total_amount = sum(item.get_subtotal() for item in self.items.all())
        return self.total_amount

    def can_cancel(self):
        """Allow cancellation only before shipping."""
        return self.status in ('pending', 'confirmed', 'processing')

    def cancel_order(self):
        """Cancel order, restore product stock, update payment status."""
        if not self.can_cancel():
            return False
        self.status = 'cancelled'
        self.save()
        # Restore stock
        for item in self.items.select_related('product'):
            item.product.stock_quantity += item.quantity
            item.product.check_availability()
            item.product.save()
        # Update payment status if exists
        if hasattr(self, 'payment') and self.payment.status == 'success':
            self.payment.status = 'refunded'
            self.payment.save()
        return True


class OrderItem(models.Model):
    """Items belonging to an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=150, blank=True)
    selected_size = models.CharField(max_length=20, default='Medium', blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.product_name and self.product:
            self.product_name = self.product.name
        super().save(*args, **kwargs)

    def get_subtotal(self):
        return self.price_at_purchase * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name or self.product.name}"


class Payment(models.Model):
    """Payment transaction details."""
    METHOD_CHOICES = (
        ('card', 'Credit / Debit Card'),
        ('upi', 'UPI Payment'),
        ('netbanking', 'Net Banking'),
        ('cod', 'Cash on Delivery'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} for Order #{self.order.id} ({self.status})"


class Review(models.Model):
    """Customer product reviews."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ by {self.user.username} on {self.product.name}"


class SalesInvoice(models.Model):
    """Sales Invoices table matching academic schema."""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'sales_invoices'
        ordering = ['-invoice_date', '-id']

    def __str__(self):
        return f"Invoice {self.invoice_number} for Order #{self.order_id}"
