from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:

        # 👑 Admin
        if instance.is_superuser:
            role = "admin"

        # 👨‍🏫 Teacher
        elif instance.is_staff:
            role = "teacher"

        # 👨‍🎓 Student
        else:
            role = "student"

        UserProfile.objects.get_or_create(user=instance, defaults={"role": role})
