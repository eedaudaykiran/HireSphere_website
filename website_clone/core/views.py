from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import datetime
from django.http import HttpResponse, JsonResponse
import re

from .forms import RegisterForm, LoginForm, EmployerRegisterForm, JobForm, CompanyProfileForm, EmployerSettingsForm
from .models import UserProfile, Job, SavedJob, ApplyJob, Application, Interview, Message, CompanyProfile, EmployerSettings


def candidate_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "❌ Please login first.")
            return redirect('login')
        try:
            profile = request.user.userprofile
        except:
            messages.error(request, "❌ Profile not found.")
            return redirect('login')
        if profile.role != 'candidate':
            messages.error(request, "❌ This page is for candidates only.")
            return redirect('employer_dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper

def employer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "❌ Please login first.")
            return redirect('login')
        try:
            profile = request.user.userprofile
        except:
            messages.error(request, "❌ Profile not found.")
            return redirect('login')
        if profile.role != 'employer':
            messages.error(request, "❌ This page is for employers only.")
            return redirect('index')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


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


# ===================== BASIC VIEWS =====================

def index(request):
    jobs = Job.objects.all()
    return render(request, 'core/index.html', {'jobs': jobs})


def search_jobs_page(request):
    query      = request.GET.get('q', '').strip()
    location   = request.GET.get('location', '').strip()
    experience = request.GET.get('experience', '').strip()

    jobs = Job.objects.filter(is_active=True)

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(skills__icontains=query) |
            Q(company__icontains=query) |
            Q(description__icontains=query)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if experience:
        jobs = jobs.filter(experience__icontains=experience)

    return render(request, 'core/search_results.html', {
        'jobs': jobs,
        'query': query,
        'location': location,
        'experience': experience,
        'total': jobs.count(),
    })


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

# ===================== LOGIN =====================
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email    = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            # Step 1: Find user by email
            try:
                user_obj = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                messages.error(request, "❌ No account found with this email.")
                return render(request, "core/login.html", {"form": form})

            # Step 2: Check password
            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"✅ Welcome back, {user.first_name}!")

                # Step 3: Redirect based on role
                # employer → employer dashboard
                # candidate → home page
                try:
                    if user.userprofile.role == 'employer':
                        return redirect('employer_dashboard')
                    else:
                        return redirect('index')
                except:
                    # If userprofile doesn't exist for some reason
                    return redirect('index')

            else:
                messages.error(request, "❌ Incorrect password.")

        else:
            messages.error(request, "❌ Please fill all fields correctly.")

    else:
        form = LoginForm()

    return render(request, "core/login.html", {"form": form})

# ===================== LOGOUT =====================
def logout_view(request):
    logout(request)
    messages.success(request, "✅ Logged out successfully.")
    return redirect("login")

# @employer_required
def employer_login_page(request):
    return render(request, 'core/employer_login.html')


# ===================== REMOTE JOBS PAGE =====================
@login_required
def remote_jobs_page(request):
    jobs = Job.objects.all().order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)
    jobs, selected_categories  = filter_by_category(jobs, request)
    jobs, selected_locations   = filter_by_location(jobs, request)
    jobs, selected_salaries    = filter_by_salary(jobs, request)
    jobs, selected_experience  = filter_by_experience(jobs, request)
    jobs, selected_freshness   = filter_by_freshness(jobs, request)

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

    location_list = ['Bangalore', 'Delhi', 'Mumbai', 'Hyderabad', 'Pune', 'Chennai',]
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

    stipend_counts = {
        'unpaid': Job.objects.filter(min_salary=0, max_salary=0).count(),
        '0-10':   Job.objects.filter(min_salary__gte=0,  max_salary__lte=10).count(),
        '10-20':  Job.objects.filter(min_salary__gte=10, max_salary__lte=20).count(),
        '20-30':  Job.objects.filter(min_salary__gte=20, max_salary__lte=30).count(),
        '30-50':  Job.objects.filter(min_salary__gte=30, max_salary__lte=50).count(),
        '50+':    Job.objects.filter(min_salary__gte=50).count(),
    }

    return render(request, 'core/remote_jobs.html', {
        'jobs':                  jobs,
        'selected_work_modes':   selected_work_modes,
        'selected_categories':   selected_categories,
        'selected_company_types': company_types,
        'selected_locations':    selected_locations,
        'selected_salaries':     selected_salaries,
        'selected_experience':   selected_experience,
        'selected_freshness':    selected_freshness,
        'selected_roles':        roles,
        'selected_stipends':     stipends,
        'selected_durations':    durations,
        'selected_educations':   educations,
        'selected_posted':       posted_by,
        'selected_industries':   industries,
        'selected_companies':    companies,
        'salary_counts':         salary_counts,
        'category_counts':       category_counts,
        'location_counts':       location_counts,
        'company_type_counts':   company_type_counts,
        'role_counts':           role_counts,
        'stipend_counts':        stipend_counts,
        'duration_counts':       duration_counts,
        'education_counts':      education_counts,
        'posted_by_counts':      posted_by_counts,
        'industry_counts':       industry_counts,
        'company_counts':        company_counts,
    })


# ===================== OTHER JOB PAGES =====================
@login_required
def mnc_jobs_page(request):

    # ===================== BASE QUERY =====================
    # First get only MNC jobs
    jobs = Job.objects.filter(
        company_type__icontains='mnc'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL MNC JOBS =====================
    # Used for counts

    all_jobs = Job.objects.filter(
        company_type__icontains='mnc'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:
            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:
            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values('category').annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/mnc_jobs.html',
        context
    )

@login_required
def banking_finance_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Banking & Finance'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL BANKING JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Banking & Finance'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/banking_finance_jobs.html',
        context
    )

@login_required
def startup_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        company_type__icontains='startup'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL STARTUP JOBS =====================

    all_jobs = Job.objects.filter(
        company_type__icontains='startup'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/startup_jobs.html',
        context
    )

@login_required
def software_it_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='IT'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL SOFTWARE IT JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='IT'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/software_it_jobs.html',
        context
    )

@login_required
def internship_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        job_type='internship'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL INTERNSHIP JOBS =====================

    all_jobs = Job.objects.filter(
        job_type='internship'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/internship_jobs.html',
        context
    )

@login_required
def engineering_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Engineering'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL ENGINEERING JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Engineering'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/engineering_jobs.html',
        context
    )

@login_required
def marketing_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(category__icontains='Marketing').order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)
    jobs, selected_categories = filter_by_category(jobs, request)
    jobs, selected_locations  = filter_by_location(jobs, request)
    jobs, selected_salaries   = filter_by_salary(jobs, request)
    jobs, selected_experience = filter_by_experience(jobs, request)
    jobs, selected_freshness  = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')
    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')
    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')
    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')
    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(category__icontains='Marketing')

    salary_ranges = [
        '0-3','3-6','6-10','10-15',
        '15-20','20-25','25-30','30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:
        try:
            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:
            salary_counts[r] = 0

    category_counts = {
        item['category']: item['total']
        for item in all_jobs.values('category').annotate(total=Count('id'))
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

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

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {
        e: all_jobs.filter(education=e).count()
        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {
        p: all_jobs.filter(posted_by=p).count()
        for p in all_posted_by
    }

    return render(request, 'core/marketing_jobs.html', {
        'jobs':                   jobs,
        'selected_work_modes':    selected_work_modes,
        'selected_categories':    selected_categories,
        'selected_company_types': company_types,
        'selected_locations':     selected_locations,
        'selected_salaries':      selected_salaries,
        'selected_experience':    selected_experience,
        'selected_freshness':     selected_freshness,
        'selected_roles':         roles,
        'selected_educations':    educations,
        'selected_posted':        posted_by,
        'salary_counts':          salary_counts,
        'category_counts':        category_counts,
        'location_counts':        location_counts,
        'company_type_counts':    company_type_counts,
        'role_counts':            role_counts,
        'education_counts':       education_counts,
        'posted_by_counts':       posted_by_counts,
    })

@login_required
def fortune_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        company_type__icontains='fortune'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL FORTUNE JOBS =====================

    all_jobs = Job.objects.filter(
        company_type__icontains='fortune'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/fortune_jobs.html',
        context
    )

@login_required
def human_resources_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Human Resources'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL HR JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Human Resources'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/human_resources_jobs.html',
        context
    )

@login_required
def project_management_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Project Management'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL PROJECT MANAGEMENT JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Project Management'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/project_management_jobs.html',
        context
    )

@login_required
def finance_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Finance'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL FINANCE JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Finance'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/finance_jobs.html',
        context
    )

@login_required
def operations_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Operations'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL OPERATIONS JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Operations'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/operations_jobs.html',
        context
    )

# ===================== SUPPLY CHAIN JOBS =====================
@login_required
def supply_chain_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Supply Chain'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL SUPPLY CHAIN JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Supply Chain'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/supply_chain_jobs.html',
        context
    )

# ===================== FOREIGN MNC JOBS =====================
@login_required
def foreign_mnc_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        company_type__icontains='MNC'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL MNC JOBS =====================

    all_jobs = Job.objects.filter(
        company_type__icontains='MNC'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/foreign_mnc_jobs.html',
        context
    )

# ===================== WORK FROM HOME JOBS =====================
@login_required
def work_from_home_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        work_mode__icontains='Work From Home'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL WORK FROM HOME JOBS =====================

    all_jobs = Job.objects.filter(
        work_mode__icontains='Work From Home'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/work_from_home_jobs.html',
        context
    )

# ===================== ANALYTICS & BI JOBS =====================
@login_required
def analytics_bi_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Analytics'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL ANALYTICS JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Analytics'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/analytics_bi_jobs.html',
        context
    )

# ===================== DATA SCIENCE JOBS =====================
@login_required
def datascience_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Data Science'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL DATA SCIENCE JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Data Science'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/datascience_jobs.html',
        context
    )

# ===================== STARTUP JOBS =====================
@login_required
def startup_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        company_type__icontains='Startup'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL STARTUP JOBS =====================

    all_jobs = Job.objects.filter(
        company_type__icontains='Startup'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/startup_page.html',
        context
    )

# ===================== SALES JOBS =====================
@login_required
def salesjobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Sales'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL SALES JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Sales'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/salesjobs_page.html',
        context
    )


@login_required
def marketingjobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Marketing'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL SALES JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Sales'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/marketingjobs_page.html',
        context
    )

# 
@login_required
def sales_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Sales'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL SALES JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Sales'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/sales_jobs_page.html',
        context
    )

# ===================== BANKING FINANCE JOBS =====================
@login_required
def banking_financejobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Banking Finance'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL BANKING FINANCE JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Banking Finance'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/banking_financejobs_page.html',
        context
    )

# ===================== ENGINEERING JOBS =====================
@login_required
def engineeringjobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Engineering'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL ENGINEERING JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Engineering'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/engineeringjobs_page.html',
        context
    )

# ===================== HR JOBS =====================
@login_required
def hr_jobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='HR'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL HR JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='HR'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/hr_jobs_page.html',
        context
    )


# ===================== FRESHER JOBS =====================
@login_required
def fresherjobs_page(request):

    # ===================== BASE QUERY =====================

    jobs = Job.objects.filter(
        category__icontains='Fresher'
    ).order_by('-id')

    # ===================== COMMON FILTERS =====================

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    # ===================== COMPANY TYPE =====================

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # ===================== DURATION =====================

    durations = request.GET.getlist('duration')

    if durations:
        jobs = jobs.filter(duration__in=durations)

    # ===================== EDUCATION =====================

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    # ===================== POSTED BY =====================

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    # ===================== INDUSTRY =====================

    industries = request.GET.getlist('industry')

    if industries:
        jobs = jobs.filter(industry__in=industries)

    # ===================== COMPANY =====================

    companies = request.GET.getlist('company')

    if companies:
        jobs = jobs.filter(company__in=companies)

    # ===================== ROLE CATEGORY =====================

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    # ===================== ALL FRESHER JOBS =====================

    all_jobs = Job.objects.filter(
        category__icontains='Fresher'
    )

    # ===================== SALARY COUNTS =====================

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            cnt = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            cnt = 0

        salary_counts[r] = cnt

    # ===================== CATEGORY COUNTS =====================

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== LOCATION COUNTS =====================

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    # ===================== COMPANY TYPE COUNTS =====================

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== ROLE COUNTS =====================

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== DURATION COUNTS =====================

    all_durations = all_jobs.exclude(
        duration__isnull=True
    ).exclude(
        duration=''
    ).values_list(
        'duration',
        flat=True
    ).distinct()

    duration_counts = {

        d: all_jobs.filter(
            duration=d
        ).count()

        for d in all_durations
    }

    # ===================== EDUCATION COUNTS =====================

    all_educations = all_jobs.exclude(
        education__isnull=True
    ).exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    # ===================== POSTED BY COUNTS =====================

    all_posted_by = all_jobs.exclude(
        posted_by__isnull=True
    ).exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    # ===================== INDUSTRY COUNTS =====================

    all_industries = all_jobs.exclude(
        industry__isnull=True
    ).exclude(
        industry=''
    ).values_list(
        'industry',
        flat=True
    ).distinct()

    industry_counts = {

        i: all_jobs.filter(
            industry=i
        ).count()

        for i in all_industries
    }

    # ===================== COMPANY COUNTS =====================

    company_counts = {

        item['company']: item['total']

        for item in all_jobs.values(
            'company'
        ).annotate(
            total=Count('id')
        )
    }

    # ===================== STIPEND FILTER =====================

    stipends = request.GET.getlist('stipend')

    if stipends:

        stipend_query = Q()

        for s in stipends:

            if s == 'unpaid':

                stipend_query |= Q(
                    min_salary=0,
                    max_salary=0
                )

            elif s == '0-10':

                stipend_query |= Q(
                    min_salary__gte=0,
                    max_salary__lte=10
                )

            elif s == '10-20':

                stipend_query |= Q(
                    min_salary__gte=10,
                    max_salary__lte=20
                )

            elif s == '20-30':

                stipend_query |= Q(
                    min_salary__gte=20,
                    max_salary__lte=30
                )

            elif s == '30-50':

                stipend_query |= Q(
                    min_salary__gte=30,
                    max_salary__lte=50
                )

            elif s == '50+':

                stipend_query |= Q(
                    min_salary__gte=50
                )

        jobs = jobs.filter(stipend_query)

    # ===================== STIPEND COUNTS =====================

    stipend_counts = {

        'unpaid': all_jobs.filter(
            min_salary=0,
            max_salary=0
        ).count(),

        '0-10': all_jobs.filter(
            min_salary__gte=0,
            max_salary__lte=10
        ).count(),

        '10-20': all_jobs.filter(
            min_salary__gte=10,
            max_salary__lte=20
        ).count(),

        '20-30': all_jobs.filter(
            min_salary__gte=20,
            max_salary__lte=30
        ).count(),

        '30-50': all_jobs.filter(
            min_salary__gte=30,
            max_salary__lte=50
        ).count(),

        '50+': all_jobs.filter(
            min_salary__gte=50
        ).count(),
    }

    # ===================== FINAL CONTEXT =====================

    context = {

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
    }

    return render(
        request,
        'core/fresherjobs_page.html',
        context
    )

@login_required
def it_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(category__icontains='IT').order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)
    jobs, selected_categories = filter_by_category(jobs, request)
    jobs, selected_locations  = filter_by_location(jobs, request)
    jobs, selected_salaries   = filter_by_salary(jobs, request)
    jobs, selected_experience = filter_by_experience(jobs, request)
    jobs, selected_freshness  = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')
    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')
    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')
    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')
    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(category__icontains='IT')

    salary_ranges = ['0-3','3-6','6-10','10-15','15-20','20-25','25-30','30-35']
    salary_counts = {}
    for r in salary_ranges:
        try:
            low, high = r.split('-')
            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low), max_salary__lte=int(high)
            ).count()
        except:
            salary_counts[r] = 0

    category_counts = {
        item['category']: item['total']
        for item in all_jobs.values('category').annotate(total=Count('id'))
    }

    location_list = ['Bangalore','Delhi','Mumbai','Hyderabad','Pune','Chennai']
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

    all_educations = all_jobs.exclude(education='').values_list('education', flat=True).distinct()
    education_counts = {e: all_jobs.filter(education=e).count() for e in all_educations}

    all_posted_by = all_jobs.exclude(posted_by='').values_list('posted_by', flat=True).distinct()
    posted_by_counts = {p: all_jobs.filter(posted_by=p).count() for p in all_posted_by}

    return render(request, 'core/it_jobs.html', {
        'jobs':                   jobs,
        'selected_work_modes':    selected_work_modes,
        'selected_categories':    selected_categories,
        'selected_company_types': company_types,
        'selected_locations':     selected_locations,
        'selected_salaries':      selected_salaries,
        'selected_experience':    selected_experience,
        'selected_freshness':     selected_freshness,
        'selected_roles':         roles,
        'selected_educations':    educations,
        'selected_posted':        posted_by,
        'salary_counts':          salary_counts,
        'category_counts':        category_counts,
        'location_counts':        location_counts,
        'company_type_counts':    company_type_counts,
        'role_counts':            role_counts,
        'education_counts':       education_counts,
        'posted_by_counts':       posted_by_counts,
    })

@login_required
def sales_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(category__icontains='Sales').order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)
    jobs, selected_categories = filter_by_category(jobs, request)
    jobs, selected_locations  = filter_by_location(jobs, request)
    jobs, selected_salaries   = filter_by_salary(jobs, request)
    jobs, selected_experience = filter_by_experience(jobs, request)
    jobs, selected_freshness  = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')
    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')
    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')
    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')
    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(category__icontains='Sales')

    salary_ranges = ['0-3','3-6','6-10','10-15','15-20','20-25','25-30','30-35']
    salary_counts = {}

    for r in salary_ranges:
        try:
            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:
            salary_counts[r] = 0

    category_counts = {
        item['category']: item['total']
        for item in all_jobs.values('category').annotate(total=Count('id'))
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

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

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {
        e: all_jobs.filter(education=e).count()
        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {
        p: all_jobs.filter(posted_by=p).count()
        for p in all_posted_by
    }

    return render(request, 'core/sales_jobs.html', {
        'jobs':                   jobs,
        'selected_work_modes':    selected_work_modes,
        'selected_categories':    selected_categories,
        'selected_company_types': company_types,
        'selected_locations':     selected_locations,
        'selected_salaries':      selected_salaries,
        'selected_experience':    selected_experience,
        'selected_freshness':     selected_freshness,
        'selected_roles':         roles,
        'selected_educations':    educations,
        'selected_posted':        posted_by,
        'salary_counts':          salary_counts,
        'category_counts':        category_counts,
        'location_counts':        location_counts,
        'company_type_counts':    company_type_counts,
        'role_counts':            role_counts,
        'education_counts':       education_counts,
        'posted_by_counts':       posted_by_counts,
    })

@login_required
def data_science_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        category__icontains='Data Science'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        category__icontains='Data Science'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/data_science_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })

@login_required
def fresher_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        experience='Fresher'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        experience='Fresher'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/fresher_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })


@login_required
def walk_in_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        job_type__icontains='Walk In'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        job_type__icontains='Walk In'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/walk_in_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })


@login_required
def part_time_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        job_type__icontains='Part Time'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        job_type__icontains='Part Time'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/part_time_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })


@login_required
def delhi_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        location__icontains='Delhi'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        location__icontains='Delhi'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/delhi_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })



@login_required
def mumbai_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        location__icontains='Mumbai'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        location__icontains='Mumbai'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/mumbai_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })


@login_required
def bangalore_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        location__icontains='Bangalore'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        location__icontains='Bangalore'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/bangalore_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })



@login_required
def hyderabad_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        location__icontains='Hyderabad'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        location__icontains='Hyderabad'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/hyderabad_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })


@login_required
def chennai_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        location__icontains='Chennai'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        location__icontains='Chennai'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/chennai_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })


@login_required
def pune_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        location__icontains='Pune'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        location__icontains='Pune'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/pune_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })


@login_required
def kolkata_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        location__icontains='Kolkata'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        location__icontains='Kolkata'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai',
        'Kolkata'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/kolkata_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })

@login_required
def ahmedabad_jobs_page(request):
    from django.db.models import Count

    jobs = Job.objects.filter(
        location__icontains='Ahmedabad'
    ).order_by('-id')

    jobs, selected_work_modes = filter_by_work_mode(jobs, request)

    jobs, selected_categories = filter_by_category(jobs, request)

    jobs, selected_locations = filter_by_location(jobs, request)

    jobs, selected_salaries = filter_by_salary(jobs, request)

    jobs, selected_experience = filter_by_experience(jobs, request)

    jobs, selected_freshness = filter_by_freshness(jobs, request)

    company_types = request.GET.getlist('company_type')

    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    educations = request.GET.getlist('education')

    if educations:
        jobs = jobs.filter(education__in=educations)

    posted_by = request.GET.getlist('posted_by')

    if posted_by:
        jobs = jobs.filter(posted_by__in=posted_by)

    roles = request.GET.getlist('role_category')

    if roles:
        jobs = jobs.filter(role_category__in=roles)

    all_jobs = Job.objects.filter(
        location__icontains='Ahmedabad'
    )

    salary_ranges = [
        '0-3',
        '3-6',
        '6-10',
        '10-15',
        '15-20',
        '20-25',
        '25-30',
        '30-35'
    ]

    salary_counts = {}

    for r in salary_ranges:

        try:

            low, high = r.split('-')

            salary_counts[r] = all_jobs.filter(
                min_salary__gte=int(low),
                max_salary__lte=int(high)
            ).count()

        except:

            salary_counts[r] = 0

    category_counts = {

        item['category']: item['total']

        for item in all_jobs.values(
            'category'
        ).annotate(
            total=Count('id')
        )
    }

    location_list = [
        'Bangalore',
        'Delhi',
        'Mumbai',
        'Hyderabad',
        'Pune',
        'Chennai',
        'Kolkata',
        'Ahmedabad'
    ]

    location_counts = {

        loc: all_jobs.filter(
            location__icontains=loc
        ).count()

        for loc in location_list
    }

    company_type_counts = {

        item['company_type']: item['total']

        for item in all_jobs.values(
            'company_type'
        ).annotate(
            total=Count('id')
        )
    }

    role_counts = {

        item['role_category']: item['total']

        for item in all_jobs.values(
            'role_category'
        ).annotate(
            total=Count('id')
        )
    }

    all_educations = all_jobs.exclude(
        education=''
    ).values_list(
        'education',
        flat=True
    ).distinct()

    education_counts = {

        e: all_jobs.filter(
            education=e
        ).count()

        for e in all_educations
    }

    all_posted_by = all_jobs.exclude(
        posted_by=''
    ).values_list(
        'posted_by',
        flat=True
    ).distinct()

    posted_by_counts = {

        p: all_jobs.filter(
            posted_by=p
        ).count()

        for p in all_posted_by
    }

    return render(request, 'core/ahmedabad_jobs.html', {

        'jobs': jobs,

        'selected_work_modes': selected_work_modes,

        'selected_categories': selected_categories,

        'selected_company_types': company_types,

        'selected_locations': selected_locations,

        'selected_salaries': selected_salaries,

        'selected_experience': selected_experience,

        'selected_freshness': selected_freshness,

        'selected_roles': roles,

        'selected_educations': educations,

        'selected_posted': posted_by,

        'salary_counts': salary_counts,

        'category_counts': category_counts,

        'location_counts': location_counts,

        'company_type_counts': company_type_counts,

        'role_counts': role_counts,

        'education_counts': education_counts,

        'posted_by_counts': posted_by_counts,
    })

# ── SHARED HELPER — builds all filter context for company pages ──
def _build_company_filter_context(request, base_qs):
    """
    Takes a base queryset (already filtered by company_type),
    applies all GET filters, returns (filtered_qs, context_dict).
    """
    from django.db.models import Count, Min, Max
    import datetime
 
    jobs = base_qs
 
    # ── Work mode ──
    work_modes = request.GET.getlist('work_mode')
    if work_modes:
        jobs = jobs.filter(work_mode__in=work_modes)
 
    # ── Location ──
    locations = request.GET.getlist('location')
    if locations:
        q = Q()
        for loc in locations:
            q |= Q(location__icontains=loc)
        jobs = jobs.filter(q)
 
    # ── Industry ──
    industries = request.GET.getlist('industry')
    if industries:
        q = Q()
        for ind in industries:
            q |= Q(industry__icontains=ind)
        jobs = jobs.filter(q)
 
    # ── Department ──
    departments = request.GET.getlist('department')
    if departments:
        jobs = jobs.filter(department__in=departments)
 
    # ── Experience ──
    experience = request.GET.get('experience')
    if experience and experience != '30':
        jobs = jobs.filter(experience__icontains=experience)
 
    # ── Nature of business ──
    nob = request.GET.getlist('nature_of_business')
    if nob:
        jobs = jobs.filter(nature_of_business__in=nob)
 
    # ── Job posting date (freshness) ──
    freshness = request.GET.get('freshness')
    if freshness:
        try:
            days   = int(freshness)
            cutoff = timezone.now() - datetime.timedelta(days=days)
            jobs   = jobs.filter(created_at__gte=cutoff)
        except (ValueError, TypeError):
            pass
 
    # ── Company type filter (additional) ──
    company_types = request.GET.getlist('company_type')
    if company_types:
        jobs = jobs.filter(company_type__in=company_types)
 
    # ── Salary ──
    salaries = request.GET.getlist('salary')
    if salaries:
        sq = Q()
        for s in salaries:
            try:
                lo, hi = s.split('-')
                sq |= Q(min_salary__gte=int(lo), max_salary__lte=int(hi))
            except Exception:
                pass
        jobs = jobs.filter(sq)
 
    # ── GROUP companies from filtered jobs ──
    # Each unique company name becomes one card
    companies = (
        jobs
        .values('company', 'company_type', 'location', 'industry', 'nature_of_business')
        .annotate(
            job_count   = Count('id'),
            avg_rating  = Count('rating'),   # placeholder — use real avg if needed
            min_sal     = Min('min_salary'),
            max_sal     = Max('max_salary'),
        )
        .order_by('-job_count')
    )
 
    # ── Also pull CompanyProfile rows for logo / description ──
    from .models import CompanyProfile
    profile_map = {
        cp.company_name.lower(): cp
        for cp in CompanyProfile.objects.all()
        if cp.company_name
    }
 
    # Attach profile data to each company dict
    enriched = []
    for c in companies:
        name    = c['company']
        profile = profile_map.get((name or '').lower())
        enriched.append({
            'name':               name,
            'company_type':       c['company_type'],
            'location':           c['location'],
            'industry':           c['industry'],
            'nature_of_business': c['nature_of_business'],
            'job_count':          c['job_count'],
            'logo':               profile.logo if profile else None,
            'description':        profile.description if profile else '',
            'rating':             profile.founded_year if profile else None,  # reuse slot
        })
 
    # ── Sidebar filter counts (from UNFILTERED base_qs) ──
    all_q = base_qs
 
    location_list   = ['Bangalore','Delhi','Mumbai','Hyderabad','Pune','Chennai']
    location_counts = {
        loc: all_q.filter(location__icontains=loc).count()
        for loc in location_list
    }
 
    company_type_counts = {
        item['company_type']: item['total']
        for item in all_q.values('company_type').annotate(total=Count('id'))
    }
 
    industry_counts = {
        item['industry']: item['total']
        for item in all_q.exclude(industry='').values('industry').annotate(total=Count('id'))
    }
 
    department_counts = {
        item['department']: item['total']
        for item in all_q.exclude(department__isnull=True).exclude(department='').values('department').annotate(total=Count('id'))
    }
 
    nob_counts = {
        item['nature_of_business']: item['total']
        for item in all_q.exclude(nature_of_business__isnull=True).values('nature_of_business').annotate(total=Count('id'))
    }
 
    salary_ranges = ['0-3','3-6','6-10','10-15','15-20','20-25','25-30','30-35']
    salary_counts = {}
    for r in salary_ranges:
        try:
            lo, hi = r.split('-')
            salary_counts[r] = all_q.filter(min_salary__gte=int(lo), max_salary__lte=int(hi)).count()
        except Exception:
            salary_counts[r] = 0
 
    context = {
        'companies':          enriched,
        'total_companies':    len(enriched),
        # selected filters (to keep checkboxes checked)
        'selected_work_modes':       work_modes,
        'selected_locations':        locations,
        'selected_industries':       industries,
        'selected_departments':      departments,
        'selected_nob':              nob,
        'selected_freshness':        freshness,
        'selected_company_types':    company_types,
        'selected_salaries':         salaries,
        'selected_experience':       experience,
        # counts
        'location_counts':           location_counts,
        'company_type_counts':       company_type_counts,
        'industry_counts':           industry_counts,
        'department_counts':         department_counts,
        'nob_counts':                nob_counts,
        'salary_counts':             salary_counts,
    }
    return jobs, context
 
 
# ══════════════════════════════════════════════════════════════
# UNICORN COMPANIES
# ══════════════════════════════════════════════════════════════
@login_required
def company_unicorn(request):
    base_qs = Job.objects.filter(
        company_type__icontains='unicorn'
    ).order_by('-id')
 
    _, context = _build_company_filter_context(request, base_qs)
    context['page_title']    = 'Unicorn Companies Actively Hiring'
    context['page_category'] = 'Unicorns'
    context['clear_url']     = 'company_unicorn'
 
    return render(request, 'core/company_unicorn.html', context)

    
 
 
# ══════════════════════════════════════════════════════════════
# MNC COMPANIES
# ══════════════════════════════════════════════════════════════
@login_required
def company_mnc_jobs_page(request):
    base_qs = Job.objects.filter(
        Q(company_type__icontains='mnc') |
        Q(company_type__icontains='multinational')
    ).order_by('-id')
 
    _, context = _build_company_filter_context(request, base_qs)
    context['page_title']    = 'MNC Companies Actively Hiring'
    context['page_category'] = 'MNCs'
    context['clear_url']     = 'company_mnc'
 
    return render(request, 'core/company_mnc_jobs.html', context)
 
 
# ══════════════════════════════════════════════════════════════
# STARTUP COMPANIES
# ══════════════════════════════════════════════════════════════
@login_required
def company_startups_jobs_page(request):
    base_qs = Job.objects.filter(
        Q(company_type__icontains='startup') |
        Q(company_type__icontains='start-up')
    ).order_by('-id')
 
    _, context = _build_company_filter_context(request, base_qs)
    context['page_title']    = 'Startup Companies Actively Hiring'
    context['page_category'] = 'Startups'
    context['clear_url']     = 'company_startups'
 
    return render(request, 'core/company_startups_jobs.html', context)


def company_jobs_page(request, company_name):
    from django.db.models import Count
 
    # ── All jobs for this company from DB ──────────────────────
    jobs = Job.objects.filter(
        company__iexact=company_name
    ).order_by('-created_at')
 
    # ── Apply filters ──────────────────────────────────────────
    jobs, selected_work_modes = filter_by_work_mode(jobs, request)
    jobs, selected_locations  = filter_by_location(jobs, request)
    jobs, selected_salaries   = filter_by_salary(jobs, request)
    jobs, selected_experience = filter_by_experience(jobs, request)
    jobs, selected_freshness  = filter_by_freshness(jobs, request)
 
    # ── CompanyProfile for logo/description ────────────────────
    from .models import CompanyProfile
    try:
        company_profile = CompanyProfile.objects.get(
            company_name__iexact=company_name
        )
    except CompanyProfile.DoesNotExist:
        company_profile = None
 
    # ── Get first job for company meta ─────────────────────────
    first_job = Job.objects.filter(company__iexact=company_name).first()
 
    # ── Counts for filter sidebar ──────────────────────────────
    all_company_jobs = Job.objects.filter(company__iexact=company_name)
 
    location_list = ['Bangalore','Delhi','Mumbai','Hyderabad','Pune','Chennai']
    location_counts = {
        loc: all_company_jobs.filter(location__icontains=loc).count()
        for loc in location_list
    }
 
    salary_ranges = ['0-3','3-6','6-10','10-15','15-20','20-25','25-30','30-35']
    salary_counts = {}
    for r in salary_ranges:
        try:
            lo, hi = r.split('-')
            salary_counts[r] = all_company_jobs.filter(
                min_salary__gte=int(lo), max_salary__lte=int(hi)
            ).count()
        except Exception:
            salary_counts[r] = 0
 
    return render(request, 'core/company_jobs.html', {
        'jobs':                 jobs,
        'company_name':         company_name,
        'company_profile':      company_profile,
        'first_job':            first_job,
        'total_jobs':           jobs.count(),
        'selected_work_modes':  selected_work_modes,
        'selected_locations':   selected_locations,
        'selected_salaries':    selected_salaries,
        'selected_experience':  selected_experience,
        'selected_freshness':   selected_freshness,
        'location_counts':      location_counts,
        'salary_counts':        salary_counts,
    })


@login_required
def company_product_based_jobs_page(request):
    base_qs = Job.objects.filter(
        Q(category__icontains='product') |
        Q(category__icontains='product based')
    ).order_by('-id')

    _, context = _build_company_filter_context(request, base_qs)

    context['page_title'] = 'Product Based Companies Hiring'
    context['page_category'] = 'Product Based'
    context['clear_url'] = 'company_product_based'

    return render(
        request,
        'core/company_product_based_jobs.html',
        context
    )


@login_required
def company_internet_jobs_page(request):
    base_qs = Job.objects.filter(
        Q(category__icontains='internet') |
        Q(industry__icontains='internet')
    ).order_by('-id')

    _, context = _build_company_filter_context(request, base_qs)

    context['page_title'] = 'Internet Companies Hiring'
    context['page_category'] = 'Internet'
    context['clear_url'] = 'company_internet'

    return render(
        request,
        'core/company_internet_jobs.html',
        context
    )


@login_required
def company_top_companies_jobs_page(request):
    base_qs = Job.objects.filter(
        Q(category__icontains='top company') |
        Q(category__icontains='top companies') |
        Q(company_type__icontains='mnc')
    ).order_by('-id')

    _, context = _build_company_filter_context(request, base_qs)

    context['page_title'] = 'Top Companies Hiring'
    context['page_category'] = 'Top Companies'
    context['clear_url'] = 'company_top_companies'

    return render(
        request,
        'core/company_top_companies_jobs.html',
        context
    )


@login_required
def company_it_companies_jobs_page(request):
    base_qs = Job.objects.filter(
        Q(industry__icontains='it') |
        Q(category__icontains='it') |
        Q(company_type__icontains='it services')
    ).order_by('-id')

    _, context = _build_company_filter_context(request, base_qs)

    context['page_title'] = 'IT Companies Hiring'
    context['page_category'] = 'IT Companies'
    context['clear_url'] = 'company_it_companies'

    return render(
        request,
        'core/company_it_companies_jobs.html',
        context
    )


@login_required
def company_fintech_companies_jobs_page(request):
    base_qs = Job.objects.filter(
        Q(industry__icontains='fintech') |
        Q(category__icontains='fintech') |
        Q(company_type__icontains='financial technology')
    ).order_by('-id')

    _, context = _build_company_filter_context(request, base_qs)

    context['page_title'] = 'Fintech Companies Hiring'
    context['page_category'] = 'Fintech'
    context['clear_url'] = 'company_fintech_companies'

    return render(
        request,
        'core/company_fintech_companies_jobs.html',
        context
    )


@login_required
def company_sponsored_companies_jobs_page(request):
    base_qs = Job.objects.filter(
        is_sponsored=True
    ).order_by('-id')

    _, context = _build_company_filter_context(request, base_qs)

    context['page_title'] = 'Sponsored Companies Hiring'
    context['page_category'] = 'Sponsored Companies'
    context['clear_url'] = 'company_sponsored_companies'

    return render(
        request,
        'core/company_sponsored_companies_jobs.html',
        context
    )


@login_required
def company_featured_companies_jobs_page(request):
    base_qs = Job.objects.filter(
        is_featured=True
    ).order_by('-id')

    _, context = _build_company_filter_context(request, base_qs)

    context['page_title'] = 'Featured Companies Hiring'
    context['page_category'] = 'Featured Companies'
    context['clear_url'] = 'company_featured_companies'

    return render(
        request,
        'core/company_featured_companies_jobs.html',
        context
    )

# ===================== SAVE JOB =====================
@candidate_required
def save_job(request, job_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    job = get_object_or_404(Job, id=job_id)
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if created:
        return JsonResponse({'status': 'saved', 'message': 'Saved successfully!'})
    else:
        saved.delete()
        return JsonResponse({'status': 'removed', 'message': 'Removed from saved jobs!'})


# ===================== APPLY JOB =====================

@candidate_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    already_applied = Application.objects.filter(
        applicant=request.user,
        job=job
    ).exists()

    if already_applied:
        messages.warning(request, "You already applied for this job.")
        return redirect('applied_jobs')

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '')
        resume       = request.FILES.get('resume')

        # Pull from form fields first, fallback to profile
        skills   = request.POST.get('skills', '')
        location = request.POST.get('location', '')
        experience = request.POST.get('experience', '')

        # If form didn't send them, try UserProfile
        if not skills or not location or not experience:
            try:
                profile    = request.user.userprofile
                skills     = skills     or ''
                location   = location   or ''
                experience = experience or profile.work_status or ''
            except:
                pass

        Application.objects.create(
            applicant=request.user,
            job=job,
            phone_number=phone_number,
            resume=resume,
            status='Applied',
            skills=skills,
            location=location,
            experience=experience,
        )

        messages.success(request, "✅ Application submitted successfully!")
        return redirect('applied_jobs')

    return render(request, 'core/apply_job.html', {'job': job})

# ===================== SAVED JOBS =====================

@candidate_required
def saved_jobs_page(request):
    saved = SavedJob.objects.filter(user=request.user).select_related('job').order_by('-saved_at')
    return render(request, 'core/saved_jobs.html', {'saved_jobs': saved})

# ===================== ALL JOBS =====================

# ===================== JOB DETAIL =====================
# core/views.py
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Safety clamp: fix any bad data that slipped through
    if job.min_salary is not None and job.min_salary <= 0:
        job.min_salary = None
    if job.max_salary is not None and job.max_salary <= 0:
        job.max_salary = None

    return render(request, 'core/job_detail.html', {'job': job})

# ===================== REMOVE SAVED JOB =====================
def remove_saved_job(request, saved_job_id):

    saved_job = get_object_or_404(
        SavedJob,
        id=saved_job_id,
        user=request.user
    )

    saved_job.delete()

    return redirect('saved_jobs')

# ===================== APPLIED JOBS =====================

@candidate_required
def applied_jobs_page(request):
    # FIX: filter by applicant=request.user so only RAM sees HIS applications
    applied_jobs = Application.objects.filter(
        applicant=request.user
    ).select_related('job').order_by('-applied_at')
    return render(request, 'core/applied_jobs.html', {'applied_jobs': applied_jobs})


# ===================== RECRUITER APPLICATIONS =====================

@employer_required
def recruiter_applications(request):
    applications = ApplyJob.objects.select_related('user', 'job').all().order_by('-applied_at')
    return render(request, 'core/recruiter_applications.html', {'applications': applications})


# ✅ CORRECT — uses Application model + redirects back to applicants
@employer_required
def update_status(request, app_id, status):
    application = get_object_or_404(Application, id=app_id)

    # Security check — only this employer can update
    if application.job.employer != request.user:
        messages.error(request, "❌ Access denied.")
        return redirect('applicants')

    valid_statuses = [
        'Applied', 'Screening', 'Shortlisted',
        'Interview', 'Technical', 'HR', 'Offer', 'Rejected'
    ]

    if status not in valid_statuses:
        messages.error(request, f"❌ Invalid status: {status}")
        return redirect('applicants')

    application.status = status
    application.save()

    candidate_name = application.applicant.get_full_name() or application.applicant.username
    messages.success(request, f"✅ {candidate_name} marked as {status}.")
    return redirect('applicants')


# ===================== EMPLOYER REGISTER =====================

def employer_register(request):
    if request.method == "POST":
        form = EmployerRegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email    = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(username=username, email=email, password=password)
            profile = form.save(commit=False)
            profile.user = user
            profile.role = "employer"
            profile.save()
            return redirect('employer_login_page')
    else:
        form = EmployerRegisterForm()
    return render(request, 'core/employer_register.html', {'form': form})


# ===================== EMPLOYER LOGIN =====================


def employer_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.userprofile.role == "employer":
                login(request, user)
                return redirect('employer_dashboard')
            else:
                return HttpResponse("Only employers can login here")
    return render(request, 'core/employer_login_page.html')


# ===================== EMPLOYER DASHBOARD =====================

@employer_required
def employer_dashboard(request):

    # STEP 1: Jobs posted by this employer (Karthikeya)
    # This works ONLY if job.employer was set when the job was posted.
    # If job.employer is None → this returns empty → dashboard shows 0.
    jobs = Job.objects.filter(employer=request.user)

    total_jobs   = jobs.count()
    active_jobs  = jobs.filter(is_active=True).count()

    # All applications for jobs posted by this employer
    all_applications = Application.objects.filter(job__employer=request.user)

    total_applications = all_applications.count()

    # STEP 3: Filters from URL
    experience = request.GET.get('experience')
    location   = request.GET.get('location')
    skill      = request.GET.get('skill')
    status     = request.GET.get('status')

    applications = all_applications

    if experience:
        applications = applications.filter(experience__gte=experience)

    if location:
        applications = applications.filter(location__icontains=location)

    if skill:
        applications = applications.filter(skills__icontains=skill)

    if status:
        applications = applications.filter(status=status)

    # STEP 5: Counts
    shortlisted_count    = applications.filter(status='Shortlisted').count()
    interviews_scheduled = applications.filter(status='Interview').count()
    pending_reviews      = applications.filter(status='Applied').count()

    # STEP 6: Recent 5 applicants
    recent_applicants = applications.select_related(
        'applicant', 'job'
    ).order_by('-applied_at')[:5]

    # STEP 7: Total views
    total_views = sum(job.views for job in jobs)

    # STEP 8: Pipeline (always from all_applications, never filtered)
    pipeline = {
        'applied':     all_applications.filter(status='Applied').count(),
        'screening':   all_applications.filter(status='Screening').count(),
        'shortlisted': all_applications.filter(status='Shortlisted').count(),
        'interview':   all_applications.filter(status='Interview').count(),
        'technical':   all_applications.filter(status='Technical').count(),
        'hr':          all_applications.filter(status='HR').count(),
        'offer':       all_applications.filter(status='Offer').count(),
    }

    # STEP 9: Application count per job (for chart)
    for job in jobs:
        job.application_count = Application.objects.filter(job=job).count()

    # STEP 10: Unread messages
    unread_messages = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    # STEP 11: Dropdown options
    default_experience = ['0','1','2','3','4','5','6','7','8','10','12','15']
    db_experience = list(
        Application.objects.filter(job__employer=request.user)
        .exclude(experience__isnull=True).exclude(experience__exact='')
        .values_list('experience', flat=True).distinct()
    )
    experience_options = sorted(set(default_experience + db_experience))

    default_locations = [
        'Ahmedabad','Bangalore','Chennai','Delhi',
        'Gurgaon','Hyderabad','Kolkata','Mumbai','Noida','Pune'
    ]
    db_locations = list(
        Application.objects.filter(job__employer=request.user)
        .exclude(location__isnull=True).exclude(location__exact='')
        .values_list('location', flat=True).distinct()
    )
    location_options = sorted(set(default_locations + db_locations))

    default_skills = [
        'AWS','CSS','Data Science','Django','Docker',
        'Flutter','HTML','Java','JavaScript','Machine Learning',
        'MongoDB','Node.js','Python','React','SQL'
    ]
    db_skills = list(
        Application.objects.filter(job__employer=request.user)
        .exclude(skills__isnull=True).exclude(skills__exact='')
        .values_list('skills', flat=True).distinct()
    )
    skill_options = sorted(set(default_skills + db_skills))

    status_choices = [
        'Applied','Screening','Shortlisted',
        'Interview','Technical','HR','Offer','Rejected'
    ]

    context = {
        'jobs':                  jobs,
        'applications':          applications,
        'active_jobs':           active_jobs,
        'total_jobs':            total_jobs,
        'total_applications':    total_applications,
        'shortlisted_count':     shortlisted_count,
        'interviews_scheduled':  interviews_scheduled,
        'pending_reviews':       pending_reviews,
        'total_views':           total_views,
        'recent_applicants':     recent_applicants,
        'pipeline':              pipeline,
        'unread_messages':       unread_messages,
        'experience_options':    experience_options,
        'location_options':      location_options,
        'skill_options':         skill_options,
        'status_choices':        status_choices,
        'selected_experience':   experience,
        'selected_location':     location,
        'selected_skill':        skill,
        'selected_status':       status,
    }

    return render(request, 'core/employer_dashboard.html', context)


# ===================== UPDATE APPLICATION STATUS =====================

@employer_required
def update_application_status(request, app_id, new_status):

    application = get_object_or_404(Application, id=app_id)

    if application.job.employer != request.user:
        messages.error(request, "Access denied.")
        return redirect('employer_dashboard')

    valid_statuses = [
        'Applied','Screening','Shortlisted',
        'Interview','Technical','HR','Offer','Rejected'
    ]

    if new_status not in valid_statuses:
        messages.error(request, f"Invalid status: {new_status}")
        return redirect('employer_dashboard')

    application.status = new_status
    application.save()

    candidate_name = application.applicant.get_full_name() or application.applicant.username
    messages.success(request, f"✅ {candidate_name}'s status updated to '{new_status}'.")

    return redirect('employer_dashboard')


# ===================== AJAX REAL-TIME DATA =====================

@employer_required
def dashboard_realtime_data(request):
    jobs = Job.objects.filter(employer=request.user)
    recent = Application.objects.filter(
        job__in=jobs
    ).select_related('applicant', 'job').order_by('-applied_at')[:10]

    data = {
        'total_applications': Application.objects.filter(job__in=jobs).count(),
        'applicants': [
            {
                'name':   app.applicant.get_full_name(),
                'job':    app.job.title,
                'date':   app.applied_at.strftime('%d %b %Y'),
                'status': app.status,
            }
            for app in recent
        ]
    }
    return JsonResponse(data)


# ===================== POST JOB =====================

@employer_required
def post_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user   # ← This is what links the job to Karthikeya
            job.save()
            messages.success(request, '✅ Job posted successfully!')
            return redirect('post_job')
    else:
        form = JobForm()

    jobs = Job.objects.filter(employer=request.user).order_by('-created_at')

    context = {
        'form': form,
        'jobs': jobs,
    }

    return render(request, 'core/post_job.html', context)


# ===================== MANAGE JOBS =====================

@employer_required
def manage_jobs(request):
    jobs = Job.objects.filter(employer=request.user).order_by('-created_at')

    total_jobs         = jobs.count()
    active_jobs        = jobs.filter(is_active=True, status='active').count()
    closed_jobs        = jobs.filter(status='closed').count()
    draft_jobs         = jobs.filter(status='draft').count()
    total_applications = Application.objects.filter(job__employer=request.user).count()
    total_views        = sum(job.views for job in jobs)

    # Recent 5 applicants for analytics panel
    recent_applicants = Application.objects.filter(
        job__employer=request.user
    ).select_related('applicant', 'job').order_by('-applied_at')[:5]

    context = {
        'jobs':               jobs,
        'total_jobs':         total_jobs,
        'active_jobs':        active_jobs,
        'closed_jobs':        closed_jobs,
        'draft_jobs':         draft_jobs,
        'total_applications': total_applications,
        'total_views':        total_views,
        'recent_applicants':  recent_applicants,
    }
    return render(request, 'core/manage_jobs.html', context)

@employer_required
def toggle_job_status(request, job_id):
    if request.method == 'POST':
        job = get_object_or_404(Job, id=job_id, employer=request.user)
        job.is_active = not job.is_active
        job.status = 'active' if job.is_active else 'closed'
        job.save()
        messages.success(request, f"✅ '{job.title}' is now {'Active' if job.is_active else 'Closed'}.")
    return redirect('manage_jobs')

# ===================== APPLICANTS =====================

import json

@employer_required
def applicants(request):

    # ── Only THIS employer's job applications ──
    applications = Application.objects.filter(
        job__employer=request.user          # ← KEY: only this employer
    ).select_related('applicant', 'job').order_by('-applied_at')

    # ── Correct counts (all filtered to this employer) ──
    total_applications = applications.count()     # should be 7 not 1974
    pending_count      = applications.filter(status='Applied').count()
    shortlisted_count  = applications.filter(status='Shortlisted').count()
    interview_count    = applications.filter(status='Interview').count()
    rejected_count     = applications.filter(status='Rejected').count()

    # ── This employer's jobs only (for dropdown) ──
    employer_jobs = Job.objects.filter(employer=request.user).order_by('title')
    total_jobs    = employer_jobs.count()         # should be 23

    # ── Build JSON → feeds the JS cards ──
    apps_list = []
    for a in applications:
        apps_list.append({
            'id':         a.id,
            'name':       a.applicant.get_full_name() or a.applicant.username,
            'email':      a.applicant.email,
            'phone':      a.phone_number or '',
            'job_title':  a.job.title,
            'job_id':     a.job.id,
            'status':     a.status,
            'skills':     a.skills or '',
            'location':   a.location or '',
            'experience': a.experience or '',
            'resume':     a.resume.url if a.resume else '',
            'applied_at': a.applied_at.strftime('%d %b %Y'),
        })

    status_choices = [
        'Applied', 'Screening', 'Shortlisted',
        'Interview', 'Technical', 'HR', 'Offer', 'Rejected'
    ]

    context = {
        # ✅ CORRECT — pass the list directly, let json_script handle encoding
        'applications_json': apps_list,
        'total_applications': total_applications,      # ← should be 7
        'pending_count':      pending_count,
        'shortlisted_count':  shortlisted_count,
        'interview_count':    interview_count,
        'rejected_count':     rejected_count,
        'employer_jobs':      employer_jobs,
        'total_jobs':         total_jobs,              # ← should be 23
        'status_choices':     status_choices,
    }
    return render(request, 'core/applicants.html', context)

# ===================== SHORTLIST CANDIDATE =====================

@employer_required
def shortlist_candidate(request, app_id):
    application = get_object_or_404(Application, id=app_id)

    if application.job.employer != request.user:
        messages.error(request, "Access denied.")
        return redirect('employer_dashboard')

    application.status = "Shortlisted"
    application.save()

    messages.success(request, "✅ Candidate shortlisted successfully.")
    return redirect('employer_dashboard')


# ===================== SHORTLISTED CANDIDATES =====================

@employer_required
def shortlisted_candidates(request):
    shortlisted = Application.objects.filter(
        job__employer=request.user,
        status='Shortlisted'
    )
    for app in shortlisted:
        if app.skills:
            app.skills_list = app.skills.split(',')
        else:
            app.skills_list = []
    return render(request, 'core/shortlisted.html', {'shortlisted': shortlisted})


# ===================== REJECT CANDIDATE =====================

@employer_required
def reject_candidate(request, app_id):
    application = get_object_or_404(Application, id=app_id)

    if application.job.employer != request.user:
        messages.error(request, "Access denied.")
        return redirect('employer_dashboard')

    application.status = "Rejected"
    application.save()

    messages.success(request, "Candidate rejected.")
    return redirect('employer_dashboard')


# ===================== INTERVIEWS =====================

@employer_required
def interviews(request):
    from django.utils import timezone
    today = timezone.now().date()

    interview_list = Interview.objects.filter(
        job__employer=request.user
    ).select_related('candidate', 'job').order_by('interview_date', 'interview_time')

    upcoming_count  = interview_list.filter(interview_date__gte=today, status='Scheduled').count()
    completed_count = interview_list.filter(status='Completed').count()
    cancelled_count = interview_list.filter(status='Cancelled').count()

    # Get all REAL round types from DB for the dropdown
    round_types = interview_list.values_list(
        'round_type', flat=True
    ).distinct()

    # Get all REAL statuses from DB for the dropdown
    statuses = interview_list.values_list(
        'status', flat=True
    ).distinct()

    return render(request, 'core/interviews.html', {
        'interviews':       interview_list,
        'upcoming_count':   upcoming_count,
        'completed_count':  completed_count,
        'cancelled_count':  cancelled_count,
        'round_types':      round_types,   # ← real rounds from DB
        'statuses':         statuses,      # ← real statuses from DB
    })

# ===================== SCHEDULE INTERVIEW =====================

@employer_required
def schedule_interview(request, app_id):
    application = get_object_or_404(Application, id=app_id)

    # Security check
    if application.job.employer != request.user:
        messages.error(request, "Access denied.")
        return redirect('shortlisted_candidates')

    if request.method == 'POST':
        round_type      = request.POST.get('round_type', 'Technical')
        interview_date  = request.POST.get('interview_date')
        interview_time  = request.POST.get('interview_time')
        meeting_link    = request.POST.get('meeting_link', '')

        # Create a real Interview row in the DB
        Interview.objects.create(
            candidate      = application.applicant,
            job            = application.job,
            round_type     = round_type,
            interview_date = interview_date,
            interview_time = interview_time,
            meeting_link   = meeting_link,
            status         = 'Scheduled',
        )

        # Also update Application status
        application.status = 'Interview Scheduled'
        application.save()

        messages.success(request, f"✅ Interview scheduled for {application.applicant.get_full_name() or application.applicant.username}!")
        return redirect('interviews')

    # GET request → show the scheduling form
    return render(request, 'core/schedule_interview.html', {
        'application': application,
    })


# ===================== INBOX MESSAGES =====================

# ===================== INBOX MESSAGES =====================
@employer_required
def inbox_messages(request):
    from django.db.models import Q

    # Get all unique candidates who messaged this employer or received messages
    all_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver').order_by('created_at')

    # Build conversation list — group by the OTHER person (candidate)
    conversations = {}
    for msg in all_messages:
        other = msg.receiver if msg.sender == request.user else msg.sender
        if other.id not in conversations:
            conversations[other.id] = {
                'candidate':        other,
                'messages':         [],
                'unread_count':     0,
                'last_message':     '',
                'last_message_time': msg.created_at,
            }
        conversations[other.id]['messages'].append(msg)
        conversations[other.id]['last_message']      = msg.message
        conversations[other.id]['last_message_time'] = msg.created_at
        if not msg.is_read and msg.receiver == request.user:
            conversations[other.id]['unread_count'] += 1

    conversations_list = list(conversations.values())

    # Mark messages as read for first conversation
    unread_count = Message.objects.filter(
        receiver=request.user, is_read=False
    ).count()

    return render(request, 'core/messages.html', {
        'conversations': conversations_list,
        'unread_count':  unread_count,
    })


# ===================== SEND MESSAGE =====================
@employer_required
def send_message(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    import json
    try:
        data         = json.loads(request.body)
        receiver_id  = data.get('receiver_id')
        message_text = data.get('message', '').strip()

        if not receiver_id or not message_text:
            return JsonResponse({'success': False, 'error': 'Missing receiver or message'})

        receiver = User.objects.get(id=receiver_id)

        msg = Message.objects.create(
            sender   = request.user,
            receiver = receiver,
            message  = message_text,
            is_read  = False,
        )

        return JsonResponse({
            'success':    True,
            'message_id': msg.id,
            'text':       msg.message,
            'time':       msg.created_at.strftime('%H:%M'),
            'sender_id':  request.user.id,
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Candidate not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ===================== FETCH MESSAGES (AJAX polling) =====================
@employer_required
def fetch_messages(request, candidate_id):
    from django.db.models import Q
    messages_qs = Message.objects.filter(
        Q(sender=request.user,   receiver_id=candidate_id) |
        Q(sender_id=candidate_id, receiver=request.user)
    ).order_by('created_at')

    # Mark as read
    messages_qs.filter(receiver=request.user, is_read=False).update(is_read=True)

    data = [{
        'id':        m.id,
        'text':      m.message,
        'sender_id': m.sender.id,
        'time':      m.created_at.strftime('%H:%M'),
    } for m in messages_qs]

    return JsonResponse({'success': True, 'messages': data})


# ===================== REPORTS =====================

@employer_required
def reports(request):
    from django.db.models import Count
    from django.utils import timezone
    import json

    today = timezone.now().date()
    jobs  = Job.objects.filter(employer=request.user)

    # ── Read filter values from Apply button ──────────────────
    date_from    = request.GET.get('date_from', '')
    date_to      = request.GET.get('date_to', '')
    selected_job = request.GET.get('job_title', '')

    # ── Base queryset — only this employer's applications ─────
    applications_qs = Application.objects.filter(job__employer=request.user)

    # ── Apply date range filter if provided ───────────────────
    if date_from:
        applications_qs = applications_qs.filter(applied_at__date__gte=date_from)
    if date_to:
        applications_qs = applications_qs.filter(applied_at__date__lte=date_to)

    # ── Apply job title filter if provided ────────────────────
    if selected_job:
        applications_qs = applications_qs.filter(job__title=selected_job)

    # ── Stat card counts (all from filtered queryset) ─────────
    total_jobs         = jobs.count()
    total_applications = applications_qs.count()
    shortlisted_count  = applications_qs.filter(status='Shortlisted').count()
    rejected_count     = applications_qs.filter(status='Rejected').count()
    pending_count      = applications_qs.filter(status='Applied').count()
    interview_count    = Interview.objects.filter(job__employer=request.user).count()
    total_views        = sum(job.views for job in jobs)

    # ── Hiring funnel percentages ─────────────────────────────
    def pct(count):
        if total_applications == 0:
            return 0
        return round((count / total_applications) * 100)

    screened_count    = applications_qs.filter(status='Screening').count()
    interviewed_count = applications_qs.filter(
        status__in=['Interview', 'Interview Scheduled']
    ).count()
    offer_count       = applications_qs.filter(status='Offer').count()

    screened_percent    = pct(screened_count)
    shortlisted_percent = pct(shortlisted_count)
    interview_percent   = pct(interviewed_count)
    selected_percent    = pct(offer_count)

    # ── Top jobs table ────────────────────────────────────────
    top_jobs_qs = jobs.annotate(
        applications_count=Count('applications')
    ).order_by('-applications_count')[:8]

    top_jobs = []
    for job in top_jobs_qs:
        sc        = Application.objects.filter(job=job, status='Shortlisted').count()
        hire_rate = round((sc / job.applications_count) * 100) if job.applications_count else 0
        top_jobs.append({
            'title':              job.title,
            'applications_count': job.applications_count,
            'shortlisted_count':  sc,
            'views':              job.views,
            'hire_rate':          hire_rate,
        })

    # ── Bar chart: applications per job ──────────────────────
    bar_labels = [j['title']              for j in top_jobs]
    bar_data   = [j['applications_count'] for j in top_jobs]

    # ── Line chart: last 6 months real data ──────────────────
    monthly_applications = []
    monthly_hires        = []
    month_labels         = []

    for i in range(5, -1, -1):
        month = (today.month - i - 1) % 12 + 1
        year  = today.year + ((today.month - i - 1) // 12)
        label = timezone.datetime(year, month, 1).strftime('%b')
        month_labels.append(label)

        apps = Application.objects.filter(
            job__employer=request.user,
            applied_at__year=year,
            applied_at__month=month
        ).count()
        hires = Application.objects.filter(
            job__employer=request.user,
            applied_at__year=year,
            applied_at__month=month,
            status='Offer'
        ).count()
        monthly_applications.append(apps)
        monthly_hires.append(hires)

    context = {
        # Stat cards
        'total_jobs':           total_jobs,
        'total_applications':   total_applications,
        'shortlisted_count':    shortlisted_count,
        'rejected_count':       rejected_count,
        'pending_count':        pending_count,
        'interview_count':      interview_count,
        'total_views':          total_views,

        # Funnel percentages
        'screened_percent':     screened_percent,
        'shortlisted_percent':  shortlisted_percent,
        'interview_percent':    interview_percent,
        'selected_percent':     selected_percent,

        # Top jobs table
        'top_jobs':             top_jobs,

        # Charts (json.dumps so JS can use directly)
        'bar_labels':           json.dumps(bar_labels),
        'bar_data':             json.dumps(bar_data),
        'month_labels':         json.dumps(month_labels),
        'monthly_applications': json.dumps(monthly_applications),
        'monthly_hires':        json.dumps(monthly_hires),

        # Filter state (keeps form values after Apply is clicked)
        'selected_job':         selected_job,
        'date_from':            date_from,
        'date_to':              date_to,
    }

    return render(request, 'core/reports.html', context)

# ===================== EXPORT PDF =====================
@employer_required
def export_reports_pdf(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import io

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story  = []

    # Title
    story.append(Paragraph("HireHub — Recruitment Report", styles['Title']))
    story.append(Spacer(1, 12))

    # Stat summary
    total_applications = Application.objects.filter(job__employer=request.user).count()
    shortlisted_count  = Application.objects.filter(job__employer=request.user, status='Shortlisted').count()
    rejected_count     = Application.objects.filter(job__employer=request.user, status='Rejected').count()
    interview_count    = Interview.objects.filter(job__employer=request.user).count()
    total_jobs         = Job.objects.filter(employer=request.user).count()

    summary_data = [
        ['Metric',            'Count'],
        ['Total Jobs Posted',  str(total_jobs)],
        ['Total Applications', str(total_applications)],
        ['Shortlisted',        str(shortlisted_count)],
        ['Interviews',         str(interview_count)],
        ['Rejected',           str(rejected_count)],
    ]
    summary_table = Table(summary_data, colWidths=[300, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN',      (0,0), (-1,-1), 'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING',    (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 24))

    # Applications table
    story.append(Paragraph("All Applications", styles['Heading2']))
    story.append(Spacer(1, 8))

    applications = Application.objects.filter(
        job__employer=request.user
    ).select_related('applicant', 'job').order_by('-applied_at')[:50]

    app_data = [['Candidate', 'Job Title', 'Status', 'Applied Date']]
    for app in applications:
        app_data.append([
            app.applicant.get_full_name() or app.applicant.username,
            app.job.title,
            app.status,
            app.applied_at.strftime('%d %b %Y'),
        ])

    app_table = Table(app_data, colWidths=[150, 150, 100, 100])
    app_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING',    (0,0), (-1,-1), 6),
    ]))
    story.append(app_table)

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="hirehub_report.pdf"'
    return response


# ===================== EXPORT EXCEL =====================
@employer_required
def export_reports_excel(request):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    import io

    wb = openpyxl.Workbook()

    # ── Sheet 1: Summary ──────────────────────────────────
    ws1 = wb.active
    ws1.title = 'Summary'

    total_jobs         = Job.objects.filter(employer=request.user).count()
    total_applications = Application.objects.filter(job__employer=request.user).count()
    shortlisted_count  = Application.objects.filter(job__employer=request.user, status='Shortlisted').count()
    rejected_count     = Application.objects.filter(job__employer=request.user, status='Rejected').count()
    interview_count    = Interview.objects.filter(job__employer=request.user).count()

    header_fill = PatternFill(start_color='4f46e5', end_color='4f46e5', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)

    ws1.append(['Metric', 'Count'])
    ws1.append(['Total Jobs Posted',  total_jobs])
    ws1.append(['Total Applications', total_applications])
    ws1.append(['Shortlisted',        shortlisted_count])
    ws1.append(['Interviews',         interview_count])
    ws1.append(['Rejected',           rejected_count])

    for cell in ws1[1]:
        cell.fill = header_fill
        cell.font = header_font

    ws1.column_dimensions['A'].width = 25
    ws1.column_dimensions['B'].width = 15

    # ── Sheet 2: All Applications ─────────────────────────
    ws2 = wb.create_sheet('Applications')
    ws2.append(['Candidate', 'Email', 'Job Title', 'Status', 'Location', 'Experience', 'Applied Date'])

    for cell in ws2[1]:
        cell.fill = header_fill
        cell.font = header_font

    applications = Application.objects.filter(
        job__employer=request.user
    ).select_related('applicant', 'job').order_by('-applied_at')

    for app in applications:
        ws2.append([
            app.applicant.get_full_name() or app.applicant.username,
            app.applicant.email,
            app.job.title,
            app.status,
            app.location  or '—',
            app.experience or '—',
            app.applied_at.strftime('%d %b %Y'),
        ])

    for col in ['A','B','C','D','E','F','G']:
        ws2.column_dimensions[col].width = 20

    # ── Sheet 3: Top Jobs ─────────────────────────────────
    ws3 = wb.create_sheet('Top Jobs')
    ws3.append(['Job Title', 'Applications', 'Shortlisted', 'Views', 'Hire Rate %'])

    for cell in ws3[1]:
        cell.fill = header_fill
        cell.font = header_font

    jobs = Job.objects.filter(employer=request.user)
    for job in jobs:
        app_count = Application.objects.filter(job=job).count()
        sc        = Application.objects.filter(job=job, status='Shortlisted').count()
        hire_rate = round((sc / app_count) * 100) if app_count else 0
        ws3.append([job.title, app_count, sc, job.views, hire_rate])

    for col in ['A','B','C','D','E']:
        ws3.column_dimensions[col].width = 20

    # ── Save and return ───────────────────────────────────
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="hirehub_report.xlsx"'
    return response

# ===================== COMPANY PROFILE =====================

@employer_required
def company_profile(request):
    profile, created = CompanyProfile.objects.get_or_create(
        employer=request.user
    )

    if request.method == 'POST':
        # ── Basic Info ──────────────────────────────────────
        profile.company_name   = request.POST.get('company_name', '').strip()
        profile.industry       = request.POST.get('industry', '').strip()
        profile.description    = request.POST.get('description', '').strip()
        profile.founded_year   = request.POST.get('founded_year') or None
        profile.employee_count = request.POST.get('company_size', '').strip()
        profile.company_type   = request.POST.get('company_type', '').strip()

        # ── Location ────────────────────────────────────────
        profile.city    = request.POST.get('city', '').strip()
        profile.state   = request.POST.get('state', '').strip()
        profile.country = request.POST.get('country', '').strip()
        profile.location = f"{profile.city}, {profile.state}, {profile.country}".strip(', ')

        # ── Contact ─────────────────────────────────────────
        profile.website    = request.POST.get('website', '').strip() or None
        profile.hr_email   = request.POST.get('hr_email', '').strip()
        profile.phone      = request.POST.get('phone', '').strip()
        profile.hr_contact = request.POST.get('hr_contact', '').strip()

        # ── Social Media ────────────────────────────────────
        profile.linkedin   = request.POST.get('linkedin', '').strip() or None
        profile.twitter    = request.POST.get('twitter', '').strip() or None
        profile.instagram  = request.POST.get('instagram', '').strip() or None
        profile.other_link = request.POST.get('other_link', '').strip() or None

        # ── Perks & Tech ────────────────────────────────────
        profile.benefits     = request.POST.get('benefits', '').strip()
        profile.technologies = request.POST.get('technologies', '').strip()

        # ── Logo upload ─────────────────────────────────────
        if request.FILES.get('logo'):
            profile.logo = request.FILES['logo']

        profile.save()
        messages.success(request, '✅ Company profile saved successfully!')
        return redirect('company_profile')

    return render(request, 'core/company_profile.html', {
        'profile': profile,
    })
    context = {
    'profile': profile,
    'industry_options': [
        'Software / IT', 'Banking / Finance', 'Healthcare',
        'E-commerce', 'Education', 'Manufacturing', 'Other'
    ],
    'size_options': [
        '1–10 Employees', '11–50 Employees', '51–200 Employees',
        '201–500 Employees', '500+ Employees'
    ],
    'type_options': [
        'Private Ltd', 'Public Ltd', 'Startup', 'MNC', 'Government'
    ],
}


# ===================== SETTINGS =====================
@employer_required
def settings(request):
    employer_settings, _ = EmployerSettings.objects.get_or_create(
        employer=request.user
    )
    if request.method == 'POST':
        # ── Profile fields ─────────────────────────────
        full_name    = request.POST.get('full_name', '').strip()
        email        = request.POST.get('email', '').strip()
        phone        = request.POST.get('phone', '').strip()
        company_name = request.POST.get('company', '').strip()
        language     = request.POST.get('language', 'English')

        # Save to auth_user
        if full_name:
            parts = full_name.split(' ', 1)
            request.user.first_name = parts[0]
            request.user.last_name  = parts[1] if len(parts) > 1 else ''
        if email:
            request.user.email = email
        request.user.save()

        # Save to UserProfile
        try:
            profile = request.user.userprofile
            if company_name:
                profile.company_name = company_name
            profile.save()
        except:
            pass

        # Save to EmployerSettings
        employer_settings.phone_number        = phone
        employer_settings.email_notifications = (request.POST.get('email_notifications') == 'on')
        employer_settings.two_factor_auth     = (request.POST.get('two_factor_enabled') == 'on')
        employer_settings.language            = language
        if request.FILES.get('profile_image'):
            employer_settings.profile_image   = request.FILES['profile_image']
        employer_settings.save()

        messages.success(request, '✅ Settings saved successfully!')
        return redirect('settings')

    return render(request, 'core/settings.html', {
        'employer_settings': employer_settings,
    })


# ===================== CHANGE PASSWORD =====================
@employer_required
def change_password(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    import json
    from django.contrib.auth import update_session_auth_hash
    try:
        data            = json.loads(request.body)
        current_password = data.get('current_password', '')
        new_password     = data.get('new_password', '')
        if not request.user.check_password(current_password):
            return JsonResponse({'success': False, 'error': 'Current password is incorrect.'})
        if len(new_password) < 6:
            return JsonResponse({'success': False, 'error': 'New password must be at least 6 characters.'})
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)  # keeps user logged in
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ===================== DEACTIVATE ACCOUNT =====================
@employer_required
def deactivate_account(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    try:
        # Hide all jobs by this employer
        Job.objects.filter(employer=request.user).update(is_active=False)
        # Deactivate the user account
        request.user.is_active = False
        request.user.save()
        logout(request)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ===================== ALL JOBS =====================

@login_required
def all_jobs(request):
    jobs = Job.objects.all()
    return render(request, 'core/all_jobs.html', {'jobs': jobs})


# ===================== DELETE JOB =====================

@employer_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, employer=request.user)
    job.delete()
    return redirect('employer_dashboard')


# ===================== EDIT JOB =====================

@employer_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, employer=request.user)

    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            updated_job = form.save(commit=False)
            updated_job.employer = request.user  # keep employer set
            updated_job.save()
            messages.success(request, f'✅ "{job.title}" updated successfully!')
            return redirect('manage_jobs')
        else:
            messages.error(request, '❌ Please fix the errors below.')
    else:
        form = JobForm(instance=job)  # ← pre-fills ALL fields including salary

    return render(request, 'core/edit_job.html', {
        'form': form,
        'job':  job,
    })

# ===================== VIEW APPLICATIONS =====================

@employer_required
def view_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    # FIX: was JobApplication (doesn't exist) → changed to Application
    applications = Application.objects.filter(job=job)

    context = {
        'job':          job,
        'applications': applications,
    }
    return render(request, 'core/view_applications.html', context)

def about(request):
    return render(request, 'about.html')

def careers(request):
    return render(request, 'careers.html')

def employer_home(request):
    return render(request, 'employer_home.html')

def sitemap(request):
    return render(request, 'sitemap.html')

def credits(request):
    return render(request, 'credits.html')

def help_center(request):
    return render(request, 'help_center.html')

def summons_notices(request):
    return render(request, 'summons_notices.html')

def grievances(request):
    return render(request, 'grievances.html')

def report_issue(request):
    return render(request, 'report_issue.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_conditions(request):
    return render(request, 'terms_conditions.html')

def fraud_alert(request):
    return render(request, 'fraud_alert.html')

def trust_safety(request):
    return render(request, 'trust_safety.html')

def search_jobs(request):
    return render(request, 'search_jobs.html')

def browser_companies(request):
    return render(request, 'browser_companies.html')

def resume_builder(request):
    return render(request, 'resume_builder.html')

def career_advice(request):
    return render(request, 'career_advice.html')

def salary_calculator(request):
    return render(request, 'salary_calculator.html')

def hiring_solutions(request):
    return render(request, 'hiring_solutions.html')

def view_plans(request):
    return render(request, 'view_plans.html')