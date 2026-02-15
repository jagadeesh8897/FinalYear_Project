import json
from datetime import datetime

from app1.models import Service
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Attendance
from .models import (
    Organization,
    Service,
    Application
)

User = get_user_model()


# ==================== AUTH ====================

@csrf_exempt
def login_page(request):
    return render(request, "login.html")


@csrf_exempt
def login_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    email = data.get("username")
    password = data.get("password")
    role = data.get("role")

    user = User.objects.filter(email=email).first()
    if not user:
        return JsonResponse({"status": "error", "message": "Email not registered"})

    # ROLE VALIDATION
    if role == "VOLUNTEER":
        if not email.endswith("@srit.ac.in") or user.role != "VOLUNTEER":
            return JsonResponse({"status": "error", "message": "Invalid volunteer account"})
        if not VolunteerProfile.objects.filter(user=user).exists():
            return JsonResponse({"status": "error", "message": "Volunteer profile missing"})

    elif role == "ORGANIZATION":
        if not email.endswith("@gmail.com") or user.role != "ORGANIZATION":
            return JsonResponse({"status": "error", "message": "Invalid organization account"})
        org = Organization.objects.filter(user=user).first()
        if not org or not org.approved:
            return JsonResponse({"status": "error", "message": "Organization not approved by admin"})

    elif role == "ADMIN":
        if user.role != "ADMIN":
            return JsonResponse({"status": "error", "message": "Not an admin account"})

    else:
        return JsonResponse({"status": "error", "message": "Invalid role"})

    user = authenticate(request, username=user.username, password=password)
    if not user:
        return JsonResponse({"status": "error", "message": "Invalid password"})

    login(request, user)
    return JsonResponse({"status": "success", "role": user.role})


# ==================== HOME ====================

def home(request):
    return render(request, "home.html")


# ==================== DASHBOARDS ====================


from django.utils.timezone import now


@login_required
def volunteer_dashboard_page(request):
    if request.user.role != "VOLUNTEER":
        return redirect("login")

    profile, created = VolunteerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.email.split("@")[0],
            "phone": "",
            "student_id": "",
            "department": "",
            "year": "",
            "skills": ""
        }
    )

    today = now().date()

    # 🔢 COUNTS (THIS IS THE FIX)
    applied = Application.objects.filter(
        volunteer=profile,
        status="APPLIED"
    ).count()

    selected = Application.objects.filter(
        volunteer=profile,
        status="SELECTED"
    ).count()

    completed = Application.objects.filter(
        volunteer=profile,
        status="COMPLETED"
    ).count()

    from django.utils import timezone

    selected_apps = Application.objects.filter(
        volunteer=profile,
        status="SELECTED"
    ).select_related("service")

    total_days = 0
    total_present = 0

    today = timezone.now().date()

    for app in selected_apps:
        service = app.service

        if service.start_date and service.end_date:

            # Count only days up to today (not future days)
            effective_end = min(service.end_date, today)

            if effective_end >= service.start_date:
                event_days = (effective_end - service.start_date).days + 1
                total_days += event_days

        present_days = Attendance.objects.filter(
            application=app,
            is_present=True
        ).count()

        total_present += present_days

    overall_attendance = (
        round((total_present / total_days) * 100, 2)
        if total_days > 0 else 0
    )

    # 🎯 GOAL
    goal = 10

    # 📅 UPCOMING SERVICES
    upcoming_services = Service.objects.filter(
        application__volunteer=profile,
        application__status__in=["APPLIED", "SELECTED"],
        start_date__gte=today
    ).select_related(
        "organization",
        "organization__user"
    ).distinct().order_by("start_date")

    return render(
        request,
        "volunteer/dashboard.html",
        {
            "profile": profile,
            "applied_count": applied,
            "selected_count": selected,
            "completed": completed,
            "goal": goal,
            "upcoming_services": upcoming_services,
            "overall_attendance": overall_attendance,
            "active_page": "dashboard",
        }
    )


@login_required
def organization_dashboard_page(request):
    if request.user.role != "ORGANIZATION":
        return redirect("login")

    org = Organization.objects.get(user=request.user)
    services = Service.objects.filter(organization=org)

    return render(request, "organization/dashboard.html", {
        "services": services
    })


@login_required
def admin_dashboard_page(request):
    if request.user.role != "ADMIN":
        return redirect("login")

    pending_org_count = Organization.objects.filter(approved=False).count()
    pending_service_count = Service.objects.filter(status__iexact="pending").count()

    return render(
        request,
        "admin_panel/dashboard.html",
        {
            "volunteers": VolunteerProfile.objects.count(),
            "approved_org_count": Organization.objects.filter(approved=True).count(),
            "active": Service.objects.filter(status="APPROVED").count(),
            "completed": Service.objects.filter(status="COMPLETED").count(),
            "pending_org_count": pending_org_count,
            "pending_service_count": pending_service_count,
        }
    )


@login_required
def admin_pending_services(request):
    if request.user.role != "ADMIN":
        return redirect("login")

    services = Service.objects.filter(status__iexact="pending")

    return render(
        request,
        "admin_panel/pending_services.html",
        {"services": services}
    )


@login_required
def admin_approve_service(request, service_id):
    if request.user.role != "ADMIN":
        return redirect("login")

    service = get_object_or_404(Service, id=service_id)
    service.status = "APPROVED"
    service.save()

    messages.success(request, "Service approved successfully")
    return redirect("admin_pending_services")


# ==================== ADMIN MODULE ====================
@login_required
def admin_volunteers(request):
    if request.user.role != 'ADMIN':
        return redirect('login')

    volunteers = VolunteerProfile.objects.all()

    # ---- Normalize year ----
    def normalize_year(y):
        if "1" in y:
            return "1"
        if "2" in y:
            return "2"
        if "3" in y:
            return "3"
        if "4" in y:
            return "4"
        return None

    for v in volunteers:
        v.norm_year = normalize_year(v.year)

    # ---- Year counts ----
    year_counts = {
        "1": sum(1 for v in volunteers if v.norm_year == "1"),
        "2": sum(1 for v in volunteers if v.norm_year == "2"),
        "3": sum(1 for v in volunteers if v.norm_year == "3"),
        "4": sum(1 for v in volunteers if v.norm_year == "4"),
    }

    # ---- Branch counts (ONLY final year) ----
    branches = ["CSE", "ECE", "EEE", "MECH", "CIVIL"]
    branch_counts = {
        b: sum(1 for v in volunteers if v.norm_year == "4" and v.department == b)
        for b in branches
    }

    # ---- Sorting ----
    sort = request.GET.get("sort", "roll")
    if sort == "name":
        volunteers = sorted(volunteers, key=lambda x: x.full_name.lower())
    else:
        volunteers = sorted(volunteers, key=lambda x: x.student_id)

    return render(request, "admin_panel/volunteers.html", {
        "volunteers": volunteers,
        "year_counts": year_counts,
        "branch_counts": branch_counts,
    })


@login_required
def admin_pending_organizations(request):
    if request.user.role != "ADMIN":
        return redirect("login")

    pending_orgs = Organization.objects.filter(approved=False)
    return render(request, "admin_panel/pending_organizations.html", {
        "organizations": pending_orgs
    })


@login_required
def approve_organization(request, org_id):
    if request.user.role != "ADMIN":
        return redirect("login")

    org = get_object_or_404(Organization, id=org_id)
    org.approved = True
    org.user.is_active = True
    org.user.save()
    org.save()

    messages.success(request, "Organization approved successfully")
    return redirect("/admin_panel/pending-organizations/")


@login_required
def reject_organization(request, org_id):
    if request.user.role != "ADMIN":
        return redirect("login")

    org = get_object_or_404(Organization, id=org_id)
    org.user.delete()

    messages.error(request, "Organization rejected")
    return redirect("/admin_panel/pending-organizations/")


# ==================== SERVICES ====================
@require_POST
@login_required
def create_service(request):
    if request.user.role != "ORGANIZATION":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    org = Organization.objects.get(user=request.user)
    data = json.loads(request.body)

    service = Service.objects.create(
        title=data["title"],
        description=data["description"],
        location=data["location"],
        start_date=datetime.strptime(data["date"], "%Y-%m-%d"),
        end_date=datetime.strptime(data["date"], "%Y-%m-%d"),
        required_volunteers=data["required_volunteers"],
        organization=org  # ✅ THIS IS ENOUGH
    )

    return JsonResponse({
        "message": "Service created",
        "service_id": service.id
    })


@login_required
def list_services(request):
    services = Service.objects.filter(status="APPROVED")
    return JsonResponse({"services": list(services.values())})


@require_POST
@login_required
def apply_service(request, service_id):
    if request.user.role != "VOLUNTEER":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    profile = VolunteerProfile.objects.get(user=request.user)
    service = get_object_or_404(Service, id=service_id)

    Application.objects.create(volunteer=profile, service=service)
    return JsonResponse({"message": "Applied successfully"})


# ==================== AI SELECTION ====================

@require_POST
@login_required
def assign_volunteers(request, service_id):
    if request.user.role != "ADMIN":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    service = Service.objects.get(id=service_id)
    applications = Application.objects.filter(
        service=service
    ).select_related("volunteer").order_by("-id")

    scored = [(calculate_score(app.volunteer, service), app) for app in applications]
    scored.sort(reverse=True, key=lambda x: x[0])

    selected = scored[:service.required_volunteers]
    for _, app in selected:
        app.status = "SELECTED"
        app.save()

    service.status = "APPROVED"
    service.save()

    return JsonResponse({"message": "AI-based selection completed"})


def calculate_score(volunteer, service):
    score = 0
    score += volunteer.attendance * 0.4

    service_skills = service.description.lower()
    volunteer_skills = volunteer.skills.lower()
    match = sum(1 for word in volunteer_skills.split(",") if word.strip() in service_skills)
    score += match * 10 * 0.4

    score += volunteer.rating * 0.2
    return score


# ==================== SUBMISSION & RATING ====================

@require_POST
@login_required
def submit_work(request, application_id):
    if request.user.role != "VOLUNTEER":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    data = json.loads(request.body)
    app = Application.objects.get(id=application_id)

    app.submission_text = data.get("submission")
    app.status = "COMPLETED"
    app.save()

    volunteer = app.volunteer
    volunteer.completed_services += 1
    volunteer.save()

    return JsonResponse({"message": "Work submitted successfully"})


@require_POST
@login_required
def rate_volunteer(request, application_id):
    if request.user.role != "ORGANIZATION":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    data = json.loads(request.body)
    app = Application.objects.get(id=application_id)

    app.rating = data.get("rating")
    app.review = data.get("review")
    app.save()

    ratings = Application.objects.filter(
        volunteer=app.volunteer, rating__gt=0
    ).values_list("rating", flat=True)

    app.volunteer.rating = sum(ratings) / len(ratings)
    app.volunteer.save()

    return JsonResponse({"message": "Volunteer rated"})


# ==================== REGISTER ====================

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return "Must contain uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Must contain lowercase letter"
    if not re.search(r"\d", password):
        return "Must contain number"
    if not re.search(r"[@$!%*?&]", password):
        return "Must contain special character"
    return None


from django.db import transaction
from django.contrib import messages
import re


def register_view(request):
    if request.method != "POST":
        return render(request, "register.html")

    role = request.POST.get("role")
    full_name = request.POST.get("full_name")
    email = request.POST.get("email")
    phone = request.POST.get("phone")
    year = request.POST.get("year") if role == "VOLUNTEER" else ""
    student_id = request.POST.get("student_id")
    department = request.POST.get("department")
    skills = request.POST.get("skills", "")
    password = request.POST.get("password")
    rpassword = request.POST.get("rpassword")

    # ---------- VALIDATIONS ----------
    if password != rpassword:
        messages.warning(request, "Passwords do not match")
        return render(request, "register.html", {
            "form_data": request.POST,
            "selected_role": role
        })

    if role == "VOLUNTEER" and not email.endswith("@srit.ac.in"):
        messages.warning(request, "Volunteer email must end with @srit.ac.in")
        return render(request, "register.html", {
            "form_data": request.POST,
            "selected_role": role
        })
    if role == "VOLUNTEER":
        if VolunteerProfile.objects.filter(student_id=student_id).exists():
            messages.warning(request, "Student ID already registered")
            return render(request, "register.html", {
                "form_data": request.POST,
                "selected_role": role
            })
        rollno = request.POST.get("student_id").lower()

        pattern = r'^\d{2}4g\d{1}a\d{2}[a-zA-Z0-9]{2}$'

        if not re.match(pattern, rollno):
            messages.error(
                request,
                "Invalid roll number format. Example: 224G1A0530"
            )
            return render(request, "register.html", {
                "form_data": request.POST,
                "selected_role": role
            })
        email_prefix = email.split("@")[0]

        if email_prefix != rollno:
            messages.error(
                request,
                "Email must match your roll number"
            )
            return render(request, "register.html", {
                "form_data": request.POST,
                "selected_role": role
            })

    if role == "ORGANIZATION" and not email.endswith("@gmail.com"):
        messages.warning(request, "Organization email must end with @gmail.com")
        return render(request, "register.html", {
            "form_data": request.POST,
            "selected_role": role
        })

    if User.objects.filter(username=email).exists():
        messages.warning(request, "Email already registered")
        return render(request, "register.html", {
            "form_data": request.POST,
            "selected_role": role
        })

    # ---------- CREATE USER ----------
    with transaction.atomic():
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role=role
        )

        if role == "VOLUNTEER":
            VolunteerProfile.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": full_name,
                    "phone": phone,
                    "student_id": student_id,
                    "department": department,
                    "year": year,
                    "skills": skills,
                }
            )

            messages.success(request, "Volunteer registered successfully")

        else:  # ORGANIZATION
            user.is_active = False
            user.save()

            letter = request.FILES.get("verification_letter")

            Organization.objects.update_or_create(
                user=user,
                defaults={
                    "organization_name": full_name,  # ✅ org name only
                    "verification_letter": letter,
                    "approved": False
                }
            )

            messages.success(
                request,
                "Organization registered. Await admin approval."
            )

    return redirect("login")


def logout_view(request):
    logout(request)  # destroys session
    return redirect('login')


@login_required
def admin_active_works(request):
    if request.user.role != "ADMIN":
        return redirect("login")

    services = Service.objects.filter(status="APPROVED")

    context = {
        "services": services,
        "active_count": services.count(),
        "org_count": services.values("organization").distinct().count(),
        "total_required": sum(s.required_volunteers for s in services),
    }

    return render(
        request,
        "admin_panel/active_works.html",
        context
    )


@login_required
def admin_completed_works(request):
    if request.user.role != "ADMIN":
        return redirect("login")

    services = Service.objects.filter(status="COMPLETED")

    return render(request, "admin_panel/completed_works.html", {
        "services": services
    })


@login_required
def organization_create_service(request):
    if request.user.role != "ORGANIZATION":
        return redirect("login")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        location = request.POST.get("location")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        required_volunteers = request.POST.get("required_volunteers")

        org = Organization.objects.get(user=request.user)

        Service.objects.create(
            title=title,
            description=description,
            location=location,
            start_date=start_date,
            end_date=end_date,
            required_volunteers=required_volunteers,
            organization=org,
            authorization_letter=request.FILES.get("authorization_letter"),
            status="PENDING"
        )

        messages.success(
            request,
            "Service submitted successfully. Await admin approval."
        )

        return redirect("organization_dashboard")

    return render(request, "organization/create_service.html")


@login_required
def admin_assign_volunteers_page(request, service_id):
    if request.user.role != "ADMIN":
        return redirect("login")

    service = get_object_or_404(Service, id=service_id)
    applications = Application.objects.filter(service=service)

    return render(
        request,
        "admin_panel/assign_volunteers.html",
        {
            "service": service,
            "applications": applications
        }
    )


# ---- AI SCORING ----
def calculate_score(volunteer, service):
    score = 0
    score += volunteer.attendance * 0.4
    score += volunteer.rating * 0.6
    return score


# ---- ADMIN ASSIGN VOLUNTEERS ----
from django.views.decorators.http import require_POST


@require_POST
def assign_volunteers(request, service_id):
    if request.user.role != "ADMIN":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    service = Service.objects.get(id=service_id)

    applications = Application.objects.filter(
        service=service,
        status="APPLIED"
    )

    scored = []
    for app in applications:
        score = calculate_score(app.volunteer, service)
        scored.append((score, app))

    scored.sort(reverse=True, key=lambda x: x[0])
    selected = scored[:service.required_volunteers]

    for _, app in selected:
        app.status = "SELECTED"
        app.save()

    service.status = "APPROVED"  # ACTIVE
    service.save()

    return redirect("admin_active_works")


@login_required
@require_POST
def admin_mark_service_completed(request, service_id):
    if request.user.role != "ADMIN":
        return redirect("home")

    service = get_object_or_404(Service, id=service_id, status="APPROVED")

    service.status = "COMPLETED"
    service.save()

    return redirect("admin_completed_works")


@login_required
def volunteer_available_services(request):
    if request.user.role != "VOLUNTEER":
        return redirect("login")

    today = timezone.now().date()

    services = Service.objects.filter(status="APPROVED")

    profile = VolunteerProfile.objects.get(user=request.user)

    applications = Application.objects.filter(volunteer=profile)

    applied_dict = {
        app.service.id: app.status
        for app in applications
    }

    return render(
        request,
        "volunteer/available_services.html",
        {
            "services": services,
            "applied_dict": applied_dict,
            "today": today,
            "active_page": "services"
        }
    )


@login_required
def volunteer_apply_service(request, service_id):
    if request.user.role != "VOLUNTEER":
        return redirect("login")

    profile = VolunteerProfile.objects.get(user=request.user)

    service = get_object_or_404(
        Service,
        id=service_id,
        status="APPROVED"
    )

    # Prevent duplicate apply
    if Application.objects.filter(
            volunteer=profile,
            service=service
    ).exists():
        messages.warning(
            request,
            "You have already sent a request for this service"
        )
        return redirect("volunteer_services")

    Application.objects.create(
        volunteer=profile,
        service=service,
        status="APPLIED"
    )

    messages.success(
        request,
        "Request sent for approval"
    )

    return redirect("volunteer_services")

@login_required
def organization_view_applicants(request, service_id):

    service = get_object_or_404(Service, id=service_id)

    # All applications for this service
    applications = Application.objects.filter(service=service)

    selected_apps = applications.filter(status="SELECTED")
    rejected_apps = applications.filter(status="REJECTED")
    applied_apps  = applications.filter(status="APPLIED")

    today = timezone.now().date()

    # ✅ attendance records for today for this service
    today_attendance = Attendance.objects.filter(
        application__service=service,
        date=today
    )

    # ✅ who is present today
    present_ids_today = set(
        today_attendance.filter(is_present=True)
        .values_list("application_id", flat=True)
    )

    # ✅ who is marked (present or absent)
    marked_ids_today = set(
        today_attendance.values_list("application_id", flat=True)
    )

    # ✅ check if any selected volunteer not yet marked today
    unmarked_exists = selected_apps.exclude(
        id__in=marked_ids_today
    ).exists()

    # ✅ event active check
    event_active = (
        service.start_date
        and service.end_date
        and service.start_date <= today <= service.end_date
    )

    context = {
        "service": service,
        "selected_apps": selected_apps,
        "rejected_apps": rejected_apps,
        "applied_apps": applied_apps,
        "event_active": event_active,
        "today": today,
        "present_ids_today": present_ids_today,
        "marked_ids_today": marked_ids_today,
        "unmarked_exists": unmarked_exists,
    }

    return render(request, "organization/view_applicants.html", context)

@login_required
def org_approve_volunteer(request, app_id):
    if request.user.role != "ORGANIZATION":
        return redirect("login")

    app = get_object_or_404(Application, id=app_id)

    # Security: only owning org can approve
    if app.service.organization.user != request.user:
        return redirect("organization_dashboard")

    app.status = "SELECTED"
    app.save()

    return redirect(
        "org_view_applicants",
        service_id=app.service.id
    )


@login_required
def org_reject_volunteer(request, app_id):
    if request.user.role != "ORGANIZATION":
        return redirect("login")

    app = get_object_or_404(Application, id=app_id)

    if app.service.organization.user != request.user:
        return redirect("organization_dashboard")

    app.status = "REJECTED"
    app.save()

    return redirect(
        "org_view_applicants",
        service_id=app.service.id
    )


@require_POST
@login_required
def org_select_volunteers(request, service_id):
    if request.user.role != "ORGANIZATION":
        return redirect("login")

    org = Organization.objects.get(user=request.user)
    service = get_object_or_404(Service, id=service_id, organization=org)

    # Get selected application IDs from form
    selected_ids = request.POST.getlist("selected_volunteers")

    if not selected_ids:
        messages.warning(
            request,
            "Please select at least one volunteer."
        )
        return redirect("org_view_applicants", service_id=service.id)

    # All applications for this service
    applications = Application.objects.filter(service=service)

    for app in applications:
        if str(app.id) in selected_ids:
            app.status = "SELECTED"
        else:
            app.status = "REJECTED"
        app.save()

    # Mark service as ACTIVE (service is now running)
    service.status = "ACTIVE"
    service.save()

    messages.success(
        request,
        "Volunteers selected successfully. Service is now ACTIVE."
    )

    return redirect("organization_dashboard")


@login_required
def org_view_volunteer_profile(request, volunteer_id):
    if request.user.role != "ORGANIZATION":
        return redirect("login")

    volunteer = get_object_or_404(
        VolunteerProfile,
        id=volunteer_id
    )

    return render(
        request,
        "organization/volunteer_profile_view.html",
        {
            "volunteer": volunteer
        }
    )


@login_required
def volunteer_applications(request):
    if request.user.role != "VOLUNTEER":
        return redirect("login")

    profile = VolunteerProfile.objects.get(user=request.user)

    applications = Application.objects.filter(
        volunteer=profile
    ).select_related("service")

    return render(
        request,
        "volunteer/my_applications.html",
        {
            "applications": applications,
            "active_page": "applications"
        }
    )


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import VolunteerProfile


@login_required
def volunteer_profile(request):
    profile = VolunteerProfile.objects.get(user=request.user)

    if request.method == "POST":

        # Basic fields
        profile.full_name = request.POST.get("full_name")
        profile.phone = request.POST.get("phone")
        profile.year = request.POST.get("year")

        # Skills (hidden input)
        skills = request.POST.get("skills")
        if skills:
            profile.skills = skills

        # Save images if uploaded
        if request.FILES.get("photo"):
            profile.photo = request.FILES.get("photo")

        if request.FILES.get("cover_photo"):
            profile.cover_photo = request.FILES.get("cover_photo")

        profile.save()

        return redirect("/volunteer/profile/?updated=true")

    return render(request, "volunteer/profile.html", {"profile": profile})


@login_required
def admin_approved_organizations(request):
    if request.user.role != "ADMIN":
        return redirect("login")

    organizations = Organization.objects.filter(approved=True)

    return render(
        request,
        "admin_panel/approved_organizations.html",
        {
            "organizations": organizations,
            "active_page": "approved_orgs"
        }
    )


@require_POST
def mark_bulk_attendance(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == "POST":


        today = timezone.now().date()

        present_ids = request.POST.getlist("present_ids")

        # all selected volunteers for this service
        selected_apps = Application.objects.filter(
            service=service,
            status="SELECTED"
        )

        for app in selected_apps:
            is_present = str(app.id) in present_ids

            Attendance.objects.update_or_create(
                application=app,
                date=today,
                defaults={
                    "is_present": is_present
                }
            )

    return redirect("org_view_applicants", service_id=service.id)

@login_required
def volunteer_attendance(request):

    profile = VolunteerProfile.objects.get(user=request.user)

    # All selected applications
    applications = Application.objects.filter(
        volunteer=profile,
        status="SELECTED"
    )

    attendance_data = []

    for app in applications:

        service = app.service

        total_days = (
            (service.end_date - service.start_date).days + 1
            if service.start_date and service.end_date
            else 0
        )

        present_days = Attendance.objects.filter(
            application=app,
            is_present=True
        ).count()

        percentage = (
            round((present_days / total_days) * 100, 2)
            if total_days > 0 else 0
        )

        attendance_data.append({
            "service": service,
            "total_days": total_days,
            "present_days": present_days,
            "percentage": percentage,
        })

    return render(request, "volunteer/attendance.html", {
        "attendance_data": attendance_data
    })
