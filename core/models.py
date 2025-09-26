from django.db import models
from django_auth_ldap.backend import populate_user


def populate_user_profile(sender, user=None, ldap_user=None, **kwargs):
    user.email = ldap_user._user_dn
    user.save()

populate_user.connect(populate_user_profile)
