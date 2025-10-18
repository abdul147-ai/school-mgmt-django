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

    path('teachers/', views.teacher_view, name='teachers'),
    path('teacher/details/', views.teacher_details, name='teacher_details'),
    path('teacher/add/', views.add_teacher, name='add_teacher'),
    path('teacher/edit/<int:id>/', views.edit_teacher, name='edit_teacher'),

]