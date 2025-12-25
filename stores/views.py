from decimal import Decimal

# --- Django Imports ---
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.db.models import Q

# --- Project Imports ---
from .models import Product, Category, Order, OrderItem
from .forms import ProductForm, CategoryForm
from cart.models import Cart, CartItem

# ==========================================
# 🛒 ส่วนของลูกค้า (Customer Views)
# ==========================================

# 1. หน้าแสดงสินค้าทั้งหมด
class ProductListView(ListView):
    model = Product
    template_name = 'stores/product_list.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        # เพิ่มข้อมูลหมวดหมู่ทั้งหมดไปที่ template เพื่อเอาไปวนลูปสร้างแท็บ
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all() 
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 1. กรองตามหมวดหมู่ (ถ้ามีการกดเลือกแท็บ)
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # 2. กรองตามคำค้นหา (Search)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query)
            )
            
        return queryset

# 1.1 หน้าแสดงรายละเอียดสินค้า
class ProductDetailView(DetailView):
    model = Product
    template_name = 'stores/product_detail.html'
    context_object_name = 'product'


# 2. ฟังก์ชันสั่งซื้อสินค้าจากตะกร้า (Checkout Cart)
@login_required(login_url='login')
def cart_checkout(request):
    # 2.1 ดึงข้อมูลตะกร้า
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
    except Cart.DoesNotExist:
        cart = None
        cart_items = []

    if not cart_items:
        return redirect('product-list') # หรือ 'home'

    # 2.2 คำนวณราคารวมสินค้า (Subtotal)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        shipping_method = request.POST.get('shipping_method')
        payment_slip = request.FILES.get('payment_slip')
        
        # คำนวณค่าส่ง
        shipping_cost = 0
        if shipping_method == 'standard':
            shipping_cost = 50
        elif shipping_method == 'express':
            shipping_cost = 100
        
        grand_total = total_price + shipping_cost

        # ใช้ transaction เพื่อความปลอดภัย (Create Order + Create Items + Cut Stock)
        with transaction.atomic():
            # 2.3 สร้าง Order (หัวบิล)
            new_order = Order.objects.create(
                customer=request.user,         # ⚠️ เช็ค models.py ว่าใช้ 'user' หรือ 'customer'
                total_price=grand_total,
                shipping_cost=shipping_cost,
                shipping_method=shipping_method,
                payment_slip=payment_slip,
                status='pending'
            )

            # 2.4 ย้ายสินค้าจาก Cart -> OrderItem
            for item in cart_items:
                OrderItem.objects.create(
                    order=new_order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                
                # ตัดสต็อกสินค้าทันที
                if item.product.stock >= item.quantity:
                    item.product.stock -= item.quantity
                    item.product.save()
                else:
                    # กรณีของหมดกลางคัน (Optional: อาจจะ raise error หรือข้ามไป)
                    pass

            # 2.5 ล้างตะกร้า
            cart_items.delete()
            # cart.delete() # ถ้าต้องการลบตัวตะกร้าด้วย

        return redirect('store_order_success')

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'stores/cart_checkout.html', context)

# 3. คลาสสั่งซื้อสินค้าชิ้นเดียว (Buy Now)
@method_decorator(login_required, name='dispatch')
class ProductCheckoutView(View):
    template_name = 'stores/checkout.html'

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return render(request, self.template_name, {'product': product})

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
            
        shipping_method = request.POST.get('shipping_method', 'pickup')
        payment_method = request.POST.get('payment_method', 'transfer')
        payment_slip = request.FILES.get('payment_slip')

        # Validate Stock
        if quantity < 1: quantity = 1
        if quantity > product.stock:
            messages.error(request, f"สินค้าเหลือเพียง {product.stock} ชิ้น")
            return redirect('product_checkout', pk=pk)

        # คำนวณราคา
        shipping_cost = Decimal('0.00')
        if shipping_method == 'standard': shipping_cost = Decimal('50.00')
        elif shipping_method == 'express': shipping_cost = Decimal('100.00')

        unit_price = product.price
        total_price = (unit_price * quantity) + shipping_cost

        # บันทึกลง Database
        with transaction.atomic():
            # สร้าง Order
            order = Order.objects.create(
                customer=request.user,      # ⚠️ เช็ค models.py ว่าใช้ 'user' หรือ 'customer'
                shipping_method=shipping_method,
                shipping_cost=shipping_cost,
                total_price=total_price,
                payment_method=payment_method,
                payment_slip=payment_slip,
                status='pending'
            )

            # สร้าง OrderItem
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=unit_price
            )

            # ตัด Stock
            product.stock -= quantity
            product.save()

        messages.success(request, "สั่งซื้อสำเร็จ! กรุณารอการตรวจสอบ")
        return redirect('store_order_success')

# 4. หน้าแสดงผลเมื่อสั่งซื้อสำเร็จ
@login_required
def order_success(request):
    # ดึงออเดอร์ล่าสุดของ User นี้
    latest_order = Order.objects.filter(customer=request.user).order_by('-created_at').first()
    # ⚠️ ถ้า models.py ใช้ field 'customer' ให้เปลี่ยนเป็น .filter(customer=request.user)
    
    return render(request, 'stores/order_success.html', {'order': latest_order})


# ==========================================
# 🔧 ส่วนของผู้ดูแลระบบ (Admin Views)
# ==========================================

# Mixin ตรวจสอบสิทธิ์ Admin (ใช้ร่วมกันทุก View ของ Admin)
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

# --- จัดการสินค้า (Product) ---
class ProductManageListView(AdminRequiredMixin, ListView):
    model = Product
    template_name = 'stores/admin/product_manage_list.html'
    context_object_name = 'products'

class ProductCreateView(AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'stores/admin/product_form.html'
    success_url = reverse_lazy('product-manage-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'stores/admin/product_form.html'
    success_url = reverse_lazy('product-manage-list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('product-manage-list')

# --- จัดการหมวดหมู่ (Category) ---
class CategoryManageListView(AdminRequiredMixin, ListView):
    model = Category
    template_name = 'stores/admin/category_manage_list.html'
    context_object_name = 'categories'

class CategoryCreateView(AdminRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'stores/admin/category_form.html'
    success_url = reverse_lazy('product-manage-list') 

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class CategoryUpdateView(AdminRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'stores/admin/category_form.html'
    success_url = reverse_lazy('category-manage-list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class CategoryDeleteView(AdminRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('category-manage-list')

# --- จัดการคำสั่งซื้อ (Order) ---
class OrderManageListView(AdminRequiredMixin, ListView):
    model = Order
    template_name = 'stores/admin/order_list.html'
    context_object_name = 'orders'
    ordering = ['-created_at']

# ฟังก์ชันอัปเดตสถานะ (Admin)
@require_POST
@login_required
def admin_update_order_status(request, pk):
    if not request.user.is_staff:
        return redirect('product-list')

    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')

    valid_status = dict(Order.STATUS_CHOICES).keys()
    if new_status in valid_status:
        order.status = new_status
        order.save()
        messages.success(request, f"อัปเดตสถานะออเดอร์ #{order.id} เรียบร้อยแล้ว")
    else:
        messages.error(request, "ค่าสถานะไม่ถูกต้อง")

    return redirect('admin-order-list')

# ฟังก์ชันลบออเดอร์ (Admin)
@require_POST
@login_required
def admin_delete_order(request, pk):
    if not request.user.is_staff:
        return redirect('product-list')

    order = get_object_or_404(Order, pk=pk)
    order.delete()
    messages.success(request, f"ลบออเดอร์ #{pk} เรียบร้อยแล้ว")
    return redirect('admin-order-list')