from django.contrib import admin
from django.urls import path,include

from . import views

urlpatterns = [
    path('logout',views.logout,name='logout'),

    path('', views.login, name='login.html'),
    path('index/', views.index, name='index.html'),


    path('students/', views.student_view, name='students'),
    path('student/details/', views.student_details, name='student_details'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/edit/<int:id>/', views.edit_student, name='edit_student'),
]