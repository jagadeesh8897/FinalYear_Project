from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import VolunteerProfile, Application, Service
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User


@csrf_exempt
def login_page(request):
    return render(request, 'login.html')

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import VolunteerProfile, Organization
import json

User = get_user_model()

@csrf_exempt
def login_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    email = data.get("username")
    password = data.get("password")
    role = data.get("role")

    # 1️⃣ Email exists check
    user = User.objects.filter(email=email).first()
    if not user:
        return JsonResponse({
            "status": "error",
            "message": "Email not registered"
        })

    # 2️⃣ ROLE VALIDATION
    if role == "VOLUNTEER":
        if not email.endswith("@srit.ac.in"):
            return JsonResponse({
                "status": "error",
                "message": "Volunteer email must end with @srit.ac.in"
            })

        if user.role != "VOLUNTEER":
            return JsonResponse({
                "status": "error",
                "message": "Not a volunteer account"
            })

        if not VolunteerProfile.objects.filter(user=user).exists():
            return JsonResponse({
                "status": "error",
                "message": "Volunteer profile not found"
            })

    elif role == "ORGANIZATION":
        if not email.endswith("@gmail.com"):
            return JsonResponse({
                "status": "error",
                "message": "Organization email must end with @gmail.com"
            })

        if user.role != "ORGANIZATION":
            return JsonResponse({
                "status": "error",
                "message": "Not an organization account"
            })

        org = Organization.objects.filter(user=user).first()
        if not org or not org.approved:
            return JsonResponse({
                "status": "error",
                "message": "Organization not approved by admin"
            })

    elif role == "ADMIN":
        if user.role != "ADMIN":
            return JsonResponse({
                "status": "error",
                "message": "Not an admin account"
            })

    else:
        return JsonResponse({
            "status": "error",
            "message": "Invalid role selected"
        })

    # 3️⃣ AUTHENTICATION
    user = authenticate(
        request,
        username=user.username,  # Django auth uses username
        password=password
    )

    if not user:
        return JsonResponse({
            "status": "error",
            "message": "Invalid password"
        })

    # 4️⃣ LOGIN
    login(request, user)

    return JsonResponse({
        "status": "success",
        "role": user.role
    })



@login_required

def volunteer_dashboard(request):
    if request.user.role != 'VOLUNTEER':
        return redirect('login')

    profile = VolunteerProfile.objects.get(user=request.user)

    assigned = Application.objects.filter(
        volunteer=profile, status='SELECTED'
    ).count()

    completed = Application.objects.filter(
        volunteer=profile, status='COMPLETED'
    ).count()

    attendance = 0
    if profile.completed_services > 0:
        attendance = int((completed / profile.completed_services) * 100)

    return render(request, 'volunteer/dashboard.html', {
        'assigned': assigned,
        'completed': completed,
        'attendance': attendance,
        'user': request.user,
        'profile': profile,
    })




@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    return JsonResponse({
        'total_volunteers': VolunteerProfile.objects.count(),
        'organizations': Organization.objects.count(),
        'active_works': Service.objects.filter(status='APPROVED').count(),
        'completed_works': Service.objects.filter(status='COMPLETED').count(),
        'pending_approvals': Organization.objects.filter(approved=False).count()
    })

@login_required
def organization_dashboard(request):
    if request.user.role != 'ORGANIZATION':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    org = Organization.objects.get(user=request.user)

    return JsonResponse({
        'total_works': Service.objects.filter(organization=org).count(),
        'active_works': Service.objects.filter(
            organization=org, status='APPROVED'
        ).count(),
        'completed_works': Service.objects.filter(
            organization=org, status='COMPLETED'
        ).count(),
    })

from django.views.decorators.http import require_POST
from datetime import datetime


@require_POST
def create_service(request):
    user = request.user

    if not user.is_authenticated or user.role != 'ORGANIZATION':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    org = Organization.objects.get(user=user)

    data = json.loads(request.body)

    service = Service.objects.create(
        title=data['title'],
        description=data['description'],
        location=data['location'],
        date=datetime.strptime(data['date'], "%Y-%m-%d"),
        required_volunteers=data['required_volunteers'],
        organization=org
    )

    return JsonResponse({
        'message': 'Service created',
        'service_id': service.id
    })

def list_services(request):
    services = Service.objects.filter(status='APPROVED')

    return JsonResponse({
        'services': list(services.values())
    })

@require_POST
def apply_service(request, service_id):
    user = request.user

    if not user.is_authenticated or user.role != 'VOLUNTEER':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    profile = VolunteerProfile.objects.get(user=user)
    service = Service.objects.get(id=service_id)

    Application.objects.create(
        volunteer=profile,
        service=service
    )

    return JsonResponse({'message': 'Applied successfully'})

@require_POST
def assign_volunteers(request, service_id):
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    service = Service.objects.get(id=service_id)

    applications = Application.objects.filter(
        service=service,
        status='APPLIED'
    )

    scored = []
    for app in applications:
        score = calculate_score(app.volunteer, service)
        scored.append((score, app))

    scored.sort(reverse=True, key=lambda x: x[0])

    selected = scored[:service.required_volunteers]

    for _, app in selected:
        app.status = 'SELECTED'
        app.save()

    service.status = 'APPROVED'
    service.save()

    return JsonResponse({'message': 'AI-based selection completed'})


from django.shortcuts import render

def home(request):
    return render(request, 'home.html')



@login_required
def volunteer_dashboard_page(request):
    profile = VolunteerProfile.objects.get(user=request.user)

    assigned = Application.objects.filter(
        volunteer=profile, status='SELECTED'
    ).count()

    completed = Application.objects.filter(
        volunteer=profile, status='COMPLETED'
    ).count()

    return render(request, 'volunteer/dashboard.html', {
        'assigned': assigned,
        'completed': completed,
        'attendance': profile.attendance
    })

@login_required
def organization_dashboard_page(request):
    org = Organization.objects.get(user=request.user)
    services = Service.objects.filter(organization=org)

    return render(request, 'organization/dashboard.html', {
        'services': services
    })
@login_required
def admin_dashboard_page(request):
    return render(request, 'admin_panel/dashboard.html', {
        'volunteers': VolunteerProfile.objects.count(),
        'organizations': Organization.objects.count(),
        'active': Service.objects.filter(status='APPROVED').count(),
        'completed': Service.objects.filter(status='COMPLETED').count()
    })

def calculate_score(volunteer, service):
    score = 0

    # Attendance (40%)
    score += volunteer.attendance * 0.4

    # Skill match (40%)
    service_skills = service.description.lower()
    volunteer_skills = volunteer.skills.lower()

    match = sum(
        1 for word in volunteer_skills.split(',')
        if word.strip() in service_skills
    )
    score += match * 10 * 0.4

    # Rating (20%)
    score += volunteer.rating * 0.2

    return score

@require_POST
def submit_work(request, application_id):
    if not request.user.is_authenticated or request.user.role != 'VOLUNTEER':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    data = json.loads(request.body)
    application = Application.objects.get(id=application_id)

    application.submission_text = data.get('submission')
    application.status = 'COMPLETED'
    application.save()

    volunteer = application.volunteer
    volunteer.completed_services += 1
    volunteer.save()

    return JsonResponse({'message': 'Work submitted successfully'})
@require_POST
def rate_volunteer(request, application_id):
    if request.user.role != 'ORGANIZATION':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    data = json.loads(request.body)
    application = Application.objects.get(id=application_id)

    application.rating = data.get('rating')
    application.review = data.get('review')
    application.save()

    volunteer = application.volunteer
    all_ratings = Application.objects.filter(
        volunteer=volunteer, rating__gt=0
    ).values_list('rating', flat=True)

    volunteer.rating = sum(all_ratings) / len(all_ratings)
    volunteer.save()

    return JsonResponse({'message': 'Volunteer rated successfully'})

import re

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return "Password must contain at least one number"

    if not re.search(r"[@$!%*?&]", password):
        return "Password must contain at least one special character (@$!%*?&)"

    return None  # ✅ Valid password



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import VolunteerProfile, Organization

User = get_user_model()


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, VolunteerProfile, Organization


from django.db import transaction

def register_view(request):
    if request.method == "POST":
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

        # 🔴 ALL VALIDATIONS FIRST

        # Domain check
        if role == "VOLUNTEER" :
            if not email.endswith("@srit.ac.in"):
                messages.warning(request, "Volunteer email must end with @srit.ac.in")
                return render(request, "register.html", {
                    "form_data": request.POST,
                    "selected_role": role
                })
            # Password match check
            if password != rpassword:
                messages.warning(request, "Passwords do not match")
                return render(request, "register.html", {
                    "form_data": request.POST,
                    "selected_role": role,
                })

            # 🔐 Detailed password validation
            password_error = validate_password(password)
            if password_error:
                messages.warning(request, password_error)
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

        # Password match
        if password != rpassword:
            messages.warning(request, "Passwords do not match")
            return render(request, "register.html", {
                "form_data": request.POST,
                "selected_role": role
            })

        # Volunteer email unique
        if role == "VOLUNTEER" :
            if User.objects.filter(email=email).exists():
                messages.warning(request, "Volunteer already registered with this email")
                return render(request, "register.html", {
                    "form_data": request.POST,
                    "selected_role": role
            })
            if VolunteerProfile.objects.filter(student_id=student_id).exists():
                messages.warning(request, "Student ID already registered")
                return render(request, "register.html", {
                    "form_data": request.POST,
                    "selected_role": role
            })

        # Organization email unique (User-level)
        if role == "ORGANIZATION" and User.objects.filter(username=email).exists():
            messages.warning(request, "Organization already registered with this email")
            return render(request, "register.html", {
                "form_data": request.POST,
                "selected_role": role
            })

        # 🔒 ATOMIC BLOCK (CRITICAL)
        with transaction.atomic():

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                role=role,
            )
            user.save();
            if role == "VOLUNTEER":
                vprofile,created =VolunteerProfile.objects.update_or_create(
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
                vprofile.save()
                messages.success(request, "Volunteer registered successfully")

            elif role == "ORGANIZATION":
                user.is_active = False
                user.save()

                Organization.objects.get_or_create(
                    user=user,
                    defaults={
                        "organization_name": full_name,
                        "approved": False
                    }
                )
                messages.success(
                    request,
                    "Organization registered. Await admin approval."
                )

        return redirect("login")

    return render(request, "register.html")
