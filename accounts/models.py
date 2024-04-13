from PIL import Image
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/%Y/%m/%d', default='avatar/custom_avatar.jpg', null=True,
                               blank=True)

    def save(self, *args, **kwargs):
        super(CustomUser, self).save(*args, **kwargs)

        avatar = Image.open(self.avatar.path)

        if avatar.width > 300 or avatar.height > 300:
            resize = (300, 300)
            avatar.thumbnail(resize, Image.LANCZOS)

            avatar.save(self.avatar.path)
