import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from shop.models import Category, Product, ProductImage, Cart, Wishlist, Address, Order, OrderItem, Payment, Review

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds CuddleCart with comprehensive categories, soft toys, demo users, orders, and verified reviews."

    def handle(self, *args, **options):
        self.stdout.write("Seeding CuddleCart Soft Toy E-Commerce database...")

        # 1. Categories
        cat_teddy, _ = Category.objects.get_or_create(
            name="Teddy Bears",
            defaults={"description": "Classic, snuggly teddy bears handcrafted with organic hypoallergenic cotton."}
        )
        cat_animals, _ = Category.objects.get_or_create(
            name="Animals",
            defaults={"description": "Adorable wildlife, jungle, and woodland plush animal companions."}
        )
        cat_cartoon, _ = Category.objects.get_or_create(
            name="Cartoon Characters",
            defaults={"description": "Fun, expressive animated soft toys full of charm and personality."}
        )
        cat_dolls, _ = Category.objects.get_or_create(
            name="Dolls",
            defaults={"description": "Soft fabric storybook dolls and whimsical fairytale companions."}
        )
        cat_baby, _ = Category.objects.get_or_create(
            name="Baby Soft Toys",
            defaults={"description": "Gentle, sensory-friendly first friends designed to soothe newborns and infants."}
        )
        cat_pillow, _ = Category.objects.get_or_create(
            name="Pillow Plushies",
            defaults={"description": "Ultra-cushiony hugging pillows and bedtime bolster plushies."}
        )

        # 2. Products matching Section 41
        products_data = [
            {
                "name": "Classic Teddy Bear",
                "category": cat_teddy,
                "brand": "TeddyLand",
                "size": "Medium",
                "age_group": "3–6 years",
                "price": 42.00,
                "stock": 25,
                "desc": "A timeless honey-brown handcrafted teddy bear with a warm velvet bow. Super soft and cuddly for storytime.",
                "image_url": "https://images.unsplash.com/photo-1559454403-b8fb88521f11?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Cute Bunny Plush",
                "category": cat_animals,
                "brand": "FluffyPaws",
                "size": "Small",
                "age_group": "0–3 years",
                "price": 35.00,
                "stock": 18,
                "desc": "Delicate pastel blush bunny with extra-long floppy ears and embroidered facial features for infant safety.",
                "image_url": "https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Panda Soft Toy",
                "category": cat_animals,
                "brand": "CuddleCart",
                "size": "Large",
                "age_group": "3–6 years",
                "price": 48.00,
                "stock": 15,
                "desc": "A lovable black-and-white giant panda plushie made from velvety organic plush fabric.",
                "image_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Elephant Plushie",
                "category": cat_animals,
                "brand": "HugMe",
                "size": "Medium",
                "age_group": "0–3 years",
                "price": 38.00,
                "stock": 12,
                "desc": "Gentle grey plush elephant with big floppy ears and a soft curved trunk. Safe for newborns.",
                "image_url": "https://images.unsplash.com/photo-1579613832125-5d34a13ffe2a?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Cartoon Bear",
                "category": cat_cartoon,
                "brand": "CuddleCart",
                "size": "Medium",
                "age_group": "3–6 years",
                "price": 39.00,
                "stock": 14,
                "desc": "Cheery cartoon-styled bear companion with vibrant amber fur and stitched smiling eyes.",
                "image_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Sleeping Cat Plush",
                "category": cat_animals,
                "brand": "FluffyPaws",
                "size": "Small",
                "age_group": "3–6 years",
                "price": 29.00,
                "stock": 20,
                "desc": "Calm, curled-up calico kitten plushie designed to bring comforting bedtime calm.",
                "image_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Puppy Soft Toy",
                "category": cat_animals,
                "brand": "TeddyLand",
                "size": "Medium",
                "age_group": "0–3 years",
                "price": 34.00,
                "stock": 16,
                "desc": "Playful golden retriever puppy stuffed companion with soft floppy ears and wagging tail.",
                "image_url": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Unicorn Plush",
                "category": cat_dolls,
                "brand": "HugMe",
                "size": "Large",
                "age_group": "6–12 years",
                "price": 46.00,
                "stock": 10,
                "desc": "Magical pastel unicorn plushie featuring shimmering soft horn and rainbow mane.",
                "image_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Penguin Soft Toy",
                "category": cat_animals,
                "brand": "CuddleCart",
                "size": "Small",
                "age_group": "0–3 years",
                "price": 28.00,
                "stock": 22,
                "desc": "Waddle-ready penguin soft friend with plush white tummy and soft orange flippers.",
                "image_url": "https://images.unsplash.com/photo-1559454403-b8fb88521f11?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Heart Pillow Plush",
                "category": cat_pillow,
                "brand": "CuddleCart",
                "size": "Large",
                "age_group": "12+ years",
                "price": 32.00,
                "stock": 15,
                "desc": "Velvety crimson heart-shaped hugging pillow. Ergonomic support and plush warmth.",
                "image_url": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Barnaby Bear",
                "category": cat_teddy,
                "brand": "CuddleCart",
                "size": "Extra Large",
                "age_group": "3–6 years",
                "price": 55.00,
                "stock": 4, # Low stock
                "desc": "Our signature giant cuddle bear. Heirloom quality craftsmanship made for lifetime companionship.",
                "image_url": "https://images.unsplash.com/photo-1559454403-b8fb88521f11?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Luna Bunny",
                "category": cat_animals,
                "brand": "CuddleCart",
                "size": "Medium",
                "age_group": "0–3 years",
                "price": 38.00,
                "stock": 2, # Low stock
                "desc": "Signature blush bunny loved by thousands of families worldwide.",
                "image_url": "https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?auto=format&fit=crop&w=600&q=80",
            },
        ]

        created_products = {}
        for item in products_data:
            p, _ = Product.objects.update_or_create(
                name=item["name"],
                defaults={
                    "category": item["category"],
                    "brand": item["brand"],
                    "size": item["size"],
                    "age_group": item["age_group"],
                    "price": item["price"],
                    "stock_quantity": item["stock"],
                    "description": item["desc"],
                    "image_url": item["image_url"],
                    "is_available": True,
                    "is_active": True,
                }
            )
            created_products[item["name"]] = p

        # 3. Demo Admin User
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@cuddlecart.com",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True
            }
        )
        admin_user.set_password("admin123")
        admin_user.role = "admin"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        # 4. Demo Customer Users
        emily_user, _ = User.objects.get_or_create(
            username="emily",
            defaults={
                "first_name": "Emily",
                "last_name": "Watson",
                "email": "emily@example.com",
                "role": "customer",
                "phone": "9876543210"
            }
        )
        emily_user.set_password("password123")
        emily_user.first_name = "Emily"
        emily_user.role = "customer"
        emily_user.save()
        Cart.objects.get_or_create(user=emily_user)
        Wishlist.objects.get_or_create(user=emily_user)

        customer_user, _ = User.objects.get_or_create(
            username="customer",
            defaults={
                "first_name": "John",
                "last_name": "Doe",
                "email": "customer@example.com",
                "role": "customer",
                "phone": "9812345678"
            }
        )
        customer_user.set_password("customer123")
        customer_user.role = "customer"
        customer_user.save()
        Cart.objects.get_or_create(user=customer_user)
        Wishlist.objects.get_or_create(user=customer_user)

        sarah_user, _ = User.objects.get_or_create(
            username="sarah_m",
            defaults={
                "first_name": "Sarah",
                "last_name": "Miller",
                "email": "sarah@example.com",
                "role": "customer",
                "phone": "9876512345"
            }
        )
        sarah_user.set_password("password123")
        sarah_user.role = "customer"
        sarah_user.save()

        david_user, _ = User.objects.get_or_create(
            username="david_k",
            defaults={
                "first_name": "David",
                "last_name": "Knight",
                "email": "david@example.com",
                "role": "customer",
                "phone": "9823456789"
            }
        )
        david_user.set_password("password123")
        david_user.role = "customer"
        david_user.save()

        # 5. Addresses
        addr1, _ = Address.objects.get_or_create(
            user=emily_user,
            full_name="Emily Watson",
            phone="9876543210",
            house_building="Apt 4B, Sunflower Residency",
            street="Park Avenue, Green Hills",
            city="Bengaluru",
            state="Karnataka",
            pincode="560001",
            country="India",
            address_type="home",
            is_default=True
        )

        addr2, _ = Address.objects.get_or_create(
            user=customer_user,
            full_name="John Doe",
            phone="9812345678",
            house_building="Flat 102, Silver Oak",
            street="MG Road",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            country="India",
            address_type="home",
            is_default=True
        )

        # 6. Orders (Delivered Orders so verified reviews work)
        if not emily_user.orders.exists():
            order1 = Order.objects.create(
                user=emily_user,
                address=addr1,
                total_amount=created_products["Classic Teddy Bear"].price,
                status='delivered'
            )
            OrderItem.objects.create(
                order=order1,
                product=created_products["Classic Teddy Bear"],
                product_name="Classic Teddy Bear",
                quantity=1,
                price_at_purchase=created_products["Classic Teddy Bear"].price
            )
            Payment.objects.create(
                order=order1,
                payment_method='card',
                amount=order1.total_amount,
                status='success',
                transaction_id='TXN-CC-2026-1001'
            )

            order2 = Order.objects.create(
                user=emily_user,
                address=addr1,
                total_amount=created_products["Cute Bunny Plush"].price,
                status='delivered'
            )
            OrderItem.objects.create(
                order=order2,
                product=created_products["Cute Bunny Plush"],
                product_name="Cute Bunny Plush",
                quantity=1,
                price_at_purchase=created_products["Cute Bunny Plush"].price
            )
            Payment.objects.create(
                order=order2,
                payment_method='upi',
                amount=order2.total_amount,
                status='success',
                transaction_id='TXN-CC-2026-1002'
            )

            order3 = Order.objects.create(
                user=emily_user,
                address=addr1,
                total_amount=created_products["Panda Soft Toy"].price,
                status='shipped'
            )
            OrderItem.objects.create(
                order=order3,
                product=created_products["Panda Soft Toy"],
                product_name="Panda Soft Toy",
                quantity=1,
                price_at_purchase=created_products["Panda Soft Toy"].price
            )
            Payment.objects.create(
                order=order3,
                payment_method='online',
                amount=order3.total_amount,
                status='success',
                transaction_id='TXN-CC-2026-1003'
            )

        # 7. Reviews
        Review.objects.get_or_create(
            product=created_products["Classic Teddy Bear"],
            user=emily_user,
            defaults={
                "rating": 5,
                "comment": "Absolutely charming teddy bear! The stitching is top notch and the organic fabric feels wonderfully gentle."
            }
        )

        Review.objects.get_or_create(
            product=created_products["Cute Bunny Plush"],
            user=sarah_user,
            defaults={
                "rating": 5,
                "comment": "The cutest bunny ever! My toddler sleeps with it every night. Washes easily and retains softness."
            }
        )

        Review.objects.get_or_create(
            product=created_products["Barnaby Bear"],
            user=david_user,
            defaults={
                "rating": 5,
                "comment": "Classic design and wonderful quality. Perfect gift for our little one!"
            }
        )

        self.stdout.write(self.style.SUCCESS("CuddleCart demo database seeded successfully!"))
