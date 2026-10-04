from django.shortcuts import render
from . import forms
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

UserModel = get_user_model()

def page_response(request):
    if request.method == 'POST':
        form = forms.PasswordResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data.get('email')
            
            user = None
            
            if username:
                try:
                    user = UserModel.objects.get(username=username)
                    email = user.email
                except UserModel.DoesNotExist:
                    pass
            elif email:
                try:
                    user = UserModel.objects.get(email=email)
                except UserModel.DoesNotExist:
                    pass
                    
            if user:
                reset_request = PasswordResetForm({'email': user.email})
                if reset_request.is_valid():
                    reset_request.save(
                        request=request,
                        email_template_name='registration/password_reset_email.html',
                        subject_template_name='registration/password_reset_subject.txt',
                        from_email='mahnoorlodhika1@gmail.com'
                    )
                    
            messages.success(
                request,
                "We've emailed you instructions for setting your password, " \
                "if an account exists with the email you entered. You should receive them shortly." \
                " If you don't receive an email, " \
                "please make sure you've entered the address you registered with, and check your spam folder.")
    else:
        form = forms.PasswordResetForm()
    
    return render(request, 'reset.html', {'form': form})
