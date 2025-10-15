from django.contrib import admin
from django.urls import path,include

from . import views

urlpatterns = [
    path('', views.login_view, name='login.html'),
    path('dashboard/', views.index, name='index.html'),
]