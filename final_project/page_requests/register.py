from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from .forms import RegisterForm

def page_response(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = (form.cleaned_data.get('username') or '').strip()
            
            if User.objects.filter(username__iexact=username).exists():
                form.add_error('username', 'That username is already taken.')
            else:
                try:
                    user = form.save(commit=False)
                    user.username = username
                    user.set_password(form.cleaned_data['password'])
                    user.save()
                    messages.success(request, "Account created successfully!")
                    return redirect('login')
                except IntegrityError:
                    form.add_error('username', 'That username is already taken.')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})
