
class AccountForm(forms.ModelForm):
    class Meta:
        model = models.Account
        fields = [
            'transaction_type',
            'title',
            'amount',
            'student',
            'teacher',
            'class_obj',
            'due_date',
            'payment_date',
            'payment_method',
            'description'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleTransactionFields()'  # For dynamic field showing/hiding
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter transaction title'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'student': forms.Select(attrs={
                'class': 'form-control',
                'id': 'student-field'
            }),
            'teacher': forms.Select(attrs={
                'class': 'form-control',
                'id': 'teacher-field'
            }),
            'class_obj': forms.Select(attrs={
                'class': 'form-control',
                'id': 'class-field'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'due-date-field'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'payment-date-field'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'id': 'payment-method-field'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields not required initially
        self.fields['student'].required = False
        self.fields['teacher'].required = False
        self.fields['class_obj'].required = False
        self.fields['due_date'].required = False
        self.fields['payment_date'].required = False
        self.fields['payment_method'].required = False

        # Set placeholders based on transaction type
        transaction_type = self.initial.get('transaction_type', '')
        if transaction_type == 'student_fee':
            self.fields['title'].widget.attrs['placeholder'] = 'e.g., Monthly Fee - January'
        elif transaction_type == 'teacher_salary':
            self.fields['title'].widget.attrs['placeholder'] = 'e.g., Salary - January 2024'
        elif transaction_type == 'school_expense':
            self.fields['title'].widget.attrs['placeholder'] = 'e.g., Electricity Bill - January'

    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        teacher = cleaned_data.get('teacher')
        amount = cleaned_data.get('amount')

        # Validate teacher salary consistency
        if transaction_type == 'teacher_salary' and teacher and teacher.salary:
            if amount != teacher.salary:
                raise forms.ValidationError(
                    f"Salary amount must match teacher's base salary of ₹{teacher.salary}"
                )

        # Validate required fields based on transaction type
        if transaction_type == 'student_fee' and not cleaned_data.get('student'):
            raise forms.ValidationError("Student is required for fee transactions")

        if transaction_type == 'teacher_salary' and not cleaned_data.get('teacher'):
            raise forms.ValidationError("Teacher is required for salary transactions")

        return cleaned_data


class PaymentForm(forms.ModelForm):
    class Meta:
        model = models.Account
        fields = ['paid_amount', 'payment_method', 'payment_date']
        widgets = {
            'paid_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Enter amount paid',
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'value': timezone.now().date()
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].required = True
        self.fields['payment_date'].required = True
        self.fields['paid_amount'].required = True

        if self.instance:
            self.fields[
                'paid_amount'].help_text = f"Total Amount: ₹{self.instance.amount} | Already Paid: ₹{self.instance.paid_amount} | Balance: ₹{self.instance.balance_amount}"

    def clean_paid_amount(self):
        """Prevent overpayment"""
        paid_amount = self.cleaned_data.get('paid_amount')
        balance = self.instance.balance_amount

        if paid_amount > balance:
            raise forms.ValidationError(
                f"Cannot pay more than balance amount. Balance: ₹{balance}"
            )

        return paid_amount

    def save(self, commit=True):
        # Add the payment to existing paid_amount
        new_payment = self.cleaned_data['paid_amount']
        self.instance.paid_amount += new_payment

        # Auto-update payment status
        if self.instance.paid_amount >= self.instance.amount:
            self.instance.payment_status = 'paid'
        elif self.instance.paid_amount > 0:
            self.instance.payment_status = 'partial'

        return super().save(commit=commit)
