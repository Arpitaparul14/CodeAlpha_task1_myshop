from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Order, OrderItem

def get_cart_count(request):
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, status='pending').first()
        if order:
            return order.items.count()
    return 0

def product_list(request):
    q = request.GET.get('q', '')
    if q:
        products = Product.objects.filter(name__icontains=q)
    else:
        products = Product.objects.all()
    return render(request, 'store/product_list.html', {
        'products': products,
        'cart_count': get_cart_count(request)
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {
        'product': product,
        'cart_count': get_cart_count(request)
    })

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form, 'cart_count': get_cart_count(request)})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('product_list')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form, 'cart_count': get_cart_count(request)})

def logout_view(request):
    logout(request)
    return redirect('product_list')

@login_required
def cart_view(request):
    order, created = Order.objects.get_or_create(user=request.user, status='pending')
    items = order.items.all()
    total = sum(item.price * item.quantity for item in items)
    return render(request, 'store/cart.html', {
        'items': items,
        'total': total,
        'cart_count': get_cart_count(request)
    })

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order, created = Order.objects.get_or_create(user=request.user, status='pending')
    item, created = OrderItem.objects.get_or_create(order=order, product=product,
                                                     defaults={'price': product.price})
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'{product.name} added to cart!')
    return redirect('cart')

@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(OrderItem, pk=pk)
    item.delete()
    return redirect('cart')

@login_required
def checkout(request):
    order = Order.objects.filter(user=request.user, status='pending').first()
    if not order:
        return redirect('cart')
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')
        order.status = 'confirmed'
        total = sum(item.price * item.quantity for item in order.items.all())
        order.total = total
        order.save()
        messages.success(request, f'✅ Order placed! Delivering to {full_name}, {address}, {city} - {pincode}. Phone: {phone}')
        return redirect('order_history')
    items = order.items.all()
    total = sum(item.price * item.quantity for item in items)
    return render(request, 'store/checkout.html', {
        'order': order,
        'items': items,
        'total': total,
        'cart_count': get_cart_count(request)
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).exclude(status='pending').order_by('-created_at')
    return render(request, 'store/order_history.html', {
        'orders': orders,
        'cart_count': get_cart_count(request)
    })
@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status == 'confirmed':
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order #{order.id} has been cancelled.')
    return redirect('order_history')