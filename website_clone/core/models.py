from django.db import models
from django.contrib.auth.models import User
import uuid

# FIX: removed "from urllib import request" — that was a wrong import that doesn't belong here
 
class UserProfile(models.Model):
 
    ROLE_CHOICES = (
        ('candidate', 'Candidate'),
        ('employer',  'Employer'),
    )
 
    WORK_STATUS_CHOICES = (
        ('experienced', 'Experienced'),
        ('fresher',     'Fresher'),
    )
 
    user          = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name     = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=15, unique=True)
    role          = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    work_status   = models.CharField(max_length=20, choices=WORK_STATUS_CHOICES, blank=True, null=True)
    company_name  = models.CharField(max_length=200, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    skills   = models.CharField(max_length=300, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
 
    def __str__(self):
        return self.full_name
 
 
class Job(models.Model):
 
    JOB_TYPE_CHOICES = (
        ('Remote',  'Remote'),
        ('On-site', 'On-site'),
        ('Hybrid',  'Hybrid'),
    )
 
    CATEGORY_CHOICES = (
        ('IT',      'IT'),
        ('Sales',   'Sales'),
        ('HR',      'HR'),
        ('General', 'General'),
    )
 
    EDUCATION_CHOICES = [
        ("PG",    "Any Postgraduate"),
        ("MBA",   "MBA/PGDM"),
        ("GRAD",  "Any Graduate"),
        ("BTECH", "B.Tech/B.E."),
        ("DIP",   "Diploma"),
        ("12TH",  "12th Pass"),
    ]
 
    POSTED_BY_CHOICES = [
        ("COMPANY",     "Company Jobs"),
        ("CONSULTANT",  "Consultant Jobs"),
    ]
 
    INDUSTRY_CHOICES = [
        ("IT",      "IT Services & Consulting"),
        ("RECRUIT", "Recruitment / Staffing"),
        ("EDU",     "Education / Training"),
        ("BPO",     "BPM / BPO"),
        ("HEALTH",  "Healthcare"),
        ("BFSI",    "BFSI"),
        ("RETAIL",  "Retail"),
    ]
 
    COMPANY_TYPE_CHOICES = (
        ('MNC',     'MNC'),
        ('Startup', 'Startup'),
        ('Product', 'Product'),
        ('Unicorn', 'Unicorn'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('draft', 'Draft'),
    )

    JOB_TYPES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
    )
 
    title         = models.CharField(max_length=200)
    company       = models.CharField(max_length=200)
    experience    = models.CharField(max_length=50)
    min_salary    = models.IntegerField(null=True, blank=True)
    max_salary    = models.IntegerField(null=True, blank=True)
    location      = models.CharField(max_length=100)
    work_mode     = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    skills        = models.CharField(max_length=300)
    conditions    = models.CharField(max_length=300, default="Hands-on projects • Paper writing • Coding explanation")
    logo          = models.ImageField(upload_to='logos/', blank=True, null=True)
    role_category = models.CharField(max_length=100)
    duration      = models.CharField(max_length=50, blank=True, null=True)
    education     = models.CharField(max_length=50, choices=EDUCATION_CHOICES)
    posted_by     = models.CharField(max_length=20, choices=POSTED_BY_CHOICES, default="COMPANY")
    industry      = models.CharField(max_length=100, blank=True)
    category      = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='General')
    company_type  = models.CharField(max_length=50, choices=COMPANY_TYPE_CHOICES, default='MNC')
    is_sponsored  = models.BooleanField(default=False)
    is_featured   = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    rating        = models.DecimalField(max_digits=2, decimal_places=1, default=3.5)
    review_count  = models.IntegerField(default=0)
    description   = models.TextField(blank=True, null=True)
    employer      = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    views         = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    company_name = models.CharField(max_length=100,null=True, blank=True)
    
    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPES
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
 
    def __str__(self):
        return self.title
 
    def skills_list(self):
        return [skill.strip() for skill in self.skills.split(',')] if self.skills else []
 
 
class ApplyJob(models.Model):
 
    STATUS_CHOICES = (
        ('Applied',     'Applied'),
        ('Pending',     'Pending'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected',    'Rejected'),
        ('Selected',    'Selected'),
    )
 
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    job        = models.ForeignKey(Job, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    status     = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Applied')
 
    def __str__(self):
        return f"{self.user.username} applied for {self.job.title}"
 
 
class SavedJob(models.Model):
 
    user     = models.ForeignKey(User, on_delete=models.CASCADE)
    job      = models.ForeignKey(Job, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        unique_together = ('user', 'job')
 
    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"
 
 
class EmailVerification(models.Model):
 
    user           = models.ForeignKey(User, on_delete=models.CASCADE)
    token          = models.UUIDField(default=uuid.uuid4, editable=False)
    email_verified = models.BooleanField(default=False)
 
class Application(models.Model):

    # ══════════════════════════════════════════════════════
    # STATUS CHOICES — the pipeline stages a job application moves through.
    # Each tuple is: ('stored_value', 'display_label')
    # 'Applied' is now the default (was 'pending review' which didn't
    # match any choice — that was a hidden bug).
    # ══════════════════════════════════════════════════════
    STATUS_CHOICES = (
        ('Applied',              'Applied'),
        ('Screening',            'Screening'),
        ('Shortlisted',          'Shortlisted'),
        ('Interview',            'Interview'),
        ('Interview Scheduled',  'Interview Scheduled'),
        ('Technical',            'Technical'),
        ('HR',                   'HR'),
        ('Offer',                'Offer'),
        ('Rejected',             'Rejected'),
    )

    # ── Core relationship fields ───────────────────────────
    job       = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'   # lets you do job.applications.all()
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE      # deletes applications if user is deleted
    )

    # ── Application details ────────────────────────────────
    resume   = models.FileField(upload_to='resumes/', null=True, blank=True)
    status   = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Applied'             # FIX: was 'pending review' — not in STATUS_CHOICES
    )

    # ── Timestamp ─────────────────────────────────────────
    # FIX: This field was completely missing before.
    # Its absence caused FieldError crashes in:
    #   employer_dashboard, applied_jobs_page,
    #   shortlisted_candidates, dashboard_realtime_data
    # After adding this field run:
    #   python manage.py makemigrations
    #   python manage.py migrate
    applied_at = models.DateTimeField(auto_now_add=True)

    # ── Applicant profile snapshot ─────────────────────────
    # These store info AT THE TIME of applying (in case profile changes later)
    experience   = models.CharField(max_length=50,  blank=True, null=True)
    location     = models.CharField(max_length=100, blank=True, null=True)
    skills       = models.CharField(max_length=300, blank=True, null=True)
    phone_number = models.CharField(max_length=15,  blank=True, null=True)

    # ── Interview scheduling fields ────────────────────────
    interview_date  = models.DateField(null=True, blank=True)
    interview_time  = models.TimeField(null=True, blank=True)
    interview_link  = models.URLField(null=True,  blank=True)
    interview_notes = models.TextField(null=True, blank=True)

    # ── Helper methods ─────────────────────────────────────
    @classmethod
    def get_status_choices(cls):
        """Returns all status values as a plain list.
        Useful for template dropdowns or validation logic.
        Example: Application.get_status_choices()
        → ['Applied', 'Screening', 'Shortlisted', ...]
        """
        return [choice[0] for choice in cls.STATUS_CHOICES]

    def __str__(self):
        # Human-readable label shown in Django admin and shell
        return f"{self.applicant.username} applied for {self.job.title}" 
 
 
class Interview(models.Model):
 
    candidate      = models.ForeignKey(User, on_delete=models.CASCADE)
    job            = models.ForeignKey(Job, on_delete=models.CASCADE)
    round_type     = models.CharField(max_length=100)
    interview_date = models.DateField()
    interview_time = models.TimeField()
    meeting_link   = models.URLField()
    status         = models.CharField(max_length=50, default='Scheduled')
    feedback       = models.TextField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"{self.candidate.username} - {self.round_type}"
 
 
class Message(models.Model):
 
    sender     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"{self.sender} → {self.receiver}"
 
 
class CompanyProfile(models.Model):
 
    employer       = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name   = models.CharField(max_length=200)
    logo           = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    description    = models.TextField()
    website        = models.URLField(blank=True, null=True)
    location       = models.CharField(max_length=200)
    industry       = models.CharField(max_length=100)
    employee_count = models.CharField(max_length=50)
    founded_year   = models.IntegerField(null=True, blank=True)
 
    def __str__(self):
        return self.company_name
 
 
class Subscription(models.Model):
 
    employer       = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_name      = models.CharField(max_length=100)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    start_date     = models.DateField()
    expiry_date    = models.DateField()
    is_active      = models.BooleanField(default=True)
    payment_status = models.CharField(max_length=50, default='Paid')
    created_at     = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"{self.employer.username} - {self.plan_name}"
 
 
class EmployerSettings(models.Model):
 
    employer            = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image       = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    phone_number        = models.CharField(max_length=20, blank=True, null=True)
    email_notifications = models.BooleanField(default=True)
    dark_mode           = models.BooleanField(default=False)
    language            = models.CharField(max_length=50, default='English')
    two_factor_auth     = models.BooleanField(default=False)
    created_at          = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return self.employer.username