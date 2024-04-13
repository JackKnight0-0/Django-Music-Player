from django.contrib.auth import get_user_model
from django.db import models

from player.models import Music

User = get_user_model()


class Review(models.Model):
    """
    The model for review,
    having relationship with user (one-to-many), music (one-to-many), and reply model (one-to-many).
    """
    user = models.ForeignKey(to=User, related_name='reviews', on_delete=models.CASCADE)
    music = models.ForeignKey(to=Music, related_name='reviews', on_delete=models.CASCADE)
    text = models.TextField(max_length=250)
    user_liked = models.ManyToManyField(to=User, related_name='liked_reviews', blank=True)
    user_disliked = models.ManyToManyField(to=User, related_name='disliked_reviews', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def liked_count(self):
        return self.user_liked.count()

    def disliked_count(self):
        return self.user_disliked.count()

    def __str__(self):
        return str(self.pk) + ' ' + self.text[:50]

    class Meta:
        ordering = ['-created_at', ]


class Reply(models.Model):
    """
    The model for reply,
     having a relationship with user (one-to-many), review model (one-to-many).
    """
    user = models.ForeignKey(to=User, related_name='replies', on_delete=models.CASCADE)
    text = models.TextField(max_length=250)
    review = models.ForeignKey(to='Review', related_name='replies', on_delete=models.CASCADE)
    user_liked = models.ManyToManyField(to=User, related_name='liked_replies', blank=True)
    user_disliked = models.ManyToManyField(to=User, related_name='disliked_replies', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def liked_count(self):
        return self.user_liked.count()

    def disliked_count(self):
        return self.user_disliked.count()

    class Meta:
        ordering = ['-created_at', ]

    def __str__(self):
        return str(self.pk) + ' ' + self.text[:50]
