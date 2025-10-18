from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from . forms import *



# Create your views here.
def login(request):
    return render(request, 'login.html')

def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'You are now logged in.')

            #redirect dashboard
            if user.user_type == 'admin':
                return redirect('admin_dashboard')
            elif user.user_type == 'teacher':
                return redirect('teacher_dashboard')
            elif user.user_type == 'student':
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Username or Password is incorrect')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You are now logged out.')
    return redirect('login')


def admin_signup(request):
    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Admin account created.')
            return redirect('login')
        else:
            messages.error(request, 'Form is invalid.')

    else:
        form = AdminSignUpForm()
    return render(request, 'admin_signup.html', {'form': form})


def student_view(request):
    return render(request, 'students.html')

def student_details(request):
    return render(request, 'student_details.html')

def add_student(request):
    return render(request, 'add_student.html')

def edit_student(request,id):
    return render(request, 'edit_student.html' , {'student_id':id})



def teacher_view(request):
    return render(request, 'teachers.html')

def teacher_details(request):
    return render(request, 'teacher_details.html')

def add_teacher(request):
    return render(request, 'add_teacher.html')

def edit_teacher(request,id):
    return render(request, 'edit_teacher.html' , {'teacher_id':id})