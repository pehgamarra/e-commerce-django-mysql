from django.shortcuts import get_object_or_404, render, redirect
from .models import Product, Cart, CartItem
from django.contrib.auth.decorators import login_required


def home_view(request):
    return render(request, 'store/home.html')

def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'store/product_detail.html', {'product': product})

@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
    item.save()

    return redirect('product_list')

@login_required
def view_cart(request):
    cart = Cart.objects.get(user=request.user)
    items = CartItem.objects.filter(cart=cart)
    return render(request, 'store/cart.html', {'items': items})
