from django.core.exceptions import ValidationError
from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm
from . import models
from .models import User, Teacher, Timetable,Class


class BaseUserForm(UserCreationForm):
    """Base form with common fields - DON'T use for direct instantiation"""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'username', 'mobile',
            'address', 'profile', 'date_of_birth', 'password1', 'password2'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['mobile'].required = True


class AdminSignUpForm(BaseUserForm):
    """Specifically for ADMIN users"""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'admin'
        if commit:
            user.save()
        return user


class TeacherSignUpForm(BaseUserForm):
    """Specifically for TEACHER users"""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        if commit:
            user.save()
        return user


class StudentSignUpForm(BaseUserForm):
    """Specifically for STUDENT users"""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        if commit:
            user.save()
        return user


# Updated Form for editing with password change option
class UserEditForm(forms.ModelForm):
    password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep current password'}),
        required=False,
        help_text="Leave blank if you don't want to change the password. Minimum 8 characters."
    )
    password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'}),
        required=False,
        help_text="Enter the same password as above for verification."
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'mobile', 'address', 'profile', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['mobile'].required = True
        self.fields['username'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # Only validate passwords if at least one password field is filled
        if password1 or password2:
            if not password1:
                raise forms.ValidationError("Please enter a new password.")
            if not password2:
                raise forms.ValidationError("Please confirm your new password.")
            if password1 != password2:
                raise forms.ValidationError("The two password fields didn't match.")
            if len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Update password if provided
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user


class TeacherForm(forms.ModelForm):
    class Meta:
        model = models.Teacher
        fields = ['teacher_id', 'gender', 'department','subjects', 'qualification',
                  'specialization', 'experience', 'joining_date', 'salary']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control','step':'0.01','min':'0','placeholder':'Enter monthly salary'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher_id'].required = True
        self.fields['department'].required = True

        self.fields['subjects'].queryset = models.Subject.objects.all().order_by('department__name', 'name')
        self.fields['subjects'].help_text = "Select subjects this teacher will teach (Hold Ctrl/Cmd to select multiple)"


class StudentForm(forms.ModelForm):
    class Meta:
        model = models.Student
        exclude = ['user', 'created_at', 'updated_at']  # Exclude auto fields
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'present_address': forms.Textarea(attrs={'rows': 3}),
            'permanent_address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields
        self.fields['student_id'].required = True
        self.fields['Class'].required = True
        self.fields['admission_number'].required = True
        self.fields['gender'].required = True
        self.fields['department'].required = True


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = models.Department
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'type': 'textarea'}),
            'hod': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show teachers in the HOD dropdown
        self.fields['hod'].queryset = Teacher.objects.all().order_by('user__first_name')
        self.fields['hod'].required = False
        self.fields['hod'].label = "Head of Department (HOD)"


class SubjectForm(forms.ModelForm):
    class Meta:
        model = models.Subject
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'subject_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject_code'].required = True
        self.fields['name'].required = True
        self.fields['department'].required = True


class ClassForm(forms.ModelForm):
    class Meta:
        model = models.Class
        fields = '__all__'
        widgets = {
            'class_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'class_teacher': forms.Select(attrs={'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'yearly_fee': forms.NumberInput(attrs={'class': 'form-control','placeholder':'Enter yearly fee'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_teacher'].required = True
        self.fields['name'].required = True
        self.fields['department'].required = True
        self.fields['class_id'].required = True
        self.fields['yearly_fee'].required = False
        self.fields['yearly_fee'].help_text = "Yearly fee for students in this class (optional)"

        if self.instance and self.instance.pk and self.instance.department:
            self.fields['class_teacher'].queryset = Teacher.objects.filter(department=self.instance.department)
        else:
            self.fields['class_teacher'].queryset = Teacher.objects.all()

# ========== ATTENDANCE FORMS ==========

class StudentAttendanceDateForm(forms.Form):
    """Simple form to select date and class for student attendance"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date()
    )
    class_obj = forms.ModelChoiceField(
        queryset=models.Class.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Class"
    )


class TeacherAttendanceDateForm(forms.Form):
    """Simple form to select date for teacher attendance"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date()
    )



class BulkTimetableForm(forms.Form):
    """Form for bulk weekly timetable creation"""
    class_obj = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'bulk-class-select',
            'required': True
        }),
        empty_label="Select Class",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        class_obj = cleaned_data.get('class_obj')

        # Example: Check if class already has timetable
        if class_obj and Timetable.objects.filter(class_obj=class_obj).exists():
            # This is just a warning, not an error, since we allow overwriting
            # You could raise ValidationError here if you don't want to allow overwriting
            pass

        return cleaned_data


class TeacherSalaryForm(forms.ModelForm):
    """Simple form for teacher salary payment status management"""

    class Meta:
        model = models.Account
        fields = ['payment_status', 'payment_method', 'payment_date', 'description']  # Use description instead of notes
        widgets = {
            'payment_status': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'togglePaymentDetails()'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Payment notes...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make payment method and date required only when marking as paid
        self.fields['payment_method'].required = False
        self.fields['payment_date'].required = False

        # Set today's date as default
        if not self.instance.payment_date:
            self.fields['payment_date'].initial = timezone.now().date()

    def clean(self):
        cleaned_data = super().clean()
        payment_status = cleaned_data.get('payment_status')
        payment_method = cleaned_data.get('payment_method')
        payment_date = cleaned_data.get('payment_date')

        # If marking as paid, require payment details
        if payment_status == 'paid':
            if not payment_method:
                raise forms.ValidationError("Payment method is required when marking as paid")
            if not payment_date:
                raise forms.ValidationError("Payment date is required when marking as paid")

        return cleaned_data

    def save(self, commit=True):
        # Auto-update paid_amount based on payment status
        if self.cleaned_data.get('payment_status') == 'paid':
            self.instance.paid_amount = self.instance.amount  # Full payment
        elif self.cleaned_data.get('payment_status') == 'pending':
            self.instance.paid_amount = 0  # Reset to pending

        return super().save(commit=commit)


class FeePaymentForm(forms.Form):
    """Simple form to record fee payment"""
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Enter payment amount'
        })
    )
    payment_date = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('cash', 'Cash'),
            ('cheque', 'Cheque'),
            ('online', 'Online Transfer'),
            ('card', 'Card'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional payment notes...'
        })
    )


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = models.Account
        fields = ['title', 'amount', 'expense_category', 'payment_date', 'payment_method', 'description']
        widgets = {
            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Internet Bill, Classroom Chairs, Sports Equipment'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'expense_category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the expense...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['amount'].required = True
        self.fields['expense_category'].required = True
        self.fields['payment_date'].initial = timezone.now().date()

        # Set help texts
        self.fields['title'].help_text = "Enter a clear title for this expense"
        self.fields['amount'].help_text = "Enter the expense amount"
        self.fields['expense_category'].help_text = "Select the expense category"



# Assignment Form (No marks field)
class AssignmentForm(forms.ModelForm):
    class Meta:
        model = models.Assignment
        fields = ['title', 'description', 'due_date', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assignment Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Assignment Description'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['due_date'].required = True

# Assignment Submission Form (Simple file upload)
class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = models.AssignmentSubmission
        fields = ['submission_file', 'notes']
        widgets = {
            'submission_file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any notes (optional)...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['submission_file'].required = True

# Syllabus Form (Same as before)
class SyllabusForm(forms.ModelForm):
    class Meta:
        model = models.Syllabus
        fields = ['topic_title', 'description', 'study_material', 'target_date', 'is_completed']
        widgets = {
            'topic_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Topic Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Topic Description'}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'study_material': forms.FileInput(attrs={'class': 'form-control'}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['topic_title'].required = True