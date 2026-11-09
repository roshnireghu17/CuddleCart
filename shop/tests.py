from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from shop.models import User, Product, ProductImage, Category, Address, Order, OrderItem, Cart, CartItem, Wishlist, WishlistItem, Payment, Review, SalesInvoice


class CuddleCartComprehensiveTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Seed Categories
        self.cat_teddy = Category.objects.create(name="Teddy Bears", description="Snuggly bears")
        self.cat_animals = Category.objects.create(name="Animals", description="Plush animals")

        # Seed Products
        self.product1 = Product.objects.create(
            name="Barnaby Bear",
            category=self.cat_teddy,
            brand="CuddleCart",
            size="Large",
            age_group="3–6 years",
            price=45.00,
            stock_quantity=20,
            is_available=True,
            is_active=True,
        )
        self.product2 = Product.objects.create(
            name="Luna Bunny",
            category=self.cat_animals,
            brand="FluffyPaws",
            size="Medium",
            age_group="0–3 years",
            price=38.00,
            stock_quantity=5,
            is_available=True,
            is_active=True,
        )
        self.product_out_of_stock = Product.objects.create(
            name="Rare Unicorn",
            category=self.cat_animals,
            brand="HugMe",
            size="Small",
            age_group="6–12 years",
            price=50.00,
            stock_quantity=0,
            is_available=False,
            is_active=True,
        )

        # Seed Users
        self.customer = User.objects.create_user(
            username="emily",
            email="emily@example.com",
            password="password123",
            first_name="Emily",
            role="customer",
            phone="9876543210"
        )
        Cart.objects.create(user=self.customer)
        Wishlist.objects.create(user=self.customer)

        self.other_customer = User.objects.create_user(
            username="david",
            email="david@example.com",
            password="password123",
            first_name="David",
            role="customer"
        )
        Cart.objects.create(user=self.other_customer)
        Wishlist.objects.create(user=self.other_customer)

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@cuddlecart.com",
            password="admin123",
            role="admin",
            is_staff=True,
            is_superuser=True
        )

        # Address for customer
        self.address = Address.objects.create(
            user=self.customer,
            full_name="Emily Watson",
            phone="9876543210",
            house_building="Apt 4B",
            street="Park Avenue",
            city="Bengaluru",
            state="Karnataka",
            pincode="560001",
            country="India",
            address_type="home",
            is_default=True
        )

    # 1. Public Homepage & Navigation Tests
    def test_homepage_loads(self):
        response = self.client.get(reverse('shop:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CuddleCart")
        self.assertContains(response, "Teddy Bears")

    # 2. Registration Tests
    def test_customer_registration_success(self):
        response = self.client.post(reverse('shop:register'), {
            'username': 'newcustomer',
            'email': 'newcustomer@example.com',
            'phone': '9123456780',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newcustomer').exists())
        new_user = User.objects.get(username='newcustomer')
        self.assertEqual(new_user.role, 'customer')
        self.assertTrue(hasattr(new_user, 'cart'))
        self.assertTrue(hasattr(new_user, 'wishlist'))

    def test_customer_registration_duplicate_email(self):
        response = self.client.post(reverse('shop:register'), {
            'username': 'differentuser',
            'email': 'emily@example.com',  # existing email
            'phone': '9123456780',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='differentuser').exists())

    # 3. Login & Logout Tests (supports email or username)
    def test_login_with_username(self):
        response = self.client.post(reverse('shop:login'), {
            'username': 'emily',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_with_email(self):
        response = self.client.post(reverse('shop:login'), {
            'username': 'emily@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)

    def test_logout(self):
        self.client.login(username='emily', password='password123')
        response = self.client.get(reverse('shop:logout'))
        self.assertEqual(response.status_code, 302)

    # 4. Product Catalog, Search & Filtering Tests
    def test_product_list_and_search(self):
        # Search by keyword
        response = self.client.get(reverse('shop:product_list'), {'q': 'Barnaby'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Barnaby Bear")
        self.assertNotContains(response, "Luna Bunny")

    def test_product_filtering_by_category_and_price(self):
        response = self.client.get(reverse('shop:product_list'), {
            'category': self.cat_teddy.id,
            'min_price': '40',
            'max_price': '50',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Barnaby Bear")
        self.assertNotContains(response, "Luna Bunny")

    def test_product_filtering_by_brand_and_size(self):
        response = self.client.get(reverse('shop:product_list'), {
            'brand': 'FluffyPaws',
            'size': 'Medium',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Luna Bunny")
        self.assertNotContains(response, "Barnaby Bear")

    def test_product_sorting_price_asc_desc(self):
        response = self.client.get(reverse('shop:product_list'), {'sort': 'price_low'})
        self.assertEqual(response.status_code, 200)

    # 5. Product Detail View
    def test_product_detail_view(self):
        response = self.client.get(reverse('shop:product_detail', args=[self.product1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.name)
        self.assertContains(response, "₹45.00")

    # 6. Cart Module Tests
    def test_add_to_cart_and_stock_limit(self):
        self.client.login(username='emily', password='password123')
        # Add 2 items
        response = self.client.post(reverse('shop:add_to_cart', args=[self.product1.pk]), {'quantity': 2})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.customer)
        item = cart.items.get(product=self.product1)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(cart.get_total(), 90.00)

        # Update cart quantity
        self.client.post(reverse('shop:update_cart_item', args=[item.id]), {'quantity': 3})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)
        self.assertEqual(cart.get_total(), 135.00)

        # Test AJAX update returns JSON with real-time recalculations
        ajax_resp = self.client.post(
            reverse('shop:update_cart_item', args=[item.id]),
            {'quantity': 2},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(ajax_resp.status_code, 200)
        data = ajax_resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['quantity'], 2)
        self.assertEqual(data['item_subtotal'], '90.00')
        self.assertEqual(data['subtotal'], '90.00')
        self.assertEqual(data['total_items'], 2)

        # Remove item
        self.client.get(reverse('shop:remove_cart_item', args=[item.id]))
        self.assertFalse(cart.items.filter(product=self.product1).exists())

    def test_add_out_of_stock_to_cart_fails(self):
        self.client.login(username='emily', password='password123')
        response = self.client.post(reverse('shop:add_to_cart', args=[self.product_out_of_stock.pk]), {'quantity': 1})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.customer)
        self.assertFalse(cart.items.filter(product=self.product_out_of_stock).exists())

    # 7. Wishlist Module Tests
    def test_wishlist_add_and_prevent_duplicates(self):
        self.client.login(username='emily', password='password123')
        self.client.post(reverse('shop:add_to_wishlist', args=[self.product1.pk]))
        self.client.post(reverse('shop:add_to_wishlist', args=[self.product1.pk]))
        wishlist = Wishlist.objects.get(user=self.customer)
        self.assertEqual(wishlist.items.filter(product=self.product1).count(), 1)

        # Move to cart
        item = wishlist.items.get(product=self.product1)
        self.client.post(reverse('shop:move_wishlist_to_cart', args=[item.id]))
        self.assertFalse(wishlist.items.filter(product=self.product1).exists())
        cart = Cart.objects.get(user=self.customer)
        self.assertTrue(cart.items.filter(product=self.product1).exists())

    # 8. Address Module Tests
    def test_address_management(self):
        self.client.login(username='emily', password='password123')
        # Add new address
        response = self.client.post(reverse('shop:add_address'), {
            'full_name': 'Emily Watson Work',
            'phone': '9876543210',
            'house_building': 'Tower 2, Tech Park',
            'street': 'Whitefield',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560066',
            'country': 'India',
            'address_type': 'work',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Address.objects.filter(user=self.customer).count(), 2)

    # 9. Checkout & Order Flow Tests
    def test_checkout_cod_order_placement_and_stock_reduction(self):
        self.client.login(username='emily', password='password123')
        # Add product to cart
        self.client.post(reverse('shop:add_to_cart', args=[self.product1.pk]), {'quantity': 2})
        
        initial_stock = self.product1.stock_quantity
        # Post checkout with COD
        response = self.client.post(reverse('shop:checkout'), {
            'address': self.address.id,
            'payment_method': 'cod'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify order created
        order = Order.objects.filter(user=self.customer).latest('id')
        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(order.subtotal, Decimal('90.00'))
        self.assertEqual(order.tax_amount, Decimal('4.50'))
        self.assertEqual(order.shipping_fee, Decimal('80.00'))
        self.assertEqual(order.total_amount, Decimal('174.50'))
        self.assertEqual(order.payment.payment_method, 'cod')
        self.assertEqual(order.payment.status, 'pending')

        # Verify sales invoice generated (Table 14)
        invoice = SalesInvoice.objects.get(order=order)
        self.assertEqual(invoice.subtotal, Decimal('90.00'))
        self.assertEqual(invoice.tax, Decimal('4.50'))
        self.assertEqual(invoice.total_amount, Decimal('174.50'))
        self.assertTrue(invoice.invoice_number.startswith('INV-'))

        # Verify stock reduced
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, initial_stock - 2)

        # Verify cart cleared
        cart = Cart.objects.get(user=self.customer)
        self.assertEqual(cart.items.count(), 0)

    # 10. Mock Payment Simulation Tests
    def test_mock_payment_success_and_failure(self):
        self.client.login(username='emily', password='password123')
        self.client.post(reverse('shop:add_to_cart', args=[self.product2.pk]), {'quantity': 1})
        
        # Checkout with Online Payment
        response = self.client.post(reverse('shop:checkout'), {
            'address': self.address.id,
            'payment_method': 'online'
        })
        order = Order.objects.filter(user=self.customer).latest('id')
        self.assertEqual(order.status, 'pending')

        # Simulate Payment Failure
        self.client.post(reverse('shop:payment_simulation', args=[order.id]), {
            'simulation_action': 'failure',
            'sub_method': 'card'
        })
        order.payment.refresh_from_db()
        self.assertEqual(order.payment.status, 'failed')

        # Simulate Payment Success
        self.client.post(reverse('shop:payment_simulation', args=[order.id]), {
            'simulation_action': 'success',
            'sub_method': 'card'
        })
        order.refresh_from_db()
        order.payment.refresh_from_db()
        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(order.payment.status, 'success')
        self.assertTrue(order.payment.transaction_id.startswith('TXN-CC'))

    # 11. Order Cancellation & Stock Restoration Tests
    def test_order_cancellation_restores_stock(self):
        self.client.login(username='emily', password='password123')
        self.client.post(reverse('shop:add_to_cart', args=[self.product1.pk]), {'quantity': 2})
        self.client.post(reverse('shop:checkout'), {
            'address': self.address.id,
            'payment_method': 'cod'
        })
        order = Order.objects.filter(user=self.customer).latest('id')
        self.product1.refresh_from_db()
        stock_after_order = self.product1.stock_quantity
        self.assertEqual(stock_after_order, 18)

        # Cancel order
        response = self.client.post(reverse('shop:cancel_order', args=[order.pk]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')

        # Verify stock restored
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 20)


    # 12. Verified Purchase Review Gate Tests
    def test_unverified_customer_cannot_review(self):
        self.client.login(username='david', password='password123')
        # David has never purchased product1
        response = self.client.post(reverse('shop:product_detail', args=[self.product1.pk]), {
            'rating': 5,
            'comment': 'Fake review attempt'
        })
        self.assertFalse(Review.objects.filter(user=self.other_customer, product=self.product1).exists())

    def test_verified_delivered_customer_can_review(self):
        # Create a delivered order for Emily with product1
        order = Order.objects.create(
            user=self.customer,
            address=self.address,
            total_amount=45.00,
            status='delivered'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            product_name="Barnaby Bear",
            quantity=1,
            price_at_purchase=45.00
        )

        self.client.login(username='emily', password='password123')
        response = self.client.post(reverse('shop:product_detail', args=[self.product1.pk]), {
            'rating': 5,
            'comment': 'Extremely soft and beautiful!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(user=self.customer, product=self.product1).exists())

    # 13. Admin Dashboard & Authorization Tests
    def test_customer_cannot_access_admin_portal(self):
        self.client.login(username='emily', password='password123')
        response = self.client.get(reverse('shop:admin_overview'))
        self.assertEqual(response.status_code, 302)  # redirected to login

    def test_admin_can_access_admin_portal(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('shop:admin_overview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back, Admin!")
        self.assertContains(response, "Total Sales")
        self.assertContains(response, "Active Orders")
        self.assertContains(response, "New Customers")
        self.assertContains(response, "Low Stock Alerts")
        self.assertContains(response, "Logout")

    def test_admin_inventory_update(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.post(reverse('shop:admin_inventory_update', args=[self.product1.pk]), {
            'stock_quantity': 50
        })
        self.assertEqual(response.status_code, 302)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 50)

    # 14. Product Size Price Test (Fixed price per product without auto-scaling)
    def test_product_size_price_scaling(self):
        # Base price: 500
        p = Product.objects.create(
            name="Test Giant Bear",
            category=self.cat_teddy,
            price=Decimal('500.00'),
            size='Medium',
            stock_quantity=10,
        )
        self.assertEqual(p.get_price_for_size('Medium'), Decimal('500.00'))
        self.assertEqual(p.get_price_for_size(), Decimal('500.00'))

    # 15. Coupon CLUB10 10% Discount & Free Delivery Tests
    def test_coupon_club10_and_free_delivery_over_600(self):
        self.client.login(username='emily', password='password123')
        
        # Product with price 1000
        p_high = Product.objects.create(
            name="Deluxe Bear",
            category=self.cat_teddy,
            price=Decimal('1000.00'),
            stock_quantity=5,
        )
        # Add to cart
        self.client.post(reverse('shop:add_to_cart', args=[p_high.pk]), {'quantity': 1, 'size': 'Medium'})

        # Apply coupon CLUB10
        response = self.client.post(reverse('shop:apply_coupon'), {'code': 'CLUB10'})
        self.assertEqual(response.status_code, 302)

        # Checkout
        checkout_resp = self.client.post(reverse('shop:checkout'), {
            'address': self.address.id,
            'payment_method': 'cod'
        })
        self.assertEqual(checkout_resp.status_code, 302)

        order = Order.objects.filter(user=self.customer).latest('id')
        # Subtotal: 1000
        # Discount: 10% = 100
        # Discounted subtotal: 900 >= 600 -> shipping_fee = 0
        # Tax: 5% of 900 = 45.00
        # Total: 900 + 45 = 945.00
        self.assertEqual(order.subtotal, Decimal('1000.00'))
        self.assertEqual(order.discount_amount, Decimal('100.00'))
        self.assertEqual(order.shipping_fee, Decimal('0.00'))
        self.assertEqual(order.tax_amount, Decimal('45.00'))
        self.assertEqual(order.total_amount, Decimal('945.00'))
        self.assertEqual(order.coupon_code, 'CLUB10')

        # Check invoice generated
        invoice = SalesInvoice.objects.get(order=order)
        self.assertEqual(invoice.subtotal, Decimal('1000.00'))
        self.assertEqual(invoice.discount, Decimal('100.00'))
        self.assertEqual(invoice.tax, Decimal('45.00'))
        self.assertEqual(invoice.total_amount, Decimal('945.00'))

        # Check invoice view status
        inv_resp = self.client.get(reverse('shop:order_invoice', args=[order.id]))
        self.assertEqual(inv_resp.status_code, 200)
        self.assertContains(inv_resp, invoice.invoice_number)
        self.assertContains(inv_resp, "TAX INVOICE")

    # 16. Cancellation Prevention on Shipped/Delivered Orders
    def test_shipped_order_cancellation_prevented(self):
        self.client.login(username='emily', password='password123')
        order = Order.objects.create(
            user=self.customer,
            address=self.address,
            total_amount=500.00,
            status='shipped'
        )
        response = self.client.post(reverse('shop:cancel_order', args=[order.pk]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'shipped')  # Remains shipped, NOT cancelled!

    # 17. Categories and About Pages Load
    def test_categories_and_about_pages(self):
        cat_resp = self.client.get(reverse('shop:categories'))
        self.assertEqual(cat_resp.status_code, 200)
        self.assertContains(cat_resp, "Soft Toy Categories")

        about_resp = self.client.get(reverse('shop:about'))
        self.assertEqual(about_resp.status_code, 200)
        self.assertContains(about_resp, "The CuddleCart Story")

    # 18. Buy Now, AJAX Cart, and User Dashboard Tests
    def test_buy_now_direct_checkout_redirect(self):
        self.client.login(username='emily', password='password123')
        response = self.client.post(reverse('shop:add_to_cart', args=[self.product1.pk]), {
            'quantity': 1,
            'buy_now': '1'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/checkout/', response.url)

    def test_ajax_add_to_cart_returns_json_without_page_reload(self):
        self.client.login(username='emily', password='password123')
        response = self.client.post(
            reverse('shop:add_to_cart', args=[self.product1.pk]),
            {'quantity': 1, 'ajax': '1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('cart_count', data)
        self.assertIn('drawer_html', data)
        self.assertIn('Barnaby Bear', data['drawer_html'])

    def test_ajax_remove_cart_item_returns_json(self):
        self.client.login(username='emily', password='password123')
        # Add item first
        self.client.post(reverse('shop:add_to_cart', args=[self.product1.pk]), {'quantity': 1})
        cart = Cart.objects.get(user__username='emily')
        item = cart.items.first()
        # Remove via AJAX
        response = self.client.get(
            reverse('shop:remove_cart_item', args=[item.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 0)
        self.assertIn('drawer_html', data)
        self.assertIn('Your Bag is Empty', data['drawer_html'])

    def test_ajax_wishlist_toggle_returns_json(self):
        self.client.login(username='emily', password='password123')
        # First toggle: add
        resp1 = self.client.post(
            reverse('shop:add_to_wishlist', args=[self.product1.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertTrue(resp1.json()['in_wishlist'])

        # Second toggle: remove
        resp2 = self.client.post(
            reverse('shop:add_to_wishlist', args=[self.product1.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(resp2.json()['in_wishlist'])

    def test_user_dashboard_loads_for_customer(self):
        self.client.login(username='emily', password='password123')
        response = self.client.get(reverse('shop:user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back")
        self.assertNotContains(response, "Continue Your Nursery Journey")
        self.assertNotContains(response, "View Member Family Guide")

    def test_product_form_image_is_mandatory(self):
        from shop.forms import ProductForm
        # Missing image and image_url
        form = ProductForm(data={
            'name': 'Test Giraffe',
            'category': self.cat_animals.pk,
            'brand': 'CuddleCart',
            'price': '499.00',
            'size': 'Medium',
            'age_group': '3–6 years',
            'stock_quantity': 10,
            'is_active': True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

        # Providing image_url makes it valid
        valid_form = ProductForm(data={
            'name': 'Test Giraffe',
            'category': self.cat_animals.pk,
            'brand': 'CuddleCart',
            'price': '499.00',
            'size': 'Medium',
            'age_group': '3–6 years',
            'stock_quantity': 10,
            'image_url': 'https://example.com/giraffe.jpg',
            'is_active': True,
        })
        self.assertTrue(valid_form.is_valid())

    def test_product_get_image_no_random_fallback(self):
        p = Product.objects.create(
            name="No Image Toy",
            category=self.cat_animals,
            price=Decimal('299.00'),
            size='Medium',
            stock_quantity=5,
        )
        self.assertEqual(p.get_image(), '')

    def test_cart_item_uses_product_size(self):
        self.client.login(username='emily', password='password123')
        # product1 is created with size "Large"
        resp = self.client.post(
            reverse('shop:add_to_cart', args=[self.product1.pk]),
            {'quantity': 1}
        )
        cart_item = CartItem.objects.filter(product=self.product1).first()
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.selected_size, 'Large')


