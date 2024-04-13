import random

from django.db.models import Window, Q, F
from django.db.models.functions import Lag, Lead
from django.template.defaultfilters import slugify

from player.models import Music


class MetaDataAudioMixin(object):
    by_field = 'id'

    def get_query(self):
        """
        Query for tracks.
        """
        return Music.objects.all()

    def get_query_with_annotate(self):
        """
        Add to query extra field next and prev track, by using window function.
        """
        query = self.get_query()
        return query.annotate(
            next_track=Window(expression=Lead('id'), order_by=self.by_field),
            prev_track=Window(expression=Lag('id'), order_by=self.by_field))

    def is_random(self):
        return self.request.data.get('random', False)

    def get_last_track(self):
        """
        Getting the last track, if not exists, returns the first one from a query.
        """
        slug = self.request.data.get('last_track', None)
        last_track = None
        if slug is not None:
            last_track = self.music_query.filter(
                Q(slug=slugify(slug)) | Q(id=F('next_track')) | Q(id=F('prev_track'))).first()
        if not last_track:
            return self.music_query.first()
        return last_track

    def get_previous(self):
        """
        Return previous track if exists.
        """
        prev_track = None
        if self.last_track.prev_track is not None:
            prev_track = Music.objects.filter(pk=self.last_track.prev_track).first()
        if prev_track is None:
            prev_track = self.prev_none
        return prev_track

    def get_next(self):
        """
        Return next track if exists.
        """
        next_track = None
        if self.last_track.next_track is not None:
            next_track = Music.objects.filter(pk=self.last_track.next_track).first()
        if next_track is None:
            next_track = self.next_none
        return next_track

    def get_audio(self):
        self.music_query = self.get_query_with_annotate()
        self.next_none = self.music_query.last()
        self.prev_none = self.music_query.first()
        if '-' in self.by_field:
            self.prev_none, self.next_none = self.next_none, self.prev_none
        self.last_track = self.get_last_track()

        is_random = self.is_random()
        has_previous = self.request.data.get('previous', False)
        has_next = self.request.data.get('next', False)

        if is_random:
            return random.choice(self.music_query.all().exclude(pk=self.last_track.pk))
        elif has_previous:
            return self.get_previous()
        elif has_next:
            return self.get_next()
        else:
            return self.music_query.first()
