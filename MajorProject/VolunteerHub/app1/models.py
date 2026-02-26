from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import models
from django.conf import settings

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
    GENDER_CHOICES = (
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    @property
    def skill_list(self):
        return [s.strip() for s in self.skills.split(",")] if self.skills else []

    def __str__(self):
        return self.full_name


class Organization(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    verification_letter = models.FileField(
        upload_to="org_letters/",
        blank=True,
        null=True
    )
    approved = models.BooleanField(default=False)
    cover_image = models.ImageField(upload_to="org_covers/", blank=True, null=True)
    logo = models.ImageField(upload_to="org_logos/", blank=True, null=True)
    tagline = models.CharField(max_length=200, blank=True)
    about = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    founded_year = models.IntegerField(blank=True, null=True)
    website = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    promo_video = models.URLField(blank=True)
    website = models.URLField(blank=True, null=True)

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

    max_volunteers = models.IntegerField()
    GENDER_PREF = (
    ("ANY", "Any"),
    ("MALE", "Male"),
    ("FEMALE", "Female"),
)

    required_gender = models.CharField(
        max_length=10,
        choices=GENDER_PREF,
        default="ANY"
    )

    required_year = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

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
        ("APPLIED", "Applied"),
        ("SELECTED", "Selected"),
        ("WAITLIST", "Waitlist"),
        ("REJECTED", "Rejected"),
       
        ("COMPLETED", "Completed"),
        ("CLOSED", "Closed"),
        ("ABSENT", "Absent"),
    ]


    volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    submission_text = models.TextField(blank=True)
    rating = models.IntegerField(default=0)
    review = models.TextField(blank=True)
    absence_requested = models.BooleanField(default=False)
    absence_approved = models.BooleanField(default=False)


class Attendance(models.Model):
    application = models.ForeignKey('Application', on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=False)

    class Meta:
        unique_together = ('application', 'date')

class OrganizationGallery(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="org_gallery/")


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Application)
def create_status_notification(sender, instance, created, **kwargs):

    # Only trigger if status changed (not on initial create)
    if not created:

        if instance.status == "SELECTED":
            Notification.objects.create(
                user=instance.volunteer.user,
                title=f"You have been selected for {instance.service.title}.",
                message=f"You have been selected for {instance.service.title}.",
                link="/volunteer/applications/"
            )

        elif instance.status == "REJECTED":
            Notification.objects.create(
                user=instance.volunteer.user,
                title="❌ Application Update",
                message=f"Your application for {instance.service.title} was not selected.",
                link="/volunteer/applications/"
            )

        elif instance.status == "WAITLIST":
            Notification.objects.create(
                user=instance.volunteer.user,
                title="⏳ Waitlisted",
                message=f"You have been placed on waitlist for {instance.service.title}.",
                link="/volunteer/applications/"
            )
@receiver(post_save, sender=Application)
def rating_notification(sender, instance, created, **kwargs):

    if instance.rating and instance.status == "COMPLETED":
        Notification.objects.create(
            user=instance.volunteer.user,
            title="⭐ You Received a Rating!",
            message=f"You were rated {instance.rating}/5 for {instance.service.title}.",
            link="/volunteer/attendance/"
        )

@receiver(post_save, sender=Attendance)
def attendance_notification(sender, instance, created, **kwargs):

    if created:
        if instance.is_present:
            msg = "You were marked Present"
        else:
            msg = "You were marked Absent"

        Notification.objects.create(
            user=instance.application.volunteer.user,
            title="📅 Attendance Updated",
            message=f"{msg} for {instance.application.service.title}.",
            link="/volunteer/attendance/"
        )

@receiver(post_save, sender=Service)
def service_completion_notification(sender, instance, created, **kwargs):

    if instance.status == "COMPLETED":

        selected_apps = Application.objects.filter(
            service=instance,
            status="COMPLETED"
        )

        for app in selected_apps:
            Notification.objects.create(
                user=app.volunteer.user,
                title="🎓 Service Completed",
                message=f"{instance.title} has been completed successfully.",
                link="/volunteer/attendance/"
            )