import datetime
import time

from PIL import Image
from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import reverse
from django.template.defaultfilters import slugify
from mutagen.mp3 import MP3

User = get_user_model()


class BaseModel(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, blank=True, null=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(BaseModel, self).save(*args, **kwargs)


class Music(BaseModel):
    author = models.ManyToManyField(to='Author', related_name='musics')
    genre = models.ManyToManyField(to='Genre', related_name='musics')
    music = models.FileField(upload_to='music/%Y/%m/%d')
    cover = models.ImageField(upload_to='cover/%Y/%m/%d')
    released_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    play_time = models.TextField(blank=True, null=True, editable=False)
    watched = models.PositiveIntegerField(default=0, blank=True, null=True, editable=False)
    album = models.ForeignKey(to='Album', on_delete=models.CASCADE, related_name='musics', blank=True, null=True)

    user_favorites = models.ManyToManyField(to=User, related_name='favorites', blank=True)

    def get_absolute_url(self):
        return reverse('track-detail', kwargs={'track_slug': self.slug})

    def __str__(self):
        return self.name[:50]

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super(Music, self).save(*args, **kwargs)
        self.album.update_type()
        if self.cover:
            cover = Image.open(self.cover.path)
            if cover.width > 300 or cover.height > 300:
                resize = (300, 300)
                cover.thumbnail(resize, Image.LANCZOS)
                cover.save(self.cover.path)
        if self.play_time is None:
            audio = MP3(self.music.path)
            self.play_time = time.strftime('%H:%M:%S', time.gmtime(audio.info.length))
            if self.released_date is None:
                self.released_date = datetime.date.today()
            self.save()

    def delete(self, *args, **kwargs):
        self.music.delete()
        self.cover.delete()
        super(Music, self).delete(*args, **kwargs)
        self.album.update_type()


class Author(BaseModel):

    def __str__(self):
        return self.name[:50]


class Genre(BaseModel):

    def __str__(self):
        return self.name[:50]


class Album(BaseModel):
    class ChooseType(models.TextChoices):
        single = ('Single', 'single')
        mini_album = ('Mini Album', 'mini_album')
        album = ('Album', 'album')

    type = models.CharField(choices=ChooseType, default=ChooseType.single, editable=False, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('album', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name[:50]

    def update_type(self):
        if self.musics.count() < 2:
            self.type = self.ChooseType.single
        elif 2 <= self.musics.count() < 7:
            self.type = self.ChooseType.mini_album
        else:
            self.type = self.ChooseType.album

        self.save()

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.type = self.ChooseType.single
        super(Album, self).save(*args, **kwargs)


class PlayList(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    cover = models.ImageField(upload_to='playlist/cover/', blank=True, null=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='playlists')
    music = models.ManyToManyField(to='Music', related_name='playlist', blank=True)

    def get_absolute_url(self):
        return reverse('playlist_detail', kwargs={'pk': self.pk})

    def get_tracks_count(self):
        return self.music.count()

    def _str_to_time(self, playtime, pattern='%H:%M:%S'):
        return time.mktime(time.strptime(playtime, pattern))

    def _time_to_str(self, seconds, pattern='%H:%M:%S'):
        return time.strftime(pattern, time.gmtime(seconds))

    def get_total_playtime(self):
        count = None
        for music in self.music.all():
            if count is None:
                count = self._str_to_time(music.play_time)
                continue
            count += self._str_to_time(music.play_time)
        return self._time_to_str(count)

    def __str__(self):
        return self.name[:50]

    def save(self, *args, **kwargs):
        super(PlayList, self).save(*args, **kwargs)
        if self.cover is None or not self.cover:
            self.cover = self.music.first().cover
            self.save(*args, **kwargs)

        if self.name is None or not self.name:
            self.name = self.music.first().name
            self.save(*args, **kwargs)
