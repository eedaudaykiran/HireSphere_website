from rest_framework import serializers
from .models import Job, Application, UserProfile, CompanyProfile

class JobSerializer(serializers.ModelSerializer):
    experience_display = serializers.ReadOnlyField()
    salary_display = serializers.ReadOnlyField()
    skills_list = serializers.ReadOnlyField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'company', 'location', 'work_mode',
            'job_type', 'category', 'min_experience', 'max_experience',
            'experience_display', 'min_salary', 'max_salary',
            'salary_display', 'skills', 'skills_list', 'description',
            'created_at', 'is_active', 'company_type', 'logo',
        ]

class ApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_title', 'applicant', 'applicant_name',
            'status', 'applied_at', 'skills', 'location', 'experience',
            'phone_number',
        ]
        read_only_fields = ['applicant', 'applied_at']

    def get_applicant_name(self, obj):
        return obj.applicant.get_full_name() or obj.applicant.username

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'full_name', 'role',
                  'work_status', 'company', 'location', 'skills']

class CompanyProfileSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='employer.username', read_only=True)

    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'company_name', 'description', 'industry',
            'founded_year', 'employee_count', 'company_type',
            'location', 'city', 'website', 'logo',
        ]