from django.urls import path
from . import views

urlpatterns = [

    path('create_order/', views.create_custom_order, name='create_custom_order'), # URL สำหรับสร้างออเดอร์สั่งทำกรอบรูป
    path('order/<int:order_id>/confirm/', views.order_confirmation, name='order_confirmation'), # URL สำหรับยืนยันออเดอร์กรอบรูป
    path('order/success/', views.order_success, name='order_success'), # URL สำหรับหน้าสำเร็จหลังจากสั่งทำกรอบรูป

    path('manager/dashboard/', views.ShopManagerView.as_view(), name='orderframings_manager'), # URL สำหรับหน้าจัดสินค้ากรอบรูป
    path('manager/order/<int:order_id>/update/', views.update_order_status, name='update_framing_status'), # URL สำหรับอัพเดทสถานะออเดอร์กรอบรูป
    path('manager/order/<int:order_id>/delete/', views.delete_order, name='delete_framing_order'), # URL สำหรับลบออเดอร์กรอบรูป
]