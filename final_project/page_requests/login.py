from django.shortcuts import render, redirect
from . import forms
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib import messages

UserModel = get_user_model()

def page_response(request):
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
        try:
            user_email = UserModel.objects.get(email=email)
            user = authenticate(request, username=user_email.username, password=password)
        except UserModel.DoesNotExist:
            user = None
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = forms.LoginForm(request.POST)
    return render(request, 'login.html', {'form': form})
