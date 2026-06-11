from django.db import models
from django.contrib.auth.models import User
import uuid
from django.core.validators import MinValueValidator
 
 
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
    company       = models.CharField(max_length=200, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    skills = models.JSONField(default=list, blank=True)
    location      = models.CharField(max_length=100, blank=True, null=True, db_index=True)
 
    def __str__(self):
        return self.full_name
 
 
class Job(models.Model):
 
    JOB_TYPE_CHOICES = (
        ('Remote',  'Remote'),
        ('On-site', 'On-site'),
        ('Hybrid',  'Hybrid'),
    )
 
    CATEGORY_CHOICES = (
        ('IT', 'IT'),
        ('Sales', 'Sales'),
        ('HR', 'HR'),
        ('General', 'General'),
        ('Finance & Accounting', 'Finance & Accounting'),
        ('Marketing', 'Marketing'),
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
        ("COMPANY",    "Company Jobs"),
        ("CONSULTANT", "Consultant Jobs"),
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
        ('draft',  'Draft'),
    )
 
    JOB_TYPES = (
        ('full_time',  'Full Time'),
        ('part_time',  'Part Time'),
        ('internship', 'Internship'),
    )
 
    NATURE_OF_BUSINESS_CHOICES = (
        ('B2B',  'B2B'),
        ('B2C',  'B2C'),
        ('SaaS', 'SaaS'),
        ('D2C',  'D2C'),
        ('PaaS', 'PaaS'),
    )
 
    DEPARTMENT_CHOICES = (
        ('Sales & Business Development', 'Sales & Business Development'),
        ('Engineering - Software & QA',  'Engineering - Software & QA'),
        ('Marketing & Communication',    'Marketing & Communication'),
        ('Human Resources',              'Human Resources'),
        ('Finance & Accounting',         'Finance & Accounting'),
        ('Operations',                   'Operations'),
    )
 
    # ── Core fields ───────────────────────────────────────────────
    title         = models.CharField(max_length=200)
    company       = models.CharField(max_length=200)
    location      = models.CharField(max_length=100, db_index=True)
    work_mode     = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
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
    is_active     = models.BooleanField(default=True)
    job_type      = models.CharField(max_length=20, choices=JOB_TYPES)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    nature_of_business = models.CharField(max_length=10, choices=NATURE_OF_BUSINESS_CHOICES, blank=True, null=True)
    department    = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, blank=True, null=True)
 
    # ── CHANGED: experience field ──────────────────────────────────
    # BEFORE: experience = models.CharField(max_length=50)
    #   Problem: stored messy strings like "2-3 years", "Fresher", "3+ yrs"
    #   You can't filter "show me jobs needing 3 years experience" on a string.
    #
    # AFTER: two IntegerFields — min and max
    #   Example: a job needing 2-5 years → min_experience=2, max_experience=5
    #   Now filtering works perfectly:
    #   Job.objects.filter(min_experience__lte=3, max_experience__gte=3)
    #   = "give me jobs where 3 years fits inside the range"
    #
    # default=0 means Fresher-friendly (no experience required minimum)
    # default=5 means up to 5 years by default — adjust as needed
    min_experience = models.IntegerField(default=0)   # e.g. 2
    max_experience = models.IntegerField(default=5)   # e.g. 5
 
    # ── CHANGED: skills field ──────────────────────────────────────
    # BEFORE: skills = models.CharField(max_length=300)
    #   Problem: stored as a plain string "Python, Django, SQL"
    #   You had to split() it manually everywhere — messy and error-prone.
    #   Also limited to 300 chars — breaks if many skills.
    #
    # AFTER: JSONField stores a real Python list ["Python", "Django", "SQL"]
    #   No more splitting. No character limit issue.
    #   In templates: {% for skill in job.skills %} — works directly.
    #   In views: Job.objects.filter(skills__contains="Python") — works.
    #
    # default=list means each new job starts with an empty list []
    # Never use default=[] directly — Django would share one list across all rows (bug).
    skills = models.JSONField(default=list)
 
    # ── Salary fields ─────────────────────────────────────────────
    salary_disclosed = models.BooleanField(default=True)
    min_salary = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )
    max_salary = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )
 
    # ── experience_display property ───────────────────────────────
    # This is a @property — it's NOT stored in the database.
    # It's a computed value you can use in templates: {{ job.experience_display }}
    # It reads min_experience and max_experience and builds a nice string.
    @property
    def experience_display(self):
        if self.min_experience == 0:
            return f"Fresher / 0-{self.max_experience} yrs"
        return f"{self.min_experience}-{self.max_experience} yrs"
 
    # ── salary_display property ───────────────────────────────────
    @property
    def salary_display(self):
        if not self.salary_disclosed:
            return "Not Disclosed"
        if self.min_salary and self.max_salary:
            return f"₹{self.min_salary:,} – ₹{self.max_salary:,} per year"
        elif self.min_salary:
            return f"₹{self.min_salary:,}+ per year"
        elif self.max_salary:
            return f"Up to ₹{self.max_salary:,} per year"
        return "Not Disclosed"
 
    # ── skills_list is now a property not a method ─────────────────
    # BEFORE: def skills_list(self): return [s.strip() for s in self.skills.split(',')]
    #   Problem: skills was a string, had to split manually.
    #
    # AFTER: skills is already a list (JSONField), so just return it directly.
    #   We still keep the name skills_list so templates don't break.
    @property
    def skills_list(self):
        if isinstance(self.skills, list):
            return self.skills
        # Safety fallback: if old string data exists, split it
        if isinstance(self.skills, str) and self.skills:
            return [s.strip() for s in self.skills.split(',')]
        return []
 
    def conditions_list(self):
        if not self.conditions:
            return []
        if '•' in self.conditions:
            return [c.strip() for c in self.conditions.split('•') if c.strip()]
        return [c.strip() for c in self.conditions.split(',') if c.strip()]
 
    class Meta:
        indexes = [
            models.Index(fields=['location', 'job_type']),  # compound index
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"
 
 
 
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
 
    def __str__(self):
        return f"{self.user.username} - verified: {self.email_verified}"
 
 
class Application(models.Model):
 
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
 
    job       = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
 
    resume   = models.FileField(upload_to='resumes/', null=True, blank=True)
    status   = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Applied'
    )
 
    applied_at = models.DateTimeField(auto_now_add=True)
 
    experience = models.PositiveIntegerField(default=0)
    location     = models.CharField(max_length=100, blank=True, null=True)
    skills       = models.JSONField(default=list, blank=True)
    phone_number = models.CharField(max_length=15,  blank=True, null=True)
 
    interview_date  = models.DateField(null=True, blank=True)
    interview_time  = models.TimeField(null=True, blank=True)
    interview_link  = models.URLField(null=True,  blank=True)
    interview_notes = models.TextField(null=True, blank=True)
 
    @classmethod
    def get_status_choices(cls):
        return [choice[0] for choice in cls.STATUS_CHOICES]
 
    def __str__(self):
        return f"{self.applicant.username} applied for {self.job.title}"
 
    class Meta:
        unique_together = ('job', 'applicant')
 
 
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
 
    logo           = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    description    = models.TextField(blank=True)
    industry       = models.CharField(max_length=100, blank=True)
    founded_year   = models.IntegerField(null=True, blank=True)
    employee_count = models.CharField(max_length=50, blank=True)
    company_type   = models.CharField(max_length=50, blank=True)
 
    location       = models.CharField(max_length=200, blank=True)
    city           = models.CharField(max_length=100, blank=True)
    state          = models.CharField(max_length=100, blank=True)
    country        = models.CharField(max_length=100, blank=True, default='India')
 
    website        = models.URLField(blank=True, null=True)
    hr_email       = models.EmailField(blank=True)
    phone          = models.CharField(max_length=20, blank=True)
    hr_contact     = models.CharField(max_length=100, blank=True)
 
    linkedin       = models.URLField(blank=True, null=True)
    twitter        = models.URLField(blank=True, null=True)
    instagram      = models.URLField(blank=True, null=True)
    other_link     = models.URLField(blank=True, null=True)
 
    benefits       = models.CharField(max_length=500, blank=True)
    technologies   = models.CharField(max_length=500, blank=True)
 
    def __str__(self):
        return self.company
 
 
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