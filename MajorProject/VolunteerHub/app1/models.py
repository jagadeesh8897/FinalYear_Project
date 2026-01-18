from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('VOLUNTEER', 'Volunteer'),
        ('ORGANIZATION', 'Organization'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} - {self.role}"


class VolunteerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    year = models.CharField(max_length=20)
    student_id = models.CharField(max_length=20, unique=True,null=True,blank=True)  # ✅ NEW
    department = models.CharField(max_length=50, null=True,blank=True)
    skills = models.TextField()

    attendance = models.IntegerField(default=0)
    completed_services = models.IntegerField(default=0)
    rating = models.FloatField(default=0)

    def __str__(self):
        return self.full_name



class Organization(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=100)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.organization_name

class Service(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('COMPLETED', 'Completed'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    date = models.DateField()
    required_volunteers = models.IntegerField()

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Application(models.Model):
    STATUS_CHOICES = [
        ('APPLIED', 'Applied'),
        ('SELECTED', 'Selected'),
        ('COMPLETED', 'Completed'),
    ]

    volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    submission_text = models.TextField(blank=True)
    rating = models.IntegerField(default=0)
    review = models.TextField(blank=True)


