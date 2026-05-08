from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
import datetime
from django.http import HttpResponse, JsonResponse

from .forms import RegisterForm, LoginForm
from .models import UserProfile, Job, SavedJob, ApplyJob, Application
from .forms import EmployerRegisterForm

# ===================== FILTER FUNCTIONS =====================

def filter_by_work_mode(qs, request):
    work_modes = request.GET.getlist('work_mode')
    if work_modes:
        qs = qs.filter(work_mode__in=work_modes)
    return qs, work_modes


def filter_by_category(qs, request):
    categories = request.GET.getlist('category')
    if categories:
        qs = qs.filter(category__in=categories)
    return qs, categories


def filter_by_location(qs, request):
    locations = request.GET.getlist('location')
    if locations:
        query = Q()
        for loc in locations:
            query |= Q(location__icontains=loc)
        qs = qs.filter(query)
    return qs, locations


def filter_by_salary(qs, request):
    """
    Expects salary values like '0-3', '3-6', ..., '30-35'
    Filters jobs where min_salary >= lower AND max_salary <= upper
    """
    salaries = request.GET.getlist('salary')
    if salaries:
        query = Q()
        for s in salaries:
            try:
                min_s, max_s = s.split('-')
                query |= Q(min_salary__gte=int(min_s), max_salary__lte=int(max_s))
            except (ValueError, AttributeError):
                continue
        qs = qs.filter(query)
    return qs, salaries


def filter_by_experience(qs, request):
    exp = request.GET.get('experience')
    if exp and exp != "30":
        qs = qs.filter(experience__icontains=exp)
    return qs, exp


def filter_by_freshness(qs, request):
    freshness = request.GET.get('freshness')
    if freshness:
        try:
            days = int(freshness)
            cutoff = timezone.now() - datetime.timedelta(days=days)
            qs = qs.filter(created_at__gte=cutoff)
        except (ValueError, TypeError):
            pass
    return qs, freshness


# ===================== EXISTING VIEWS =====================

def index(request):
    jobs = Job.objects.all()
    return render(request, 'core/index.html', {'jobs': jobs})


def search_jobs(request):
    keyword    = request.GET.get('keyword', '')
    experience = request.GET.get('experience', '')
    location   = request.GET.get('location', '')

    jobs = Job.objects.all()

    if keyword:
        jobs = jobs.filter(
            Q(title__icontains=keyword) |
            Q(company__icontains=keyword) |
            Q(skills__icontains=keyword)
        )
    if experience:
        jobs = jobs.filter(experience__icontains=experience)
    if location:
        jobs = jobs.filter(location__icontains=location)

    context = {
        'jobs': jobs,
        'keyword': keyword,
        'experience': experience,
        'location': location,
    }
    return render(request, 'core/search_results.html', context)


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            full_name     = form.cleaned_data["full_name"]
            email         = form.cleaned_data["email"]
            password      = form.cleaned_data["password"]
            mobile_number = form.cleaned_data["mobile_number"]
            work_status   = form.cleaned_data["work_status"]

            base_username = email.split("@")[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name
            )

            UserProfile.objects.create(
                user=user,
                full_name=full_name,
                mobile_number=mobile_number,
                work_status=work_status
            )

            messages.success(request, f"✅ Registration successful! Welcome {full_name}. Please login.")
            return redirect("login")
        else:
            messages.error(request, "❌ Registration failed. Please fix errors below.")
    else:
        form = RegisterForm()

    return render(request, "core/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email    = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            try:
                user_obj = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                messages.error(request, "❌ No account found with this email.")
                return render(request, "core/login.html", {"form": form})

            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"✅ Welcome back, {user.first_name}!")
                return redirect("index")
            else:
                messages.error(request, "❌ Incorrect password.")
        else:
            messages.error(request, "❌ Please fill all fields correctly.")
    else:
        form = LoginForm()

    return render(request, "core/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "✅ Logged out successfully.")
    return redirect("login")


def employer_login_page(request):
    return render(request, 'core/employer_login.html')


# ===================== REFACTORED remote_jobs_page =====================

def remote_jobs_page(request):
    jobs = Job.objects.all().order_by('-id')

    jobs, selected_work_modes  = filter_by_work_mode(jobs, request)
    jobs, selected_categories   = filter_by_category(jobs, request)
    jobs, selected_locations    = filter_by_location(jobs, request)
    jobs, selected_salaries     = filter_by_salary(jobs, request)
    jobs, selected_experience   = filter_by_experience(jobs, request)
    jobs, selected_freshness    = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')
    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    durations = request.GET.getlist('duration')
    if durations:
        jobs = jobs.filter(duration__in=durations)

    educations = request.GET.getlist('education')
    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')
    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    industries = request.GET.getlist('industry')
    if industries:
        jobs = jobs.filter(industry__in=industries)

    companies = request.GET.getlist('company')
    if companies:
        jobs = jobs.filter(company__in=companies)

    roles = request.GET.getlist('role_category')
    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.all()

    salary_ranges = ['0-3', '3-6', '6-10', '10-15', '15-20', '20-25', '25-30', '30-35']
    salary_counts = {}
    for r in salary_ranges:
        try:
            low, high = r.split('-')
            cnt = all_jobs.filter(min_salary__gte=int(low), max_salary__lte=int(high)).count()
        except:
            cnt = 0
        salary_counts[r] = cnt

    category_counts = {
        item['category']: item['total']
        for item in all_jobs.values('category').annotate(total=Count('id'))
    }

    location_list = ['Bangalore', 'Delhi', 'Mumbai', 'Hyderabad', 'Pune', 'Chennai']
    location_counts = {
        loc: all_jobs.filter(location__icontains=loc).count()
        for loc in location_list
    }

    company_type_counts = {
        item['company_type']: item['total']
        for item in all_jobs.values('company_type').annotate(total=Count('id'))
    }

    role_counts = {
        item['role_category']: item['total']
        for item in all_jobs.values('role_category').annotate(total=Count('id'))
    }

    all_durations = all_jobs.exclude(duration__isnull=True).exclude(duration='').values_list('duration', flat=True).distinct()
    duration_counts = {d: all_jobs.filter(duration=d).count() for d in all_durations}

    all_educations = all_jobs.exclude(education__isnull=True).exclude(education='').values_list('education', flat=True).distinct()
    education_counts = {e: all_jobs.filter(education=e).count() for e in all_educations}

    all_posted_by = all_jobs.exclude(posted_by__isnull=True).exclude(posted_by='').values_list('posted_by', flat=True).distinct()
    posted_by_counts = {p: all_jobs.filter(posted_by=p).count() for p in all_posted_by}

    all_industries = all_jobs.exclude(industry__isnull=True).exclude(industry='').values_list('industry', flat=True).distinct()
    industry_counts = {i: all_jobs.filter(industry=i).count() for i in all_industries}

    company_counts = {
        item['company']: item['total']
        for item in all_jobs.values('company').annotate(total=Count('id'))
    }

    # Get selected stipends from request
    stipends = request.GET.getlist('stipend')
    if stipends:
        stipend_query = Q()
        for s in stipends:
            if s == 'unpaid':
                stipend_query |= Q(min_salary=0, max_salary=0)
            elif s == '0-10':
                stipend_query |= Q(min_salary__gte=0, max_salary__lte=10)
            elif s == '10-20':
                stipend_query |= Q(min_salary__gte=10, max_salary__lte=20)
            elif s == '20-30':
                stipend_query |= Q(min_salary__gte=20, max_salary__lte=30)
            elif s == '30-50':
                stipend_query |= Q(min_salary__gte=30, max_salary__lte=50)
            elif s == '50+':
                stipend_query |= Q(min_salary__gte=50)
        jobs = jobs.filter(stipend_query)

    # Stipend counts for display
    stipend_ranges = {
        'unpaid': jobs.filter(min_salary=0, max_salary=0).count(),
        '0-10':   Job.objects.filter(min_salary__gte=0,  max_salary__lte=10).count(),
        '10-20':  Job.objects.filter(min_salary__gte=10, max_salary__lte=20).count(),
        '20-30':  Job.objects.filter(min_salary__gte=20, max_salary__lte=30).count(),
        '30-50':  Job.objects.filter(min_salary__gte=30, max_salary__lte=50).count(),
        '50+':    Job.objects.filter(min_salary__gte=50).count(),
    }
    stipend_counts = stipend_ranges

    return render(request, 'core/remote_jobs.html', {
        'jobs': jobs,
        'selected_work_modes': selected_work_modes,
        'selected_categories': selected_categories,
        'selected_company_types': company_types,
        'selected_locations': selected_locations,
        'selected_salaries': selected_salaries,
        'selected_experience': selected_experience,
        'selected_freshness': selected_freshness,
        'selected_roles': roles,
        'selected_stipends': stipends,
        'selected_durations': durations,
        'selected_educations': educations,
        'selected_posted': posted_by,
        'selected_industries': industries,
        'selected_companies': companies,
        'salary_counts': salary_counts,
        'category_counts': category_counts,
        'location_counts': location_counts,
        'company_type_counts': company_type_counts,
        'role_counts': role_counts,
        'stipend_counts': stipend_counts,
        'duration_counts': duration_counts,
        'education_counts': education_counts,
        'posted_by_counts': posted_by_counts,
        'industry_counts': industry_counts,
        'company_counts': company_counts,
    })


# ===================== OTHER PAGES =====================

def mnc_jobs_page(request):
    jobs = Job.objects.filter(company_type__iexact="mnc").order_by('-id')
    return render(request, 'core/mnc_jobs.html', {'jobs': jobs})

def banking_finance_jobs_page(request):
    jobs = Job.objects.filter(category__iexact="Banking & Finance", work_mode__iexact="Remote")
    return render(request, 'core/banking_finance_jobs.html', {'jobs': jobs})

def startup_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', company_type__iexact='startup')
    return render(request, 'core/startup_jobs.html', {'jobs': jobs})

def software_it_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', category__icontains='software')
    return render(request, 'core/software_it_jobs.html', {'jobs': jobs})

def internship_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', category__icontains='internship').order_by('-id')
    return render(request, 'core/internship_jobs.html', {'jobs': jobs})

def engineering_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', category__icontains='engineering').order_by('-id')
    return render(request, 'core/engineering_jobs.html', {'jobs': jobs})

def marketing_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', category__icontains='marketing').order_by('-id')
    return render(request, 'core/marketing_jobs.html', {'jobs': jobs})

def fortune_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', company_type__icontains='fortune').order_by('-id')
    return render(request, 'core/fortune_jobs.html', {'jobs': jobs})

def human_resources_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', category__iexact='Human Resources').order_by('-id')
    return render(request, 'core/human_resources_jobs.html', {'jobs': jobs})

def project_management_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', category__icontains='Project Management').order_by('-id')
    return render(request, 'core/project_management_jobs.html', {'jobs': jobs})

def it_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', category__icontains='IT').order_by('-id')
    return render(request, 'core/it_jobs.html', {'jobs': jobs})

def sales_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', category__icontains='Sales').order_by('-id')
    return render(request, 'core/sales_jobs.html', {'jobs': jobs})

def data_science_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', category__icontains='Data Science').order_by('-id')
    return render(request, 'core/data_science_jobs.html', {'jobs': jobs})

def fresher_jobs_page(request):
    jobs = Job.objects.filter(experience__iexact='Fresher', work_mode__iexact='Remote').order_by('-id')
    return render(request, 'core/fresher_jobs.html', {'jobs': jobs})

def walk_in_jobs_page(request):
    jobs = Job.objects.filter(work_mode__icontains='walk').order_by('-id')
    return render(request, 'core/walk_in_jobs.html', {'jobs': jobs})

def part_time_jobs_page(request):
    jobs = Job.objects.filter(work_mode__icontains='part time').order_by('-id')
    return render(request, 'core/part_time_jobs.html', {'jobs': jobs})

def delhi_jobs_page(request):
    jobs = Job.objects.filter(location__icontains='Delhi', work_mode__iexact='Remote').order_by('-id')
    return render(request, 'core/delhi_jobs.html', {'jobs': jobs})

def mumbai_jobs_page(request):
    jobs = Job.objects.filter(location__icontains='Mumbai', work_mode__iexact='Remote').order_by('-id')
    return render(request, 'core/mumbai_jobs.html', {'jobs': jobs})

def bangalore_jobs_page(request):
    jobs = Job.objects.filter(Q(location__icontains='Bangalore') | Q(location__icontains='Bengaluru'), work_mode__iexact='Remote').order_by('-id')
    return render(request, 'core/bangalore_jobs.html', {'jobs': jobs})

def hyderabad_jobs_page(request):
    jobs = Job.objects.filter(location__icontains='Hyderabad').filter(Q(work_mode__iexact='Remote') | Q(work_mode__iexact='Hybrid') | Q(work_mode__iexact='On-site')).order_by('-id')
    return render(request, 'core/hyderabad_jobs.html', {'jobs': jobs})

def chennai_jobs_page(request):
    jobs = Job.objects.filter(location__icontains='Chennai').filter(Q(work_mode__iexact='Remote') | Q(work_mode__iexact='Hybrid') | Q(work_mode__iexact='On-site')).order_by('-id')
    return render(request, 'core/chennai_jobs.html', {'jobs': jobs})

def pune_jobs_page(request):
    jobs = Job.objects.filter(location__icontains='Pune').filter(Q(work_mode__iexact='Remote') | Q(work_mode__iexact='Hybrid') | Q(work_mode__iexact='On-site')).order_by('-id')
    return render(request, 'core/pune_jobs.html', {'jobs': jobs})

def company_unicorn(request):
    jobs = Job.objects.filter(company_type__icontains='unicorn').order_by('-id')
    return render(request, 'core/company_unicorn.html', {'jobs': jobs})

def company_mnc_jobs_page(request):
    jobs = Job.objects.filter(Q(company_type__icontains='mnc') | Q(company_type__icontains='multinational')).order_by('-id')
    return render(request, 'core/company_mnc_jobs.html', {'jobs': jobs})

def company_startups_jobs_page(request):
    jobs = Job.objects.filter(Q(company_type__icontains='startup') | Q(company_type__icontains='start-up')).order_by('-id')
    return render(request, 'core/company_startups_jobs.html', {'jobs': jobs})

def company_product_based_jobs_page(request):
    jobs = Job.objects.filter(Q(category__icontains='product') | Q(category__icontains='product based')).order_by('-id')
    return render(request, 'core/company_product_based_jobs.html', {'jobs': jobs})

def company_internet_jobs_page(request):
    jobs = Job.objects.filter(Q(company_type__icontains='internet') | Q(company_type__icontains='online') | Q(company_type__icontains='web')).order_by('-id')
    return render(request, 'core/company_internet_jobs.html', {'jobs': jobs})

def company_top_companies_jobs_page(request):
    company_keywords = ['unicorn', 'mnc', 'multinational', 'startup', 'start-up', 'internet', 'online', 'web']
    category_keywords = ['product']
    query = Q()
    for word in company_keywords:
        query |= Q(company_type__icontains=word)
    for word in category_keywords:
        query |= Q(category__icontains=word)
    jobs = Job.objects.filter(query).order_by('-id').distinct()
    return render(request, 'core/company_top_companies_jobs.html', {'jobs': jobs})

def company_it_companies_jobs_page(request):
    keywords = ['information technology', 'technology', 'tech', 'software']
    query = Q()
    for word in keywords:
        query |= Q(company_type__icontains=word)
    jobs = Job.objects.filter(query).order_by('-id').distinct()
    return render(request, 'core/company_it_companies_jobs.html', {'jobs': jobs})

def company_fintech_jobs_page(request):
    keywords = ['fintech', 'financial technology', 'finance technology', 'payments', 'digital payments', 'banking', 'nbfc']
    query = Q()
    for word in keywords:
        query |= Q(company_type__icontains=word)
    jobs = Job.objects.filter(query).order_by('-id').distinct()
    return render(request, 'core/company_fintech_companies_jobs.html', {'jobs': jobs})

def company_sponsored_companies_jobs_page(request):
    jobs = Job.objects.filter(is_sponsored=True).order_by('-id')
    return render(request, 'core/company_sponsored_companies_jobs.html', {'jobs': jobs})

def company_featured_companies_jobs_page(request):
    jobs = Job.objects.filter(is_featured=True).order_by('-id')
    return render(request, 'core/company_featured_companies_jobs.html', {'jobs': jobs})


# ===================== SAVE / APPLY / SAVED JOBS =====================

@login_required
def save_job(request, job_id):
    # Only allow POST requests from AJAX
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    job = get_object_or_404(Job, id=job_id)
    
    saved, created = SavedJob.objects.get_or_create(
        user=request.user,
        job=job
    )
    
    if created:
        # Job was newly saved
        return JsonResponse({'status': 'saved', 'message': 'Saved successfully!'})
    else:
        # Job already existed → remove it
        saved.delete()
        return JsonResponse({'status': 'removed', 'message': 'Removed from saved jobs!'})


from django.contrib import messages

@login_required
def apply_job(request, job_id):

    job = Job.objects.get(id=job_id)

    already_applied = ApplyJob.objects.filter(
        user=request.user,
        job=job
    ).exists()

    if already_applied:

        messages.warning(
            request,
            'You already applied for this job'
        )

    else:

        ApplyJob.objects.create(
            user=request.user,
            job=job
        )

        messages.success(
            request,
            'Job applied successfully'
        )

    return redirect('remote_jobs')

@login_required
def saved_jobs_page(request):
    saved = SavedJob.objects.filter(user=request.user).select_related('job').order_by('-saved_at')
    return render(request, 'core/saved_jobs.html', {
        'saved_jobs': saved
    })

@login_required
def applied_jobs_page(request):

    applied_jobs = ApplyJob.objects.filter(
        user=request.user
    ).select_related('job')

    return render(
        request,
        'core/applied_jobs.html',
        {'applied_jobs': applied_jobs}
    )
@login_required
def recruiter_applications(request):

    applications = ApplyJob.objects.select_related(
        'user',
        'job'
    ).all().order_by('-applied_at')

    return render(
        request,
        'core/recruiter_applications.html',
        {'applications': applications}
    )

@login_required
def update_status(request, app_id, status):

    application = ApplyJob.objects.get(id=app_id)

    application.status = status

    application.save()

    return redirect('recruiter_applications')

# Employer registration view

def employer_register(request):

    if request.method == "POST":

        form = EmployerRegisterForm(request.POST)

        if form.is_valid():

            username = form.cleaned_data['username']

            email = form.cleaned_data['email']

            password = form.cleaned_data['password']

            # Create Django User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # Create UserProfile
            profile = form.save(commit=False)

            profile.user = user

            profile.role = "employer"

            profile.save()

            return redirect('employer_login_page')

    else:

        form = EmployerRegisterForm()

    return render(
        request,
        'core/employer_register.html',
        {'form': form}
    )

# ===================== EMPLOYER LOGIN VIEW =====================

def employer_login(request):

    if request.method == "POST":

        username = request.POST.get('username')

        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if user.userprofile.role == "employer":

                login(request, user)

                return redirect('employer_dashboard')

            else:

                return HttpResponse(
                    "Only employers can login here"
                )

    return render(
        request,
        'core/employer_login_page.html'
    )
# ===================== EMPLOYER DASHBOARD VIEW =====================

@login_required
def employer_dashboard(request):

    # FIX 6: safely check userprofile exists
    try:
        if request.user.userprofile.role != "employer":
            return redirect('index')
    except:
        return redirect('index')

    # ✅ annotate adds application_count directly on each job object
    jobs = Job.objects.filter(employer=request.user).annotate(
        application_count=Count('applications')
    )
    total_jobs = jobs.count()

    total_applications = sum(job.application_count for job in jobs)

    total_views = sum(job.views for job in jobs)

    recent_applicants = Application.objects.filter(
        job__in=jobs
    ).select_related('applicant', 'job').order_by('-applied_at')[:10]

    context = {
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'total_views': total_views,
        'recent_applicants': recent_applicants,
        'jobs': jobs,
    }

    return render(request, 'core/employer_dashboard.html', context)

# AJAX endpoint for real-time dashboard data (e.g. for charts)

@login_required
def dashboard_realtime_data(request):
    jobs = Job.objects.filter(employer=request.user)
    recent = Application.objects.filter(
        job__in=jobs
    ).select_related('applicant', 'job').order_by('-applied_at')[:10]

    data = {
        'total_applications': Application.objects.filter(job__in=jobs).count(),
        'applicants': [
            {
                'name': app.applicant.get_full_name(),
                'job': app.job.title,
                'date': app.applied_at.strftime('%d %b %Y'),
                'status': app.status,
            }
            for app in recent
        ]
    }
    return JsonResponse(data)