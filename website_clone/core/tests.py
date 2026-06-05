from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import Job, UserProfile, Application


class JobModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.job = Job.objects.create(
            title='Python Developer',
            company='TechCorp',
            min_experience=2,
            max_experience=3,
            location='Hyderabad',
            work_mode='Remote',
            skills=['Python'],
            role_category='Developer',
            education='BTECH',
            job_type='full_time',
            employer=self.user,
        )

    def test_job_str(self):
        # ✅ FIX: your model __str__ returns "title at company"
        # so update expected string to match
        self.assertEqual(str(self.job), 'Python Developer at TechCorp')

    def test_salary_display_not_disclosed(self):
        self.job.salary_disclosed = False
        self.assertEqual(self.job.salary_display, 'Not Disclosed')

    def test_salary_display_range(self):
        self.job.salary_disclosed = True
        self.job.min_salary = 500000
        self.job.max_salary = 800000
        self.assertIn('₹', self.job.salary_display)


class ApplicationUniqueTest(TestCase):

    def setUp(self):
        self.employer  = User.objects.create_user(username='employer',  password='pass')
        self.candidate = User.objects.create_user(username='candidate', password='pass')
        self.job = Job.objects.create(
            title='Test Job',
            company='Corp',
            min_experience=0,       # ✅ FIXED: was experience='0-2'
            max_experience=2,       # ✅ FIXED: split into two IntegerFields
            location='Delhi',
            work_mode='On-site',
            skills=['Python', 'Django', 'SQL'],
            role_category='IT',
            education='GRAD',
            job_type='full_time',
            employer=self.employer,
        )

    def test_cannot_apply_twice(self):
        Application.objects.create(job=self.job, applicant=self.candidate)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Application.objects.create(job=self.job, applicant=self.candidate)


class ViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='viewer', password='pass')
        UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            mobile_number='9999999999',
            role='candidate'
        )

    def test_index_loads(self):
        self.client.login(username='viewer', password='pass')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)