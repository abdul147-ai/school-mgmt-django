from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, Q
from decimal import Decimal

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
    subjects = models.ManyToManyField('Subject', related_name='teachers',blank=True)
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

    @property
    def get_subjects(self):
        return "," .join([subject.name for subject in self.subjects.all()])

    @property
    def is_hod(self):
        return Department.objects.filter(hod=self).exists()
    @property
    def hod_department(self):
        try:
            return Department.objects.get(hod=self)
        except Department.DoesNotExist:
            return None

    @property
    def assigned_classes(self):
        return Class.objects.filter(class_teacher=self)
    @property
    def is_class_teacher(self):
        return self.assigned_classes.exists()

    @property
    def can_view_department_attendance(self):
        return self.is_hod

    @property
    def get_current_month_salary_record(self, month=None):
        """Get salary record for current or specified month"""
        if not month:
            from django.utils import timezone
            month = timezone.now().strftime('%B %Y')

        return Account.objects.filter(
            transaction_type='teacher_salary',
            teacher=self,
            month=month
        ).first()

    @property
    def has_salary_for_month(self, month):
        """Check if salary record exists for given month"""
        return Account.objects.filter(
            transaction_type='teacher_salary',
            teacher=self,
            month=month
        ).exists()

    def generate_salary_record(self, month, created_by):
        """Generate salary record for this teacher"""
        if not self.salary or self.salary <= 0:
            return None

        return Account.objects.create(
            transaction_type='teacher_salary',
            title=f"Salary - {self.get_name} - {month}",
            amount=self.salary,  # Use teacher's base salary
            teacher=self,
            month=month,
            description=f"Monthly salary for {month}",
            created_by=created_by
        )

    def __str__(self):
        return f"{self.get_name} - {self.department}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=11, unique=True)
    gender = models.CharField(choices=GENDER, max_length=10, blank=True)
    Class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, related_name='students')
    admission_number = models.CharField(max_length=11, blank=True, null=True)
    subject = models.TextField(blank=True, null=True, default='[]')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, related_name='students')

    religion = models.CharField(max_length=50, blank=True, null=True)
    section = models.CharField(max_length=50, blank=True, null=True)
    joining_date = models.DateField(null=True, blank=True)

    # Parents information
    father_name = models.CharField(max_length=100, blank=True, null=True)
    father_occupation = models.CharField(max_length=100, blank=True, null=True)
    father_mobile = models.CharField(max_length=15, blank=True, null=True)
    father_email = models.EmailField(blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    mother_occupation = models.CharField(max_length=100, blank=True, null=True)
    mother_mobile = models.CharField(max_length=15, blank=True, null=True)
    mother_email = models.EmailField(blank=True, null=True)

    # Address
    present_address = models.TextField(blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name

    def __str__(self):
        return f"{self.get_name} - {self.student_id}"


class Department(models.Model):
    department_id = models.CharField(max_length=11, unique=True)
    name = models.CharField(max_length=100,blank=True,null=True)
    hod = models.ForeignKey('Teacher',on_delete=models.SET_NULL, null=True,blank=True, related_name='hod_departments')
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

    @property
    def hod_name(self):
        return self.hod.get_name if self.hod else "Not assigned"

class Subject(models.Model):
    subject_code = models.CharField(max_length=11, unique=True)
    name = models.CharField(max_length=100,blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, related_name='subjects')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.subject_code}"


class Class(models.Model):
    class_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100,blank=True,null=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, related_name='classes')
    class_teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, related_name='classes')
    room_number = models.CharField(max_length=11, blank=True,null=True)
    capacity = models.IntegerField(default=0)
    yearly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.department}"


class StudentAttendance(models.Model):
    ATTENDANCE_STATUS = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('on_leave', 'On Leave'),
        ('half_day', 'Half Day'),
    ]

    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS)
    class_obj = models.ForeignKey('Class', on_delete=models.CASCADE)  # To know which class student belongs to
    remarks = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['student', 'date']  # One record per student per day
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.get_name} - {self.date} - {self.status}"


class TeacherAttendance(models.Model):
    ATTENDANCE_STATUS = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('on_leave', 'On Leave'),
        ('half_day', 'Half Day'),
    ]

    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS)
    department = models.ForeignKey('Department', on_delete=models.CASCADE)  # To know which department teacher belongs to
    remarks = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_attendances')

    class Meta:
        unique_together = ['teacher', 'date']  # One record per teacher per day
        ordering = ['-date']

    def __str__(self):
        return f"{self.teacher.get_name} - {self.date} - {self.status}"


class Timetable(models.Model):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]

    PERIODS = {
        1: ('09:00', '09:45'),
        2: ('09:45', '10:30'),
        3: ('10:45', '11:30'),
        4: ('11:30', '12:15'),
        5: ('12:15', '13:00'),
        6: ('13:45', '14:30'),
        7: ('14:30', '15:15'),
    }

    PERIOD_CHOICES = [
        (f"{num}", f"Period {num} ({start} - {end})")
        for num, (start, end) in PERIODS.items()
    ]

    class_obj = models.ForeignKey('Class', on_delete=models.CASCADE, related_name='timetables')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    period = models.IntegerField(choices=PERIOD_CHOICES)
    room_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        unique_together = [
            ['class_obj', 'day', 'period'],
            ['teacher', 'day', 'period'],
            #['room_number', 'day', 'period'],

        ]
        ordering = ['day', 'period']

    def clean(self):
        # Validate that teacher can teach the selected subject
        if self.teacher and self.subject:
            if not self.teacher.subjects.filter(id=self.subject.id).exists():
                raise ValidationError(f"{self.teacher.get_name} cannot teach {self.subject.name}")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_time_slot(self):
        period_num = int(self.period)
        start,end = self.PERIODS.get(period_num, ('',''))
        return f"{start} - {end}"

    def get_start_time(self):
        period_num = int(self.period)
        return self.PERIODS.get(period_num, ('',''))[0]

    def get_end_time(self):
        period_num = int(self.period)
        return self.PERIODS.get(period_num, ('',''))[1]

    def __str__(self):
        return f"{self.class_obj.name} - {self.day} - {self.subject.name}"


class Account(models.Model):
    TRANSACTION_TYPES = [
        ('student_fee', 'Student Fee'),
        ('teacher_salary', 'Teacher Salary'),
        ('school_expense', 'School Expense'),
        ('other_income', 'Other Income'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
    ]

    EXPENSE_CATEGORY = [
        ('academic', 'Academic expense'),
        ('administration','Administration Expense'),
        ('infrastructure', 'Infrastructure Expense'),
        ('other','Other expense'),
    ]

    # Basic Information
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    # Amount Details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                      validators=[MinValueValidator(Decimal('0.00'))])

    # Payment Information
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS, blank=True, null=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)

    # Dates
    due_date = models.DateField(blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    transaction_date = models.DateField(auto_now_add=True)

    # Relationships
    student = models.ForeignKey('Student', on_delete=models.CASCADE, blank=True, null=True, related_name='accounts')
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, blank=True, null=True, related_name='accounts')
    class_obj = models.ForeignKey('Class', on_delete=models.SET_NULL, blank=True, null=True)

    # Additional info
    month = models.CharField(max_length=20, blank=True, null=True)
    academic_year = models.CharField(max_length=9, blank=True, null=True)
    expense_category = models.CharField(max_length=100, blank=True, null=True,choices=EXPENSE_CATEGORY)

    # Audit
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'month'],
                condition=models.Q(transaction_type='teacher_salary'),
                name='unique_teacher_monthly_salary'
            )
        ]

    def clean(self):
        """Validate teacher salary consistency"""
        from django.core.exceptions import ValidationError

        if (self.transaction_type == 'teacher_salary' and
                self.teacher and
                self.teacher.salary and
                self.amount != self.teacher.salary):
            raise ValidationError(
                f"Salary amount (₹{self.amount}) must match teacher's base salary (₹{self.teacher.salary})"
            )

        # Validate that month is provided for teacher salary
        if self.transaction_type == 'teacher_salary' and not self.month:
            raise ValidationError("Month is required for teacher salary records")

        # Validate that teacher is provided for teacher salary
        if self.transaction_type == 'teacher_salary' and not self.teacher:
            raise ValidationError("Teacher is required for teacher salary records")

    def save(self, *args, **kwargs):
        # Run validation
        self.clean()

        # Auto-update payment status based on amounts
        if self.paid_amount >= self.amount:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'pending'

        # Auto-generate receipt number
        if not self.receipt_number and self.payment_status == 'paid':
            import uuid
            prefix = {
                'student_fee': 'FEE',
                'teacher_salary': 'SAL',
                'school_expense': 'EXP',
                'other_income': 'INC'
            }.get(self.transaction_type, 'TXN')
            self.receipt_number = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

        super().save(*args, **kwargs)

    @property
    def balance_amount(self):
        return self.amount - self.paid_amount

    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.amount

    @property
    def get_related_person(self):
        if self.student:
            return self.student.get_name
        elif self.teacher:
            return self.teacher.get_name
        return "School"

    # Class methods for monthly summaries
    @classmethod
    def get_monthly_summary(cls, year, month):
        """Get monthly summary directly from Account records"""
        transactions = cls.objects.filter(
            payment_date__year=year,
            payment_date__month=month,
            payment_status='paid'
        )

        summary = transactions.aggregate(
            total_fee=Sum('paid_amount', filter=Q(transaction_type='student_fee')),
            total_salary=Sum('paid_amount', filter=Q(transaction_type='teacher_salary')),
            total_expense=Sum('paid_amount', filter=Q(transaction_type='school_expense')),
            total_income=Sum('paid_amount', filter=Q(transaction_type='other_income'))
        )

        return {
            'month': f"{month}/{year}",
            'total_fee_collected': summary['total_fee'] or 0,
            'total_salary_paid': summary['total_salary'] or 0,
            'total_expenses': summary['total_expense'] or 0,
            'total_income': summary['total_income'] or 0,
            'net_balance': (summary['total_fee'] or 0) + (summary['total_income'] or 0) -
                           (summary['total_salary'] or 0) - (summary['total_expense'] or 0)
        }

    @classmethod
    def get_current_month_summary(cls):
        """Get current month summary"""
        from datetime import datetime
        current = datetime.now()
        return cls.get_monthly_summary(current.year, current.month)

    # NEW: Salary generation methods
    @classmethod
    def generate_monthly_salaries(cls, month, created_by, overwrite=False):
        """
        Generate salary records for all teachers with salary for given month
        Returns: (created_count, updated_count, errors)
        """
        from django.utils import timezone

        teachers = Teacher.objects.filter(salary__gt=0)
        created_count = 0
        updated_count = 0
        errors = []

        for teacher in teachers:
            try:
                # Check if record already exists
                existing_record = cls.objects.filter(
                    transaction_type='teacher_salary',
                    teacher=teacher,
                    month=month
                ).first()

                if existing_record:
                    if overwrite:
                        # Update existing record
                        existing_record.amount = teacher.salary
                        existing_record.title = f"Salary - {teacher.get_name} - {month}"
                        existing_record.description = f"Monthly salary for {month}"
                        existing_record.save()
                        updated_count += 1
                else:
                    # Create new record
                    cls.objects.create(
                        transaction_type='teacher_salary',
                        title=f"Salary - {teacher.get_name} - {month}",
                        amount=teacher.salary,
                        teacher=teacher,
                        month=month,
                        due_date=timezone.now().date(),
                        description=f"Monthly salary for {month}",
                        created_by=created_by
                    )
                    created_count += 1

            except Exception as e:
                errors.append(f"Error processing {teacher.get_name}: {str(e)}")

        return created_count, updated_count, errors

    @classmethod
    def get_teacher_salary_status(cls, month=None):
        """Get salary status for all teachers for given month"""
        from django.utils import timezone

        if not month:
            month = timezone.now().strftime('%B %Y')

        teachers = Teacher.objects.all()
        salary_data = []

        for teacher in teachers:
            salary_record = cls.objects.filter(
                transaction_type='teacher_salary',
                teacher=teacher,
                month=month
            ).first()

            salary_data.append({
                'teacher': teacher,
                'base_salary': teacher.salary,
                'salary_record': salary_record,
                'payment_status': salary_record.payment_status if salary_record else 'not_generated',
                'paid_amount': salary_record.paid_amount if salary_record else 0,
                'balance': salary_record.balance_amount if salary_record else teacher.salary,
            })

        return salary_data

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.title} - ₹{self.amount}"


# Assignment Model (No marks/grading)
class Assignment(models.Model):
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    class_obj = models.ForeignKey('Class', on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.subject.name}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        return timezone.now().date() > self.due_date

    @property
    def submission_count(self):
        return self.submissions.count()


# Assignment Submission Model (No marks/grading)
class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('Student', on_delete=models.CASCADE)

    submission_file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)  # Optional notes from student

    class Meta:
        unique_together = ['assignment', 'student']

    def __str__(self):
        return f"{self.student.get_name} - {self.assignment.title}"

    @property
    def is_submitted(self):
        return self.submitted_at is not None

    @property
    def is_late(self):
        return self.submitted_at.date() > self.assignment.due_date


# Syllabus Model (Same as before)
class Syllabus(models.Model):
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    class_obj = models.ForeignKey('Class', on_delete=models.CASCADE)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)

    topic_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    study_material = models.FileField(upload_to='syllabus/', blank=True, null=True)
    target_date = models.DateField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['target_date']

    def __str__(self):
        return f"{self.topic_title} - {self.subject.name}"