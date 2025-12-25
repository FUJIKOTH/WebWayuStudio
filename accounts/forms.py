from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

# ==================== ฟอร์มสมัครสมาชิก ====================
class CustomUserCreationForm(UserCreationForm):

    first_name = forms.CharField(label='ชื่อจริง:', max_length=150, required=True)
    last_name = forms.CharField(label='นามสกุล:', max_length=150, required=True)
    email = forms.EmailField(label='อีเมล:', required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'address', 'image'
        )
        labels = {
            'username': 'ชื่อผู้ใช้:',
            'phone_number': 'เบอร์โทรศัพท์:',
            'address': 'ที่อยู่:',
            'image': 'รูปโปรไฟล์:',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].widget = forms.Textarea(attrs={'rows': 3})

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        user.phone_number = self.cleaned_data.get('phone_number')
        user.address = self.cleaned_data.get('address')

        if commit:
            user.save()

        return user

    
# ==================== ฟอร์มแก้ไขโปรไฟล์ ====================
class CustomUserUpdateForm(forms.ModelForm):

    class Meta:
        model = CustomUser
        
        fields = ['first_name', 'last_name', 'email', 
                  'image', 'phone_number', 'address']
        
        labels = {
            'first_name': 'ชื่อจริง',
            'last_name': 'นามสกุล',
            'email': 'อีเมล',
            'image': 'เปลี่ยนรูปโปรไฟล์',
            'phone_number': 'เบอร์โทรศัพท์',
            'address': 'ที่อยู่'
        }
        
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }