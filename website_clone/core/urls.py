from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import employer_login, employer_register, employer_dashboard

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path("logout/", views.logout_view, name="logout"),
    path('employer-login/', views.employer_login_page, name='employer_login'),
    path('search/', views.search_jobs, name='search_jobs'),
    path('remote-jobs/', views.remote_jobs_page, name='remote_jobs'),
    path('mnc-jobs/',views.mnc_jobs_page, name='mnc_jobs'),
    path('banking-finance-jobs/', views.banking_finance_jobs_page, name='banking_finance_jobs'),
    path('startup-jobs/', views.startup_jobs_page, name='startup_jobs'),
    path('software-it-jobs/', views.software_it_jobs_page, name='software_it_jobs'),
    path('internship-jobs/', views.internship_jobs_page, name='internship_jobs'),
    path('engineering-jobs/', views.engineering_jobs_page, name='engineering_jobs'),
    path('marketing-jobs/', views.marketing_jobs_page, name='marketing_jobs'),
    path('fortune-jobs/', views.fortune_jobs_page, name='fortune_jobs'),
    path('human-resources-jobs/', views.human_resources_jobs_page, name='human_resources_jobs'),
    path('project-management-jobs/', views.project_management_jobs_page, name='project_management_jobs'),
    path('it-jobs/', views.it_jobs_page, name='it_jobs'),
    path('sales-jobs/', views.sales_jobs_page, name='sales_jobs'),
    path('data-science-jobs/', views.data_science_jobs_page, name='data_science_jobs'),
    path('fresher-jobs/', views.fresher_jobs_page, name='fresher_jobs'),
    path('walk-in-jobs/', views.walk_in_jobs_page, name='walk_in_jobs'),
    path('part-time-jobs/', views.part_time_jobs_page, name='part_time_jobs'),
    path('delhi-jobs/', views.delhi_jobs_page, name='delhi_jobs'),
    path('mumbai-jobs/', views.mumbai_jobs_page, name='mumbai_jobs'),
    path('bangalore-jobs/', views.bangalore_jobs_page, name='bangalore_jobs'),
    path('hyderabad-jobs/', views.hyderabad_jobs_page, name='hyderabad_jobs'),
    path('chennai-jobs/', views.chennai_jobs_page, name='chennai_jobs'),
    path('pune-jobs/', views.pune_jobs_page, name='pune_jobs'),
    path('company-unicorn/', views.company_unicorn, name='company_unicorn'),
    path('company-mnc/', views.company_mnc_jobs_page, name='company_mnc'),
    path('company-startups/', views.company_startups_jobs_page, name='company_startups'),
    path('company-product-based/', views.company_product_based_jobs_page, name='company_product_based'),
    path('company-internet/', views.company_internet_jobs_page, name='company_internet'),
    path('top-companies-jobs/', views.company_top_companies_jobs_page, name='top_companies_jobs'),
    path('company-it-companies-jobs/', views.company_it_companies_jobs_page, name='company_it_companies_jobs'),
    path('company-fintech-companies-jobs/', views.company_fintech_jobs_page, name='company_fintech_companies_jobs'),
    path('company-sponsored-jobs/', views.company_sponsored_companies_jobs_page, name='company_sponsored_companies_jobs'),
    path('company-featured-jobs/', views.company_featured_companies_jobs_page, name='company_featured_companies_jobs'),
    path('saved-jobs/', views.saved_jobs_page, name='saved_jobs'),
    path('save-job/<int:job_id>/', views.save_job, name='save_job'),
    path(
        'apply-job/<int:job_id>/',
        views.apply_job,
        name='apply_job'
    ),
    path(
    'applied-jobs/',
    views.applied_jobs_page,
    name='applied_jobs'
    ),
    path(
    'recruiter-applications/',
    views.recruiter_applications,
    name='recruiter_applications'
    ),
    path(
    'update-status/<int:app_id>/<str:status>/',
    views.update_status,
    name='update_status'
    ),
    path(
        'employer/register/',
        employer_register,
        name='employer_register'
    ),
    path(
        'employer/login/',
        employer_login,
        name='employer_login'
    ),
    path(
    'employer-login-page/',
    views.employer_login,
    name='employer_login_page'
    ),
    
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('employer/dashboard/data/', views.dashboard_realtime_data, name='dashboard_data'),
    path('post-job/', views.post_job, name='post_job'),
    path('manage-jobs/', views.manage_jobs, name='manage_jobs'),
    path(
    'applicants/',
    views.applicants,
    name='applicants'
    ),
    path(
    'shortlisted/',
    views.shortlisted_candidates,
    name='shortlisted_candidates'
    ),
    path(
    'interviews/',
    views.interviews,
    name='interviews'
    ),
    # ✅ CORRECT
    path(
    'messages/',
    views.inbox_messages,   # ← updated to new function name
    name='messages'         # ← URL name stays same, no HTML changes needed
    ),
    path(
    'reports/',
    views.reports,
    name='reports'
    ),
    path(
    'company-profile/',
    views.company_profile,
    name='company_profile'
    ),
    path(
    'subscription/',
    views.subscription,
    name='subscription'
    ),
    path(
    'settings/',
    views.settings,
    name='settings'
    ),
    path(
    'logout/',
    views.logout_view,
    name='logout'
    ),
    path('jobs/', views.all_jobs, name='all_jobs'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)