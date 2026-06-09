from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import employer_login, employer_register, employer_dashboard
 
urlpatterns = [
    # ===================== BASIC =====================
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('jobs/search/', views.search_jobs, name='search_jobs'),
 
    # ===================== JOB PAGES =====================
    path('remote-jobs/', views.remote_jobs_page, name='remote_jobs_page'),
    path('mnc-jobs/', views.mnc_jobs_page, name='mnc_jobs'),
    path('banking-finance-jobs/', views.banking_finance_jobs_page, name='banking_finance_jobs'),
    path('startup-jobs/', views.startup_jobs_page, name='startup_jobs'),
    path('software-it-jobs/', views.software_it_jobs_page, name='software_it_jobs'),
    path('internship-jobs/', views.internship_jobs_page, name='internship_jobs'),
    path('engineering-jobs/', views.engineering_jobs_page, name='engineering_jobs'),
    path('marketing-jobs/', views.marketing_jobs_page, name='marketing_jobs'),
    path('fortune-jobs/', views.fortune_jobs_page, name='fortune_jobs'),
    path('human-resources-jobs/', views.human_resources_jobs_page, name='human_resources_jobs'),
    path('project-management-jobs/', views.project_management_jobs_page, name='project_management_jobs'),
    path('it-jobs/', views.software_it_jobs_page, name='it_jobs'),
    path('sales-jobs/', views.sales_jobs_page, name='sales_jobs'),
    path('data-science-jobs/', views.datascience_jobs_page, name='data_science_jobs'),
    path('fresher-jobs/', views.fresher_jobs_page, name='fresher_jobs'),
    path('walk-in-jobs/', views.walk_in_jobs_page, name='walk_in_jobs'),
    path('part-time-jobs/', views.part_time_jobs_page, name='part_time_jobs'),
    path('jobs/', views.all_jobs, name='all_jobs'),
    path(
    'finance-jobs/',
    views.finance_jobs_page,
    name='finance_jobs_page'
    ),
    path(
    'operations-jobs/',
    views.operations_jobs_page,
    name='operations_jobs_page'
    ),
 
    # ===================== CITY JOBS =====================
    path('delhi-jobs/', views.delhi_jobs_page, name='delhi_jobs'),
    path('mumbai-jobs/', views.mumbai_jobs_page, name='mumbai_jobs'),
    path('bangalore-jobs/', views.bangalore_jobs_page, name='bangalore_jobs'),
    path('hyderabad-jobs/', views.hyderabad_jobs_page, name='hyderabad_jobs'),
    path('chennai-jobs/', views.chennai_jobs_page, name='chennai_jobs'),
    path('pune-jobs/', views.pune_jobs_page, name='pune_jobs'),
    path(
    'ahmedabad-jobs/',
    views.ahmedabad_jobs_page,
    name='ahmedabad_jobs_page'
    ),

    path(
    'kolkata-jobs/',
    views.kolkata_jobs_page,
    name='kolkata_jobs_page'
    ),

    # ===================== COMPANY TYPE PAGES =====================
    path('company-unicorn/', views.company_unicorn, name='company_unicorn'),
    path('company-mnc/', views.company_mnc_jobs_page, name='company_mnc'),
    path('company-startups/', views.company_startups_jobs_page, name='company_startups'),
    path('company-product-based/', views.company_product_based_jobs_page, name='company_product_based'),
    path('company-internet/', views.company_internet_jobs_page, name='company_internet'),
    path('top-companies-jobs/', views.company_top_companies_jobs_page, name='top_companies_jobs'),
    path('company-it-companies-jobs/', views.company_it_companies_jobs_page, name='company_it_companies_jobs'),
    path(
    'company-fintech-companies-jobs/',
    views.company_fintech_companies_jobs_page,
    name='company_fintech_companies_jobs'
    ),
    path('company-sponsored-jobs/', views.company_sponsored_companies_jobs_page, name='company_sponsored_companies_jobs'),
    path('company-featured-jobs/', views.company_featured_companies_jobs_page, name='company_featured_companies_jobs'),
    
    # ===================== CANDIDATE ACTIONS =====================
    path('saved-jobs/', views.saved_jobs_page, name='saved_jobs'),
    path(
    'job/<int:job_id>/',
    views.job_detail,
    name='job_detail'
    ),
    path(
    'remove-saved-job/<int:saved_job_id>/',
    views.remove_saved_job,
    name='remove_saved_job'
    ),
    path('save-job/<int:job_id>/', views.save_job, name='save_job'),
    path('apply-job/<int:job_id>/', views.apply_job, name='apply_job'),
    path('applied-jobs/', views.applied_jobs_page, name='applied_jobs'),
 
    # ===================== RECRUITER =====================
    path('recruiter-applications/', views.recruiter_applications, name='recruiter_applications'),
    # ✅ Remove <str:status> from the URL
    # path('update-status/<int:app_id>/', views.update_status, name='update_status'),
    path(
    'update-status/<int:app_id>/<str:status>/',
    views.update_status,
    name='update_status'
    ),
 
    # ===================== EMPLOYER AUTH =====================
    path('employer/register/', employer_register, name='employer_register'),
    path('employer/login/', employer_login, name='employer_login'),
    path('employer-login/', views.employer_login_page, name='employer_login_page'),
    path('employer-login-page/', views.employer_login, name='employer_login_page'),
 
    # ===================== EMPLOYER DASHBOARD =====================
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('employer/dashboard/data/', views.dashboard_realtime_data, name='dashboard_data'),
 
    # ===================== NEW: UPDATE APPLICATION STATUS =====================
    # When employer clicks Screening / Interview / Technical / HR / Offer button
    # URL example: /update-application-status/42/Screening/
    # 42 = application ID, Screening = new status to set
    path(
        'update-application-status/<int:app_id>/<str:new_status>/',
        views.update_application_status,
        name='update_application_status'
    ),
 
    # ===================== EMPLOYER TOOLS =====================
    path('post-job/', views.post_job, name='post_job'),
    path('manage-jobs/', views.manage_jobs, name='manage_jobs'),
    path('applicants/', views.applicants, name='applicants'),
    path('shortlist-candidate/<int:app_id>/', views.shortlist_candidate, name='shortlist_candidate'),
    path('shortlisted-candidates/', views.shortlisted_candidates, name='shortlisted_candidates'),
    path('reject/<int:app_id>/', views.reject_candidate, name='reject_candidate'),
    path('interviews/', views.interviews, name='interviews'),
    path('messages/', views.inbox_messages, name='messages'),
    path('reports/', views.reports, name='reports'),
    path('company-profile/', views.company_profile, name='company_profile'),
    path('settings/', views.settings, name='settings'),
    path(
    'schedule-interview/<int:app_id>/',
    views.schedule_interview,
    name='schedule_interview'
    ),
    path(
    'edit-job/<int:job_id>/',
    views.edit_job,
    name='edit_job'
    ),
    path(
    'delete-job/<int:job_id>/',
    views.delete_job,
    name='delete_job'
    ),
    path(
    'view-applications/<int:job_id>/',
    views.view_applications,
    name='view_applications'
    ),
    path('jobs/toggle/<int:job_id>/', views.toggle_job_status, name='toggle_job_status'),
    path('reports/export/pdf/',   views.export_reports_pdf,   name='export_reports_pdf'),
    path('reports/export/excel/', views.export_reports_excel, name='export_reports_excel'),
    path('employer/change-password/',   views.change_password,   name='change_password'),
    path('employer/deactivate-account/', views.deactivate_account, name='deactivate_account'),
    path('send-message/',                  views.send_message,    name='send_message'),
    path('fetch-messages/<int:candidate_id>/', views.fetch_messages, name='fetch_messages'),
    path(
    'supply-chain-jobs/',
    views.supply_chain_jobs_page,
    name='supply_chain_jobs'
    ),
    path('foreign-mnc-jobs/', views.mnc_jobs_page, name='foreign_mnc_jobs'),
    path(
    'work-from-home-jobs/',
    views.work_from_home_jobs_page,
    name='work_from_home_jobs'
    ),
    path(
    'analytics-bi-jobs/',
    views.analytics_bi_jobs_page,
    name='analytics_bi_jobs'
    ),
    path(
    'datascience-jobs/',
    views.datascience_jobs_page,
    name='datascience_jobs'
    ),
    path('startup-jobs/',
        views.startup_jobs_page,
        name='startup_jobs'
    ),
    path('sales-jobs/', views.sales_jobs_page, name='salesjobs'),
    path('marketing-jobs/', views.marketing_jobs_page, name='marketingjobs'),
    path('banking-finance/', views.banking_finance_jobs_page, name='banking_financejobs'),
    path('engineering-jobs/', views.engineering_jobs_page, name='engineeringjobs'),
    path('hr-jobs/', views.human_resources_jobs_page, name='hr_jobs_page'),
    path('fresher-jobs/', views.fresher_jobs_page, name='fresherjobs'),
    path('about/', views.about, name='about'),
    path('careers/', views.careers, name='careers'),
    path('employer-home/', views.employer_home, name='employer_home'),
    path('sitemap/', views.sitemap, name='sitemap'),
    path('credits/', views.credits, name='credits'),
    path('help-center/', views.help_center, name='help_center'),
    path('summons-notices/', views.summons_notices, name='summons_notices'),
    path('grievances/', views.grievances, name='grievances'),
    path('report-issue/', views.report_issue, name='report_issue'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('fraud-alert/', views.fraud_alert, name='fraud_alert'),
    path('trust-safety/', views.trust_safety, name='trust_safety'),
    path('search-jobs/', views.search_jobs, name='search_jobs'),
    path('browser-companies/', views.browser_companies, name='browser_companies'),
    path('resume-builder/', views.resume_builder, name='resume_builder'),
    path('career-advice/', views.career_advice, name='career_advice'),
    path('salary-calculator/', views.salary_calculator, name='salary_calculator'),
    path('hiring-solutions/', views.hiring_solutions, name='hiring_solutions'),
    path('view-plans/', views.view_plans, name='view_plans'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)