"""
URL configuration for VolunteerHub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import volunteer_dashboard, admin_dashboard, organization_dashboard, create_service, \
    list_services, apply_service, assign_volunteers, home, login_page, volunteer_dashboard_page, \
    organization_dashboard_page, admin_dashboard_page, submit_work, rate_volunteer, \
    register_view, login_api

urlpatterns = [
    path('', home),

    path('admin/', admin.site.urls),


    path('login/', login_page, name='login'),
    path("api/login/", login_api, name="login_api"),
    path("register/", register_view, name="register"),

    path('volunteer/dashboard/', volunteer_dashboard),
    path('organization/dashboard/', organization_dashboard),
    path('admin-panel/dashboard/', admin_dashboard),
    path('volunteer/submit/<int:application_id>/', submit_work),
    path('organization/rate/<int:application_id>/', rate_volunteer),










]
