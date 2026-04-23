from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from .forms import RegisterForm, LoginForm
from .models import UserProfile, Job
from django.db.models import Count

 
 
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
 
 
# -----------------------------------
# REGISTER VIEW
# -----------------------------------
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
 
        if form.is_valid():
            full_name     = form.cleaned_data["full_name"]
            email         = form.cleaned_data["email"]
            password      = form.cleaned_data["password"]
            mobile_number = form.cleaned_data["mobile_number"]
            work_status   = form.cleaned_data["work_status"]
 
            # ✅ Generate unique username from email prefix
            # CONDITION: username derived from email is also unique
            base_username = email.split("@")[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
 
            # ✅ Create Django User — password is hashed automatically (NEVER stored as plain text)
            user = User.objects.create_user(
                username=username,
                email=email,           # saved to auth_user.email
                password=password,     # saved as bcrypt hash to auth_user.password
                first_name=full_name
            )
 
            # ✅ Create UserProfile linked to User
            UserProfile.objects.create(
                user=user,
                full_name=full_name,
                mobile_number=mobile_number,
                work_status=work_status
            )
 
            messages.success(
                request,
                f"✅ Registration successful! Welcome {full_name}. Please login with your credentials."
            )
            return redirect("login")
 
        else:
            # Field-level errors display inline in the template
            messages.error(
                request,
                "❌ Registration failed. Please fix the errors highlighted below and try again."
            )
 
    else:
        form = RegisterForm()
 
    return render(request, "core/register.html", {"form": form})
 
 
# -----------------------------------
# LOGIN VIEW
# -----------------------------------
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
 
        if form.is_valid():
            email    = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
 
            # ✅ Look up user by email (email is unique per our form validation)
            try:
                user_obj = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                messages.error(
                    request,
                    "❌ No account found with this email address. "
                    "Please check your email or register for a new account."
                )
                return render(request, "core/login.html", {"form": form})
 
            # ✅ Verify password against the stored hash
            user = authenticate(request, username=user_obj.username, password=password)
 
            if user is not None:
                login(request, user)
                messages.success(
                    request,
                    f"✅ Welcome back, {user.first_name}! You are now logged in."
                )
                return redirect("index")
            else:
                messages.error(
                    request,
                    "❌ Incorrect password. Please try again. "
                    "Tip: Make sure CAPS LOCK is off."
                )
 
        else:
            messages.error(request, "❌ Please fill in all fields correctly.")
 
    else:
        form = LoginForm()
 
    return render(request, "core/login.html", {"form": form})
 
 
# -----------------------------------
# LOGOUT VIEW
# -----------------------------------
def logout_view(request):
    logout(request)
    messages.success(request, "✅ You have been logged out successfully.")
    return redirect("login")
 
 
def employer_login_page(request):
    return render(request, 'core/employer_login.html')
 
def remote_jobs_page(request):
    jobs = Job.objects.all().order_by('-id')

    # 🔹 Work Mode (multiple checkbox)
    work_modes = request.GET.getlist('work_mode')
    if work_modes:
        jobs = jobs.filter(work_mode__in=work_modes)

    # 🔹 Category (Department filter)
    categories = request.GET.getlist('category')
    if categories:
        jobs = jobs.filter(category__in=categories)

     # 🔥 ADD HERE (AFTER filters or before render)
    category_counts_qs = Job.objects.values('category').annotate(total=Count('id'))
    category_counts = {item['category']: item['total'] for item in category_counts_qs}

    # 🔹 Company Type
    company_types = request.GET.getlist('company_type')
    if company_types:
        jobs = jobs.filter(company_type__in=company_types)

    # 🔹 Experience (slider)
    experience = request.GET.get('experience')
    if experience and experience != "30":
        jobs = jobs.filter(experience__icontains=experience)

    return render(request, 'core/remote_jobs.html', {
        'jobs': jobs,

        # 👇 send selected values to template (IMPORTANT)
        'selected_work_modes': work_modes,
        'selected_categories': categories,
        'selected_company_types': company_types,
        'selected_experience': experience,
        'category_counts': category_counts,
    })

def mnc_jobs_page(request):
    jobs = Job.objects.filter(company_type__iexact="mnc").order_by('-id')
    return render(request, 'core/mnc_jobs.html', {'jobs': jobs})

def banking_finance_jobs_page(request):
    jobs = Job.objects.filter(
        category__iexact="Banking & Finance",
        work_mode__iexact="Remote"
    )
    return render(request, 'core/banking_finance_jobs.html', {'jobs': jobs})

def startup_jobs_page(request):
    jobs = Job.objects.filter(work_mode__iexact='Remote', company_type__iexact='startup')
    return render(request, 'core/startup_jobs.html', {'jobs': jobs})

def software_it_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        category__icontains='software'
    )
    return render(request, 'core/software_it_jobs.html', {'jobs': jobs})

def internship_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        category__icontains='internship'
    ).order_by('-id')

    return render(request, 'core/internship_jobs.html', {
        'jobs': jobs
    })

def engineering_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        category__icontains='engineering'
    ).order_by('-id')

    return render(request, 'core/engineering_jobs.html', {
        'jobs': jobs
    })

def marketing_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        category__icontains='marketing'
    ).order_by('-id')

    return render(request, 'core/marketing_jobs.html', {
        'jobs': jobs
    })

def fortune_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        company_type__icontains='fortune'
    ).order_by('-id')

    return render(request, 'core/fortune_jobs.html', {
        'jobs': jobs
    })

def human_resources_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        category__iexact='Human Resources'
    ).order_by('-id')

    return render(request, 'core/human_resources_jobs.html', {
        'jobs': jobs
    })

def project_management_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        category__icontains='Project Management'
    ).order_by('-id')

    return render(request, 'core/project_management_jobs.html', {
        'jobs': jobs
    })

def it_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        category__icontains='IT'
    ).order_by('-id')

    return render(request, 'core/it_jobs.html', {
        'jobs': jobs
    })

def sales_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        category__icontains='Sales'
    ).order_by('-id')

    return render(request, 'core/sales_jobs.html', {
        'jobs': jobs
    })

def data_science_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__iexact='Remote',
        category__icontains='Data Science'
    ).order_by('-id')

    return render(request, 'core/data_science_jobs.html', {
        'jobs': jobs
    })

def fresher_jobs_page(request):
    jobs = Job.objects.filter(
        experience__iexact='Fresher',
        work_mode__iexact='Remote'
    ).order_by('-id')

    return render(request, 'core/fresher_jobs.html', {
        'jobs': jobs
    })

def walk_in_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__icontains='walk'
    ).order_by('-id')

    return render(request, 'core/walk_in_jobs.html', {
        'jobs': jobs
    })

def part_time_jobs_page(request):
    jobs = Job.objects.filter(
        work_mode__icontains='part time'
    ).order_by('-id')

    return render(request, 'core/part_time_jobs.html', {
        'jobs': jobs
    })

def delhi_jobs_page(request):
    jobs = Job.objects.filter(
        location__icontains='Delhi',
        work_mode__iexact='Remote'
    ).order_by('-id')

    return render(request, 'core/delhi_jobs.html', {
        'jobs': jobs
    })

def mumbai_jobs_page(request):
    jobs = Job.objects.filter(
        location__icontains='Mumbai',
        work_mode__iexact='Remote'
    ).order_by('-id')

    return render(request, 'core/mumbai_jobs.html', {
        'jobs': jobs
    })



def bangalore_jobs_page(request):
    jobs = Job.objects.filter(
        Q(location__icontains='Bangalore') | Q(location__icontains='Bengaluru'),
        work_mode__iexact='Remote'
    ).order_by('-id')

    return render(request, 'core/bangalore_jobs.html', {
        'jobs': jobs
    })

def hyderabad_jobs_page(request):
    jobs = Job.objects.filter(
    location__icontains='Hyderabad'
).filter(
    Q(work_mode__iexact='Remote') |
    Q(work_mode__iexact='Hybrid') |
    Q(work_mode__iexact='On-site')
).order_by('-id')

    return render(request, 'core/hyderabad_jobs.html', {
        'jobs': jobs
    })

def chennai_jobs_page(request):
    jobs = Job.objects.filter(
    location__icontains='Chennai'
).filter(
    Q(work_mode__iexact='Remote') |
    Q(work_mode__iexact='Hybrid') |
    Q(work_mode__iexact='On-site')
).order_by('-id')

    return render(request, 'core/chennai_jobs.html', {
        'jobs': jobs
    })

def pune_jobs_page(request):
    jobs = Job.objects.filter(
    location__icontains='Pune'
).filter(
    Q(work_mode__iexact='Remote') |
    Q(work_mode__iexact='Hybrid') |
    Q(work_mode__iexact='On-site')
).order_by('-id')

    return render(request, 'core/pune_jobs.html', {
        'jobs': jobs
    })

def company_unicorn(request):
    jobs = Job.objects.filter(
        company_type__icontains='unicorn'
    ).order_by('-id')

    return render(request, 'core/company_unicorn.html', {
        'jobs': jobs
    })

def company_mnc_jobs_page(request):
    jobs = Job.objects.filter(
    Q(company_type__icontains='mnc') |
    Q(company_type__icontains='multinational')
    ).order_by('-id')

    return render(request, 'core/company_mnc_jobs.html', {
        'jobs': jobs
    })

def company_startups_jobs_page(request):
    jobs = Job.objects.filter(
        Q(company_type__icontains='startup') |
        Q(company_type__icontains='start-up')
    ).order_by('-id')

    return render(request, 'core/company_startups_jobs.html', {
        'jobs': jobs
    })

def company_product_based_jobs_page(request):
    jobs = Job.objects.filter(
        Q(category__icontains='product') |
        Q(category__icontains='product based')
    ).order_by('-id')

    return render(request, 'core/company_product_based_jobs.html', {
        'jobs': jobs
    })

def company_internet_jobs_page(request):
    jobs = Job.objects.filter(
        Q(company_type__icontains='internet') |
        Q(company_type__icontains='online') |
        Q(company_type__icontains='web')
    ).order_by('-id')

    return render(request, 'core/company_internet_jobs.html', {
        'jobs': jobs
    })

def company_top_companies_jobs_page(request):
    # Keywords for top companies
    company_keywords = [
        'unicorn', 'mnc', 'multinational',
        'startup', 'start-up',
        'internet', 'online', 'web'
    ]

    category_keywords = [
        'product'
    ]

    # Build dynamic OR query
    query = Q()

    for word in company_keywords:
        query |= Q(company_type__icontains=word)

    for word in category_keywords:
        query |= Q(category__icontains=word)

    # Fetch jobs
    jobs = Job.objects.filter(query).order_by('-id').distinct()

    return render(request, 'core/company_top_companies_jobs.html', {
        'jobs': jobs
    })

def company_it_companies_jobs_page(request):
    keywords = [
        'information technology',
        'technology',
        'tech',
        'software'
    ]

    query = Q()

    for word in keywords:
        query |= Q(company_type__icontains=word)

    jobs = Job.objects.filter(query).order_by('-id').distinct()

    return render(request, 'core/company_it_companies_jobs.html', {
        'jobs': jobs
    })

def company_fintech_jobs_page(request):
    keywords = [
        'fintech',
        'financial technology',
        'finance technology',
        'payments',
        'digital payments',
        'banking',
        'nbfc'
    ]

    query = Q()

    for word in keywords:
        query |= Q(company_type__icontains=word)

    jobs = Job.objects.filter(query).order_by('-id').distinct()

    return render(request, 'core/company_fintech_companies_jobs.html', {
        'jobs': jobs
    })

def company_sponsored_companies_jobs_page(request):
    jobs = Job.objects.filter(is_sponsored=True).order_by('-id')

    return render(request, 'core/company_sponsored_companies_jobs.html', {
        'jobs': jobs
    })

def company_featured_companies_jobs_page(request):
    jobs = Job.objects.filter(is_featured=True).order_by('-id')

    return render(request, 'core/company_featured_companies_jobs.html', {
        'jobs': jobs
    })