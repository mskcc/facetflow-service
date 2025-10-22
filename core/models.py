from enum import IntEnum
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django_auth_ldap.backend import populate_user
from django.contrib.auth import get_user_model


User = get_user_model()


class AccessLevel(IntEnum):
    VIEW = 0
    PERSONAL = 1
    FULL = 2


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_level = models.IntegerField(
        choices=[(access_level.value, access_level.name) for access_level in AccessLevel],
        default=AccessLevel.PERSONAL
    )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


def populate_user_profile(sender, user=None, ldap_user=None, **kwargs):
    user.email = ldap_user._user_dn
    user.save()

populate_user.connect(populate_user_profile)
