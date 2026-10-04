from django.shortcuts import render, redirect
from . import forms
from django.contrib.auth import logout, authenticate, get_user_model
from django.contrib import messages

def page_response(request):
    logout(request)
    return redirect('home')
