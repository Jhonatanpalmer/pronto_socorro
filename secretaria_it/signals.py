from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group

from .models import GroupAccess


@receiver(post_save, sender=Group)
def create_group_access(sender, instance: Group, created: bool, **kwargs):
    if created:
        GroupAccess.objects.get_or_create(group=instance)


def ensure_group_access_for_all():  # pragma: no cover
    """Utility to ensure every existing group has a GroupAccess row."""
    for g in Group.objects.all():
        GroupAccess.objects.get_or_create(group=g)
