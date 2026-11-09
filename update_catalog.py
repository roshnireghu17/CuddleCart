import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cuddlecart.settings')
django.setup()

from shop.models import Product, Category, ProductImage

def run_update():
    # 1. Update existing products with correct plushie photos
    updates = {
        15: {'image': 'products/unicorn_plush.jpg', 'image_url': '', 'name': 'Magical Unicorn Plush'},
        10: {'image': 'products/panda_plush.jpg', 'image_url': '', 'name': 'Fluffy Panda Soft Toy'},
        11: {'image': 'products/elephant_plush.jpg', 'image_url': '', 'name': 'Sweet Elephant Plushie'},
        12: {'image': 'products/cartoon_bear.jpg', 'image_url': '', 'name': 'Cozy Honey Bear Plush'},
        13: {'image': 'products/sleeping_cat.jpg', 'image_url': '', 'name': 'Sleeping Kitty Soft Toy'},
        14: {'image': 'products/puppy_plush.jpg', 'image_url': '', 'name': 'Cuddly Puppy Soft Toy'},
        16: {'image': 'products/pip_penguin.jpg', 'image_url': '', 'name': 'Pip Penguin Soft Toy'},
        17: {'image': 'products/heart_pillow.jpg', 'image_url': '', 'name': 'Heart Pillow Plush Cushion'},
        8:  {'image': 'products/barnaby_bear.jpg', 'image_url': '', 'name': 'Classic Heritage Teddy Bear'},
        9:  {'image': 'products/luna_bunny.jpg', 'image_url': '', 'name': 'Luna Bunny Plush Friend'},
        5:  {'image': 'products/barnaby_bear.jpg', 'image_url': '', 'name': 'Ramsey Baby Bear'},
    }

    for pid, fields in updates.items():
        try:
            p = Product.objects.get(id=pid)
            for k, v in fields.items():
                setattr(p, k, v)
            p.is_available = True
            p.is_active = True
            if p.stock_quantity == 0:
                p.stock_quantity = 25
            p.save()
            print(f'Updated product {pid}: {p.name} -> {p.image}')
        except Product.DoesNotExist:
            print(f'Product {pid} not found')

    # 2. Add More Gift Sets
    gift_cat, _ = Category.objects.get_or_create(
        name='Gift Sets',
        defaults={'description': 'Curated luxury gift sets for newborns, birthdays and baby showers.'}
    )

    gift_sets_to_add = [
        {
            'name': 'Newborn Welcome Gift Hamper',
            'category': gift_cat,
            'description': 'The quintessential nursery welcome hamper featuring our ultra-soft organic bunny plush, hand-knitted cotton blanket, and beechwood soothing rattle in a keepsake woven basket.',
            'price': 78.00,
            'brand': 'CuddleCart',
            'size': 'Large',
            'age_group': '0–3 years',
            'stock_quantity': 25,
            'image': 'products/gift_newborns.jpg',
            'image_url': '',
        },
        {
            'name': 'Birthday Celebration Gift Box',
            'category': gift_cat,
            'description': 'Delight little dreamers on their birthday with this curated celebration box featuring our lovable Barnaby Bear, a party plushie, and a keepsake embroidered milestone pouch.',
            'price': 85.00,
            'brand': 'CuddleCart',
            'size': 'Large',
            'age_group': '3–6 years',
            'stock_quantity': 20,
            'image': 'products/gift_birthdays.jpg',
            'image_url': '',
        },
        {
            'name': 'Woodland Trio Luxury Gift Box',
            'category': gift_cat,
            'description': 'A magical trio of woodland companions including Finnegan Fox, Pip Penguin, and Barnaby Bear, beautifully wrapped with golden silk ribbon and an adoption certificate.',
            'price': 95.00,
            'brand': 'CuddleCart',
            'size': 'Extra Large',
            'age_group': '3–6 years',
            'stock_quantity': 15,
            'image': 'products/honey_bear_gift.jpg',
            'image_url': '',
        }
    ]

    for g_data in gift_sets_to_add:
        p, created = Product.objects.get_or_create(name=g_data['name'], defaults=g_data)
        if not created:
            for k, v in g_data.items():
                setattr(p, k, v)
            p.save()
        print(f'Gift set ready: {p.name} (id={p.id})')

    # 3. Add rich gallery images
    ProductImage.objects.all().delete()
    gallery_items = [
        ('Barnaby Bear', ['products/cartoon_bear.jpg', 'products/honey_bear_gift.jpg']),
        ('Luna Bunny', ['products/gift_newborns.jpg']),
        ('Finnegan Fox', ['products/honey_bear_gift.jpg']),
        ('Magical Unicorn Plush', ['products/gift_birthdays.jpg']),
        ('Fluffy Panda Soft Toy', ['products/cartoon_bear.jpg']),
        ('Sweet Elephant Plushie', ['products/snuggle_elephant.jpg']),
        ('Snuggle Elephant', ['products/elephant_plush.jpg']),
        ('Newborn Welcome Gift Hamper', ['products/luna_bunny.jpg']),
        ('Birthday Celebration Gift Box', ['products/barnaby_bear.jpg']),
        ('Woodland Trio Luxury Gift Box', ['products/finnegan_fox.jpg', 'products/pip_penguin.jpg']),
    ]

    for prod_name, img_list in gallery_items:
        prods = Product.objects.filter(name__icontains=prod_name)
        if prods.exists():
            pr = prods.first()
            for img_path in img_list:
                ProductImage.objects.create(product=pr, image=img_path, alt_text=f'{pr.name} detailed view')
            print(f'Added gallery images for {pr.name}')

    print('Database catalog update completed successfully!')

if __name__ == '__main__':
    run_update()
