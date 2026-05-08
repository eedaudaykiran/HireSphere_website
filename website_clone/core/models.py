from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class UserProfile(models.Model):

    ROLE_CHOICES = (
        ('candidate', 'Candidate'),
        ('employer', 'Employer'),
    )

    WORK_STATUS_CHOICES = (
        ('experienced', 'Experienced'),
        ('fresher', 'Fresher'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Common fields
    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=15, unique=True)

    # Role
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='candidate'
    )

    # Candidate fields
    work_status = models.CharField(
        max_length=20,
        choices=WORK_STATUS_CHOICES,
        blank=True,
        null=True
    )

    # Employer fields
    company_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )
    email_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Job(models.Model):
    JOB_TYPE_CHOICES = (
        ('Remote', 'Remote'),
        ('On-site', 'On-site'),
        ('Hybrid', 'Hybrid'),
    )

    CATEGORY_CHOICES = (
        ('IT', 'IT'),
        ('Sales', 'Sales'),
        ('HR', 'HR'),
        ('General', 'General'),
    )

    EDUCATION_CHOICES = [
        ("PG", "Any Postgraduate"),
        ("MBA", "MBA/PGDM"),
        ("GRAD", "Any Graduate"),
        ("BTECH", "B.Tech/B.E."),
        ("DIP", "Diploma"),
        ("12TH", "12th Pass"),
    ]

    POSTED_BY_CHOICES = [
        ("COMPANY", "Company Jobs"),
        ("CONSULTANT", "Consultant Jobs"),
    ]

    INDUSTRY_CHOICES = [
        ("IT", "IT Services & Consulting"),
        ("RECRUIT", "Recruitment / Staffing"),
        ("EDU", "Education / Training"),
        ("BPO", "BPM / BPO"),
        ("HEALTH", "Healthcare"),
        ("BFSI", "BFSI"),
        ("RETAIL", "Retail"),
    ]

    COMPANY_TYPE_CHOICES = (
        ('MNC', 'MNC'),
        ('Startup', 'Startup'),
        ('Product', 'Product'),
        ('Unicorn', 'Unicorn'),
    )

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    experience = models.CharField(max_length=50)
    min_salary = models.IntegerField(null=True, blank=True)
    max_salary = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=100)
    work_mode = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    skills = models.CharField(max_length=300)
    conditions = models.CharField(max_length=300, default="Hands-on projects • Paper writing • Coding explanation")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    role_category = models.CharField(max_length=100)
    duration = models.CharField(max_length=50, blank=True, null=True)
    education = models.CharField(max_length=50, choices=EDUCATION_CHOICES)
    posted_by = models.CharField(max_length=20, choices=POSTED_BY_CHOICES, default="COMPANY")
    industry = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='General')
    company_type = models.CharField(max_length=50, choices=COMPANY_TYPE_CHOICES, default='MNC')
    is_sponsored = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=3.5)
    review_count = models.IntegerField(default=0)
    employer = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    null=True,
    blank=True
    )
    views = models.IntegerField(default=0)  # track job views
    

    def __str__(self):
        return self.title

    def skills_list(self):
        """Returns a list of individual skills, splitting by comma and stripping whitespace."""
        return [skill.strip() for skill in self.skills.split(',')] if self.skills else []


class ApplyJob(models.Model):
    STATUS_CHOICES = (
        ('Applied', 'Applied'),
        ('Pending', 'Pending'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected', 'Rejected'),
        ('Selected', 'Selected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)   # candidate
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Applied')

    def __str__(self):
        return f"{self.user.username} applied for {self.job.title}"


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')   # prevent duplicate saves

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"
    
class EmailVerification(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False
    )
    email_verified = models.BooleanField(default=False)

class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='New Applied')

# This model is used to track applications for each job, allowing us to easily count applications and update statuses without complex queries.

class JobApplication(models.Model):

    applicant = models.ForeignKey(User, on_delete=models.CASCADE)

    job = models.ForeignKey(Job, on_delete=models.CASCADE)

    applied_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=50,
        default='Pending'
    )

    def __str__(self):
        return f"{self.applicant.username} applied for {self.job.title}"
    
    
# This model is used to schedule and manage interviews for candidates who have applied for jobs. It tracks the interview details, status, and feedback.


class Interview(models.Model):

    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE
    )

    round_type = models.CharField(
        max_length=100
    )

    interview_date = models.DateField()

    interview_time = models.TimeField()

    meeting_link = models.URLField()

    status = models.CharField(
        max_length=50,
        default='Scheduled'
    )

    feedback = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.candidate.username} - {self.round_type}"
    
# This model is used to facilitate messaging between candidates and employers, allowing them to communicate directly within the platform regarding job applications, interview schedules, and other related discussions.

class Message(models.Model):

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.sender} → {self.receiver}"