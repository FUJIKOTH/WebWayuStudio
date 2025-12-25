from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required # <--- จำเป็นต้องใช้
from .forms import CustomPlaqueOrderForm
from .models import CustomPlaqueOrder

# 1. หน้าสั่งทำ (บังคับล็อกอิน)
@login_required(login_url='/accounts/login/') 
def create_plaque_order(request):
    if request.method == 'POST':
        form = CustomPlaqueOrderForm(request.POST, request.FILES)
        if form.is_valid():
            # A. ดึงข้อมูลมาพักไว้ก่อน อย่าเพิ่ง save ลง DB
            order = form.save(commit=False)
            
            # B. ฝัง User ID ของคนที่ล็อกอินอยู่ลงไป
            order.user = request.user
            
            # C. บันทึกจริง
            order.save()

            # D. ส่งไปหน้า Checkout (ส่ง id ไปด้วย)
            return redirect('plaque_checkout', order_id=order.id) 
    else:
        form = CustomPlaqueOrderForm()

    return render(request, 'plaques/order_form.html', {'form': form})

# 2. หน้า Checkout (เลือกส่ง + อัปสลิป)
@login_required
def plaque_checkout(request, order_id):
    # ต้องเป็นเจ้าของออเดอร์เท่านั้นถึงจะเข้าหน้านี้ได้ (กันคนอื่นมามั่ว)
    order = get_object_or_404(CustomPlaqueOrder, pk=order_id, user=request.user)

    if request.method == 'POST':
        shipping_method = request.POST.get('shipping_method')
        payment_slip = request.FILES.get('payment_slip')

        # คำนวณค่าส่ง
        shipping_cost = 0
        if shipping_method == 'standard':
            shipping_cost = 50
        elif shipping_method == 'express':
            shipping_cost = 100
        
        # อัปเดตข้อมูล
        order.shipping_method = shipping_method
        order.final_price = order.price + shipping_cost 
        
        if payment_slip:
            order.PAYMENT_SLIP = payment_slip
            order.status = 'pending' # เปลี่ยนสถานะเป็นรอตรวจสอบ
        
        order.save()
        
        return redirect('plaque_order_success')

    return render(request, 'plaques/checkout.html', {'order': order})

# 3. หน้าขอบคุณ (เพิ่มฟังก์ชันนี้เข้าไปครับ)
def order_success(request):
    # ใช้ไฟล์ html เดิม (thankyou.html) หรือจะเปลี่ยนชื่อไฟล์ html ก็ได้
    return render(request, 'plaques/order_success.html')

# 4. หน้า Manager (สำหรับแอดมิน)
# ควรใส่ @user_passes_test หรือเช็คว่าเป็น superuser ไหม เพื่อความปลอดภัย
def orderplaques_manager(request):
    orders = CustomPlaqueOrder.objects.all().order_by('-created_at')
    total_sales = sum(order.price for order in orders if order.price)
    
    return render(request, 'plaques/admin/orderplaques_manager.html', {
        'orders': orders,
        'total_sales': total_sales
    })

# 5. อัปเดตสถานะ (สำหรับแอดมิน)
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(CustomPlaqueOrder, pk=order_id)
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
    return redirect('orderplaques_manager')

def delete_plaque_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(CustomPlaqueOrder, pk=order_id)
        order.delete()
    return redirect('orderplaques_manager')