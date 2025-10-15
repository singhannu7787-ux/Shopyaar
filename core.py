# core.py — combines settings, models, views, urls in one file
import os
from django.conf import settings
from django.urls import path
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.wsgi import get_wsgi_application
from django.apps import apps

# -------------------- DJANGO CONFIG --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

settings.configure(
    DEBUG=True,
    SECRET_KEY='shopyaar_secret_key',
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=['*'],
    INSTALLED_APPS=[
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        __name__,
    ],
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR],
        'APP_DIRS': True,
    }],
    STATIC_URL='/static/',
    STATICFILES_DIRS=[os.path.join(BASE_DIR, "static")],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': os.path.join(BASE_DIR, 'db.sqlite3')}},
)

apps.populate(settings.INSTALLED_APPS)

# -------------------- MODELS --------------------
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    def total_price(self):
        return self.product.price * self.quantity

# -------------------- VIEWS --------------------
def index(request):
    products = Product.objects.all()
    return render(request, "templates.html", {"page": "home", "products": products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "templates.html", {"page": "product", "product": product})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order, created = Order.objects.get_or_create(user=request.user, completed=False)
    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
    order_item.quantity += 1
    order_item.save()
    return redirect("cart")

@login_required
def cart(request):
    order, created = Order.objects.get_or_create(user=request.user, completed=False)
    return render(request, "templates.html", {"page": "cart", "order": order})

@login_required
def checkout(request):
    order = Order.objects.get(user=request.user, completed=False)
    order.completed = True
    order.save()
    return render(request, "templates.html", {"page": "checkout"})

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("index")
    else:
        form = UserCreationForm()
    return render(request, "templates.html", {"page": "auth", "form": form})

# -------------------- URLS --------------------
urlpatterns = [
    path('', index, name="index"),
    path('product/<int:pk>/', product_detail, name="product_detail"),
    path('add/<int:pk>/', add_to_cart, name="add_to_cart"),
    path('cart/', cart, name="cart"),
    path('checkout/', checkout, name="checkout"),
    path('register/', register_view, name="register"),
]

application = get_wsgi_application()