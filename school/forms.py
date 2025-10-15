from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from . import models
from .models import Teacher


class AdminSignUpForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }


class TeacherSignUpForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }
class TeacherForm(forms.ModelForm):
    class Meta:
        model = models.Teacher
        exclude = ['user']



class StudentSignUpForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }

class StudentForm(forms.ModelForm):
    class Meta:
        model =models.Student
        exclude = ['user']
