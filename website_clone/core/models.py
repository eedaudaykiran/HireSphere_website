from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    WORK_STATUS_CHOICES = (
        ('experienced', 'Experienced'),
        ('fresher', 'Fresher'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)  # ✅ link to Django User
    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=15, unique=True)
    work_status = models.CharField(max_length=20, choices=WORK_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Job(models.Model):
    JOB_TYPE_CHOICES = (
        ('Remote', 'Remote'),
        ('On-site', 'On-site'),
        ('Hybrid', 'Hybrid'),
    )

    # 👇 NEW CATEGORY CHOICES
    CATEGORY_CHOICES = (
        ('IT', 'IT'),
        ('Sales', 'Sales'),
        ('HR', 'HR'),
        ('General', 'General'),
    )

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    experience = models.CharField(max_length=50)
    salary = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    work_mode = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    skills = models.CharField(max_length=300)
    conditions = models.CharField(max_length=300, default="Hands-on projects • Paper writing • Coding explanation")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    
    # 👇 MODIFIED: use choices instead of plain CharField
    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        default='General'
    )
    
    COMPANY_TYPE_CHOICES = (
        ('MNC', 'MNC'),
        ('Startup', 'Startup'),
        ('Product', 'Product'),
        ('Unicorn', 'Unicorn'),
    )

    company_type = models.CharField(
        max_length=50,
        choices=COMPANY_TYPE_CHOICES,
        default='MNC'
    )
    is_sponsored = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def skills_list(self):
        """Returns a list of individual skills, splitting by comma and stripping whitespace."""
        return [skill.strip() for skill in self.skills.split(',')]


