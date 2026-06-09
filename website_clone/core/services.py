# ============================================================
# services.py  —  Business logic extracted from views
# Rule: Views only handle request/response.
#       All business logic lives here.
# ============================================================

import json
import datetime
from django.utils import timezone
from django.db.models import Count


# ===================== REPORT SERVICE =====================

class ReportService:
    """
    Centralised report logic used by:
      - reports()        view
      - export_reports_pdf()  view
      - export_reports_excel() view

    Before: same DB queries copy-pasted in 3 places  ❌
    After:  one place, three views just call it       ✅
    """

    @staticmethod
    def get_summary(user):
        """
        Returns basic counts used by both PDF and Excel export
        and the reports dashboard.
        """
        from .models import Application, Interview, Job

        applications = Application.objects.filter(job__employer=user)
        return {
            'total_jobs':         Job.objects.filter(employer=user).count(),
            'total_applications': applications.count(),
            'shortlisted_count':  applications.filter(status='Shortlisted').count(),
            'rejected_count':     applications.filter(status='Rejected').count(),
            'interview_count':    Interview.objects.filter(job__employer=user).count(),
        }

    @staticmethod
    def get_dashboard_context(user, date_from='', date_to='', selected_job=''):
        """
        Full context for the reports dashboard page.
        Accepts optional filters: date range and job title.
        """
        from .models import Application, Interview, Job

        today = timezone.now().date()
        jobs  = Job.objects.filter(employer=user)

        # ── Base filtered queryset ────────────────────────
        applications_qs = Application.objects.filter(job__employer=user)
        if date_from:
            applications_qs = applications_qs.filter(applied_at__date__gte=date_from)
        if date_to:
            applications_qs = applications_qs.filter(applied_at__date__lte=date_to)
        if selected_job:
            applications_qs = applications_qs.filter(job__title=selected_job)

        total_applications = applications_qs.count()

        def pct(count):
            return round((count / total_applications) * 100) if total_applications else 0

        # ── Top jobs ──────────────────────────────────────
        top_jobs_qs = jobs.annotate(
            applications_count=Count('applications')
        ).order_by('-applications_count')[:8]

        top_jobs = []
        for job in top_jobs_qs:
            sc = Application.objects.filter(job=job, status='Shortlisted').count()
            top_jobs.append({
                'title':              job.title,
                'applications_count': job.applications_count,
                'shortlisted_count':  sc,
                'views':              job.views,
                'hire_rate':          round((sc / job.applications_count) * 100)
                                      if job.applications_count else 0,
            })

        # ── Monthly trend (last 6 months) ─────────────────
        monthly_applications, monthly_hires, month_labels = [], [], []
        for i in range(5, -1, -1):
            month = (today.month - i - 1) % 12 + 1
            year  = today.year + ((today.month - i - 1) // 12)
            month_labels.append(timezone.datetime(year, month, 1).strftime('%b'))
            monthly_applications.append(
                Application.objects.filter(
                    job__employer=user,
                    applied_at__year=year,
                    applied_at__month=month
                ).count()
            )
            monthly_hires.append(
                Application.objects.filter(
                    job__employer=user,
                    applied_at__year=year,
                    applied_at__month=month,
                    status='Offer'
                ).count()
            )

        interviewed_count = applications_qs.filter(
            status__in=['Interview', 'Interview Scheduled']
        ).count()

        return {
            'total_jobs':           jobs.count(),
            'total_applications':   total_applications,
            'shortlisted_count':    applications_qs.filter(status='Shortlisted').count(),
            'rejected_count':       applications_qs.filter(status='Rejected').count(),
            'pending_count':        applications_qs.filter(status='Applied').count(),
            'interview_count':      Interview.objects.filter(job__employer=user).count(),
            'total_views':          sum(job.views for job in jobs),
            'screened_percent':     pct(applications_qs.filter(status='Screening').count()),
            'shortlisted_percent':  pct(applications_qs.filter(status='Shortlisted').count()),
            'interview_percent':    pct(interviewed_count),
            'selected_percent':     pct(applications_qs.filter(status='Offer').count()),
            'top_jobs':             top_jobs,
            'bar_labels':           json.dumps([j['title'] for j in top_jobs]),
            'bar_data':             json.dumps([j['applications_count'] for j in top_jobs]),
            'month_labels':         json.dumps(month_labels),
            'monthly_applications': json.dumps(monthly_applications),
            'monthly_hires':        json.dumps(monthly_hires),
            'selected_job':         selected_job,
            'date_from':            date_from,
            'date_to':              date_to,
        }

    @staticmethod
    def get_all_applications(user):
        """
        Returns latest 50 applications for PDF export.
        Reused so export_pdf doesn't query independently.
        """
        from .models import Application
        return (
            Application.objects
            .filter(job__employer=user)
            .select_related('applicant', 'job')
            .order_by('-applied_at')[:50]
        )

    @staticmethod
    def get_top_jobs_for_excel(user):
        """
        Returns all employer jobs with application + shortlist counts.
        Used by Excel export sheet 3.
        """
        from .models import Application, Job
        result = []
        for job in Job.objects.filter(employer=user):
            app_count = Application.objects.filter(job=job).count()
            sc        = Application.objects.filter(job=job, status='Shortlisted').count()
            result.append({
                'title':     job.title,
                'app_count': app_count,
                'sc':        sc,
                'views':     job.views,
                'hire_rate': round((sc / app_count) * 100) if app_count else 0,
            })
        return result


# ===================== SETTINGS SERVICE =====================

class SettingsService:
    """
    Handles all settings update logic.

    Before: settings view touched 3 models directly  ❌
    After:  view calls one method, service handles all ✅
    """

    @staticmethod
    def update_all(user, post_data, files):
        """
        Master method — updates User + UserProfile + EmployerSettings
        in one call from the view.
        """
        SettingsService._update_user(user, post_data)
        SettingsService._update_user_profile(user, post_data)
        SettingsService._update_employer_settings(user, post_data, files)

    @staticmethod
    def _update_user(user, data):
        full_name = data.get('full_name', '').strip()
        if full_name:
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name  = parts[1] if len(parts) > 1 else ''
        email = data.get('email', '').strip()
        if email:
            user.email = email
        user.save()

    @staticmethod
    def _update_user_profile(user, data):
        try:
            profile = user.userprofile
            company = data.get('company', '').strip()
            if company:
                profile.company = company
            profile.save()
        except Exception:
            pass

    @staticmethod
    def _update_employer_settings(user, data, files):
        from .models import EmployerSettings
        employer_settings, _ = EmployerSettings.objects.get_or_create(employer=user)
        employer_settings.phone_number        = data.get('phone', '').strip()
        employer_settings.email_notifications = (data.get('email_notifications') == 'on')
        employer_settings.two_factor_auth     = (data.get('two_factor_enabled') == 'on')
        employer_settings.language            = data.get('language', 'English')
        if files.get('profile_image'):
            employer_settings.profile_image = files['profile_image']
        employer_settings.save()