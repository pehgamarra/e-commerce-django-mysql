from django.shortcuts import get_object_or_404, render, redirect
from .models import Category, Product, Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required


def home_view(request):
    return render(request, 'store/home.html')

#REGISTER / LOGOUT
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


#PRODUCTS

def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    category = request.GET.get('category')
    if category:
        products = products.filter(category__id=category)

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    context = {
        'products': products,
        'categories': categories,
        'user_is_authenticated': request.user.is_authenticated,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    context = {
        'product': product,
        'user_is_authenticated': request.user.is_authenticated,
    }
    return render(request, 'store/product_detail.html', context)

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
