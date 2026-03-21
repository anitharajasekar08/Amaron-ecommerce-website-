from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from datetime import datetime
from .models import Address
from .models import Order
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
import json
from .models import Product, Cart, CartItem, Order, OrderItem, Wishlist, Address
from .forms import RegisterForm
from django.shortcuts import render

# ------------------ CART UTILITY ------------------

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()

    session_id = request.session.session_key
    cart, created = Cart.objects.get_or_create(session_id=session_id)
    return cart


# ------------------ SHOP VIEWS ------------------

def index_view(request):
    products = Product.objects.order_by('-id')[:8]
    return render(request, 'shop/index.html', {'products': products})


def shop_view(request):
    product_list = Product.objects.all().order_by('-id')
    paginator = Paginator(product_list, 8)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    return render(request, 'shop/shop.html', {'products': products})


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'shop/product_detail.html', {'product': product})


def service(request):
    return render(request, 'shop/service.html')


def contact(request):
    return render(request, 'shop/contact.html')


def about(request):
    return render(request, 'shop/about.html')

def success(request):
    return render(request, "shop/success.html")
# ------------------ USER AUTH ------------------

def register(request):
    next_url = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(next_url or "index")
    else:
        form = RegisterForm()
    return render(request, "shop/register.html", {"form": form, "next": next_url})


def logout_view(request):
    logout(request)
    return redirect("index")


# ------------------ CART VIEWS ------------------

@login_required
def add_to_cart(request, product_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        qty = int(data.get("qty", 1))
    except:
        qty = 1

    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += qty
    else:
        cart_item.quantity = qty

    if cart_item.quantity > product.stock:
        cart_item.quantity = product.stock

    cart_item.save()
    return JsonResponse({"status": "success"})


def get_cart(request):
    cart = get_or_create_cart(request)
    cart_items = CartItem.objects.filter(cart=cart)

    items = []
    total = 0
    total_qty = 0

    for item in cart_items:
        subtotal = item.product.price * item.quantity
        total += subtotal
        total_qty += item.quantity
        items.append({
            "id": item.id,
            "name": item.product.name,
            "image": item.product.image.url if item.product.image else "",
            "price": float(item.product.price),
            "qty": item.quantity,
            "subtotal": float(subtotal)
        })

    return JsonResponse({
        "items": items,
        "total": float(total),
        "total_qty": total_qty
    })

@login_required
def update_cart(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cart_id = data.get("cart_id")
            change = int(data.get("change", 0))
        except:
            return JsonResponse({"status": "error", "message": "Invalid data"}, status=400)

        cart_item = get_object_or_404(CartItem, id=cart_id, cart__user=request.user)

        new_quantity = cart_item.quantity + change

        # Prevent going below 1
        if new_quantity < 1:
            return JsonResponse({"status": "error", "message": "Minimum quantity is 1"})

        # Prevent exceeding stock
        if new_quantity > cart_item.product.stock:
            return JsonResponse({"status": "error", "message": "Stock limit reached"})

        cart_item.quantity = new_quantity
        cart_item.save()

        # Return new cart totals for frontend update
        cart_items = CartItem.objects.filter(cart=cart_item.cart)
        total = sum(item.product.price * item.quantity for item in cart_items)
        total_qty = sum(item.quantity for item in cart_items)

        return JsonResponse({
            "status": "success",
            "qty": cart_item.quantity,
            "total": float(total),
            "total_qty": total_qty
        })
def remove_cart(request):
    if request.method == "POST":
        cart_id = request.POST.get("cart_id")
        CartItem.objects.filter(id=cart_id).delete()
        return JsonResponse({"status": "success"})


# ------------------ CHECKOUT ------------------

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("shop")

    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == "POST":
        if "update_address" in request.POST:
          address_id = request.POST.get("address_id")
          address = Address.objects.get(id=address_id, user=request.user)

          address.full_name = request.POST.get("full_name")
          address.phone = request.POST.get("phone")
          address.address_line = request.POST.get("address_line")
          address.city = request.POST.get("city")
          address.state = request.POST.get("state")
          address.pincode = request.POST.get("pincode")
          address.save()

          return redirect("checkout")
        if "new_address" in request.POST:
            Address.objects.create(
                user=request.user,
                full_name=request.POST.get("full_name"),
                phone=request.POST.get("phone"),
                address_line=request.POST.get("address_line"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                pincode=request.POST.get("pincode"),
            )
            messages.success(request, "Address added successfully.")
            return redirect("checkout")

        if "place_order" in request.POST:
            address_id = request.POST.get("address_id")
            payment_method = request.POST.get("payment_method")
            upi_txn_id = request.POST.get("upi_transaction_id")

            if not address_id:
                messages.error(request, "Please select an address.")
                return redirect("checkout")

            selected_address = get_object_or_404(Address, id=address_id, user=request.user)

            payment_status = "Unpaid" if payment_method == "COD" else "pending"

            order = Order.objects.create(
                user=request.user,
                address=selected_address,
                total_amount=total_amount,
                payment_method=payment_method,
                payment_status=payment_status,
                upi_transaction_id=upi_txn_id if payment_method == "UPI" else None
            )

            for item in cart_items:
                product = item.product
                if product.stock < item.quantity:
                    messages.error(request, "Not enough stock available")
                    return redirect("checkout")
                product.stock -= item.quantity
                product.save()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price
                )

            cart_items.delete()
            return redirect("order_success", order_id=order.id)

    addresses = Address.objects.filter(user=request.user)
    return render(request, "shop/checkout.html", {
        "cart_items": cart_items,
        "total_amount": total_amount,
        "addresses": addresses
    })


# ------------------ ORDER HISTORY ------------------

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "shop/my_orders.html", {"orders": orders})

@login_required(login_url="login")
def order_success(request, order_id):
    order = Order.objects.filter(id=order_id, user=request.user).first()
    if not order:
        return redirect("index")
    return render(request, "shop/order_success.html", {"order": order})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == "Pending":
        order.status = "Cancelled"
        order.save()

        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

    return redirect("my_orders")

@login_required
def download_invoice(request, order_id):
    order = Order.objects.get(id=order_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order.id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading1"]
    bold = styles["Heading2"]

    # =========================
    # COMPANY HEADER
    # =========================
    elements.append(Paragraph("<b>A R ANITHA AGENCIES</b>", heading))
    elements.append(Paragraph("Email: anitharajasekar083@gmail.com", normal))
    elements.append(Paragraph("Phone: +91 9443962286", normal))
    elements.append(Spacer(1, 0.3 * inch))

    # =========================
    # INVOICE INFO
    # =========================
    elements.append(Paragraph(f"<b>Invoice No:</b> {order.id}", normal))
    elements.append(Paragraph(f"<b>Date:</b> {order.created_at.strftime('%d-%m-%Y')}", normal))
    elements.append(Paragraph(f"<b>Payment Method:</b> {order.payment_method}", normal))
    elements.append(Spacer(1, 0.3 * inch))

    # =========================
    # BILL TO
    # =========================
    elements.append(Paragraph("<b>Bill To:</b>", bold))
    elements.append(Paragraph(order.address.full_name, normal))
    elements.append(Paragraph(order.address.phone, normal))
    elements.append(Paragraph(order.address.address_line, normal))
    elements.append(
        Paragraph(
            f"{order.address.city}, {order.address.state} - {order.address.pincode}",
            normal
        )
    )
    elements.append(Spacer(1, 0.4 * inch))

    # =========================
    # TABLE DATA
    # =========================
    data = []

    # Header Row
    data.append([
        Paragraph("<b>Product</b>", normal),
        Paragraph("<b>Qty</b>", normal),
        Paragraph("<b>Price (₹)</b>", normal),
        Paragraph("<b>Total (₹)</b>", normal),
    ])

    total_amount = 0

    # Product Rows
    for item in order.items.all():
        total = item.quantity * item.price
        total_amount += total

        data.append([
            Paragraph(item.product.name, normal),
            Paragraph(str(item.quantity), normal),
            Paragraph(f"{item.price:.2f}", normal),
            Paragraph(f"{total:.2f}", normal),
        ])

    # Grand Total Row
    data.append([
        "",
        "",
        Paragraph("<b>Grand Total</b>", normal),
        Paragraph(f"<b>₹ {total_amount:.2f}</b>", normal),
    ])

    # =========================
    # CREATE TABLE
    # =========================
    table = Table(
        data,
        colWidths=[3 * inch, 0.8 * inch, 1 * inch, 1.2 * inch]
    )

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    # =========================
    # FOOTER
    # =========================
    elements.append(Paragraph("<b>Thank you for shopping with us!</b>", bold))

    doc.build(elements)

    return response
# ------------------ WISHLIST ------------------

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('wishlist')


@login_required
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {'items': items})

def edit_address(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)

    if request.method == "POST":
        address.full_name = request.POST.get('full_name')
        address.phone = request.POST.get('phone')
        address.address_line = request.POST.get('address_line')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.pincode = request.POST.get('pincode')
        address.save()

        return redirect('checkout')   # after update go back to checkout

    return render(request, 'edit_address.html', {'address': address})