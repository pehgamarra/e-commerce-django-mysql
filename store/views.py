from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
import matplotlib
from .forms import ShippingAddressForm
from .models import Category, Product, Order
import matplotlib.pyplot as plt
import io
import base64


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
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    context = {
        'product': product,
        'user_is_authenticated': request.user.is_authenticated,
    }
    return render(request, 'store/product_detail.html', context)


#Cart view
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    product_id_str = str(product_id)

    if product_id_str not in cart:
        cart[product_id_str] = {
            'quantity': quantity, 
            'price': str(product.price),
        }
    else:
        cart[product_id_str]['quantity'] += quantity

    request.session['cart'] = cart
    return redirect('cart_detail')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[product_id]

    request.session['cart'] = cart
    return redirect('cart_detail')

def cart_detail(request):
    cart = request.session.get('cart', {})
    
    if not cart:
        return render(request, 'store/cart_detail.html', {'message': 'Your cart is empty.'})

    cart_items = []
    total = 0
    
    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        total_price = float(item['price']) * item['quantity']
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'total_price': round(total_price, 2)
        })
        total += total_price

    context = {
        'cart_items': cart_items,
        'cart_total': round(total, 2),
    }
    
    return render(request, 'store/cart_detail.html', context)


#checkout & shipping
def calculate_shipping(total_amount):
    shipping_rate = 0.05
    return total_amount * shipping_rate


@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    
    if not cart:
        return render(request, 'store/checkout.html', {'message': 'Your cart is empty.'})

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        cvv = request.POST.get('cvv')
        
        if form.is_valid():
            address = form.cleaned_data

            total_price = sum(float(item['price']) * item['quantity'] for item in cart.values())
            shipping_cost = calculate_shipping(total_price)
            grand_total = round(total_price + shipping_cost, 2)

            order = Order.objects.create(
                user=request.user,
                total_price=round(total_price, 2),
                shipping_cost=shipping_cost,
                grand_total=grand_total,
                address=f"{address['address_line1']}, {address.get('address_line2', '')}, {address['city']}, {address['state']}, {address['postal_code']}, {address['country']}",
                
            )

            request.session['cart'] = {}

            return render(request, 'store/checkout_complete.html', {
                'order': order,
                'address': address,
                'card_number': card_number,
                'expiry_date': expiry_date,
                'cvv': cvv
            })
    else:
        form = ShippingAddressForm()
    
    total_price = sum(float(item['price']) * item['quantity'] for item in cart.values())
    shipping_cost = round(calculate_shipping(total_price), 2)
    grand_total = round(total_price + shipping_cost, 2)
    
    context = {
        'cart': cart,
        'total_price': round(total_price, 2),
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
        'form': form
    }
    
    return render(request, 'store/checkout.html', context)

def checkout_complete(request):
    return render(request, 'store/checkout_complete.html')

#remove & edit cart:

@require_POST
def remove_all_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]

    request.session['cart'] = cart
    return redirect('cart_detail')

@require_POST
def update_cart_item(request, product_id):
    cart = request.session.get('cart', {})
    quantity = int(request.POST.get('quantity', 1))
    
    if str(product_id) in cart:
        if quantity > 0:
            cart[str(product_id)]['quantity'] = quantity
        else:
            del cart[str(product_id)]
    else:
        return redirect('cart_detail')

    request.session['cart'] = cart
    return redirect('cart_detail')

#staff methods

@staff_member_required
def admin_order_list(request):
    orders = Order.objects.all()
    return render(request, 'admin_custom/orders.html', {'orders': orders})

@staff_member_required
def admin_dashboard(request):
    matplotlib.use('Agg')
    status_filter = request.GET.get('status')
    orders = Order.objects.all()

    if status_filter:
        orders = orders.filter(status=status_filter)

        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        shipped_orders = Order.objects.filter(status='shipped').count()
        delivered_orders = Order.objects.filter(status='delivered').count()

        total_products = Product.objects.count()
        out_of_stock_products = Product.objects.filter(stock=0).count()

        orders = Order.objects.all()
        total_sales = {}
        
        for order in orders:
            month = order.created_at.month  
            total_sales[month] = total_sales.get(month, 0) + order.grand_total

        plt.figure(figsize=(10, 5))
        plt.plot(total_sales.keys(), total_sales.values(), marker='o')
        plt.title('Total Sales / Month')
        plt.xlabel('Months')
        plt.ylabel('Total Sales')
        plt.xticks(list(total_sales.keys())) 
        plt.grid()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        graphic = base64.b64encode(image_png)
        graphic = graphic.decode('utf-8') 

        context = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'shipped_orders': shipped_orders,
            'delivered_orders': delivered_orders,
            'total_products': total_products,
            'out_of_stock_products': out_of_stock_products,
            'orders': orders,
            'status_filter': status_filter,
            'graphic': graphic,
        }
        
    return render(request, 'store/admin_dashboard.html', context)

