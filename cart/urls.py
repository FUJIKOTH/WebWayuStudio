from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # C (Create) - เพิ่มสินค้าลงในตะกร้า
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    # R (Read) - แสดงหน้าตะกร้าสินค้า
    path('', views.cart_detail, name='cart_detail'), 
    
    # U (Update) - แก้ไขจำนวนสินค้าในตะกร้า
    # โดยใช้ item_id แทน product_id เพื่อระบุรายการในตะกร้าโดยตรง
    path('update/<int:item_id>/', views.update_cart, name='update_cart'), 
    
    # D (Delete) - ลบรายการสินค้าออกจากตะกร้า
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
]