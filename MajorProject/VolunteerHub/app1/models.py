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
    student_id = models.CharField(max_length=20)
    department = models.CharField(max_length=20, default="", blank=True)

    year = models.CharField(max_length=20)
    skills = models.TextField(blank=True)

    photo = models.ImageField(upload_to="profiles/", blank=True, null=True)
    cover_photo = models.ImageField(upload_to="covers/", blank=True, null=True)

    rating = models.FloatField(default=0)
    attendance = models.IntegerField(default=0)

    @property
    def skill_list(self):
        return [s.strip() for s in self.skills.split(",")] if self.skills else []

    def __str__(self):
        return self.full_name


class Organization(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=100)
    verification_letter = models.FileField(
        upload_to="org_letters/",
        blank=True,
        null=True
    )
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
    start_date = models.DateField()
    end_date = models.DateField()

    required_volunteers = models.IntegerField()

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )

    organization_name = models.CharField(
        max_length=200,
        blank=True
    )  # ✅ NEW FIELD (typed manually)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    authorization_letter = models.FileField(
        upload_to="service_letters/",
        null=True,
        blank=True
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


class Attendance(models.Model):
    application = models.ForeignKey('Application', on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=False)

    class Meta:
        unique_together = ('application', 'date')
