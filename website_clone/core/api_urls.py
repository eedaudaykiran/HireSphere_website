from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'jobs', api_views.JobViewSet, basename='job')
router.register(r'applications', api_views.ApplicationViewSet, basename='application')

urlpatterns = [
    path('auth/register/', api_views.api_register, name='api_register'),
    path('auth/login/', api_views.api_login, name='api_login'),
    path('auth/logout/', api_views.api_logout, name='api_logout'),
    path('profile/', api_views.api_profile, name='api_profile'),
    path('', include(router.urls)),
]