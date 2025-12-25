from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Sum

from django.http import JsonResponse
from .models import WorkSchedule
from django.contrib.auth.decorators import login_required, user_passes_test

# --- 1. Import Models ทั้ง 3 ตัว ---
# (ตรวจสอบชื่อ App ให้ถูกต้องตามโฟลเดอร์ของคุณนะครับ)
from stores.models import Order 
from framings.models import CustomFrameOrder  
from plaques.models import CustomPlaqueOrder

User = get_user_model()

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff and self.request.user.is_active

class HomePageView(TemplateView):
    template_name = "home.html"

# --- Dashboard View ---
class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # สถานะที่นับเป็นยอดขาย (เงินเข้าแล้ว)
        paid_status = ['processing', 'shipped']

        # --- 1. คำนวณยอดขายแยกประเภท ---
        
        # 1.1 ร้านค้าทั่วไป (Order)
        sales_general = Order.objects.filter(status__in=paid_status).aggregate(sum=Sum('total_price'))['sum'] or 0

        # 1.2 สั่งทำกรอบรูป (CustomFrameOrder)
        sales_framing = CustomFrameOrder.objects.filter(status__in=paid_status).aggregate(sum=Sum('total_price'))['sum'] or 0

        # 1.3 สั่งทำป้ายหินอ่อน (CustomPlaqueOrder) - ใช้ final_price
        sales_plaque = CustomPlaqueOrder.objects.filter(status__in=paid_status).aggregate(sum=Sum('final_price'))['sum'] or 0

        # --- 2. ยอดรวมสุทธิ (Grand Total) ---
        grand_total = sales_general + sales_framing + sales_plaque

        # --- 3. ข้อมูลอื่นๆ (จำนวนออเดอร์รวม) ---
        total_orders_count = (
            Order.objects.count() + 
            CustomFrameOrder.objects.count() + 
            CustomPlaqueOrder.objects.count()
        )
        
        # ออเดอร์รอตรวจสอบ (Pending) รวมทุกประเภท
        pending_count = (
            Order.objects.filter(status='pending').count() +
            CustomFrameOrder.objects.filter(status='pending').count() +
            CustomPlaqueOrder.objects.filter(status='pending').count()
        )

        # --- ส่งค่าไปที่ Template ---
        context['sales_general'] = sales_general
        context['sales_framing'] = sales_framing
        context['sales_plaque'] = sales_plaque
        context['grand_total'] = grand_total
        
        context['total_orders_count'] = total_orders_count
        context['pending_count'] = pending_count
        
        return context

# --- User Management (จัดการผู้ใช้) ---

class UserManageView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'user_manage.html'
    context_object_name = 'users'
    ordering = ['-date_joined'] 

def toggle_user_status(request, user_id):
    if not request.user.is_staff:
        return redirect('home')
    
    user = get_object_or_404(User, id=user_id)
    
    # ป้องกันไม่ให้แบนตัวเอง หรือ Superuser
    if user.is_superuser or user == request.user:
        messages.error(request, "ไม่สามารถระงับการใช้งานผู้ดูแลระบบสูงสุดหรือตัวเองได้")
    else:
        user.is_active = not user.is_active
        user.save()
        status = "เปิดใช้งาน" if user.is_active else "ระงับการใช้งาน"
        # พยายามหาชื่อมาแสดง (Username หรือ Email)
        name_display = getattr(user, 'username', user.email)
        messages.success(request, f"อัปเดตสถานะ {name_display} เป็น {status} แล้ว")
        
    return redirect('user_manage')

def delete_user(request, user_id):
    if not request.user.is_staff:
        return redirect('home')
        
    user = get_object_or_404(User, id=user_id)
    
    if user.is_superuser or user == request.user:
        messages.error(request, "ไม่สามารถลบผู้ดูแลระบบสูงสุดหรือตัวเองได้")
    else:
        name_display = getattr(user, 'username', user.email)
        user.delete()
        messages.success(request, f"ลบผู้ใช้ {name_display} เรียบร้อยแล้ว")
        
    return redirect('user_manage')

def is_admin(user):
    return user.is_authenticated and user.is_superuser

# 1. หน้าจัดการตารางงาน (สำหรับ Admin เท่านั้น)
@user_passes_test(is_admin)
def admin_calendar(request):
    # ดึงข้อมูลงานทั้งหมดมาแสดงเป็นรายการด้านล่าง (เผื่ออยากดูแบบ List)
    events = WorkSchedule.objects.all().order_by('-start_date')
    
    if request.method == "POST":
        title = request.POST.get('title')
        date = request.POST.get('date')
        if title and date:
            WorkSchedule.objects.create(title=title, start_date=date)
            messages.success(request, f"เพิ่มคิวงาน '{title}' เรียบร้อยแล้ว")
            return redirect('admin_calendar')
            
    return render(request, 'admin_calendar.html', {'events': events})

# 2. API ส่งข้อมูล JSON ให้ปฏิทิน (แก้ไขใหม่: เปิดเผยรายละเอียดให้ทุกคนเห็น)
def calendar_events(request):
    events = WorkSchedule.objects.all()
    data = []
    
    for event in events:
        # --- 1. ชื่องาน: ให้ทุกคนเห็นรายละเอียดจริง (ไม่ต้องเช็ค is_staff แล้ว) ---
        display_title = event.title  # ✅ โชว์ชื่อเต็มให้ทุกคนเห็น

        # --- 2. สี: (อันนี้แล้วแต่คุณ ถ้าอยากให้สีต่างกันระหว่างแอดมินกับลูกค้าก็เก็บไว้ได้) ---
        if request.user.is_staff:
            bg_color = '#3b82f6' # สีฟ้า (มุมมองแอดมิน)
            text_color = '#ffffff'
        else:
            bg_color = '#EAB308' # สีเหลือง (มุมมองลูกค้า)
            text_color = '#000000'

        data.append({
            'id': event.id,
            'title': display_title,
            'start': event.start_date.isoformat(),
            'color': bg_color,
            'textColor': text_color,
            'allDay': True 
        })
        
    return JsonResponse(data, safe=False)

# 3. เพิ่มฟังก์ชันสำหรับบันทึกการแก้ไข (Update)
@user_passes_test(is_admin)
def edit_event(request, event_id):
    event = get_object_or_404(WorkSchedule, id=event_id)
    
    if request.method == "POST":
        title = request.POST.get('title')
        date = request.POST.get('date')
        
        if title and date:
            event.title = title
            event.start_date = date
            event.save()
            messages.success(request, f"แก้ไขงาน '{title}' เรียบร้อยแล้ว")
            
    return redirect('admin_calendar')

# 4. ลบงาน (สำหรับ Admin เท่านั้น)
@user_passes_test(is_admin)
def delete_event(request, event_id):
    event = get_object_or_404(WorkSchedule, id=event_id)
    title = event.title
    event.delete()
    messages.success(request, f"ลบคิวงาน '{title}' เรียบร้อยแล้ว")
    return redirect('admin_calendar')