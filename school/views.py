from gc import get_objects
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from datetime import datetime
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django import forms
from .forms import *
from .models import *


# user test function
def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'


def is_teacher(user):
    return user.is_authenticated and user.user_type == 'teacher'


def is_student(user):
    return user.is_authenticated and user.user_type == 'student'


def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url='login_view')
    @user_passes_test(is_admin, login_url='login_view')
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def teacher_required(view_func):
    @wraps(view_func)
    @login_required(login_url='login_view')
    @user_passes_test(is_teacher, login_url='login_view')
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def student_required(view_func):
    @wraps(view_func)
    @login_required(login_url='login_view')
    @user_passes_test(is_student, login_url='login_view')
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def login_view(request):
    """Handles both displaying login page and form submission"""
    next_url = request.GET.get('next')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, 'You are now logged in.')

            if next_url:
                return redirect(next_url)

            # Redirect to appropriate dashboard
            if user.user_type == 'admin':
                return redirect('admin_dashboard')
            elif user.user_type == 'teacher':
                return redirect('teacher_dashboard')
            elif user.user_type == 'student':
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Username or Password is incorrect')

    return render(request, 'login.html', {'next': next_url})


def logout_view(request):
    logout(request)
    messages.success(request, 'You are now logged out.')
    return redirect('login_view')


def admin_signup(request):
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        if request.user.is_admin:
            return redirect('admin_dashboard')
        else:
            return redirect('login')

    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Log the user in after signup
            auth_login(request, user)
            messages.success(request, 'Admin account created successfully! Welcome to your dashboard.')
            return redirect('admin_dashboard')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = AdminSignUpForm()

    return render(request, 'admin_signup.html', {'form': form})


@admin_required
def admin_dashboard(request):
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_departments = Department.objects.count()

    recent_students = Student.objects.select_related('user').order_by('-id')[:5]
    recent_teachers = Teacher.objects.select_related('user').order_by('-id')[:5]

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_departments': total_departments,
        'recent_students': recent_students,
        'recent_teachers': recent_teachers,
    }
    return render(request, 'index.html', context)


@admin_required
def department_list(request):
    department = Department.objects.all().order_by('name')
    return render(request, 'department_list.html', {'department': department})


@admin_required
def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, 'Department added successfully!')
            return redirect('department_list')
        else:
            messages.error(request, 'Department already exists!')
    else:
        form = DepartmentForm()

    return render(request, 'add_department.html', {'form': form})


@admin_required
def edit_department(request, id):
    department = get_object_or_404(Department, id=id)

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department "{department.name}" updated successfully!')
            return redirect('department_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DepartmentForm(instance=department)

    return render(request, 'edit_department.html', {
        'form': form,
        'department': department
    })


@admin_required
def delete_department(request, id):
    department = get_object_or_404(Department, id=id)
    department.delete()
    messages.success(request, 'Department deleted successfully!')
    return redirect('department_list')


# admin Student
@admin_required
def student_view(request):
    students = Student.objects.select_related('user', 'department').all()
    return render(request, 'students.html', {'students': students})


@admin_required
def student_details(request, id):
    student = get_object_or_404(Student, id=id)
    return render(request, 'student_details.html', {'student': student})


@admin_required
def add_student(request):
    if request.method == 'POST':
        user_form = StudentSignUpForm(request.POST, request.FILES)
        student_form = StudentForm(request.POST)

        if user_form.is_valid() and student_form.is_valid():
            # Create user with student type
            user = user_form.save()

            # Create student profile
            student = student_form.save(commit=False)
            student.user = user
            student.save()

            messages.success(request, f'Student {user.get_full_name()} added successfully!')
            return redirect('students')
        else:
            print("User form errors:", user_form.errors)
            print("Student form errors:", student_form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = StudentSignUpForm()
        student_form = StudentForm()

    departments = Department.objects.all()
    return render(request, 'add_student.html', {
        'user_form': user_form,
        'student_form': student_form,
        'departments': departments,
    })


@admin_required
def edit_student(request, id):
    student = get_object_or_404(Student, id=id)
    user = student.user

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, request.FILES, instance=user)
        student_form = StudentForm(request.POST, instance=student)

        if user_form.is_valid() and student_form.is_valid():
            user = user_form.save()
            student_form.save()

            if user_form.cleaned_data.get('password1'):
                messages.success(request, f'Student {user.get_full_name()} updated successfully with new password!')
            else:
                messages.success(request, f'Student {user.get_full_name()} updated successfully!')

            return redirect('students')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserEditForm(instance=user)
        student_form = StudentForm(instance=student)

    departments = Department.objects.all()
    return render(request, 'edit_student.html', {
        'user_form': user_form,
        'student_form': student_form,
        'departments': departments,
        'student': student,
    })


@admin_required
def delete_student(request, id):
    student = get_object_or_404(Student, id=id)

    if request.method == 'POST':
        user_name = student.user.get_full_name()
        student.user.delete()
        messages.success(request, f'Student {user_name} deleted successfully!')
        return redirect('students')

    messages.warning(request, 'Invalid request method.')
    return redirect('students')


# admin Teacher
@admin_required
def teacher_view(request):
    teachers = Teacher.objects.select_related('user', 'department').prefetch_related('subjects').all()
    return render(request, 'teachers.html', {'teachers': teachers})


@admin_required
def teacher_details(request, id):
    teacher = get_object_or_404(Teacher, id=id)
    return render(request, 'teacher_details.html', {'teacher': teacher})


@admin_required
def add_teacher(request):
    if request.method == 'POST':
        user_form = TeacherSignUpForm(request.POST, request.FILES)
        teacher_form = TeacherForm(request.POST)

        if user_form.is_valid() and teacher_form.is_valid():
            # Create user with teacher type
            user = user_form.save()

            # Create teacher profile
            teacher = teacher_form.save(commit=False)
            teacher.user = user
            teacher.save()

            teacher_form.save_m2m()

            messages.success(request, f'Teacher {user.get_full_name()} added successfully!')
            return redirect('teachers')
        else:
            print("User form errors:", user_form.errors)
            print("Teacher form errors:", teacher_form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = TeacherSignUpForm()
        teacher_form = TeacherForm()

    departments = Department.objects.all()
    return render(request, 'add_teacher.html', {
        'user_form': user_form,
        'teacher_form': teacher_form,
        'departments': departments,
    })


@admin_required
def edit_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)
    user = teacher.user

    if request.method == 'POST':
        # Use updated UserEditForm with password fields
        user_form = UserEditForm(request.POST, request.FILES, instance=user)
        teacher_form = TeacherForm(request.POST, instance=teacher)

        if user_form.is_valid() and teacher_form.is_valid():
            user = user_form.save()  # This will handle password change if provided
            teacher_form.save()

            # Show appropriate message based on whether password was changed
            if user_form.cleaned_data.get('password1'):
                messages.success(request, f'Teacher {user.get_full_name()} updated successfully with new password!')
            else:
                messages.success(request, f'Teacher {user.get_full_name()} updated successfully!')

            return redirect('teachers')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserEditForm(instance=user)
        teacher_form = TeacherForm(instance=teacher)

    departments = Department.objects.all()
    return render(request, 'edit_teacher.html', {
        'user_form': user_form,
        'teacher_form': teacher_form,
        'departments': departments,
        'teacher': teacher,
    })


@admin_required
def delete_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)

    if request.method == 'POST':
        user_name = teacher.user.get_full_name()
        teacher.user.delete()
        messages.success(request, f'Teacher {user_name} deleted successfully!')
        return redirect('teachers')

    # If accessed via GET, redirect back
    messages.warning(request, 'Invalid request method.')
    return redirect('teachers')


# admin Subject
@admin_required
def subject_list(request):
    """List all subjects with department and class info"""
    subjects = Subject.objects.select_related('department').all().order_by('department__name', 'name')

    # Get subject-teacher relationships
    for subject in subjects:
        subject.teacher_count = Teacher.objects.filter(subjects=subject).count()  # Using the ManyToMany relationship

    return render(request, 'subject_list.html', {'subjects': subjects})


@admin_required
def add_subject(request):
    """Add new subject"""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" added successfully!')
            return redirect('subject_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectForm()

    return render(request, 'add_subject.html', {'form': form})


@admin_required
def edit_subject(request, id):
    """Edit existing subject"""
    subject = get_object_or_404(Subject, id=id)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" updated successfully!')
            return redirect('subject_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectForm(instance=subject)

    return render(request, 'edit_subject.html', {
        'form': form,
        'subject': subject
    })


@admin_required
def delete_subject(request, id):
    subject = get_object_or_404(Subject, id=id)

    if request.method == 'POST':
        subject_name = subject.name
        subject.delete()
        messages.success(request, f'Subject "{subject_name}" deleted successfully!')
        return redirect('subject_list')

    # If accessed via GET, redirect back with warning
    messages.warning(request, 'Invalid request method.')
    return redirect('subject_list')


@admin_required
def class_list(request):
    classes = Class.objects.select_related('department', 'class_teacher').prefetch_related('students').all().order_by(
        'department__name', 'name')

    for class_obj in classes:
        class_obj.student_count = class_obj.students.count()
    return render(request, 'class_list.html', {'classes': classes})


# admin Class
@admin_required
def add_class(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_obj = form.save()
            messages.success(request, f'Class "{class_obj.name}" added successfully!')
            return redirect('class_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClassForm()

    return render(request, 'add_class.html', {'form': form})


@admin_required
def edit_class(request, id):
    class_obj = get_object_or_404(Class, id=id)

    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            class_obj = form.save()
            messages.success(request, f'Class "{class_obj.name}" updated successfully!')
            return redirect('class_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClassForm(instance=class_obj)
    return render(request, 'edit_class.html', {'form': form, 'class_obj': class_obj})


@admin_required
def delete_class(request, id):
    class_obj = get_object_or_404(Class, id=id)
    if request.method == 'POST':
        class_name = class_obj.name
        class_obj.delete()
        messages.success(request, f'Class "{class_name}" deleted successfully!')
        return redirect('class_list')

    messages.warning(request, 'Invalid request method.')
    return redirect('class_list')


@login_required
def class_details(request, id):
    class_obj = get_object_or_404(Class, id=id)

    # Check permissions
    if request.user.is_admin:
        # Admin can view all classes - no restriction
        pass
    elif request.user.is_teacher:
        teacher = get_object_or_404(Teacher, user=request.user)
        # Teacher can only view classes in their department or where they are class teacher
        if class_obj.department != teacher.department and class_obj.class_teacher != teacher:
            messages.error(request, 'You are not authorized to view this class.')
            return redirect('teacher_dashboard')
    else:
        # Students or other users not allowed
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('login_view')

    # Get class data (this should be outside the if conditions)
    students = class_obj.students.select_related('user').all()
    timetable = class_obj.timetables.select_related('subject', 'teacher').all()

    return render(request, 'class_details.html', {
        'class_obj': class_obj,
        'students': students,  # Fixed variable name from 'student' to 'students'
        'timetable': timetable
    })


# Admin Teacher attendance
@admin_required
def admin_teacher_attendance(request):
    if request.method == 'POST':
        # Handle form submission (save attendance)
        if 'date' in request.POST:
            # This is the date selection form submission
            form = TeacherAttendanceDateForm(request.POST)
            if form.is_valid():
                date = form.cleaned_data['date']

                # Get all teachers
                teachers = Teacher.objects.all().select_related('user', 'department')

                # Get existing attendance for this date to pre-populate
                existing_attendance_records = TeacherAttendance.objects.filter(
                    date=date
                ).select_related('teacher')

                # Create teacher data with existing attendance
                teacher_data = []
                for teacher in teachers:
                    existing_att = None
                    for att in existing_attendance_records:
                        if att.teacher_id == teacher.id:
                            existing_att = att
                            break

                    teacher_data.append({
                        'teacher': teacher,
                        'existing_attendance': existing_att
                    })

                return render(request, 'admin_teacher_attendance.html', {
                    'teacher_data': teacher_data,
                    'date': date,
                    'show_attendance_form': True,
                })

        else:
            # This is the attendance marking form submission
            date_str = request.POST.get('attendance_date')

            # Parse date from YYYY-MM-DD format
            from datetime import datetime
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid date format.')
                return redirect('admin_teacher_attendance')

            teachers = Teacher.objects.all()
            saved_count = 0
            current_user = request.user

            for teacher in teachers:
                status = request.POST.get(f'status_{teacher.id}', 'absent')
                remarks = request.POST.get(f'remarks_{teacher.id}', '')

                # Create or update attendance record
                attendance, created = TeacherAttendance.objects.update_or_create(
                    teacher=teacher,
                    date=date,
                    defaults={
                        'status': status,
                        'department': teacher.department,
                        'remarks': remarks,
                        'recorded_by': current_user,
                    }
                )
                saved_count += 1

            messages.success(request, f'Attendance saved for {saved_count} teachers on {date.strftime("%b %d, %Y")}!')
            return redirect('admin_teacher_attendance_view')

    else:
        # GET request - show date selection form
        form = TeacherAttendanceDateForm()

    return render(request, 'admin_teacher_attendance.html', {
        'form': form,
        'show_attendance_form': False,
    })


@admin_required
def admin_teacher_attendance_view(request):
    attendance_records = TeacherAttendance.objects.all().select_related(
        'teacher', 'teacher__user', 'department', 'recorded_by'
    ).order_by('-date')

    # Check if user clicked on a specific date
    selected_date = request.GET.get('date')
    date_details = None

    if selected_date:
        try:
            from datetime import date
            selected_date_obj = date.fromisoformat(selected_date)
            date_records = [r for r in attendance_records if r.date == selected_date_obj]
            date_details = {
                'date': selected_date_obj,
                'records': date_records
            }
        except ValueError:
            selected_date = None

    # Group attendance by date for summary
    attendance_summary = {}
    for record in attendance_records:
        date_str = record.date.isoformat()
        if date_str not in attendance_summary:
            attendance_summary[date_str] = {
                'date': record.date,
                'total_teachers': 0,
                'present': 0,
                'absent': 0,
                'on_leave': 0,
                'half_day': 0,
            }

        # Update counts
        attendance_summary[date_str]['total_teachers'] += 1
        if record.status == 'present':
            attendance_summary[date_str]['present'] += 1
        elif record.status == 'absent':
            attendance_summary[date_str]['absent'] += 1
        elif record.status == 'on_leave':
            attendance_summary[date_str]['on_leave'] += 1
        elif record.status == 'half_day':
            attendance_summary[date_str]['half_day'] += 1

    # Convert to list and sort
    summary_list = sorted(
        attendance_summary.values(),
        key=lambda x: x['date'],
        reverse=True
    )

    return render(request, 'admin_teacher_attendance_view.html', {
        'attendance_summary': summary_list,
        'date_details': date_details,
        'selected_date': selected_date,
    })


# Admin schedule timetable
@admin_required
def class_wise_timetable(request, class_id=None):
    """View weekly timetable for a specific class"""
    if class_id:
        class_obj = get_object_or_404(Class, id=class_id)
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        periods = Timetable.PERIOD_CHOICES

        # Get timetable data for the class - FIXED STRUCTURE
        timetable_data = {}
        for day in days:
            timetable_data[day] = {}
            for period_num, period_display in periods:
                try:
                    # Get the first entry for this time slot (or handle multiple)
                    entry = Timetable.objects.filter(
                        class_obj=class_obj,
                        day=day,
                        period=period_num
                    ).first()  # Use first() instead of get() to avoid MultipleObjectsReturned
                    timetable_data[day][period_num] = entry
                except Exception as e:
                    timetable_data[day][period_num] = None

        return render(request, 'timetable/class_wise_timetable.html', {
            'class_obj': class_obj,
            'timetable_data': timetable_data,
            'days': days,
            'periods': periods,
        })
    else:
        # Show class selection
        classes = Class.objects.all()
        return render(request, 'timetable/class_selection.html', {
            'classes': classes,
            'title': 'Select Class to View Timetable'
        })


@admin_required
def teacher_wise_timetable(request, teacher_id=None):
    """View weekly timetable for a specific teacher"""
    if teacher_id:
        teacher = get_object_or_404(Teacher, id=teacher_id)
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        periods = Timetable.PERIOD_CHOICES

        # Get timetable data for the teacher
        timetable_data = {}
        for day in days:
            timetable_data[day] = {}
            for period_num, period_display in periods:
                try:
                    entry = Timetable.objects.get(
                        teacher=teacher,
                        day=day,
                        period=period_num
                    )
                    timetable_data[day][period_num] = entry
                except Timetable.DoesNotExist:
                    timetable_data[day][period_num] = None

        return render(request, 'timetable/teacher_wise_timetable.html', {
            'teacher': teacher,
            'timetable_data': timetable_data,
            'days': days,
            'periods': periods,
        })
    else:
        # Show teacher selection
        teachers = Teacher.objects.all()
        return render(request, 'timetable/teacher_selection.html', {
            'teachers': teachers,
            'title': 'Select Teacher to View Timetable'
        })


@admin_required
def timetable_create(request, class_id=None):
    if class_id:
        class_obj = get_object_or_404(Class, id=class_id)

        # MODIFY: Load existing data if timetable exists
        existing_timetable = Timetable.objects.filter(class_obj=class_obj).exists()
        existing_data = {}

        if existing_timetable:
            # ADD: Load existing timetable entries
            existing_entries = Timetable.objects.filter(class_obj=class_obj)
            for entry in existing_entries:
                key = f"{entry.day}_{entry.period}"
                existing_data[key] = {
                    'subject_id': entry.subject_id,
                    'teacher_id': entry.teacher_id,
                    'room_number': entry.room_number
                }

        subjects = Subject.objects.filter(department=class_obj.department)

        # Create teachers grouped by subjects they can teach
        teachers_by_subject = {}
        for subject in subjects:
            teachers_by_subject[subject.id] = Teacher.objects.filter(subjects=subject)

        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        periods = Timetable.PERIOD_CHOICES

        if request.method == 'POST':
            created_count = 0
            errors = []

            # ✅ MODIFY: Only delete if we're overwriting existing timetable
            if existing_timetable:
                # Optional: Add confirmation message
                messages.warning(request, f'Overwriting existing timetable for {class_obj.name}')

            # Delete existing entries (keep this but now it's conditional)
            Timetable.objects.filter(class_obj=class_obj).delete()

            # Process each period
            for day in days:
                for period_num, period_display in periods:
                    subject_id = request.POST.get(f'{day}_{period_num}_subject')
                    teacher_id = request.POST.get(f'{day}_{period_num}_teacher')
                    room_number = request.POST.get(f'{day}_{period_num}_room', '').strip()

                    # Only create if both subject and teacher are selected
                    if subject_id and teacher_id:
                        try:
                            # Validate teacher can teach this subject
                            subject = Subject.objects.get(id=subject_id)
                            teacher = Teacher.objects.get(id=teacher_id)

                            if not teacher.subjects.filter(id=subject.id).exists():
                                errors.append(
                                    f"{day.title()} period {period_num}: {teacher.get_name} cannot teach {subject.name}")
                                continue

                            # ✅ ADD: Check for teacher conflicts
                            teacher_conflict = Timetable.objects.filter(
                                teacher=teacher,
                                day=day,
                                period=period_num
                            ).exists()

                            if teacher_conflict:
                                errors.append(
                                    f"{day.title()} period {period_num}: {teacher.get_name} is already assigned to another class")
                                continue

                            # Create new entry
                            timetable = Timetable(
                                class_obj=class_obj,
                                subject_id=subject_id,
                                teacher_id=teacher_id,
                                day=day,
                                period=period_num,
                                room_number=room_number if room_number else None
                            )
                            timetable.save()
                            created_count += 1

                        except Exception as e:
                            errors.append(f"{day.title()} period {period_num}: {str(e)}")

            # Show results
            if created_count > 0:
                messages.success(request,
                                 f'Successfully created {created_count} timetable entries for {class_obj.name}')
            if errors:
                for error in errors:
                    messages.error(request, error)

            return redirect('class_wise_timetable_detail', class_id=class_id)

        return render(request, 'timetable/bulk_timetable_form.html', {
            'class_obj': class_obj,
            'subjects': subjects,
            'teachers_by_subject': teachers_by_subject,
            'days': days,
            'periods': periods,
            # ✅ FIX: Dynamic title based on mode
            'title': f'{"Edit" if existing_timetable else "Create"} Timetable - {class_obj.name}',
            'existing_timetable': existing_timetable,
            'existing_data': existing_data,
            'mode': 'edit' if existing_timetable else 'create'
        })


@admin_required
def timetable_dashboard(request):
    """Admin timetable dashboard with quick overview"""
    classes = Class.objects.all()
    teachers = Teacher.objects.all()

    # Get recent timetable entries
    recent_entries = Timetable.objects.select_related(
        'class_obj', 'subject', 'teacher'
    ).order_by('-id')[:5]

    # Get classes without timetable
    classes_with_timetable = Class.objects.filter(
        timetables__isnull=False
    ).distinct()
    classes_without_timetable = Class.objects.exclude(
        id__in=classes_with_timetable.values('id')
    )

    return render(request, 'timetable/timetable_dashboard.html', {
        'classes': classes,
        'teachers': teachers,
        'recent_entries': recent_entries,
        'classes_with_timetable': classes_with_timetable,
        'classes_without_timetable': classes_without_timetable,
        'total_entries': Timetable.objects.count(),
    })


#Admin Account Manage
@admin_required
def admin_account_dashboard(request):
    # Current month summary
    current_summary = Account.get_current_month_summary()

    # Quick stats
    total_pending_fees = Account.objects.filter(
        transaction_type='student_fee',
        payment_status__in=['pending', 'partial']
    ).count()

    total_pending_salaries = Account.objects.filter(
        transaction_type='teacher_salary',
        payment_status__in=['pending', 'partial']
    ).count()

    total_pending_expenses = Account.objects.filter(
        transaction_type='school_expense',
        payment_status__in=['pending', 'partial']
    ).count()

    # Recent transactions
    recent_transactions = Account.objects.all().order_by('-created_at')[:10]

    # Overdue fees (past due date)
    overdue_fees = Account.objects.filter(
        transaction_type='student_fee',
        due_date__lt=timezone.now().date(),
        payment_status__in=['pending', 'partial']
    )

    context = {
        'current_summary': current_summary,
        'total_pending_fees': total_pending_fees,
        'total_pending_salaries': total_pending_salaries,
        'total_pending_expenses': total_pending_expenses,
        'recent_transactions': recent_transactions,
        'overdue_fees': overdue_fees,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@admin_required
def admin_teacher_salaries(request):
    """Main view to see all teacher salaries with filters"""
    # Get current month
    current_month = timezone.now().strftime('%B %Y')
    month_filter = request.GET.get('month', current_month)

    # Filter by payment status
    status_filter = request.GET.get('status', '')

    # Get all teachers with salary data
    teachers = Teacher.objects.all().select_related('user', 'department')
    teachers_data = []

    for teacher in teachers:
        # Get salary record for selected month
        salary_record = Account.objects.filter(
            transaction_type='teacher_salary',
            teacher=teacher,
            month=month_filter
        ).first()

        teacher_data = {
            'teacher': teacher,
            'base_salary': teacher.salary,
            'salary_record': salary_record,
            'payment_status': salary_record.payment_status if salary_record else 'not_generated',
        }

        # Apply status filter
        if status_filter:
            if status_filter == 'not_generated' and not salary_record:
                teachers_data.append(teacher_data)
            elif status_filter == salary_record.payment_status if salary_record else '':
                teachers_data.append(teacher_data)
        else:
            teachers_data.append(teacher_data)

    # Get unique months for dropdown
    months = Account.objects.filter(
        transaction_type='teacher_salary'
    ).values_list('month', flat=True).distinct().order_by('-month')

    context = {
        'teachers_data': teachers_data,
        'current_month': current_month,
        'selected_month': month_filter,
        'selected_status': status_filter,
        'months': months,
    }
    return render(request, 'accounts/admin_teacher_salaries.html', context)


@admin_required
def admin_record_salary_payment(request, account_id):
    """Update payment status with details"""
    salary_record = get_object_or_404(Account, pk=account_id, transaction_type='teacher_salary')

    if request.method == 'POST':
        form = TeacherSalaryForm(request.POST, instance=salary_record)
        if form.is_valid():
            form.save()
            status = form.cleaned_data.get('payment_status')
            if status == 'paid':
                messages.success(request, f'Salary marked as PAID for {salary_record.teacher.get_name}')
            else:
                messages.info(request, f'Salary marked as PENDING for {salary_record.teacher.get_name}')
            return redirect('admin_teacher_salaries')
    else:
        form = TeacherSalaryForm(instance=salary_record)

    context = {
        'form': form,
        'salary_record': salary_record,
    }
    return render(request, 'accounts/admin_record_salary_payment.html', context)


@admin_required
def admin_mark_salary_paid(request, account_id):
    """Quick mark salary as paid (one-click)"""
    salary_record = get_object_or_404(Account, pk=account_id, transaction_type='teacher_salary')

    if request.method == 'POST':
        salary_record.payment_status = 'paid'
        salary_record.paid_amount = salary_record.amount
        salary_record.payment_date = timezone.now().date()
        salary_record.payment_method = 'cash'  # Default payment method
        salary_record.save()

        messages.success(request, f'Salary marked as PAID for {salary_record.teacher.get_name}')

    return redirect('admin_teacher_salaries')


@admin_required
def admin_mark_salary_pending(request, account_id):
    """Quick mark salary as pending (one-click)"""
    salary_record = get_object_or_404(Account, pk=account_id, transaction_type='teacher_salary')

    if request.method == 'POST':
        salary_record.payment_status = 'pending'
        salary_record.paid_amount = 0
        salary_record.payment_date = None
        salary_record.payment_method = None
        salary_record.save()

        messages.info(request, f'Salary marked as PENDING for {salary_record.teacher.get_name}')

    return redirect('admin_teacher_salaries')


@admin_required
def admin_generate_payment_slip(request, account_id):
    """Generate payment receipt/slip"""
    salary_record = get_object_or_404(Account, pk=account_id, transaction_type='teacher_salary')

    context = {
        'salary_record': salary_record,
        'school_name': 'PreSkool',  # You can make this dynamic
        'current_date': timezone.now().date(),
    }
    return render(request, 'accounts/admin_payment_slip.html', context)


@admin_required
def admin_salary_history(request, teacher_id):
    """View salary payment history for a specific teacher"""
    teacher = get_object_or_404(Teacher, pk=teacher_id)

    # Get all salary records for this teacher
    salary_history = Account.objects.filter(
        transaction_type='teacher_salary',
        teacher=teacher
    ).order_by('-month', '-created_at')

    # Calculate summary
    total_records = salary_history.count()
    paid_records = salary_history.filter(payment_status='paid').count()
    pending_records = salary_history.filter(payment_status='pending').count()

    total_amount = sum([record.amount for record in salary_history])
    total_paid = sum([record.paid_amount for record in salary_history])

    context = {
        'teacher': teacher,
        'salary_history': salary_history,
        'total_records': total_records,
        'paid_records': paid_records,
        'pending_records': pending_records,
        'total_amount': total_amount,
        'total_paid': total_paid,
    }
    return render(request, 'accounts/admin_salary_history.html', context)


@admin_required
def admin_generate_all_salaries(request):
    """Generate salary records for all teachers for current month"""
    if request.method == 'POST':
        current_month = timezone.now().strftime('%B %Y')

        created_count, updated_count, errors = Account.generate_monthly_salaries(
            month=current_month,
            created_by=request.user,
            overwrite=False
        )

        if created_count > 0:
            messages.success(request, f'Generated {created_count} new salary records for {current_month}')
        if updated_count > 0:
            messages.info(request, f'Updated {updated_count} existing salary records')
        if not created_count and not updated_count:
            messages.info(request, 'All salary records are already generated')

        if errors:
            for error in errors:
                messages.error(request, error)

    return redirect('admin_teacher_salaries')

#student fee
@admin_required
def admin_fee_class_list(request):
    """Display all classes for fee management"""
    classes = Class.objects.all().select_related('department', 'class_teacher').prefetch_related('students')

    # Add student count and fee summary for each class
    for class_obj in classes:
        class_obj.student_count = class_obj.students.count()

        # Calculate fee summary for this class - FIXED: Use 'student_fee' consistently
        students = class_obj.students.all()
        total_yearly_fee = class_obj.yearly_fee * students.count() if class_obj.yearly_fee else 0

        # Get total paid from Account records
        total_paid = Account.objects.filter(
            student__in=students,
            transaction_type='student_fee'  # FIXED: Use 'student_fee'
        ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

        total_pending = total_yearly_fee - total_paid
        class_obj.fee_collected = total_paid
        class_obj.fee_pending = total_pending
        class_obj.total_yearly_fee = total_yearly_fee

    return render(request, 'accounts/admin_class_list.html', {
        'classes': classes
    })


@admin_required
def admin_class_student_fees(request, class_id):
    """Show all students in a class with their fee status"""
    class_obj = get_object_or_404(Class, id=class_id)
    students = class_obj.students.select_related('user').all()

    student_fees = []
    for student in students:
        # Get all fee payments for this student - FIXED: Use 'student_fee'
        fee_payments = Account.objects.filter(
            student=student,
            transaction_type='student_fee'  # FIXED: Use 'student_fee'
        ).order_by('-payment_date')

        total_paid = fee_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        balance = class_obj.yearly_fee - total_paid if class_obj.yearly_fee else 0

        # Determine payment status
        if class_obj.yearly_fee and total_paid >= class_obj.yearly_fee:
            status = 'paid'
            status_class = 'success'
            status_icon = '✅'
        elif total_paid == 0:
            status = 'pending'
            status_class = 'danger'
            status_icon = '⏳'
        else:
            status = 'partial'
            status_class = 'warning'
            status_icon = '⚠️'

        student_fees.append({
            'student': student,
            'total_paid': total_paid,
            'balance': balance,
            'status': status,
            'status_class': status_class,
            'status_icon': status_icon,
            'fee_payments': fee_payments,
            'yearly_fee': class_obj.yearly_fee or 0
        })

    # Calculate class fee summary
    total_students = students.count()
    fully_paid = len([s for s in student_fees if s['status'] == 'paid'])
    partial_paid = len([s for s in student_fees if s['status'] == 'partial'])
    pending = len([s for s in student_fees if s['status'] == 'pending'])

    total_collected = sum([s['total_paid'] for s in student_fees])
    total_pending = sum([s['balance'] for s in student_fees])

    return render(request, 'accounts/class_student_fees.html', {
        'class_obj': class_obj,
        'student_fees': student_fees,
        'total_students': total_students,
        'fully_paid': fully_paid,
        'partial_paid': partial_paid,
        'pending': pending,
        'total_collected': total_collected,
        'total_pending': total_pending
    })


@admin_required
def record_fee_payment(request, student_id):
    """Record fee payment with proper status handling"""
    student = get_object_or_404(Student, id=student_id)
    class_obj = student.Class

    # Calculate current fee status - FIXED: Use 'student_fee' consistently
    total_paid = Account.objects.filter(
        student=student,
        transaction_type='student_fee'
    ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    balance = class_obj.yearly_fee - total_paid if class_obj.yearly_fee else 0

    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payment_date = form.cleaned_data['payment_date']
            payment_method = form.cleaned_data['payment_method']
            notes = form.cleaned_data.get('notes', '')

            # Prevent overpayment
            if amount > balance:
                messages.error(request, f'Payment amount (₹{amount}) cannot exceed balance (₹{balance})')
            else:
                # Create payment record
                Account.objects.create(
                    student=student,
                    transaction_type='student_fee',
                    title=f"Fee Payment - {student.get_name}",
                    amount=amount,
                    paid_amount=amount,
                    payment_status='paid',
                    payment_method=payment_method,
                    payment_date=payment_date,
                    description=f"Fee payment - {notes}",
                    created_by=request.user,
                    class_obj=class_obj
                )

                messages.success(request, f'Payment of ₹{amount} recorded successfully!')
                return redirect('admin_class_student_fees', class_id=class_obj.id)
    else:
        form = FeePaymentForm()

    return render(request, 'accounts/record_fee_payment.html', {
        'form': form,
        'student': student,
        'class_obj': class_obj,
        'total_paid': total_paid,
        'balance': balance,
        'yearly_fee': class_obj.yearly_fee or 0
    })


@admin_required
def generate_fee_receipt(request, account_id):
    """Generate fee payment receipt"""
    payment = get_object_or_404(Account,
                                id=account_id,
                                transaction_type='student_fee'  # FIXED: Use 'student_fee'
                                )
    student = payment.student
    class_obj = student.Class

    # Calculate payment details - FIXED: Use 'student_fee'
    previous_payments = Account.objects.filter(
        student=student,
        transaction_type='student_fee',
        payment_date__lt=payment.payment_date
    ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

    balance_before = class_obj.yearly_fee - previous_payments
    balance_after = balance_before - payment.paid_amount

    context = {
        'payment': payment,
        'student': student,
        'class_obj': class_obj,
        'previous_payments': previous_payments,
        'balance_before': balance_before,
        'balance_after': balance_after,
        'receipt_date': timezone.now().date(),
        'receipt_number': f"FEE{payment.id:06d}",
    }

    return render(request, 'accounts/fee_receipt.html', context)


@admin_required
def student_fee_history(request, student_id):
    """View complete fee history for a student"""
    student = get_object_or_404(Student, id=student_id)
    class_obj = student.Class

    # Get all fee payments - FIXED: Use 'student_fee'
    fee_payments = Account.objects.filter(
        student=student,
        transaction_type='student_fee'
    ).order_by('-payment_date')

    # Calculate summary - FIXED: Use paid_amount
    total_paid = fee_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    balance = class_obj.yearly_fee - total_paid if class_obj.yearly_fee else 0

    payment_summary = {
        'yearly_fee': class_obj.yearly_fee or 0,
        'total_paid': total_paid,
        'balance': balance,
        'payment_count': fee_payments.count(),
        'last_payment': fee_payments.first().payment_date if fee_payments.exists() else None
    }

    return render(request, 'accounts/student_fee_history.html', {
        'student': student,
        'class_obj': class_obj,
        'fee_payments': fee_payments,
        'payment_summary': payment_summary
    })

#other expanses and report
@admin_required
def record_expense(request):
    """Record school expenses"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.transaction_type = 'school_expense'
            expense.payment_status = 'paid'  # Expenses are immediately paid
            expense.paid_amount = expense.amount
            expense.created_by = request.user
            expense.save()

            messages.success(request, f'Expense of ₹{expense.amount} recorded successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()

    return render(request, 'accounts/record_expense.html', {'form': form})


@admin_required
def expense_list(request):
    """View all expenses with filters"""
    expenses = Account.objects.filter(transaction_type='school_expense').order_by('-payment_date')

    # Filters
    category_filter = request.GET.get('category')
    month_filter = request.GET.get('month')

    if category_filter:
        expenses = expenses.filter(expense_category=category_filter)

    # Summary calculations
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # Category-wise summary
    category_summary = Account.objects.filter(
        transaction_type='school_expense'
    ).values('expense_category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    return render(request, 'accounts/expense_list.html', {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'category_summary': category_summary,
        'expense_categories': Account.EXPENSE_CATEGORY,
    })


@admin_required
def financial_report(request):
    """Generate complete financial report"""
    # Get date range (default: current month)
    from datetime import datetime
    today = timezone.now().date()
    first_day = today.replace(day=1)

    # Get filters from request
    start_date = request.GET.get('start_date', first_day.isoformat())
    end_date = request.GET.get('end_date', today.isoformat())

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = first_day
        end_date = today

    # INCOME Calculations
    fee_income = Account.objects.filter(
        transaction_type='student_fee',
        payment_date__range=[start_date, end_date],
        payment_status='paid'
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    total_income = fee_income

    # EXPENSE Calculations
    salary_expenses = Account.objects.filter(
        transaction_type='teacher_salary',
        payment_date__range=[start_date, end_date],
        payment_status='paid'
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    school_expenses = Account.objects.filter(
        transaction_type='school_expense',
        payment_date__range=[start_date, end_date],
        payment_status='paid'
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    total_expenses = salary_expenses + school_expenses

    # Category-wise expense breakdown
    expense_by_category = Account.objects.filter(
        transaction_type='school_expense',
        payment_date__range=[start_date, end_date]
    ).values('expense_category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Net Balance
    net_balance = total_income - total_expenses

    # Recent transactions (last 10)
    recent_transactions = Account.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'teacher').order_by('-payment_date')[:10]

    return render(request, 'accounts/financial_report.html', {
        'start_date': start_date,
        'end_date': end_date,
        'fee_income': fee_income,
        'total_income': total_income,
        'salary_expenses': salary_expenses,
        'school_expenses': school_expenses,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'expense_by_category': expense_by_category,
        'recent_transactions': recent_transactions,
    })


@admin_required
def delete_expense(request, expense_id):
    """Delete an expense record"""
    expense = get_object_or_404(Account, id=expense_id, transaction_type='school_expense')

    if request.method == 'POST':
        amount = expense.amount
        expense.delete()
        messages.success(request, f'Expense of ₹{amount} deleted successfully!')
        return redirect('expense_list')

    return render(request, 'accounts/delete_expense.html', {'expense': expense})







# Teacher Dashboard Views
@teacher_required
def teacher_dashboard(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    # Different queries based on teacher type
    if teacher.is_hod:
        # HOD sees all students in department
        my_students = Student.objects.filter(department=teacher.department)
        total_teachers = Teacher.objects.filter(department=teacher.department).count()
    else:
        # Regular teacher sees only students in their assigned classes
        teacher_classes = Class.objects.filter(class_teacher=teacher)
        if teacher_classes.exists():
            my_students = Student.objects.filter(Class__in=teacher_classes)
        else:
            my_students = Student.objects.none()
        total_teachers = None

    # Get statistics for dashboard
    total_students = my_students.count()
    recent_students = my_students.select_related('user').order_by('-created_at')[:5]

    context = {
        'teacher': teacher,
        'total_students': total_students,
        'recent_students': recent_students,
        'total_teachers': total_teachers,  # Only for HOD
    }
    return render(request, 'teacher/teacher_dashboard.html', context)


@teacher_required
def teacher_students(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    # Different query based on teacher type
    if teacher.is_hod:
        students = Student.objects.filter(department=teacher.department).select_related('user')
    else:
        teacher_classes = Class.objects.filter(class_teacher=teacher)
        if teacher_classes.exists():
            students = Student.objects.filter(Class__in=teacher_classes).select_related('user')
        else:
            students = Student.objects.none()

    return render(request, 'teacher/teacher_students.html', {
        'students': students,
        'teacher': teacher
    })


@teacher_required
def teacher_student_details(request, id):
    teacher = get_object_or_404(Teacher, user=request.user)
    student = get_object_or_404(Student, id=id, department=teacher.department)

    return render(request, 'teacher/teacher_student_details.html', {
        'student': student,
        'teacher': teacher
    })


@teacher_required
def teacher_add_student(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    if request.method == 'POST':
        user_form = StudentSignUpForm(request.POST, request.FILES)
        student_form = StudentForm(request.POST)

        if user_form.is_valid() and student_form.is_valid():
            # Create user with student type
            user = user_form.save()

            # Create student profile - automatically assign to teacher's department
            student = student_form.save(commit=False)
            student.user = user
            student.department = teacher.department  # Auto-assign to teacher's department
            student.save()

            messages.success(request, f'Student {user.get_full_name()} added successfully!')
            return redirect('teacher_students')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = StudentSignUpForm()
        student_form = StudentForm(initial={'department': teacher.department})
        # Hide department field since it's auto-assigned
        student_form.fields['department'].widget = forms.HiddenInput()

    return render(request, 'teacher/teacher_add_student.html', {
        'user_form': user_form,
        'student_form': student_form,
        'teacher': teacher,
    })


@teacher_required
def teacher_edit_student(request, id):
    teacher = get_object_or_404(Teacher, user=request.user)
    student = get_object_or_404(Student, id=id, department=teacher.department)
    user = student.user

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, request.FILES, instance=user)
        student_form = StudentForm(request.POST, instance=student)

        if user_form.is_valid() and student_form.is_valid():
            user = user_form.save()
            student = student_form.save(commit=False)
            student.department = teacher.department  # Ensure student stays in teacher's department
            student.save()

            if user_form.cleaned_data.get('password1'):
                messages.success(request, f'Student {user.get_full_name()} updated successfully with new password!')
            else:
                messages.success(request, f'Student {user.get_full_name()} updated successfully!')
            return redirect('teacher_students')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserEditForm(instance=user)
        student_form = StudentForm(instance=student)
        # Hide department field since it's fixed
        student_form.fields['department'].widget = forms.HiddenInput()

    return render(request, 'teacher/teacher_edit_student.html', {
        'user_form': user_form,
        'student_form': student_form,
        'student': student,
        'teacher': teacher,
    })


@teacher_required
def teacher_delete_student(request, id):
    teacher = get_object_or_404(Teacher, user=request.user)
    student = get_object_or_404(Student, id=id, department=teacher.department)

    if request.method == 'POST':
        user_name = student.user.get_full_name()
        student.user.delete()
        messages.success(request, f'Student {user_name} deleted successfully!')
        return redirect('teacher_students')

    messages.warning(request, 'Invalid request method.')
    return redirect('teacher_students')


# HOD-specific views
@teacher_required
def teacher_department_view(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    # Only HOD can access department details
    if not teacher.is_hod:
        messages.error(request, "You don't have permission to access department details.")
        return redirect('teacher_dashboard')

    department = teacher.hod_department
    department_students = Student.objects.filter(department=department)
    department_teachers = Teacher.objects.filter(department=department)

    context = {
        'teacher': teacher,
        'department': department,
        'department_students': department_students,
        'department_teachers': department_teachers,
    }
    return render(request, 'teacher/teacher_department.html', context)


@teacher_required
def hod_department_attendance(request):
    """HOD can view all department attendance class-wise"""
    teacher = get_object_or_404(Teacher, user=request.user)

    # Only HOD can access this view
    if not teacher.is_hod:
        messages.error(request, "You don't have permission to view department attendance.")
        return redirect('teacher_dashboard')

    department = teacher.department

    # Get filter parameters
    selected_date = request.GET.get('date')
    selected_class = request.GET.get('class')

    # Default to today if no date selected
    from datetime import date, timedelta
    if selected_date:
        try:
            selected_date = date.fromisoformat(selected_date)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    # Get all classes in department
    department_classes = Class.objects.filter(department=department).order_by('name')

    # Filter by selected class if provided
    if selected_class:
        selected_class_obj = get_object_or_404(Class, id=selected_class, department=department)
        department_classes = [selected_class_obj]

    # Get attendance summary for each class
    class_attendance_summary = []

    for class_obj in department_classes:
        # Get students in this class
        students = Student.objects.filter(Class=class_obj)
        students_count = students.count()

        # Get attendance records for this class on selected date
        attendance_records = StudentAttendance.objects.filter(
            class_obj=class_obj,
            date=selected_date
        ).select_related('student', 'student__user')

        # Calculate statistics
        present_count = attendance_records.filter(status='present').count()
        absent_count = attendance_records.filter(status='absent').count()
        on_leave_count = attendance_records.filter(status='on_leave').count()
        half_day_count = attendance_records.filter(status='half_day').count()
        not_recorded_count = students_count - (present_count + absent_count + on_leave_count + half_day_count)

        # Calculate percentage
        attendance_percentage = (present_count / students_count * 100) if students_count > 0 else 0

        # Get detailed attendance for this class
        detailed_attendance = []
        for student in students:
            attendance_record = attendance_records.filter(student=student).first()
            detailed_attendance.append({
                'student': student,
                'attendance': attendance_record,
                'status': attendance_record.status if attendance_record else 'Not Recorded'
            })

        class_attendance_summary.append({
            'class_obj': class_obj,
            'students_count': students_count,
            'present_count': present_count,
            'absent_count': absent_count,
            'on_leave_count': on_leave_count,
            'half_day_count': half_day_count,
            'not_recorded_count': not_recorded_count,
            'attendance_percentage': round(attendance_percentage, 1),
            'class_teacher': class_obj.class_teacher.get_name if class_obj.class_teacher else "Not assigned",
            'is_my_class': class_obj in teacher.assigned_classes,  # Check if HOD is also class teacher
            'detailed_attendance': detailed_attendance,
            'total_recorded': present_count + absent_count + on_leave_count + half_day_count
        })

    context = {
        'teacher': teacher,
        'department': department,
        'selected_date': selected_date,
        'selected_class': selected_class,
        'department_classes': Class.objects.filter(department=department).order_by('name'),
        'class_attendance_summary': class_attendance_summary,
    }

    return render(request, 'attendance/hod_department_attendance.html', context)


# Student attendance
@teacher_required
def teacher_mark_student_attendance(request):
    """Teacher marks attendance for students in their class"""
    teacher = get_object_or_404(Teacher, user=request.user)

    # Get classes taught by this teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)

    if request.method == 'POST':
        form = StudentAttendanceDateForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            class_obj = form.cleaned_data['class_obj']

            # Verify teacher teaches this class
            if class_obj not in teacher_classes:
                messages.error(request, 'You can only mark attendance for your assigned classes!')
                return redirect('teacher_dashboard')

            # Get students in this class
            students = Student.objects.filter(Class=class_obj).select_related('user')

            # Get existing attendance and prepare simple data structure
            existing_attendance_records = StudentAttendance.objects.filter(
                date=date,
                class_obj=class_obj
            ).select_related('student')

            # Create a simple list of student data with their existing attendance
            student_data = []
            for student in students:
                existing_att = None
                for att in existing_attendance_records:
                    if att.student_id == student.id:
                        existing_att = att
                        break

                student_data.append({
                    'student': student,
                    'existing_attendance': existing_att
                })

            return render(request, 'attendance/teacher_mark_students.html', {
                'student_data': student_data,
                'date': date,
                'class_obj': class_obj,
                'teacher': teacher,
            })
    else:
        form = StudentAttendanceDateForm()
        # Only show classes taught by this teacher
        form.fields['class_obj'].queryset = teacher_classes

    return render(request, 'attendance/teacher_mark_attendance.html', {
        'form': form,
        'teacher': teacher,
    })


@teacher_required
def teacher_save_student_attendance(request):
    """Teacher saves student attendance"""
    teacher = get_object_or_404(Teacher, user=request.user)

    if request.method == 'POST':
        date_str = request.POST.get('date')
        class_obj_id = request.POST.get('class_obj')

        # Parse date from YYYY-MM-DD format
        from datetime import datetime
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('teacher_mark_student_attendance')

        class_obj = get_object_or_404(Class, id=class_obj_id)

        # Authorization check - ensure teacher teaches this class
        if class_obj.class_teacher != teacher:
            messages.error(request, 'You are not authorized to mark attendance for this class!')
            return redirect('teacher_dashboard')

        students = Student.objects.filter(Class=class_obj)
        saved_count = 0

        for student in students:
            status = request.POST.get(f'status_{student.id}', 'absent')  # Default to absent if not specified
            remarks = request.POST.get(f'remarks_{student.id}', '')

            # Create or update attendance record
            attendance, created = StudentAttendance.objects.update_or_create(
                student=student,
                date=date,
                defaults={
                    'status': status,
                    'class_obj': class_obj,
                    'remarks': remarks,
                    'recorded_by': teacher,
                }
            )
            saved_count += 1

        messages.success(request, f'Attendance saved for {saved_count} students in {class_obj.name}!')
        return redirect('teacher_student_attendance_view')

    messages.error(request, 'Invalid request method.')
    return redirect('teacher_mark_student_attendance')


@teacher_required
def teacher_student_attendance_view(request):
    """Teacher views attendance records grouped by date"""
    teacher = get_object_or_404(Teacher, user=request.user)

    # Get classes taught by this teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)

    # Get recent attendance (last 30 days for better performance)
    from datetime import date, timedelta
    thirty_days_ago = date.today() - timedelta(days=30)

    attendance_records = StudentAttendance.objects.filter(
        class_obj__in=teacher_classes,
        date__gte=thirty_days_ago
    ).select_related(
        'student',
        'student__user',
        'class_obj',
        'recorded_by'
    ).order_by('-date')

    # Check if user clicked on a specific date
    selected_date = request.GET.get('date')
    date_details = None

    if selected_date:
        try:
            # Filter records for the selected date
            selected_date_obj = date.fromisoformat(selected_date)
            date_records = [r for r in attendance_records if r.date == selected_date_obj]
            date_details = {
                'date': selected_date_obj,
                'records': date_records
            }
        except ValueError:
            selected_date = None

    # Group attendance by date for summary
    attendance_summary = {}
    for record in attendance_records:
        date_str = record.date.isoformat()
        if date_str not in attendance_summary:
            attendance_summary[date_str] = {
                'date': record.date,
                'total_students': 0,
                'present': 0,
                'absent': 0,
                'on_leave': 0,
                'half_day': 0,
            }

        # Update counts
        attendance_summary[date_str]['total_students'] += 1
        if record.status == 'present':
            attendance_summary[date_str]['present'] += 1
        elif record.status == 'absent':
            attendance_summary[date_str]['absent'] += 1
        elif record.status == 'on_leave':
            attendance_summary[date_str]['on_leave'] += 1
        elif record.status == 'half_day':
            attendance_summary[date_str]['half_day'] += 1

    # Convert to list and sort
    summary_list = sorted(
        attendance_summary.values(),
        key=lambda x: x['date'],
        reverse=True
    )

    return render(request, 'attendance/teacher_student_attendance_view.html', {
        'attendance_summary': summary_list,
        'date_details': date_details,
        'selected_date': selected_date,
        'teacher_classes': teacher_classes,
        'teacher': teacher,
    })


@teacher_required
def teacher_timetable_view(request):
    """Teacher views their own weekly timetable - Simple dynamic version"""
    teacher = get_object_or_404(Teacher, user=request.user)

    # Use the actual choices from the model
    days = [choice[0] for choice in Timetable.DAY_CHOICES]
    periods = Timetable.PERIOD_CHOICES

    # Get all timetable entries
    timetable_entries = Timetable.objects.filter(
        teacher=teacher
    ).select_related('subject', 'class_obj')

    # Create dynamic structure
    timetable_data = []

    for period_num, period_display in periods:
        period_row = {
            'period_num': period_num,
            'period_display': period_display,
            'days': {}
        }

        # Find entries for each day in this period
        for day in days:
            entry = timetable_entries.filter(day=day, period=period_num).first()
            period_row['days'][day] = entry

        timetable_data.append(period_row)

    return render(request, 'teacher/teacher_timetable.html', {
        'teacher': teacher,
        'timetable_data': timetable_data,
        'days': days,
        'title': 'My Weekly Timetable'
    })


@teacher_required
def teacher_student_fees_view(request):
    """Teacher views student fees for all their classes in one comprehensive table"""
    teacher = get_object_or_404(Teacher, user=request.user)

    # Get classes where this teacher is class teacher
    teacher_classes = Class.objects.filter(class_teacher=teacher)

    # Get all students from teacher's classes
    students = Student.objects.filter(Class__in=teacher_classes).select_related('user', 'Class')

    student_fee_data = []

    for student in students:
        # Get all fee payments for this student
        fee_payments = Account.objects.filter(
            student=student,
            transaction_type='student_fee'
        ).order_by('-payment_date')

        total_paid = fee_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        yearly_fee = student.Class.yearly_fee or 0
        balance = yearly_fee - total_paid

        # Determine payment status
        if yearly_fee and total_paid >= yearly_fee:
            status = 'paid'
            status_class = 'success'
        elif total_paid > 0:
            status = 'partial'
            status_class = 'warning'
        else:
            status = 'pending'
            status_class = 'danger'

        student_fee_data.append({
            'student': student,
            'class_name': student.Class.name,
            'yearly_fee': yearly_fee,
            'total_paid': total_paid,
            'balance': balance,
            'status': status,
            'status_class': status_class,
            'last_payment_date': fee_payments.first().payment_date if fee_payments.exists() else None,
            'payment_count': fee_payments.count()
        })

    # Calculate overall summary
    total_students = len(student_fee_data)
    total_collected = sum(item['total_paid'] for item in student_fee_data)
    total_pending = sum(item['balance'] for item in student_fee_data)

    # Sort student data by class and student name
    student_fee_data.sort(key=lambda x: (x['class_name'], x['student'].get_name))

    return render(request, 'teacher/teacher_student_fees.html', {
        'teacher': teacher,
        'student_fee_data': student_fee_data,
        'total_students': total_students,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'title': 'Student Fee Records'
    })


# ========== TEACHER ASSIGNMENT VIEWS ==========

@teacher_required
def teacher_assignments(request):
    """List all assignments created by teacher"""
    teacher = get_object_or_404(Teacher, user=request.user)

    # Get assignments created by this teacher
    assignments = Assignment.objects.filter(teacher=teacher).select_related(
        'subject', 'class_obj'
    ).order_by('-created_at')

    # Create a list of assignment data with submission counts
    assignment_data = []
    for assignment in assignments:
        submission_count = AssignmentSubmission.objects.filter(
            assignment=assignment
        ).count()
        total_students = assignment.class_obj.students.count()

        assignment_data.append({
            'assignment': assignment,
            'submission_count': submission_count,
            'total_students': total_students,
            'is_overdue': assignment.is_overdue,
        })

    return render(request, 'teacher/teacher_assignments.html', {
        'teacher': teacher,
        'assignment_data': assignment_data,
    })

@teacher_required
def teacher_create_assignment(request):
    """Create new assignment"""
    teacher = get_object_or_404(Teacher, user=request.user)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = teacher

            # Auto-assign subject and class based on teacher's timetable
            subject_id = request.POST.get('subject')
            class_id = request.POST.get('class_obj')

            if subject_id and class_id:
                assignment.subject_id = subject_id
                assignment.class_obj_id = class_id
                assignment.save()

                messages.success(request, f'Assignment "{assignment.title}" created successfully!')
                return redirect('teacher_assignments')
            else:
                messages.error(request, 'Please select subject and class')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignmentForm()

    # Get teacher's subjects and classes from timetable
    teacher_subjects = teacher.subjects.all()
    teacher_classes = Class.objects.filter(
        timetables__teacher=teacher
    ).distinct()

    return render(request, 'teacher/teacher_create_assignment.html', {
        'teacher': teacher,
        'form': form,
        'teacher_subjects': teacher_subjects,
        'teacher_classes': teacher_classes,
    })


@teacher_required
def teacher_assignment_detail(request, assignment_id):
    """View assignment details and submissions"""
    teacher = get_object_or_404(Teacher, user=request.user)
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)

    # Get all submissions for this assignment
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).select_related('student', 'student__user')

    # Get students who haven't submitted
    submitted_student_ids = submissions.values_list('student_id', flat=True)
    pending_students = Student.objects.filter(
        Class=assignment.class_obj
    ).exclude(id__in=submitted_student_ids)

    total_students = assignment.class_obj.students.count()
    submission_count = submissions.count()

    return render(request, 'teacher/teacher_assignment_detail.html', {
        'teacher': teacher,
        'assignment': assignment,
        'submissions': submissions,
        'pending_students': pending_students,
        'total_students': total_students,
        'submission_count': submission_count,
    })


@teacher_required
def teacher_delete_assignment(request, assignment_id):
    """Delete assignment"""
    teacher = get_object_or_404(Teacher, user=request.user)
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)

    assignment_title = assignment.title
    assignment.delete()
    messages.success(request, f'Assignment "{assignment_title}" deleted successfully!')
    return redirect('teacher_assignments')


# ========== TEACHER SYLLABUS VIEWS ==========

@teacher_required
def teacher_syllabus(request):
    """Manage syllabus for teacher's subjects"""
    teacher = get_object_or_404(Teacher, user=request.user)

    # Get syllabus topics for teacher's subjects
    syllabus_topics = Syllabus.objects.filter(
        teacher=teacher
    ).select_related('subject', 'class_obj').order_by('subject__name', 'target_date')

    # Group by subject
    syllabus_by_subject = {}
    for topic in syllabus_topics:
        subject_name = topic.subject.name
        if subject_name not in syllabus_by_subject:
            syllabus_by_subject[subject_name] = []
        syllabus_by_subject[subject_name].append(topic)

    return render(request, 'teacher/teacher_syllabus.html', {
        'teacher': teacher,
        'syllabus_by_subject': syllabus_by_subject,
    })


@teacher_required
def teacher_add_syllabus_topic(request):
    """Add new syllabus topic"""
    teacher = get_object_or_404(Teacher, user=request.user)

    if request.method == 'POST':
        form = SyllabusForm(request.POST, request.FILES)
        if form.is_valid():
            syllabus_topic = form.save(commit=False)
            syllabus_topic.teacher = teacher

            # Auto-assign subject and class
            subject_id = request.POST.get('subject')
            class_id = request.POST.get('class_obj')

            if subject_id and class_id:
                syllabus_topic.subject_id = subject_id
                syllabus_topic.class_obj_id = class_id
                syllabus_topic.save()

                messages.success(request, f'Syllabus topic "{syllabus_topic.topic_title}" added successfully!')
                return redirect('teacher_syllabus')
            else:
                messages.error(request, 'Please select subject and class')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SyllabusForm()

    # Get teacher's subjects and classes
    teacher_subjects = teacher.subjects.all()
    teacher_classes = Class.objects.filter(
        timetables__teacher=teacher
    ).distinct()

    return render(request, 'teacher/teacher_add_syllabus_topic.html', {
        'teacher': teacher,
        'form': form,
        'teacher_subjects': teacher_subjects,
        'teacher_classes': teacher_classes,
    })


@teacher_required
def teacher_edit_syllabus_topic(request, topic_id):
    """Edit syllabus topic"""
    teacher = get_object_or_404(Teacher, user=request.user)
    syllabus_topic = get_object_or_404(Syllabus, id=topic_id, teacher=teacher)

    if request.method == 'POST':
        form = SyllabusForm(request.POST, request.FILES, instance=syllabus_topic)
        if form.is_valid():
            form.save()
            messages.success(request, f'Syllabus topic "{syllabus_topic.topic_title}" updated successfully!')
            return redirect('teacher_syllabus')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SyllabusForm(instance=syllabus_topic)

    return render(request, 'teacher/teacher_edit_syllabus_topic.html', {
        'teacher': teacher,
        'form': form,
        'syllabus_topic': syllabus_topic,
    })


@teacher_required
def teacher_delete_syllabus_topic(request, topic_id):
    """Delete syllabus topic"""
    teacher = get_object_or_404(Teacher, user=request.user)
    syllabus_topic = get_object_or_404(Syllabus, id=topic_id, teacher=teacher)

    if request.method == 'POST':
        topic_title = syllabus_topic.topic_title
        syllabus_topic.delete()
        messages.success(request, f'Syllabus topic "{topic_title}" deleted successfully!')
        return redirect('teacher_syllabus')

    return render(request, 'teacher/teacher_delete_syllabus_topic.html', {
        'teacher': teacher,
        'syllabus_topic': syllabus_topic,
    })


@teacher_required
def teacher_mark_topic_complete(request, topic_id):
    """Mark syllabus topic as completed/incomplete"""
    teacher = get_object_or_404(Teacher, user=request.user)
    syllabus_topic = get_object_or_404(Syllabus, id=topic_id, teacher=teacher)

    if request.method == 'POST':
        syllabus_topic.is_completed = not syllabus_topic.is_completed
        syllabus_topic.save()

        status = "completed" if syllabus_topic.is_completed else "marked as incomplete"
        messages.success(request, f'Topic "{syllabus_topic.topic_title}" {status}!')

    return redirect('teacher_syllabus')








# Student Dashboard Views
@student_required
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)

    # Get basic info
    class_obj = student.Class
    department = student.department

    # Get current month attendance summary
    from datetime import datetime
    current_month = datetime.now().month
    current_year = datetime.now().year

    monthly_attendance = StudentAttendance.objects.filter(
        student=student,
        date__month=current_month,
        date__year=current_year
    )

    present_count = monthly_attendance.filter(status='present').count()
    total_days = monthly_attendance.count()
    attendance_percentage = (present_count / total_days * 100) if total_days > 0 else 0

    # Get fee summary
    fee_payments = Account.objects.filter(
        student=student,
        transaction_type='student_fee'
    )
    total_paid = fee_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    yearly_fee = class_obj.yearly_fee if class_obj else 0
    fee_balance = yearly_fee - total_paid if yearly_fee else 0

    # Get today's timetable
    today = datetime.now().strftime('%A').lower()
    today_timetable = Timetable.objects.filter(
        class_obj=class_obj,
        day=today
    ).order_by('period') if class_obj else []

    context = {
        'student': student,
        'class_obj': class_obj,
        'department': department,
        'attendance_percentage': round(attendance_percentage, 1),
        'present_count': present_count,
        'total_days': total_days,
        'yearly_fee': yearly_fee,
        'total_paid': total_paid,
        'fee_balance': fee_balance,
        'today_timetable': today_timetable,
        'fee_status': 'paid' if fee_balance <= 0 else 'partial' if total_paid > 0 else 'pending',
    }
    return render(request, 'student/student_dashboard.html', context)


@student_required
def student_attendance_view(request):
    student = get_object_or_404(Student, user=request.user)

    # Get month and year from request or use current
    month = request.GET.get('month', datetime.now().month)
    year = request.GET.get('year', datetime.now().year)

    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = datetime.now().month
        year = datetime.now().year

    # Get attendance for the selected month
    attendance_records = StudentAttendance.objects.filter(
        student=student,
        date__year=year,
        date__month=month
    ).order_by('date')

    # Calculate monthly summary
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count()
    on_leave_count = attendance_records.filter(status='on_leave').count()
    half_day_count = attendance_records.filter(status='half_day').count()
    total_days = attendance_records.count()

    attendance_percentage = (present_count / total_days * 100) if total_days > 0 else 0

    # Create calendar data
    import calendar
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)

    # Create attendance calendar
    attendance_calendar = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:  # Day not in current month
                week_data.append({'day': '', 'status': '', 'record': None})
            else:
                date_obj = datetime(year, month, day).date()
                attendance_record = attendance_records.filter(date=date_obj).first()
                status = attendance_record.status if attendance_record else ''
                week_data.append({
                    'day': day,
                    'status': status,
                    'record': attendance_record
                })
        attendance_calendar.append(week_data)

    # Get available months for dropdown
    from django.db.models import Min
    earliest_date = StudentAttendance.objects.filter(
        student=student
    ).aggregate(Min('date'))['date__min']

    available_months = []
    if earliest_date:
        current_date = datetime.now().date()
        start_date = datetime(earliest_date.year, earliest_date.month, 1)

        while start_date.date() <= current_date:
            available_months.append({
                'month': start_date.month,
                'year': start_date.year,
                'display': start_date.strftime('%B %Y')
            })
            # Move to next month
            if start_date.month == 12:
                start_date = datetime(start_date.year + 1, 1, 1)
            else:
                start_date = datetime(start_date.year, start_date.month + 1, 1)

    available_months.reverse()  # Show latest first

    context = {
        'student': student,
        'attendance_records': attendance_records,
        'attendance_calendar': attendance_calendar,
        'present_count': present_count,
        'absent_count': absent_count,
        'on_leave_count': on_leave_count,
        'half_day_count': half_day_count,
        'total_days': total_days,
        'attendance_percentage': round(attendance_percentage, 1),
        'current_month': month,
        'current_year': year,
        'month_name': datetime(year, month, 1).strftime('%B %Y'),
        'available_months': available_months,
    }
    return render(request, 'student/student_attendance.html', context)


@student_required
def student_timetable_view(request):
    student = get_object_or_404(Student, user=request.user)
    class_obj = student.Class

    if not class_obj:
        messages.error(request, "You are not assigned to any class.")
        return redirect('student_dashboard')

    # Get timetable for student's class
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    periods = Timetable.PERIOD_CHOICES

    timetable_data = {}
    for day in days:
        timetable_data[day] = {}
        for period_num, period_display in periods:
            try:
                entry = Timetable.objects.filter(
                    class_obj=class_obj,
                    day=day,
                    period=period_num
                ).first()
                timetable_data[day][period_num] = entry
            except Exception:
                timetable_data[day][period_num] = None

    # Get today's timetable
    today = datetime.now().strftime('%A').lower()
    today_timetable = []
    if today in days:
        for period_num, period_display in periods:
            entry = timetable_data[today].get(period_num)
            if entry:
                today_timetable.append({
                    'period': period_display,
                    'subject': entry.subject,
                    'teacher': entry.teacher,
                    'room_number': entry.room_number,
                    'time_slot': entry.get_time_slot()
                })

    context = {
        'student': student,
        'class_obj': class_obj,
        'timetable_data': timetable_data,
        'days': days,
        'periods': periods,
        'today_timetable': today_timetable,
        'today': today.capitalize(),
    }
    return render(request, 'student/student_timetable.html', context)


@student_required
def student_fee_summary(request):
    student = get_object_or_404(Student, user=request.user)
    class_obj = student.Class

    # Get all fee payments
    fee_payments = Account.objects.filter(
        student=student,
        transaction_type='student_fee'
    ).order_by('-payment_date')

    # Calculate totals
    total_paid = fee_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    yearly_fee = class_obj.yearly_fee if class_obj else 0
    balance = yearly_fee - total_paid

    # Determine payment status
    if yearly_fee and total_paid >= yearly_fee:
        payment_status = 'paid'
        status_class = 'success'
        status_text = 'Fully Paid'
    elif total_paid > 0:
        payment_status = 'partial'
        status_class = 'warning'
        status_text = 'Partially Paid'
    else:
        payment_status = 'pending'
        status_class = 'danger'
        status_text = 'Pending'

    # Payment history
    payment_history = []
    for payment in fee_payments:
        payment_history.append({
            'date': payment.payment_date,
            'amount': payment.paid_amount,
            'method': payment.get_payment_method_display(),
            'receipt_number': payment.receipt_number,
            'description': payment.description
        })

    context = {
        'student': student,
        'class_obj': class_obj,
        'yearly_fee': yearly_fee,
        'total_paid': total_paid,
        'balance': balance,
        'payment_status': payment_status,
        'status_class': status_class,
        'status_text': status_text,
        'payment_history': payment_history,
        'fee_payments': fee_payments,
    }
    return render(request, 'student/student_fee_summary.html', context)


# ========== STUDENT ASSIGNMENT VIEWS ==========

@student_required
def student_assignments(request):
    """List all assignments for student's class"""
    student = get_object_or_404(Student, user=request.user)

    # Get assignments for student's class and subjects
    assignments = Assignment.objects.filter(
        class_obj=student.Class
    ).select_related('subject', 'teacher').order_by('-created_at')

    # Check submission status for each assignment
    assignment_data = []
    for assignment in assignments:
        submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=student
        ).first()

        assignment_data.append({
            'assignment': assignment,
            'submission': submission,
            'is_submitted': submission is not None,
            'is_late': submission.is_late if submission else False,
        })

    return render(request, 'student/student_assignments.html', {
        'student': student,
        'assignment_data': assignment_data,
    })


@student_required
def student_assignment_detail(request, assignment_id):
    """View assignment details and submit work"""
    student = get_object_or_404(Student, user=request.user)
    assignment = get_object_or_404(Assignment, id=assignment_id, class_obj=student.Class)

    # Check if already submitted
    submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=student
    ).first()

    if request.method == 'POST':
        # Prevent multiple submissions
        if submission:
            messages.error(request, 'You have already submitted this assignment!')
            return redirect('student_assignment_detail', assignment_id=assignment_id)

        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = student
            submission.save()

            messages.success(request, 'Assignment submitted successfully!')
            return redirect('student_assignments')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignmentSubmissionForm()

    return render(request, 'student/student_assignment_detail.html', {
        'student': student,
        'assignment': assignment,
        'form': form,
        'submission': submission,
    })


@student_required
def student_view_submission(request, assignment_id):
    """View submitted assignment"""
    student = get_object_or_404(Student, user=request.user)
    assignment = get_object_or_404(Assignment, id=assignment_id, class_obj=student.Class)

    submission = get_object_or_404(
        AssignmentSubmission,
        assignment=assignment,
        student=student
    )

    return render(request, 'student/student_view_submission.html', {
        'student': student,
        'assignment': assignment,
        'submission': submission,
    })


# ========== STUDENT SYLLABUS VIEWS ==========

@student_required
def student_syllabus(request):
    """View syllabus for student's subjects"""
    student = get_object_or_404(Student, user=request.user)

    # Get syllabus for student's class
    syllabus_topics = Syllabus.objects.filter(
        class_obj=student.Class
    ).select_related('subject', 'teacher').order_by('subject__name', 'target_date')

    # Group by subject
    syllabus_by_subject = {}
    for topic in syllabus_topics:
        subject_name = topic.subject.name
        if subject_name not in syllabus_by_subject:
            syllabus_by_subject[subject_name] = []
        syllabus_by_subject[subject_name].append(topic)

    return render(request, 'student/student_syllabus.html', {
        'student': student,
        'syllabus_by_subject': syllabus_by_subject,
    })