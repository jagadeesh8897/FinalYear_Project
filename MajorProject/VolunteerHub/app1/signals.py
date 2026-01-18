from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, VolunteerProfile, Organization


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'VOLUNTEER':
            VolunteerProfile.objects.create(
                user=instance,
                phone='',
                year='',
                skills=''
            )

        elif instance.role == 'ORGANIZATION':
            Organization.objects.create(
                user=instance,
                organization_name=instance.username
            )
