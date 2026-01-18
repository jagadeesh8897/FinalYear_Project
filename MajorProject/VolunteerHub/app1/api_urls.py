from django.urls import path
from . import views

urlpatterns = [
    # AUTH
    path("login/", views.login_api),

    # REGISTRATION
    path("volunteer/register/", views.volunteer_register_api),
    path("organization/register/", views.organization_register_api),
]
