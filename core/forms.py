from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Review, Booking, UserProfile, ContactMessage


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'your@email.com'}))
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+61 400 000 000'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Confirm Password'})

    def clean_first_name(self):
        import re
        value = self.cleaned_data.get('first_name', '').strip()
        if not value:
            raise forms.ValidationError('First name is required.')
        if not re.match(r'^[A-Za-z\s\-]+$', value):
            raise forms.ValidationError('First name must contain letters only.')
        return value

    def clean_last_name(self):
        import re
        value = self.cleaned_data.get('last_name', '').strip()
        if not value:
            raise forms.ValidationError('Last name is required.')
        if not re.match(r'^[A-Za-z\s\-]+$', value):
            raise forms.ValidationError('Last name must contain letters only.')
        return value

    def clean_email(self):
        import re
        value = self.cleaned_data.get('email', '').strip()
        if not value:
            raise forms.ValidationError('Email is required.')
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', value):
            raise forms.ValidationError('Enter a valid email address.')
        if User.objects.filter(email=value).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return value

    def clean_phone(self):
        import re
        value = self.cleaned_data.get('phone', '').strip()
        if value and not re.match(r'^[0-9+\-\s().]+$', value):
            raise forms.ValidationError('Phone must contain digits only — no letters.')
        return value


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Password'})


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, max_value=5, widget=forms.HiddenInput())

    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Share your experience...'}),
        }


class SessionBookingForm(forms.ModelForm):
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-input', 'rows': 3,
        'placeholder': 'Any health conditions or special requests?'
    }))

    class Meta:
        model = Booking
        fields = ('notes',)


class PaymentForm(forms.Form):
    card_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Name on Card'}))
    card_number = forms.CharField(max_length=19, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '1234 5678 9012 3456', 'maxlength': '19'}))
    expiry = forms.CharField(max_length=5, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'MM/YY', 'maxlength': '5'}))
    cvv = forms.CharField(max_length=4, widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'CVV', 'maxlength': '4'}))


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))

    class Meta:
        model = UserProfile
        fields = ('phone', 'bio', 'avatar', 'emergency_contact', 'health_notes')
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Name & Phone'}),
            'health_notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Injuries, conditions the instructor should know about'}),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'subject', 'message')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'your@email.com'}),
            'subject': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'placeholder': 'Your message...'}),
        }

    def clean_name(self):
        import re
        value = self.cleaned_data.get('name', '').strip()
        if not value:
            raise forms.ValidationError('Name is required.')
        if not re.match(r'^[A-Za-z\s\-]+$', value):
            raise forms.ValidationError('Name must contain letters only.')
        return value

    def clean_message(self):
        value = self.cleaned_data.get('message', '').strip()
        if len(value) < 10:
            raise forms.ValidationError('Message must be at least 10 characters.')
        return value
