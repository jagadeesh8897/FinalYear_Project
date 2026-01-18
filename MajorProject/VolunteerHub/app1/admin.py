from django.contrib import admin
from .models import User, VolunteerProfile, Organization, Service, Application

admin.site.register(User)
admin.site.register(VolunteerProfile)
admin.site.register(Organization)

admin.site.register(Service)
admin.site.register(Application)
