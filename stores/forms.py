from django import forms
from .models import Product, Category

# --- 1. สร้าง Form สำหรับ Category ---
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        
        fields = ['name'] 

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded shadow-sm'
            }),
        }

# --- 2. อัปเดต ProductForm ให้เลือก Category ได้ ---
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # --- อัปเดต 'fields' ให้ครบ ---
        fields = [
            'category', 
            'name', 
            'description', 
            'price',
            'stock',
            'image'
        ]
        
        # (ขั้นสูง) คุณสามารถใช้ widgets เพื่อจัดสไตล์ฟอร์มด้วย Tailwind ได้
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full p-2 border rounded'}),
        }