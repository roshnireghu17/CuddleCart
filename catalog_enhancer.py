import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cuddlecart.settings')
django.setup()

from shop.models import Product, Category, ProductImage

def enhance_catalog():
    # Ensure categories exist
    cats = {
        'Teddy Bears': Category.objects.get_or_create(name='Teddy Bears', defaults={'description': 'Timeless handcrafted teddy bears stitched with organic cotton.'})[0],
        'Plushies': Category.objects.get_or_create(name='Plushies', defaults={'description': 'Adorable plush companions from playful bunnies to sweet cubs.'})[0],
        'Baby Soft Toys': Category.objects.get_or_create(name='Baby Soft Toys', defaults={'description': 'Infant-safe, ultra-soft first friends tested for 0+ months.'})[0],
        'Gift Sets': Category.objects.get_or_create(name='Gift Sets', defaults={'description': 'Curated luxury keepsake boxes and gift hampers.'})[0],
    }

    # 1. Update existing products with minimum Rs. 400 price and unique identities
    product_updates = [
        {
            'id': 1,
            'name': 'Barnaby Bear Heritage',
            'category': cats['Teddy Bears'],
            'price': Decimal('599.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 35,
            'image': 'products/barnaby_bear.jpg',
            'description': 'Our beloved flagship teddy bear crafted with ultra-plush organic cotton fur and gentle velvet paws. The perfect cuddle friend for childhood bedtime.'
        },
        {
            'id': 2,
            'name': 'Luna Bunny Plush',
            'category': cats['Plushies'],
            'price': Decimal('499.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 40,
            'image': 'products/luna_bunny.jpg',
            'description': 'A sweet floppy-eared bunny with velvety soft fur and hand-embroidered sleepy eyes. Hypoallergenic and ready for hugs.'
        },
        {
            'id': 3,
            'name': 'Finnegan Fox Plush',
            'category': cats['Plushies'],
            'price': Decimal('479.00'),
            'size': 'Medium',
            'age_group': '3–6 years',
            'stock_quantity': 30,
            'image': 'products/finnegan_fox.jpg',
            'description': 'Spirited and charming, Finnegan Fox brings storybook adventures to life with rich copper-toned fleece and a snow-white bushy tail.'
        },
        {
            'id': 4,
            'name': 'Pip Penguin Soft Toy',
            'category': cats['Plushies'],
            'price': Decimal('459.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 28,
            'image': 'products/pip_penguin.jpg',
            'description': 'An endearing baby penguin with super-soft velvety wings and a plump, huggable tummy designed for gentle snuggles.'
        },
        {
            'id': 5,
            'name': 'Ramsey Baby Bear',
            'category': cats['Baby Soft Toys'],
            'price': Decimal('449.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 25,
            'image': 'products/barnaby_bear.jpg',
            'description': 'Specially scaled for newborn tiny hands, Ramsey Baby Bear features 100% GOTS organic cotton yarns and gentle embroidered features.'
        },
        {
            'id': 6,
            'name': 'Snuggle Elephant First Friend',
            'category': cats['Baby Soft Toys'],
            'price': Decimal('529.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 22,
            'image': 'products/snuggle_elephant.jpg',
            'description': 'A gentle pastel grey baby elephant with floppy satin-trimmed ears and a comforting touch ideal for soothing infants.'
        },
        {
            'id': 7,
            'name': 'Honey Bear Keepsake Box',
            'category': cats['Gift Sets'],
            'price': Decimal('799.00'),
            'size': 'Large',
            'age_group': '3–6 years',
            'stock_quantity': 18,
            'image': 'products/honey_bear_gift.jpg',
            'description': 'A delightful gift set featuring Honey Bear nestled in a keepsake illustrated gift box tied with our signature emerald satin ribbon.'
        },
        {
            'id': 8,
            'name': 'Theodore Classic Teddy',
            'category': cats['Teddy Bears'],
            'price': Decimal('549.00'),
            'size': 'Medium',
            'age_group': '3–6 years',
            'stock_quantity': 32,
            'image': 'products/cartoon_bear.jpg',
            'description': 'A nostalgic, warm honey-toned teddy bear with a classic ribbon collar and exceptionally cuddly down-like hypoallergenic fill.'
        },
        {
            'id': 9,
            'name': 'Bella Buttercup Bunny',
            'category': cats['Plushies'],
            'price': Decimal('489.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 26,
            'image': 'products/luna_bunny.jpg',
            'description': 'An angelic soft bunny in buttermilk cream hue, crafted for soothing naps and imaginative daytime tea parties.'
        },
        {
            'id': 10,
            'name': 'Fluffy Panda Soft Toy',
            'category': cats['Plushies'],
            'price': Decimal('529.00'),
            'size': 'Medium',
            'age_group': '3–6 years',
            'stock_quantity': 24,
            'image': 'products/panda_plush.jpg',
            'description': 'Irresistibly cuddly black-and-white panda bear plush made from ultra-dense cloud fleece that retains its bounce hug after hug.'
        },
        {
            'id': 11,
            'name': 'Ellie Gentle Elephant',
            'category': cats['Plushies'],
            'price': Decimal('549.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 20,
            'image': 'products/elephant_plush.jpg',
            'description': 'A heartwarming stuffed elephant with soft trunk and generous ears, designed to bring a comforting presence to any nursery.'
        },
        {
            'id': 12,
            'name': 'Cozy Honey Bear Plush',
            'category': cats['Teddy Bears'],
            'price': Decimal('499.00'),
            'size': 'Medium',
            'age_group': '3–6 years',
            'stock_quantity': 25,
            'image': 'products/cartoon_bear.jpg',
            'description': 'A smiling teddy companion with plush corduroy accents and rounded ears, ideal for toddler cuddles.'
        },
        {
            'id': 13,
            'name': 'Sleeping Kitty Soft Toy',
            'category': cats['Plushies'],
            'price': Decimal('449.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 30,
            'image': 'products/sleeping_cat.jpg',
            'description': 'A curled-up sleepy kitten soft toy made from soothing brushed organic cotton fleece.'
        },
        {
            'id': 14,
            'name': 'Cuddly Puppy Soft Toy',
            'category': cats['Plushies'],
            'price': Decimal('479.00'),
            'size': 'Medium',
            'age_group': '3–6 years',
            'stock_quantity': 28,
            'image': 'products/puppy_plush.jpg',
            'description': 'A loyal, floppy-eared golden puppy plush with embroidered paws that invites endless affection.'
        },
        {
            'id': 15,
            'name': 'Magical Unicorn Plush',
            'category': cats['Plushies'],
            'price': Decimal('569.00'),
            'size': 'Medium',
            'age_group': '3–6 years',
            'stock_quantity': 22,
            'image': 'products/unicorn_plush.jpg',
            'description': 'An enchanted white unicorn with a gentle golden spiral horn and pastel rainbow mane crafted from baby-safe organic threads.'
        },
        {
            'id': 16,
            'name': 'Oliver Owl Soft Toy',
            'category': cats['Baby Soft Toys'],
            'price': Decimal('469.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 20,
            'image': 'products/pip_penguin.jpg',
            'description': 'A wise and whimsical feathered friend with plush wings and friendly embroidered eyes for curious little minds.'
        },
        {
            'id': 17,
            'name': 'Heart Pillow Plush Cushion',
            'category': cats['Baby Soft Toys'],
            'price': Decimal('429.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 35,
            'image': 'products/heart_pillow.jpg',
            'description': 'A velvety soft heart-shaped cuddle cushion that adds a loving touch to your child crib or rocking chair.'
        },
        {
            'id': 18,
            'name': 'Newborn Welcome Gift Hamper',
            'category': cats['Gift Sets'],
            'price': Decimal('1299.00'),
            'size': 'Large',
            'age_group': '0–3 years',
            'stock_quantity': 15,
            'image': 'products/gift_newborns.jpg',
            'description': 'The premier newborn welcome hamper featuring Luna Bunny plush, organic cotton receiving blanket, and beechwood teether in a keepsake hamper.'
        },
        {
            'id': 19,
            'name': 'Birthday Celebration Gift Box',
            'category': cats['Gift Sets'],
            'price': Decimal('1499.00'),
            'size': 'Large',
            'age_group': '3–6 years',
            'stock_quantity': 12,
            'image': 'products/gift_birthdays.jpg',
            'description': 'Celebrate milestone birthdays with Barnaby Bear, a festive party plush crown, celebratory greeting card, and luxury ribbon gift box.'
        },
        {
            'id': 20,
            'name': 'Woodland Trio Luxury Gift Box',
            'category': cats['Gift Sets'],
            'price': Decimal('1899.00'),
            'size': 'Extra Large',
            'age_group': '3–6 years',
            'stock_quantity': 10,
            'image': 'products/honey_bear_gift.jpg',
            'description': 'A collector gift set featuring Barnaby Bear, Finnegan Fox, and Pip Penguin packed in our royal green embossed gift trunk.'
        },
    ]

    for pdata in product_updates:
        pid = pdata['id']
        try:
            prod = Product.objects.get(id=pid)
            for k, v in pdata.items():
                if k != 'id':
                    setattr(prod, k, v)
            prod.is_available = True
            prod.is_active = True
            prod.save()
            print(f"Updated product #{pid}: {prod.name} -> Rs.{prod.price}")
        except Product.DoesNotExist:
            pdata_copy = dict(pdata)
            del pdata_copy['id']
            prod = Product.objects.create(id=pid, **pdata_copy)
            print(f"Created product #{pid}: {prod.name}")

    # 2. Add New Unique Products to expand catalog to 26 products
    new_products = [
        {
            'name': 'Buttercup Sunny Giraffe',
            'category': cats['Baby Soft Toys'],
            'price': Decimal('549.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 25,
            'image': 'products/elephant_plush.jpg',
            'image_url': 'https://images.unsplash.com/photo-1563089145-599997674d42?auto=format&fit=crop&w=600&q=80',
            'description': 'A cheerful and sunny giraffe with a soft patterned coat and huggable neck, hand-stitched from 100% certified organic cotton.'
        },
        {
            'name': 'Milo The Cuddly Koala',
            'category': cats['Plushies'],
            'price': Decimal('579.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 20,
            'image': 'products/panda_plush.jpg',
            'image_url': 'https://images.unsplash.com/photo-1540573133985-87b6da6d54a9?auto=format&fit=crop&w=600&q=80',
            'description': 'An adorable eucalyptus-loving koala with fluffy fleece ears and a soft velvet nose ready for gentle bedtime adventures.'
        },
        {
            'name': 'Daisy Meadow Lamb Plush',
            'category': cats['Baby Soft Toys'],
            'price': Decimal('499.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 30,
            'image': 'products/luna_bunny.jpg',
            'image_url': 'https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=600&q=80',
            'description': 'A sweet meadow lamb featuring soft textured boucle wool and gentle embroidered eyes, soothing for bedtime lullabies.'
        },
        {
            'name': 'Leo Little Lion Soft Toy',
            'category': cats['Plushies'],
            'price': Decimal('529.00'),
            'size': 'Medium',
            'age_group': '3–6 years',
            'stock_quantity': 22,
            'image': 'products/finnegan_fox.jpg',
            'image_url': 'https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80',
            'description': 'A brave yet gentle little lion with a soft yarn mane and golden cotton coat, inspiring sweet courage in little hearts.'
        },
        {
            'name': 'Barnaby & Friends Deluxe Cuddle Trunk',
            'category': cats['Gift Sets'],
            'price': Decimal('2199.00'),
            'size': 'Extra Large',
            'age_group': '3–6 years',
            'stock_quantity': 8,
            'image': 'products/gift_birthdays.jpg',
            'image_url': 'https://images.unsplash.com/photo-1513151233558-d860c5398176?auto=format&fit=crop&w=600&q=80',
            'description': 'Our ultimate heirloom gift trunk containing Barnaby Bear, Daisy Lamb, personalized birth certificate, and keepsake wooden memory box.'
        },
        {
            'name': 'Sleepy Sloth Organic Plush',
            'category': cats['Plushies'],
            'price': Decimal('519.00'),
            'size': 'Medium',
            'age_group': '0–3 years',
            'stock_quantity': 24,
            'image': 'products/sleeping_cat.jpg',
            'image_url': 'https://images.unsplash.com/photo-1589656966895-2f33e7653819?auto=format&fit=crop&w=600&q=80',
            'description': 'A slow-moving, peaceful sloth companion with hook-and-loop hugging arms designed to hang around cribs and gentle arms.'
        }
    ]

    for np in new_products:
        p, created = Product.objects.get_or_create(name=np['name'], defaults=np)
        if not created:
            for k, v in np.items():
                setattr(p, k, v)
            p.save()
        print(f"Product ready: {p.name} (id={p.id}, price=Rs.{p.price})")

    # Double check all products have price >= 400
    for p in Product.objects.all():
        if p.price < Decimal('400.00'):
            p.price = Decimal('449.00')
            p.save()
            print(f"Bumped price of #{p.id} to Rs. 449.00")

    print(f"Catalog successfully enhanced! Total products now: {Product.objects.count()}")

if __name__ == '__main__':
    enhance_catalog()
