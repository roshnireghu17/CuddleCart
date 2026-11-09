import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .models import User, Address, Product, ProductImage, Category, Review, Order


WIDGET_ATTRS = {'class': 'form-control'}
SELECT_ATTRS = {'class': 'form-select'}


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Enter your email address', 'autocomplete': 'off'})
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Enter 10-digit mobile number', 'maxlength': '10', 'autocomplete': 'off'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Enter your full name', 'autocomplete': 'off'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                **WIDGET_ATTRS,
                'placeholder': 'Min 8 chars, 1 uppercase, 1 number & 1 symbol',
                'autocomplete': 'new-password'
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                **WIDGET_ATTRS,
                'placeholder': 'Re-enter password to confirm',
                'autocomplete': 'new-password'
            })

    def clean_username(self):
        raw_val = self.cleaned_data.get('username', '')

        # Check for empty string or only whitespace
        if not raw_val or not raw_val.strip():
            raise ValidationError('Name cannot be empty or contain only blank spaces.')

        # Check for space tags or HTML tags like &nbsp;, <space>, etc.
        if re.search(r'<[^>]+>', raw_val) or any(tag in raw_val.lower() for tag in ['&nbsp;', '&emsp;', '&ensp;', '<space>', '</space>']):
            raise ValidationError('Name cannot contain space tags (&nbsp;) or HTML tags.')

        cleaned = raw_val.strip()

        # Reject strings without any letters
        if not re.search(r'[a-zA-Z]', cleaned):
            raise ValidationError('Name must contain letters.')

        if len(cleaned) < 3:
            raise ValidationError('Name must be at least 3 characters long.')

        if len(cleaned) > 150:
            raise ValidationError('Name cannot exceed 150 characters.')

        # Check for valid characters: letters, numbers, spaces, dots, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9 ._\-]+$', cleaned):
            raise ValidationError('Name can only contain letters, numbers, spaces, dots, hyphens, and underscores.')

        # Normalize multiple internal spaces to a single space
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Normalize candidate username for unique username checking
        candidate_username = re.sub(r'\s+', '_', cleaned)

        if User.objects.filter(username__iexact=candidate_username).exists() or User.objects.filter(username__iexact=cleaned).exists():
            raise ValidationError('This name / username is already taken. Please choose another.')

        return candidate_username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            digits = re.sub(r'[\s\-\(\)\+]', '', phone)
            if digits.startswith('91') and len(digits) == 12:
                digits = digits[2:]
            elif digits.startswith('0') and len(digits) == 11:
                digits = digits[1:]
            if not re.match(r'^\d{10}$', digits):
                raise ValidationError('Phone number must be exactly 10 digits.')
            return digits
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError('Email address is required.')

        # Strict RFC-compliant email pattern check
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email) or '..' in email:
            raise ValidationError('Please enter a valid email address.')

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address already exists. Please sign in instead.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if not password:
            raise ValidationError('Password is required.')
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase capital letter (A-Z).')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter (a-z).')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must contain at least one number (0-9).')
        if not re.search(r'[^a-zA-Z0-9]', password):
            raise ValidationError('Password must contain at least one special character or symbol (e.g. !@#$%^&*).')
        return password

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2', '')
        if not p2:
            raise ValidationError('Please re-enter your password to confirm.')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Passwords do not match. Please ensure both passwords are identical.')
        return p2

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match. Please ensure both passwords are identical.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.role = 'customer'

        raw_name = self.data.get('username', '').strip()
        parts = raw_name.split(' ', 1)
        if len(parts) > 1:
            user.first_name = parts[0]
            user.last_name = parts[1]
        else:
            user.first_name = raw_name

        if commit:
            user.save()
        return user


class StyledAuthenticationForm(AuthenticationForm):
    """Allows login via either Username or Email with thorough validation."""
    username = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Enter email or username', 'autofocus': True})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Enter your password'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError('Please enter your email or username.')
        if re.search(r'<[^>]+>', username) or '&nbsp;' in username.lower():
            raise ValidationError('Input cannot contain HTML or space tags.')
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if not password:
            raise ValidationError('Please enter your password.')
        return password

    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username_or_email and password:
            user = None
            # Check if input is email
            if '@' in username_or_email:
                try:
                    user_obj = User.objects.get(email__iexact=username_or_email)
                    user = authenticate(self.request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            if user is None:
                user = authenticate(self.request, username=username_or_email, password=password)

            if user is None:
                raise forms.ValidationError('Invalid email/username or password. Please verify your credentials and try again.')
            elif not user.is_active or not getattr(user, 'is_active_customer', True):
                raise forms.ValidationError('This account has been deactivated. Please contact support.')
            self.user_cache = user

        return self.cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
        widgets = {
            'first_name': forms.TextInput(attrs=WIDGET_ATTRS),
            'last_name': forms.TextInput(attrs=WIDGET_ATTRS),
            'email': forms.EmailInput(attrs=WIDGET_ATTRS),
            'phone': forms.TextInput(attrs=WIDGET_ATTRS),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        user_id = self.instance.id if self.instance else None
        if User.objects.filter(email__iexact=email).exclude(id=user_id).exists():
            raise ValidationError('This email address is already in use by another account.')
        return email


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('full_name', 'phone', 'house_building', 'street', 'city', 'state', 'pincode', 'country', 'address_type', 'is_default')
        widgets = {
            'full_name': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Full recipient name'}),
            'phone': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': '10-digit mobile number', 'maxlength': '10', 'inputmode': 'numeric'}),
            'house_building': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Flat / House No., Building Name'}),
            'street': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Street, Area, Landmark'}),
            'city': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'City / Town'}),
            'state': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': '6-digit PIN code', 'maxlength': '6', 'inputmode': 'numeric'}),
            'country': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Country'}),
            'address_type': forms.Select(attrs=SELECT_ATTRS),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_phone(self):
        raw = self.cleaned_data.get('phone', '').strip()
        digits = re.sub(r'[\s\-\(\)\+]', '', raw)
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        if not digits:
            raise ValidationError('Contact mobile number is required.')
        if not re.match(r'^\d{10}$', digits):
            raise ValidationError('Contact mobile number must be exactly 10 digits.')
        return digits

    def clean_pincode(self):
        raw = self.cleaned_data.get('pincode', '').strip()
        digits = re.sub(r'\s+', '', raw)
        if not digits:
            raise ValidationError('PIN code is required.')
        if not re.match(r'^\d{6}$', digits):
            raise ValidationError('PIN code must be exactly 6 digits.')
        return digits


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.Select(
                choices=[
                    (5, '⭐⭐⭐⭐⭐ (5 - Exceptional)'),
                    (4, '⭐⭐⭐⭐ (4 - Very Good)'),
                    (3, '⭐⭐⭐ (3 - Good)'),
                    (2, '⭐⭐ (2 - Fair)'),
                    (1, '⭐ (1 - Poor)'),
                ],
                attrs=SELECT_ATTRS
            ),
            'comment': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 4, 'placeholder': 'Write your honest review about this soft toy (quality, softness, stitching, etc.)...'}),
        }


class CheckoutForm(forms.Form):
    address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        widget=forms.Select(attrs=SELECT_ATTRS),
        empty_label="-- Choose a delivery address --",
        required=True
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('online', 'Online Payment (Card / UPI / Net Banking - Instant Simulated)'),
            ('cod', 'Cash on Delivery (Pay upon delivery)'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='online'
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['address'].queryset = Address.objects.filter(user=user)
            default_address = Address.objects.filter(user=user, is_default=True).first()
            if default_address:
                self.fields['address'].initial = default_address.id


# ---------- Admin forms ----------

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'image', 'image_url', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'e.g., Teddy Bears'}),
            'description': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3, 'placeholder': 'Short description of this category...'}),
            'image': forms.FileInput(attrs=WIDGET_ATTRS),
            'image_url': forms.URLInput(attrs={**WIDGET_ATTRS, 'placeholder': 'https://example.com/category-image.jpg'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'category', 'name', 'brand', 'price', 'size', 'age_group',
            'stock_quantity', 'image', 'image_url', 'description', 'is_active'
        )
        widgets = {
            'category': forms.Select(attrs=SELECT_ATTRS),
            'name': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'e.g., Barnaby Cuddle Bear'}),
            'brand': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'e.g., CuddleCart'}),
            'price': forms.NumberInput(attrs={**WIDGET_ATTRS, 'placeholder': '0.00', 'step': '0.01', 'min': '0.01'}),
            'size': forms.Select(attrs=SELECT_ATTRS),
            'age_group': forms.Select(attrs=SELECT_ATTRS),
            'stock_quantity': forms.NumberInput(attrs={**WIDGET_ATTRS, 'placeholder': '0', 'min': '0'}),
            'image': forms.FileInput(attrs=WIDGET_ATTRS),
            'image_url': forms.URLInput(attrs={**WIDGET_ATTRS, 'placeholder': 'https://example.com/product-image.jpg'}),
            'description': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 4, 'placeholder': 'Detailed soft toy description, fabric materials, washing instructions...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')
        has_existing_image = bool(self.instance and self.instance.pk and (self.instance.image or self.instance.image_url))

        if not image and not image_url and not has_existing_image:
            self.add_error('image', 'Product image is mandatory. Please upload an image file or provide an image URL.')
        return cleaned_data

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise ValidationError('Price must be greater than zero.')
        return price

    def clean_stock_quantity(self):
        stock = self.cleaned_data.get('stock_quantity')
        if stock is not None and stock < 0:
            raise ValidationError('Stock quantity cannot be negative.')
        return stock


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ('image', 'image_url', 'alt_text')
        widgets = {
            'image': forms.FileInput(attrs=WIDGET_ATTRS),
            'image_url': forms.URLInput(attrs={**WIDGET_ATTRS, 'placeholder': 'https://...'}),
            'alt_text': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Image caption/alt text'}),
        }


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status',)
        widgets = {'status': forms.Select(attrs=SELECT_ATTRS)}
