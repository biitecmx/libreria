from email.mime import image
from django.db.models.signals import post_save
from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django.utils.text import slugify

from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from djbooks.helpers import upload_with_uuid

from mercadopago import SDK

PATH = "static/assets/books/"

def book_cover_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT / slug/<filename>
    return 'static/assets/books/libro_{0}/cover_{1}'.format(instance.slug, filename)

def book_back_path(instance, filename):
    return 'static/assets/books/libro_{0}/back_{1}'.format(instance.slug, filename)

def category_path(instance, filename):
    return 'static/assets/categories/{0}/{1}'.format(instance.name, filename)

class Category(models.Model):
    name = models.CharField(max_length=40)
    image = models.ImageField(upload_to=category_path,
    default="djbooks/static/assets/images/inner-page/banner.jpg", 
    null=True)
    slug = models.SlugField(max_length=40, blank=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = "Categories"

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=30)
    category = models.ManyToManyField(Category)
    editorial = models.CharField(max_length=30, blank=True)
    edition = models.CharField(max_length=20, blank=True)
    year = models.CharField(max_length=4, blank=True)
    price = models.FloatField(default=0, blank=True)
    discount_price = models.FloatField(blank=True, null=True)
    cover = models.ImageField(upload_to=book_cover_path,
    default="djbooks/static/assets/images/inner-page/category/1.jpg", blank=True)
    back = models.ImageField(upload_to=book_back_path, null=True, blank=True)
    description = models.TextField(default=None, null=True, blank=True)
    condition = models.TextField(default=None, null=True, blank=True)
    stock = models.IntegerField(default=1)
    slug = models.SlugField(max_length=255, unique=True, blank=True) 
    tags = TaggableManager(blank=True)
    related_books = models.ManyToManyField('self', blank=True)
    users_wishlist = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="user_wishlist", blank=True)


    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Book, self).save(*args, **kwargs)

    @property
    def cover_url(self):
        if self.cover and hasattr(self.cover, 'url'):
            return self.cover.url

    @property
    def back_url(self):
        if self.back and hasattr(self.back, 'url'):
            return self.back.url

    def __str__(self):
        return self.title

    def get_category_name(self):
        return self.category.first().name
    
    def get_category_slug(self):
        return self.category.first().slug

    
    @classmethod
    # TODO: move outside
    def get_book_all_categories_count(cls):
        counts = dict()
        for cat in Category.objects.all():
            counts[cat] = cls.objects.filter(category=cat).count()
        return counts
    
    def get_related_books(self):
        return self.related_books.all()

    def get_price(self) -> str: # TODO: annotate the other methods
        return f"{self.discount_price:,.2f}" if self.discount_price else f"{self.price:,.2f}"
    
    def get_original_price(self) -> str:
        return f"{self.price:,.2f}"
    
    def get_absolute_url(self):
        return reverse("djbooks:book_detail", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("djbooks:add-to-cart", kwargs={"slug": self.slug})

    def get_add_to_wishlist(self):
        return reverse("djbooks:add-to-wishlist", kwargs={"slug": self.slug})

class ExtraImage(models.Model):
    book = models.ForeignKey(Book, default=None, on_delete=models.CASCADE)
    image = models.FileField(upload_to=upload_with_uuid(path=PATH))
    cover = models.BooleanField(default=False)
    back = models.BooleanField(default=False)
 
    def __str__(self):
        return self.book.title

    def save(self, *args, **kwargs):
        if self.cover:
            self.book.cover = self.image
            self.book.save()
        if self.back:
            self.book.back = self.image
            self.book.save()
        super(ExtraImage, self).save(*args, **kwargs)

class OrderBook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        if self.item.discount_price:
            return self.quantity * self.item.discount_price
        return self.quantity * self.item.price

    def get_items_final_price(self) -> str: # TODO: annotate the other methods
        return f"{self.get_total_item_price():,.2f}"


class Order(models.Model):  
    class ShippingOption(models.TextChoices):
        dhl = 'dhl', _('DHL')
        sepomex = 'sepomex', _('SEPOMEX')
        local_pickup = 'local_pickup', _('Entrega directa')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    items = models.ManyToManyField(OrderBook)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    paid = models.BooleanField(default=False)
    ordered = models.BooleanField(default=False)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    shipping_option = models.CharField(max_length=12, choices=ShippingOption.choices, null=True)
    shipping_address = models.ForeignKey(
        "Address",
        related_name="shipping_address",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    """
    1. Book added to cart
    2. Adding a billing address (Failed checkout)
    3. Payment (Preprocessing, processing, packaging etc.)
    4. Being delivered
    5. Received
    6. Refunds
    """

    def __str__(self):
        return f"Compra de {self.user.username}"

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_item_price()
        return total

    def get_preference(self):
        sdk = SDK(str(settings.MERCADO_PAGO_PRIVATE_KEY))
        
        if not self.paid:
            preference_data = {
                "items": [

                ],
                "auto_return": "approved",
                "back_urls": {
                    "success": "http://localhost:8000/payments/approved",
                    "failure": "http://localhost:8000/payments/failure",
                    "pending": "http://localhost:8000/payments/pending"
                }

            }
            # TODO: FIX PICTURE 
            for order_item in self.items.all():
                preference_data['items'].append({
                    "id": order_item.item.id,
                    "title": order_item.item.title,
                    "description": order_item.item.description,
                    "quantity": order_item.quantity,
                    #"picture_url": "https://cdn.shopify.com/s/files/1/1830/5085/products/VE0007_BCAA_Capsule_90ct_2048x2048.png?v=1494855182",
                    "unit_price": float(order_item.get_total_item_price())
                })
            # preference_data['total_amount'] = str(self.get_total())
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response["response"]
            # import json
            # print("Data: ", json.dumps(preference, indent=4))
            #print("PREFERENCE: ", json.dumps(preference_response, indent=4))
            print(f"ID: {preference.get('id')}")
            return preference.get("id")


ADDRESS_CHOICES = (
    ("B", "Billing"),
    ("S", "Shipping"),
)

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    names = models.CharField(max_length=20)
    last_names = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=20)
    street_address = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100)
    shipping_city = models.CharField(max_length=100)
    shipping_zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.street_address

    class Meta:
        verbose_name_plural = "Addresses"


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        paypal = 'PP', _('Paypal')
        mercado_pago = 'MP', _('Mercado Pago')
    charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True
    )
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=2, choices=PaymentMethod.choices)

    def __str__(self):
        return f"Pago de {self.user.username} usando {self.payment_method.label}"