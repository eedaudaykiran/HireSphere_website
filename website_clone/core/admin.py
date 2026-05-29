from django.contrib import admin
from .models import (
    Job, UserProfile, Application, Interview,
    Message, CompanyProfile, EmployerSettings, SavedJob
)
 
 
# ── Job Admin ─────────────────────────────────────────────────
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
 
    list_display = (
        'title', 'company', 'location',
        'salary_info', 'salary_disclosed',
        'status', 'is_active', 'created_at'
    )
 
    list_filter = (
        'salary_disclosed', 'status',
        'is_active', 'work_mode',
        'category', 'company'
    )
 
    search_fields = ('title', 'company', 'location')
 
    list_editable = (
        'salary_disclosed',
        'status',
        'is_active',
    )
 
    fieldsets = (
        ('📋 Basic Info', {
            # FIX: 'company' stays here only — removed from Company Details below
            'fields': ('title', 'company', 'location', 'experience', 'work_mode', 'job_type', 'status', 'is_active')
        }),
        ('💰 Salary', {
            'fields': ('salary_disclosed', 'min_salary', 'max_salary'),
            'description': 'Set salary_disclosed=False to show "Not Disclosed". Enter LPA values (e.g. 5 for ₹5 LPA).'
        }),
        ('🏢 Company Details', {
            # FIX: removed 'company' from here — it was duplicated from Basic Info above
            'fields': ('industry', 'category', 'posted_by', 'employer')
        }),
        ('📝 Job Details', {
            'fields': ('description', 'skills', 'conditions', 'role_category', 'education', 'duration')
        }),
        ('⭐ Extras', {
            'fields': ('is_featured', 'is_sponsored', 'logo', 'rating', 'views'),
            'classes': ('collapse',)
        }),
    )
 
    @admin.display(description='Salary')
    def salary_info(self, obj):
        return obj.salary_display
 
 
# ── UserProfile Admin ──────────────────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
 
    list_display = ('full_name', 'role', 'company', 'work_status')
 
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
    # FIX: 'company' is not a field on CompanyProfile model — replaced with 'employer'
    list_display  = ('employer', 'industry', 'location')
    search_fields = ('employer__username',)
 
 
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