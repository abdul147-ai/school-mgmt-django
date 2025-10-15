from django.contrib.auth.models import AbstractUser
from django.db import models





GENDER = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Others', 'Others'),
    ]
class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student')
    ]

    user_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=20, default='student')
    mobile = models.CharField(max_length=15)
    address = models.TextField()
    profile = models.ImageField(upload_to='profile/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} - {self.user_type}"

    @property
    def is_admin(self):
        return self.user_type == 'admin'

    @property
    def is_teacher(self):
        return self.user_type == 'teacher'

    @property
    def is_student(self):
        return self.user_type == 'student'


class Teacher(models.Model):


    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=11, unique=True)
    gender = models.CharField(choices=GENDER, max_length=10, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, related_name='teachers')
    qualification = models.CharField(max_length=100,blank=True,null=True)
    specialization = models.CharField(max_length=100,blank=True,null=True)
    experience = models.CharField(max_length=100,blank=True,null=True)
    joining_date = models.DateField(null=True,blank=True)
    salary = models.DecimalField( max_digits=10,decimal_places=2,null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def get_name(self):
        return self.user.first_name + " "+ self.user.last_name

    def __str__(self):
        return f"{self.get_name} - {self.department}"




class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=11, unique=True)
    gender = models.CharField(choices=GENDER, max_length=10, blank=True)
    Class = models.CharField(max_length=100,blank=True,null=True)
    admission_number = models.CharField(max_length=11,blank=True,null=True)
    subject = models.TextField(blank=True,null=True,default='[]')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, related_name='student')


    #parents
    father_name = models.CharField(max_length=100,blank=True,null=True)
    occupation = models.CharField(max_length=100,blank=True,null=True)
    mother_name = models.CharField(max_length=100,blank=True,null=True)
    contact_number = models.CharField(max_length=11,blank=True,null=True)
    permanent_address = models.TextField(blank=True,null=True)

    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name

    def __str__(self):
        return f"{self.get_name} - {self.student_id}"


class Department(models.Model):
    department_id = models.CharField(max_length=11, unique=True)
    name = models.CharField(max_length=100,blank=True,null=True)

    description = models.TextField(blank=True,null=True)
    start_date = models.DateField(null=True,blank=True)
    number_of_students = models.IntegerField(null=True,blank=True)
    number_of_teachers = models.IntegerField(null=True,blank=True)

    #contact
    email = models.EmailField(null=True,blank=True)
    phone_number = models.CharField(max_length=15,blank=True,null=True)
    office_location = models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
        return f"{self.name} - {self.department_id}"


