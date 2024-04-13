from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from player.models import Music, Album


@receiver(post_save, sender=Music)
def create_album(sender, instance, created, *args, **kwargs):
    if created:
        if instance.album is None:
            album = Album.objects.create(name=instance.name)
            album.save()
            instance.album = album
            instance.save()
