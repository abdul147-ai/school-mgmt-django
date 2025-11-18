# In admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Teacher, Student, Department, Subject, Class, StudentAttendance, TeacherAttendance, Timetable, \
    Account, Assignment, AssignmentSubmission, Syllabus


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': (
                'user_type',
                'mobile',
                'address',
                'profile',
                'date_of_birth'
            )
        }),
    )

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'get_name', 'department', 'joining_date')
    search_fields = ('teacher_id', 'user__first_name', 'user__last_name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_name', 'Class', 'admission_number')
    search_fields = ('student_id', 'user__first_name', 'user__last_name')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_id','name','hod' )
    list_filter = ['hod']

admin.site.register(Subject)
admin.site.register(Class)
admin.site.register(StudentAttendance)
admin.site.register(TeacherAttendance)
admin.site.register(Timetable)
admin.site.register(Account)
admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
admin.site.register(Syllabus)