from django.urls import path
from . import views

urlpatterns = [
    path('order/', views.create_plaque_order, name='create_plaque_order'), # URL สำหรับฟอร์มสั่งทำป้าย
    path('checkout/<int:order_id>/', views.plaque_checkout, name='plaque_checkout'), # URL สำหรับหน้าชำระเงินคำสั่งทำป้าย
    path('order/success/', views.order_success, name='plaque_order_success'), # URL สำหรับหน้าขอบคุณหลังสั่งทำป้าย

    path('manager/', views.orderplaques_manager, name='orderplaques_manager'), # URL สำหรับหน้าจัดการคำสั่งทำป้าย
    path('manager/update/<int:order_id>/', views.update_order_status, name='update_order_status'), # URL สำหรับอัปเดตสถานะคำสั่งทำป้าย
    path('manager/delete/<int:order_id>/', views.delete_plaque_order, name='delete_plaque_order'), # URL สำหรับลบคำสั่งทำป้าย
]