from django.contrib import admin
from .models import (
    Job, UserProfile, Application, Interview,
    Message, CompanyProfile, EmployerSettings, SavedJob
)


# ── Job Admin ─────────────────────────────────────────────────
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):

    # What columns show in the job list page
    list_display = (
        'title', 'company', 'location',
        'salary_info', 'salary_disclosed',
        'status', 'is_active', 'created_at'
    )

    # Right sidebar filters
    list_filter = (
        'salary_disclosed', 'status',
        'is_active', 'work_mode',
        'category', 'company_type'
    )

    # Search bar
    search_fields = ('title', 'company', 'location')

    # ✅ Click salary fields directly in the list — no need to open each job
    list_editable = (
        'salary_disclosed',
        'status',
        'is_active',
    )

    # Organize the job edit page into sections
    fieldsets = (
        ('📋 Basic Info', {
            'fields': ('title', 'company', 'location', 'experience', 'work_mode', 'job_type', 'status', 'is_active')
        }),
        ('💰 Salary', {
            'fields': ('salary_disclosed', 'min_salary', 'max_salary'),
            'description': 'Set salary_disclosed=False to show "Not Disclosed". Enter LPA values (e.g. 5 for ₹5 LPA).'
        }),
        ('🏢 Company Details', {
            'fields': ('company_type', 'industry', 'category', 'posted_by', 'employer')
        }),
        ('📝 Job Details', {
            'fields': ('description', 'skills', 'conditions', 'role_category', 'education', 'duration')
        }),
        ('⭐ Extras', {
            'fields': ('is_featured', 'is_sponsored', 'logo', 'rating', 'views'),
            'classes': ('collapse',)  # hidden by default, click to expand
        }),
    )

    # Custom column showing salary cleanly in list view
    @admin.display(description='Salary')
    def salary_info(self, obj):
        return obj.salary_display


# ── UserProfile Admin ──────────────────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = ('full_name', 'role', 'company_name', 'work_status')

    class Media:
        js = ('js/profile_toggle.js',)


# ── Other models ───────────────────────────────────────────────
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display  = ('applicant', 'job', 'status', 'applied_at')
    list_filter   = ('status',)
    search_fields = ('applicant__username', 'job__title')
    list_editable = ('status',)


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'round_type', 'interview_date', 'status')
    list_filter  = ('status',)


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display  = ('company_name', 'employer', 'industry', 'location')
    search_fields = ('company_name',)


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'saved_at')


@admin.register(EmployerSettings)
class EmployerSettingsAdmin(admin.ModelAdmin):
    list_display = ('employer', 'email_notifications', 'dark_mode', 'two_factor_auth')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'is_read', 'created_at')
    list_filter  = ('is_read',)