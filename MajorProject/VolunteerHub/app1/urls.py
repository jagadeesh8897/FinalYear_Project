from django.urls import path
from . import views
from .views import logout_view

urlpatterns = [

    # HOME
    path('', views.home, name='home'),

    # AUTH
    path('login/', views.login_page, name='login'),
    path('api/login/', views.login_api, name='login_api'),
    path('register/', views.register_view, name='register'),
    path('logout/', logout_view, name='logout'),


    # VOLUNTEER
    path('volunteer/dashboard/', views.volunteer_dashboard_page, name='volunteer_dashboard'),
    path('volunteer/services/', views.volunteer_available_services, name='volunteer_services'),
    path('volunteer/apply/<int:service_id>/', views.volunteer_apply_service, name='volunteer_apply_service'),
    path('volunteer/applications/', views.volunteer_applications, name='volunteer_applications'),
    path('volunteer/profile/', views.volunteer_profile, name='volunteer_profile'),

    # ORGANIZATION
    path('organization/dashboard/', views.organization_dashboard_page, name='organization_dashboard'),
    path('organization/create-service/', views.organization_create_service, name='create_service'),
path(
    "organization/service/<int:service_id>/applications/",
    views.organization_view_applicants,
    name="org_view_applicants"
),

    path('organization/service/<int:service_id>/select/', views.org_select_volunteers, name='org_select_volunteers'),
    path('organization/volunteer/<int:volunteer_id>/profile/', views.org_view_volunteer_profile, name='org_view_volunteer_profile'),
    path('organization/application/<int:app_id>/approve/', views.org_approve_volunteer, name='org_approve_volunteer'),
    path('organization/application/<int:app_id>/reject/', views.org_reject_volunteer, name='org_reject_volunteer'),

    # ADMIN PANEL (CUSTOM)
    path('admin_panel/dashboard/', views.admin_dashboard_page, name='admin_dashboard'),
    path('admin_panel/volunteers/', views.admin_volunteers, name='admin_volunteers'),
    path('admin_panel/pending-organizations/', views.admin_pending_organizations, name='pending_orgs'),
    path('admin_panel/approved-organizations/', views.admin_approved_organizations, name='admin_approved_organizations'),
    path('admin_panel/pending-services/', views.admin_pending_services, name='admin_pending_services'),
    path('admin_panel/approve-service/<int:service_id>/', views.admin_approve_service, name='admin_approve_service'),
    path('admin_panel/active-works/', views.admin_active_works, name='admin_active_works'),
    path('admin_panel/completed-works/', views.admin_completed_works, name='admin_completed_works'),
    path('admin_panel/complete-service/<int:service_id>/', views.admin_mark_service_completed, name='admin_complete_service'),
    path('admin_panel/assign/<int:service_id>/', views.admin_assign_volunteers_page, name='admin_assign_page'),
    path('admin_panel/assign-confirm/<int:service_id>/', views.assign_volunteers, name='assign_volunteers'),
]
