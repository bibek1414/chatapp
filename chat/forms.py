from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Message
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'phone_number']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'file', 'message_type']

class ContactSearchForm(forms.Form):
    search = forms.CharField(max_length=100, required=False)