import re  # FIX: removed "from ast import pattern" — that was a wrong import
 
from django import forms
from django.contrib.auth.models import User
from .models import Application, UserProfile, Job, CompanyProfile, EmployerSettings
 
 
class RegisterForm(forms.Form):
 
    full_name = forms.CharField(
        max_length=150,
        error_messages={'required': 'Full name is required.'}
    )
    email = forms.EmailField(
        error_messages={'required': 'Email is required.'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        error_messages={'required': 'Password is required.'}
    )
    mobile_number = forms.CharField(
        max_length=15,
        error_messages={'required': 'Mobile number is required.'}
    )
    work_status = forms.ChoiceField(
        choices=[('', 'Select'), ('experienced', 'Experienced'), ('fresher', 'Fresher')],
        error_messages={'required': 'Work status is required.'}
    )
 
    # CONDITION 1: Full name min 3 characters
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if len(full_name) < 3:
            raise forms.ValidationError("Full name must be at least 3 characters.")
        return full_name
 
    # CONDITION 2: Email must be unique
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "❌ This email is already registered. "
                "Please use a different email or login with this one."
            )
        return email
 
    # CONDITION 3: Strong password
    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        errors = []
 
        if len(password) < 8:
            errors.append("at least 8 characters")
        if not re.search(r'[A-Z]', password):
            errors.append("at least one uppercase letter (A–Z)")
        if not re.search(r'[a-z]', password):
            errors.append("at least one lowercase letter (a–z)")
        if not re.search(r'[0-9]', password):
            errors.append("at least one number (0–9)")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('at least one special character (e.g. !@#$%^&*)')
 
        if errors:
            raise forms.ValidationError(
                "❌ Weak password! Your password must include: "
                + ", ".join(errors)
                + ". Example of a strong password: MyPass@123"
            )
        return password
 
    # CONDITION 4: Mobile number format + unique
    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get('mobile_number', '').strip()
 
        # FIX: removed unreachable "return f'91+{mobile_number}'" that was
        # placed after a raise — it could never execute and was confusing
        if not re.match(r'^\d{10}$', mobile_number):
            raise forms.ValidationError("❌ Enter exactly 10 digits mobile number")
 
        if UserProfile.objects.filter(mobile_number=mobile_number).exists():
            raise forms.ValidationError(
                "❌ This mobile number is already registered. "
                "Please use a different number."
            )
        return mobile_number
 
    # CONDITION 5: Work status must be selected
    def clean_work_status(self):
        work_status = self.cleaned_data.get('work_status', '')
        if work_status not in ['experienced', 'fresher']:
            raise forms.ValidationError("Please select your work status (Experienced or Fresher).")
        return work_status
 
 
class LoginForm(forms.Form):
 
    email = forms.EmailField(
        error_messages={'required': 'Email is required.'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        error_messages={'required': 'Password is required.'}
    )
 
 
class EmployerRegisterForm(forms.ModelForm):
 
    username = forms.CharField(max_length=100)
    email    = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
 
    class Meta:
        model  = UserProfile
        fields = ['full_name', 'mobile_number']
 
 
class JobForm(forms.ModelForm):
 
    class Meta:
        model  = Job
        fields = [
            'title',
            'company',
            'min_experience', 'max_experience',
            'min_salary',
            'max_salary',
            'salary_disclosed',
            'location',
            'work_mode',
            'skills',
            'role_category',
            'education',
            'category',
            'company_type',
            'logo',
            'description',
            'is_featured',
            'is_sponsored',
        ]
        

        widgets = {
            'min_salary':  forms.NumberInput(attrs={'placeholder': 'Min Salary'}),
            'max_salary':  forms.NumberInput(attrs={'placeholder': 'Max Salary'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter job description'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        disclosed = cleaned_data.get('salary_disclosed')
        min_s = cleaned_data.get('min_salary')
        max_s = cleaned_data.get('max_salary')

        if disclosed:
            if min_s is not None and min_s <= 0:
                self.add_error('min_salary', 'Salary must be a positive number.')
            if max_s is not None and max_s <= 0:
                self.add_error('max_salary', 'Salary must be a positive number.')

            if min_s and max_s and max_s < min_s:
                self.add_error('max_salary', 'Max salary cannot be less than min salary.')

        # ✅ NEW: if disclosed=True but both fields empty → auto-fix silently
            if not min_s and not max_s:
                cleaned_data['salary_disclosed'] = False

        else:
            cleaned_data['min_salary'] = None
            cleaned_data['max_salary'] = None

            return cleaned_data
    
class CompanyProfileForm(forms.ModelForm):
 
    class Meta:
        model   = CompanyProfile
        fields  = '__all__'
        exclude = ['employer']
 
 
class EmployerSettingsForm(forms.ModelForm):
 
    class Meta:
        model   = EmployerSettings
        fields  = '__all__'
        exclude = ['employer']

# NEW: Added form for scheduling interviews, which was missing before

class InterviewScheduleForm(forms.ModelForm):

    class Meta:

        model = Application

        fields = [
            'interview_date',
            'interview_time',
            'interview_link',
            'interview_notes',
        ]

        widgets = {

            'interview_date': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'interview_time': forms.TimeInput(
                attrs={'type': 'time'}
            ),

            'interview_link': forms.URLInput(
                attrs={
                    'placeholder': 'Google Meet Link'
                }
            ),

            'interview_notes': forms.Textarea(
                attrs={
                    'placeholder': 'Interview instructions'
                }
            ),
        }
 