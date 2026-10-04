from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class ArtistForm(forms.Form):
    artist = forms.CharField(label="Artist Name", max_length=100)

class RegisterForm(forms.ModelForm):

    email = forms.EmailField(
        max_length=50,
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Email',
                'class': 'form-control form-control-sm'
            }
        ),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password',
                'class': 'form-control form-control-sm'
            }
        ),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Confirm Password',
                'class': 'form-control form-control-sm'
            }
        ),
        label="Confirm Password"
    )
    
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Username',
            'class': 'form-control form-control-sm'
        }),
        label="Username"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

        help_texts = {
            'username': None
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Username',
                'class': 'form-control form-control-sm'
            })
        }
    
    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("That username is already taken.")
        return username
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("Email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        username = cleaned_data.get("username")
        
        if not self.errors:
            if password != confirm_password:
                raise ValidationError("Passwords do not match")
            if password:
                try:
                    validate_password(password, user=User(username=username))
                except ValidationError as e:
                    raise ValidationError(e.messages)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['username'].strip()
        user.set_password(self.cleaned_data['password'])  # hash!
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=50,
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Email',
                'class': 'form-control form-control-sm'
            }
        ),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password',
                'class': 'form-control form-control-sm'
            }
        ),
        label="Password"
    )

class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        max_length=50,
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Email',
                'class': 'form-control form-control-sm'
            }
        ),
        label="Email",
        required=False,
    )
    
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Username',
        'class': 'form-control form-control-sm'
        }),
        label="Username",
        required=False,
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        if not username and not email:
            raise ValidationError("Please enter either a username or an email.")
        return cleaned_data
