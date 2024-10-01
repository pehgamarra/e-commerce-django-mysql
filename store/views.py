
from datetime import datetime
import matplotlib
import openpyxl
import matplotlib.pyplot as plt
import io
import base64

from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse

from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Avg


from .forms import ShippingAddressForm, ReviewForm, CustomAuthenticationForm, CustomUserCreationForm
from .models import Category, Product, Order, Review, OrderItem, CartItem


def home_view(request):
    return render(request, 'store/home.html')

#REGISTER / LOGOUT
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! You are now logged in.')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    authentication_form = CustomAuthenticationForm
    if request.method == 'POST':
        form = authentication_form(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login realizado com sucesso!')
                return redirect('home')
            else:
                messages.error(request, 'Nome de usuário ou senha incorretos.')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'store/login.html', {'form': form})


@login_required(login_url='login')
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

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)

    all_reviews = product.reviews.all()
    if all_reviews.exists():
        average_rating = all_reviews.aggregate(Avg('rating'))['rating__avg']
    else:
        average_rating = 0

    stars = range(1, 6)

    filter_stars = request.GET.get('stars')
    if filter_stars:
        reviews = all_reviews.filter(rating=filter_stars)
    else:
        reviews = all_reviews

    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'stars': stars,
        'form': form,
        'average_rating': round(average_rating, 1),
        'total_reviews': all_reviews.count(),
        'filter_stars': filter_stars,
    })

# Add product to cart
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    # Check if the quantity is greater than available stock
    if quantity > product.stock:
        messages.error(request, "Not enough stock available")
        return redirect('product_detail', product_id=product_id)

    cart = request.session.get('cart', {})
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

# View cart details
def cart_detail(request):
    cart = request.session.get('cart', {})

    if not cart:
        return render(request, 'store/cart_detail.html', {'message': 'Your cart is empty.'})

    cart_items = []
    total = 0

    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)

        # Ensure quantity doesn't exceed stock
        quantity = min(item['quantity'], product.stock)

        # Calculate total price using the existing quantity
        total_price = quantity * product.price 
        
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': round(total_price, 2)
        })
        total += total_price

    context = {
        'cart_items': cart_items,
        'cart_total': round(total, 2),
    }
    
    return render(request, 'store/cart_detail.html', context)


#remove & edit cart:

@require_POST
def remove_all_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]
    
    request.session['cart'] = cart

    try:
        cart_item = CartItem.objects.get(product_id=product_id, user=request.user)
        cart_item.delete()
        return redirect('cart_detail')
    except CartItem.DoesNotExist:
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
        
        request.session['cart'] = cart
    else:
        cart_item = get_object_or_404(CartItem, id=product_id, user=request.user)
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()  # Remove from database if quantity is zero

    return redirect('cart_detail')

#checkout & shipping
def calculate_shipping(total_amount):
    shipping_rate = 0.05
    return round(total_amount * shipping_rate, 2)


# Checkout process
@login_required(login_url='login')
def checkout(request):
    cart = request.session.get('cart', {})
    
    if not cart:
        return render(request, 'store/checkout.html', {'message': 'Your cart is empty.'})

    total_price = 0
    shipping_cost = 0
    grand_total = 0

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        cvv = request.POST.get('cvv')
        
        if form.is_valid():
            address = form.cleaned_data

            # Calculate the total price for all products in the cart
            order_items = []  # To store the order items
            for product_id, item in cart.items():
                product = get_object_or_404(Product, id=product_id)

                # Check if stock is available before checkout
                quantity = min(item['quantity'], product.stock)

                item_price = float(item['price']) * quantity
                total_price += item_price

                # Prepare the order items data
                order_items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': float(item['price'])
                })

                # Update stock after purchase
                product.stock -= quantity
                product.save()

            shipping_cost = calculate_shipping(total_price)
            grand_total = round(total_price + shipping_cost, 2)

            # Create order record
            order = Order.objects.create(
                user=request.user,
                total_price=round(total_price, 2),
                shipping_cost=shipping_cost,
                grand_total=grand_total,
                address=f"{address['address_line1']}, {address.get('address_line2', '')}, {address['city']}, {address['state']}, {address['postal_code']}, {address['country']}",
            )

            # Create OrderItem records for each product in the cart
            for item in order_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['price'],
                )

            # Clear the cart after purchase
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

        # Calculate the total price for all products in the cart if it's a GET request
        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id)
            quantity = min(item['quantity'], product.stock)
            item_price = float(item['price']) * quantity
            total_price += item_price

        shipping_cost = calculate_shipping(total_price)
        grand_total = round(total_price + shipping_cost, 2)

    return render(request, 'store/checkout.html', {
        'form': form,
        'total_price': round(total_price, 2),
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    })



def checkout_complete(request):
    return render(request, 'store/checkout_complete.html')


#staff methods

@staff_member_required
def admin_order_list(request):
    orders = Order.objects.all()
    return render(request, 'admin_custom/orders.html', {'orders': orders})


@staff_member_required
def admin_dashboard(request):
    matplotlib.use('Agg')

    current_year = datetime.now().year
    years = range(2020, current_year + 5)

    #Requisition parameters
    month = request.GET.get('month')
    year = request.GET.get('year')
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all()

      # Apply status filter if present
    if year and year != 'None':
        try:
            year = int(year)
            orders = orders.filter(created_at__year=year)
        except ValueError:
            year = None

    if month and month != 'None':
        try:
            month = int(month)
            orders = orders.filter(created_at__month=month)
        except ValueError:
            month = None

    if status_filter:
        orders = orders.filter(status=status_filter)

    # ordernation filter
    order_by = request.GET.get('order_by', 'id')
    sort_order = request.GET.get('sort_order', 'asc') 

    if sort_order == 'desc':
        order_by = f'-{order_by}'

    valid_order_fields = ['id', 'total_price', 'user', 'address', 'created_at', 'status']
    if order_by.lstrip('-') in valid_order_fields:
        orders = orders.order_by(order_by)
    else:
        orders = orders.order_by('id') 
        

    # Pagination
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_orders = orders.count()
    total_sales = {}


    # Calculate total sales per month
    for order in orders:
        order_month = order.created_at.month
        total_sales[order_month] = total_sales.get(order_month, 0) + order.grand_total

    # Generate graphic if necessary
    graphic = None
    if not month and year:  # Generate graphic only if a year is selected without a month
        if total_sales:
            plt.figure(figsize=(10, 5))
            plt.bar(list(total_sales.keys()), list(total_sales.values()), color='blue')
            plt.title(f'Total Sales for Year: {year}')
            plt.xlabel('Months')
            plt.ylabel('Total Sales')
            plt.xticks(list(total_sales.keys())) 
            plt.grid()

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            graphic = base64.b64encode(image_png).decode('utf-8')

    # Pass context to the template
    context = {
        'total_orders': total_orders,
        'orders': page_obj,
        'month': month,
        'year': year,
        'graphic': graphic,
        'years': years,
        'order_by': order_by,
        'sort_order': 'desc' if sort_order == 'asc' else 'asc',
        'status_filter': status_filter,
    }
    return render(request, 'store/admin_dashboard.html', context)

@staff_member_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()
        messages.success(request, 'Order status updated successfully.')

    # Capture the original query parameters
    referrer = request.META.get('HTTP_REFERER', '')
    
    # Redirect back to the same page with the original query parameters
    return HttpResponseRedirect(referrer)


@staff_member_required
def download_report(request):
    # Use Agg backend for matplotlib to avoid display issues
    matplotlib.use('Agg')
    month = request.GET.get('month')  # Get the selected month from the request
    year = request.GET.get('year')  # Get the selected year from the request
    
    # Retrieve all orders initially
    orders = Order.objects.all()
    # Filter orders by year and month if provided
    if month and year:
        month = int(month)  # Convert month to integer
        year = int(year)  # Convert year to integer
        orders = orders.filter(created_at__year=year, created_at__month=month)
    
    # Create a new Excel workbook and select the active worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Report"  # Set the title of the worksheet

    # Append header row to the worksheet
    ws.append(['ID', 'Total Price', 'Username', 'Ship Address', 'Status'])

    # Add each order's details to the worksheet
    for order in orders:
        ws.append([order.id, order.total_price, order.user.username, order.address, order.status])

    # Create an HTTP response with Excel file content type
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"sales_report_{year}_{month}.xlsx"  # Filename for the Excel file
    response['Content-Disposition'] = f'attachment; filename={filename}'  # Specify attachment filename

    wb.save(response)  # Save the workbook to the response
    return response  # Return the response to the client


@staff_member_required
def export_sales_report(request, report_type):
    # Create a new Excel workbook
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Sales Report'  # Set the title of the worksheet

    # Append header row to the worksheet
    sheet.append(['ID', 'Total Price', 'Username', 'Ship Address', 'Status'])

    # Get year and month from the request, defaulting year to current year
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month')

    # Filter orders based on the report type (annual or monthly)
    if report_type == 'annual':
        orders = Order.objects.filter(created_at__year=year)
    elif report_type == 'monthly' and month:
        orders = Order.objects.filter(created_at__year=year, created_at__month=month)
    else:
        orders = Order.objects.filter(created_at__year=year)  # Default to yearly if no month

    # Add each order's details to the worksheet
    for order in orders:
        sheet.append([
            order.id,
            order.total_price,
            order.user.username,
            order.address,
            order.status
        ])

    # Create an HTTP response with Excel file content type
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # Set the filename based on report type
    if report_type == 'annual':
        response['Content-Disposition'] = f'attachment; filename=annual_sales_report_{year}.xlsx'
    else:
        response['Content-Disposition'] = f'attachment; filename=monthly_sales_report_{year}_{month}.xlsx'

    workbook.save(response)  # Save the workbook to the response
    return response  # Return the response to the client


