from ast import pattern
from django import forms
from django.contrib.auth.models import User
import re
from .models import UserProfile, Job, CompanyProfile, EmployerSettings

 
 
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
 
    # ✅ CONDITION 1: Full name min 3 characters
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if len(full_name) < 3:
            raise forms.ValidationError("Full name must be at least 3 characters.")
        return full_name
 
    # ✅ CONDITION 2: Email must be unique — same email cannot register twice
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "❌ This email is already registered. "
                "Please use a different email or login with this one."
            )
        return email
 
    # ✅ CONDITION 3: Strong password — must meet all 5 rules
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
 
    # ✅ CONDITION 4: Mobile number must be unique + correct format
    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get('mobile_number', '').strip()

        pattern = r'^\d{10}$'
        if not re.match(pattern, mobile_number):
            raise forms.ValidationError(
                "❌ Enter exactly 10 digits mobile number"
            )

            return f"91+{mobile_number}"
 
        from .models import UserProfile
        if UserProfile.objects.filter(mobile_number=mobile_number).exists():
            raise forms.ValidationError(
                "❌ This mobile number is already registered. "
                "Please use a different number."
            )
        return mobile_number
 
    # ✅ CONDITION 5: Work status must be selected
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

# Employer Registration Form

class EmployerRegisterForm(forms.ModelForm):

    username = forms.CharField(max_length=100)

    email = forms.EmailField()

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:

        model = UserProfile

        fields = [
            'full_name',
            'mobile_number',
            'company_name',
        ]

class JobForm(forms.ModelForm):

    class Meta:
        model = Job

        fields = [
            'title',
            'company',
            'experience',
            'min_salary',
            'max_salary',
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

            'min_salary': forms.NumberInput(attrs={
                'placeholder': 'Min Salary'
            }),

            'max_salary': forms.NumberInput(attrs={
                'placeholder': 'Max Salary'
            }),

            'description': forms.Textarea(attrs={
                'placeholder': 'Enter job description'
            }),

        }
        
# Employer Company Profile Form
class CompanyProfileForm(forms.ModelForm):

    class Meta:

        model = CompanyProfile

        fields = '__all__'

        exclude = ['employer']



# Employer Settings Form
class EmployerSettingsForm(forms.ModelForm):

    class Meta:

        model = EmployerSettings

        fields = '__all__'

        exclude = ['employer']

