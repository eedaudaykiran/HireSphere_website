from django.contrib import admin
from .models import Job, UserProfile 

admin.site.register(Job)


class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'role',
        'company_name',
        'work_status'
    )

    class Media:

        js = (
            'js/profile_toggle.js',
        )


admin.site.register(UserProfile, UserProfileAdmin)