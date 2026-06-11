from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db.models import Q
from .models import Job, Application, UserProfile, CompanyProfile
from .serializers import (
    JobSerializer, ApplicationSerializer,
    UserProfileSerializer, CompanyProfileSerializer,
)


# ── Authentication ───────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def api_register(request):
    """POST /api/auth/register/ — create candidate account"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    full_name = request.data.get('full_name', '')
    mobile_number = request.data.get('mobile_number', '')

    if not username or not email or not password:
        return Response({'error': 'username, email, password are required'},
                        status=status.HTTP_400_BAD_REQUEST)

    from django.contrib.auth.models import User
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'},
                        status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username, email=email,
        password=password, first_name=full_name
    )
    UserProfile.objects.create(
        user=user, full_name=full_name,
        mobile_number=mobile_number, role='candidate'
    )
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user_id': user.id, 'username': user.username},
                    status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def api_login(request):
    """POST /api/auth/login/ — returns auth token"""
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'error': 'Invalid credentials'},
                        status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    try:
        role = user.userprofile.role
    except UserProfile.DoesNotExist:
        role = 'unknown'
    return Response({'token': token.key, 'user_id': user.id,
                     'username': user.username, 'role': role})


@api_view(['POST'])
def api_logout(request):
    """POST /api/auth/logout/ — deletes token"""
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'})


# ── Jobs ─────────────────────────────────────────────────────────────────────

class JobViewSet(viewsets.ModelViewSet):
    """
    GET    /api/jobs/            — list all active jobs (paginated)
    POST   /api/jobs/            — create job (employer only)
    GET    /api/jobs/{id}/       — job detail
    PUT    /api/jobs/{id}/       — update job (owner only)
    DELETE /api/jobs/{id}/       — delete job (owner only)
    GET    /api/jobs/search/     — search jobs ?q=python&location=Hyderabad
    GET    /api/jobs/my_jobs/    — employer's own jobs
    """
    serializer_class = JobSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'company', 'description', 'location']
    ordering_fields = ['created_at', 'min_salary', 'max_salary']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Job.objects.filter(is_active=True)
        # Filter support via query params
        location = self.request.query_params.get('location')
        category = self.request.query_params.get('category')
        job_type = self.request.query_params.get('job_type')
        min_exp = self.request.query_params.get('min_experience')
        company_type = self.request.query_params.get('company_type')

        if location:
            qs = qs.filter(location__icontains=location)
        if category:
            qs = qs.filter(category__icontains=category)
        if job_type:
            qs = qs.filter(job_type=job_type)
        if min_exp:
            try:
                qs = qs.filter(min_experience__lte=int(min_exp),
                               max_experience__gte=int(min_exp))
            except ValueError:
                pass
        if company_type:
            qs = qs.filter(company_type__icontains=company_type)
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user)

    def update(self, request, *args, **kwargs):
        job = self.get_object()
        if job.employer != request.user:
            return Response({'error': 'You can only edit your own jobs'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        job = self.get_object()
        if job.employer != request.user:
            return Response({'error': 'You can only delete your own jobs'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my_jobs(self, request):
        """GET /api/jobs/my_jobs/ — employer's own jobs"""
        jobs = Job.objects.filter(employer=request.user)
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """GET /api/jobs/search/?q=python&location=Hyderabad&experience=2"""
        q = request.query_params.get('q', '').strip()
        location = request.query_params.get('location', '').strip()
        experience = request.query_params.get('experience', '').strip()
        qs = Job.objects.filter(is_active=True)
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(company__icontains=q) |
                Q(description__icontains=q)
            )
        if location:
            qs = qs.filter(location__icontains=location)
        if experience:
            try:
                exp_int = int(experience)
                qs = qs.filter(min_experience__lte=exp_int,
                               max_experience__gte=exp_int)
            except ValueError:
                pass
        serializer = self.get_serializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})


# ── Applications ─────────────────────────────────────────────────────────────

class ApplicationViewSet(viewsets.ModelViewSet):
    """
    GET    /api/applications/          — candidate sees their applications
    POST   /api/applications/          — submit application
    GET    /api/applications/{id}/     — detail
    PATCH  /api/applications/{id}/     — employer updates status
    GET    /api/applications/my_applications/ — shortcut for candidate
    """
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            if user.userprofile.role == 'employer':
                return Application.objects.filter(
                    job__employer=user
                ).select_related('applicant', 'job')
        except UserProfile.DoesNotExist:
            pass
        return Application.objects.filter(
            applicant=user
        ).select_related('job')

    def perform_create(self, serializer):
        job = serializer.validated_data['job']
        if Application.objects.filter(applicant=self.request.user, job=job).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError('You have already applied for this job.')
        serializer.save(applicant=self.request.user, status='Applied')

    def partial_update(self, request, *args, **kwargs):
        app = self.get_object()
        # Only employer who owns the job can change status
        if app.job.employer != request.user:
            return Response({'error': 'Access denied'},
                            status=status.HTTP_403_FORBIDDEN)
        new_status = request.data.get('status')
        valid = ['Applied','Screening','Shortlisted','Interview',
                 'Technical','HR','Offer','Rejected']
        if new_status not in valid:
            return Response({'error': f'Invalid status. Must be one of: {valid}'},
                            status=status.HTTP_400_BAD_REQUEST)
        app.status = new_status
        app.save()
        return Response(ApplicationSerializer(app).data)

    @action(detail=False, methods=['get'])
    def my_applications(self, request):
        apps = Application.objects.filter(
            applicant=request.user
        ).select_related('job')
        serializer = self.get_serializer(apps, many=True)
        return Response(serializer.data)


# ── User Profile ─────────────────────────────────────────────────────────────

@api_view(['GET', 'PATCH'])
def api_profile(request):
    """
    GET   /api/profile/ — get current user profile
    PATCH /api/profile/ — update profile
    """
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(UserProfileSerializer(profile).data)

    serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)