from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import CustomFrameOrder
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

PRICE_LIST = {
    '8x10': 150,   # ขนาด 8x10 นิ้ว = 150 บาท
    '10x12': 200,    # ขนาด 10x12 = 400 บาท
    '16x20': 600,    # ขนาด 16x20 = 600 บาท
}

# Mixin สำหรับเช็คสิทธิ์แอดมิน
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff and self.request.user.is_active

@login_required(login_url='/accounts/login/')
def create_custom_order(request):
    if request.method == 'POST':
        uploaded_image = request.FILES.get('image')
        size = request.POST.get('size_option')
        style = request.POST.get('style_option')      
        mounting = request.POST.get('mounting_option')
        
        # [เพิ่ม] รับค่าหมายเหตุจากฟอร์ม
        note = request.POST.get('note', '') 

        estimated_price = PRICE_LIST.get(size, 0)

        # สร้าง Order เบื้องต้น
        order = CustomFrameOrder.objects.create(
            user=request.user if request.user.is_authenticated else None,
            uploaded_image=uploaded_image,
            size_option=size,
            style_option=style,         
            mounting_option=mounting,
            note=note,  # [เพิ่ม] บันทึกหมายเหตุลงฐานข้อมูล
            total_price=estimated_price,
            status='pending'
        )
        
        return redirect('order_confirmation', order_id=order.id)

    return render(request, 'framings/create_orderframing.html')

def order_confirmation(request, order_id):
    order = get_object_or_404(CustomFrameOrder, id=order_id)

    if request.method == 'POST':
        # รับค่าการจัดส่งและจ่ายเงิน
        shipping_method = request.POST.get('shipping_method')
        payment_method = request.POST.get('payment_method')
        uploaded_slip = request.FILES.get('payment_slip')

        # รับค่าจำนวนสินค้า (Quantity)
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1: quantity = 1
        except (ValueError, TypeError):
            quantity = 1

        # คำนวณค่าส่ง
        if shipping_method == 'pickup':
            shipping_cost = 0          # รับเอง ฟรี
        elif shipping_method == 'express':
            shipping_cost = 100        # ด่วน 100
        else:
            shipping_cost = 50         # ธรรมดา 50 (standard)

        # คำนวณราคารวมใหม่
        unit_price = PRICE_LIST.get(order.size_option, 0)
        
        # สูตร: (ราคาต่อชิ้น x จำนวน) + ค่าส่ง
        grand_total = (unit_price * quantity) + shipping_cost

        # บันทึกอัปเดตข้อมูลลง Database
        order.quantity = quantity
        order.shipping_method = shipping_method
        order.payment_method = payment_method
        order.total_price = grand_total

        # ถ้าโอนเงิน ต้องแนบสลิป
        if payment_method == 'transfer':
            if uploaded_slip:
                order.payment_slip = uploaded_slip
            else:
                messages.error(request, "กรุณาแนบสลิปโอนเงิน")
                return redirect('order_confirmation', order_id=order.id)
        
        order.status = 'pending' 
        order.save()
        
        return redirect('order_success')

    return render(request, 'framings/order_confirmation.html', {'order': order})

def order_success(request):
    return render(request, 'framings/order_success.html')

class ShopManagerView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CustomFrameOrder
    template_name = 'framings/admin/orderframings_manager.html'
    context_object_name = 'orders'
    ordering = ['-created_at']

    def test_func(self):
        return self.request.user.is_staff and self.request.user.is_active
    
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(CustomFrameOrder, id=order_id)
    new_status = request.POST.get('status')
    order.status = new_status
    order.save()
    return redirect('orderframings_manager')

@require_POST
def delete_order(request, order_id):
    order = get_object_or_404(CustomFrameOrder, id=order_id)
    order.delete()
    return redirect('orderframings_manager')