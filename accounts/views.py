from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomUserUpdateForm 
from django.db import IntegrityError

from stores.models import Order
from framings.models import CustomFrameOrder 
from plaques.models import CustomPlaqueOrder

# View สำหรับหน้าล็อกอิน
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

# View สำหรับการล็อกเอาท์
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # ลองบันทึกข้อมูล
                form.save()
                messages.success(request, 'สมัครสมาชิกสำเร็จ! กรุณาล็อกอิน')
                return redirect('login')
                
            except IntegrityError:
                # ถ้าบันทึกไม่ผ่านเพราะข้อมูลซ้ำ (IntegrityError)
                # ให้เพิ่ม Error เข้าไปที่ช่อง username เพื่อให้แสดงผลสีแดงใต้ช่องนั้น
                form.add_error('username', 'ชื่อผู้ใช้นี้มีอยู่ในระบบแล้ว โปรดใช้ชื่ออื่น')
                
                # หรือถ้าอยากแจ้งเป็น pop-up ด้านบนก็ใช้:
                # messages.error(request, 'ชื่อผู้ใช้นี้มีคนใช้แล้ว')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'accounts/signup.html', {'form': form})

# View สำหรับโปรไฟล์ผู้ใช้ 
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'โปรไฟล์ของคุณถูกอัปเดตเรียบร้อยแล้ว!')
            return redirect('profile')

    else:
        form = CustomUserUpdateForm(instance=request.user)

    context = {
        'form': form 
    }
    return render(request, 'accounts/profile.html', context)

# View สำหรับเปลี่ยนรหัสผ่าน
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'รหัสผ่านของคุณถูกเปลี่ยนเรียบร้อยแล้ว!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def order_dashboard(request):
    """แสดงหน้า Dashboard ให้เลือกประเภท"""
    return render(request, 'accounts/order_dashboard.html')

@login_required
def order_history(request, order_type):
    context = {}
    current_status = request.GET.get('status', 'all')
    
    # 1. เช็คประเภทและดึงข้อมูล (แก้ชื่อ field user/customer ให้ตรง database)
    if order_type == 'products':
        page_title = "รายการสั่งซื้อสินค้า"
        template_name = 'stores/order_history_products.html'
        # สินค้าปกติใช้ 'customer'
        orders = Order.objects.filter(customer=request.user).order_by('-created_at')
        
    elif order_type == 'framings':
        page_title = "รายการสั่งทำกรอบรูป"
        template_name = 'framings/order_history_framings.html'
        # กรอบรูปใช้ 'user' (ตาม Error log)
        orders = CustomFrameOrder.objects.filter(user=request.user).order_by('-created_at')
        
    elif order_type == 'plaques':
        page_title = "รายการสั่งทำป้ายหินอ่อน"
        template_name = 'plaques/order_history_plaques.html'
        # ป้ายหินอ่อนใช้ 'user' (ตาม Error log)
        orders = CustomPlaqueOrder.objects.filter(user=request.user).order_by('-created_at')
        
    else:
        # ถ้า URL ผิด ให้กลับไปหน้า Dashboard
        return redirect('order_dashboard')

    # 2. Logic กรองสถานะ (เหมือนเดิม)
    if current_status != 'all':
        orders = orders.filter(status__iexact=current_status)

    context = {
        'orders': orders,
        'page_title': page_title,
        'order_type': order_type,
        'current_status': current_status
    }

    return render(request, template_name, context)

@login_required
def product_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'stores/order_detail.html', {'order': order})

@login_required
def framing_order_detail(request, order_id):
    order = get_object_or_404(CustomFrameOrder, id=order_id, user=request.user)
    return render(request, 'framings/order_framing_detail.html', {'order': order})

@login_required
def plaque_order_detail(request, order_id):
    order = get_object_or_404(CustomPlaqueOrder, id=order_id, user=request.user)
    return render(request, 'plaques/order_plaque_detail.html', {'order': order})

