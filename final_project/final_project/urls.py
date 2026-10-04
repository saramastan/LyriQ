"""
URL configuration for final_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

from page_requests import game, home, howto, login, register, logout, reset, leaderboard, start


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', home.page_response, name='home'),
    path('howto', howto.page_response, name='howto'),
    path('game', game.page_response, name='game'),
    path('leaderboard', leaderboard.page_response, name='leaderboard'),
    path('start', start.page_response, name='start'),


    path('register', register.page_response, name='register'),
    path('reset', reset.page_response, name='reset'),
    path('login', login.page_response, name='login'),
    path('logout', logout.page_response, name='logout'),
    
    path("accounts/reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),
         name="password_reset_confirm"),
    path("accounts/reset/done/",
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
         name="password_reset_complete"),
    ]
    
