from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q, Prefetch
from django.http import StreamingHttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import reverse, redirect
from django.views import generic
from django.views.generic.detail import SingleObjectTemplateResponseMixin, SingleObjectMixin
from rest_framework import generics as drf_generic
from rest_framework.response import Response

import player.models as model
import reviews.models as reviews_model
from player.mixin import MetaDataAudioMixin
from player.serializers import PlayListSerializer, TrackMetaDataSerializer, TrackSuggestionSerializer

User = get_user_model()


class TrackPreviewView(generic.DetailView):
    """
    View for snowing the detail page of current track.
    """
    model = model.Music
    template_name = 'player/track_preview.html'
    context_object_name = 'track'
    slug_url_kwarg = 'track_slug'

    def get_object(self, queryset=None):
        """
        Optimization the query.
        """
        users = User.objects.all()
        try:
            replies = reviews_model.Reply.objects.select_related('user').only('user__username', 'user__avatar', 'text',
                                                                              'review_id').prefetch_related(
                Prefetch('user_liked', queryset=users.only('id')),
                Prefetch('user_disliked', queryset=users.only('id')))
            prefetch_reviews = reviews_model.Review.objects.select_related('user').only('user_id', 'music_id',
                                                                                        'text').prefetch_related(
                Prefetch('replies', queryset=replies.all()), Prefetch('user_liked', queryset=users.only('id')),
                Prefetch('user_disliked', queryset=users.only('id')))
            music = model.Music.objects.prefetch_related(
                Prefetch('reviews', queryset=prefetch_reviews.all()[:10], to_attr='reviews_list')
            ).get(slug=self.kwargs.get('track_slug', None))
        except (model.Music.DoesNotExist, model.Music.MultipleObjectsReturned):
            raise Http404
        return music

    def get_context_data(self, **kwargs):
        context = super(TrackPreviewView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:  # check if user is logged, if so, add to context data for
            # optimization query
            music = context['track']
            context['user_playlists'] = self.request.user.playlists.all()
            context['user_reviews'] = self.request.user.reviews.filter(music=music)
        return context


class SteamAudioAPI(drf_generic.GenericAPIView):
    """
    The View returns audio by chunks
    """

    def get_audio(self):
        return get_object_or_404(model.Music, slug=self.kwargs.get('track_slug'))

    def iter_audio(self):
        """
        The function is yield, return the audio by chunk.
        """
        chunk_size = 1048576  # 1 MB
        if hasattr(settings, 'AUDIO_CHUNK_SIZE'):
            chunk_size = settings.AUDIO_CHUNK_SIZE
        audio = self.get_audio()
        audio_path = audio.music.path
        audio.watched += 1
        audio.save()

        with open(audio_path, 'rb') as audio_bytes:
            while True:
                chunk = audio_bytes.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def get(self, request, *args, **kwargs):
        response = StreamingHttpResponse(self.iter_audio(), content_type='audio/mpeg')
        response['Cache-control'] = 'no-cache'
        return response


class MetaDataAudioAPIView(drf_generic.GenericAPIView):
    """
    The view is return audio data.
    """

    def get_object(self):
        try:
            return model.Music.objects.prefetch_related('author').get(slug=self.kwargs.get('track_slug'))
        except model.Music.DoesNotExist:
            raise Http404

    def get_audio(self):
        return TrackMetaDataSerializer(self.get_object()).data

    def get(self, request, *args, **kwargs):
        return Response({'data': self.get_audio()})


class MetaDataGlobalAudio(MetaDataAudioMixin, drf_generic.GenericAPIView):
    """
    The view is using mixin to parse next and prev audio in the player.
    """

    def post(self, request, *args, **kwargs):
        return Response({'redirect': self.get_audio().get_absolute_url()})


class MetaDataAudioFromPlaylistAPIView(LoginRequiredMixin, MetaDataAudioMixin, drf_generic.GenericAPIView):
    """
    The view is using mixin to parse next and prev audio in the playlist
    """
    by_field = '-id'  # change order by field in mixin query

    def get_query(self):
        return get_object_or_404(model.PlayList, pk=self.kwargs.get('playlist')).music.all()

    def get_track_data(self):
        track_serializer = TrackMetaDataSerializer(self.get_audio())
        return track_serializer.data

    def post(self, request, *args, **kwargs):
        return Response({'data': self.get_track_data()})


class AddRemoveFavorite(LoginRequiredMixin, drf_generic.GenericAPIView):
    """
    The view is adding or removing favorite song from user favorites, return 0 as a remove and 1 as an add
    """

    def get_object(self):
        slug = self.request.data.get('track-slug')
        return get_object_or_404(model.Music, slug=slug)

    def add_remove_fav(self):
        user = self.request.user
        track = self.get_object()
        response = None
        if track in user.favorites.all():
            user.favorites.remove(track)
            response = 0
        else:
            user.favorites.add(track)
            response = 1

        return response

    def put(self, request, *args, **kwargs):
        response = self.add_remove_fav()
        return Response({'action': response})


class HomePageView(generic.ListView):
    """
    The view is rendering the main page with audios.
    """
    template_name = 'home.html'
    model = model.Music
    context_object_name = 'musics'
    paginate_by = 5

    def get_context_data(self, *args, **kwargs):
        context = super(HomePageView, self).get_context_data(*args, **kwargs)
        if self.request.user.is_authenticated:
            context['user_playlists'] = self.request.user.playlists.all()
            context['user_favorites'] = self.request.user.favorites.all()
        return context

    def get_queryset(self):
        tracks = model.Music.objects.prefetch_related(
            Prefetch('author', queryset=model.Author.objects.all(), to_attr='author_names')
        ).all()
        return tracks


class UserFavoritesMusicView(LoginRequiredMixin, generic.ListView):
    """
    The view is rendering favorite music of the current user.
    """
    template_name = 'player/favorites_list.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        favorites_music = model.Music.objects.filter(user_favorites=self.request.user).prefetch_related('author').only(
            'id', 'slug', 'name', 'cover', 'author')
        return favorites_music


class CreatePlayListAPIView(LoginRequiredMixin, drf_generic.GenericAPIView):
    """
    The view is creating the playlist by song data
    """

    def get_music(self):
        return get_object_or_404(model.Music, slug=self.kwargs.get('track_slug'))

    def create_playlist(self):
        """
        The function is creating playlist by taken the name and cover from music.
        """
        music = self.get_music()
        playlist = model.PlayList.objects.create(
            name=music.name,
            cover=music.cover,
            user=self.request.user,
        )
        playlist.music.add(music)
        return playlist

    def post(self, request, *args, **kwargs):
        playlist = self.create_playlist()
        data_playlist = PlayListSerializer(playlist)
        return Response({'playlist': data_playlist.data})


class AddToPlayListAPIView(LoginRequiredMixin, drf_generic.GenericAPIView):
    """
    The view is added to playlist audio.
    """

    def get_music(self):
        return get_object_or_404(model.Music, slug=self.kwargs.get('track_slug'))

    def get_playlist(self):
        return get_object_or_404(model.PlayList, pk=self.kwargs.get('playlist_pk'), user=self.request.user)

    def add_music_to_playlist(self):
        playlist = self.get_playlist()
        music = self.get_music()
        playlist.music.add(music)

    def post(self, request, *args, **kwargs):
        self.add_music_to_playlist()
        return Response({'answer': 'ok'})


class RemoveMusicFromPlayListAPIView(LoginRequiredMixin, UserPassesTestMixin, drf_generic.GenericAPIView):
    """
    The view is removing audio from playlist if music in playlist.
    """

    def get_music(self):
        return get_object_or_404(model.Music, slug=self.kwargs.get('track_slug'))

    def get_playlist(self):
        return get_object_or_404(model.PlayList, pk=self.kwargs.get('playlist_pk'), user=self.request.user)

    def remove_music_playlist(self):
        music = self.get_music()
        if music not in self.playlist.music.all():
            raise Http404
        self.playlist.music.remove(music)

    def delete(self, request, *args, **kwargs):
        self.remove_music_playlist()
        return Response({'status': 'ok'})

    def test_func(self):
        self.playlist = self.get_playlist()
        return self.playlist.user == self.request.user


class PlaylistView(LoginRequiredMixin, SingleObjectTemplateResponseMixin, SingleObjectMixin, generic.View):
    """
    The view is rendering page of user playlists.
    """
    template_name = 'player/playlist.html'

    def get_user_playlists(self):
        return self.request.user.playlists.all()

    def get_context_data(self, **kwargs):
        context = dict()
        context['playlists'] = self.get_user_playlists()
        return context

    def get(self, request, *args, **kwargs):
        return self.render_to_response(context=self.get_context_data())


class PlayListDetail(LoginRequiredMixin, UserPassesTestMixin, generic.DetailView):
    """
    The view is rendering detail user playlist.
    """
    template_name = 'player/playlist_detail.html'
    model = model.PlayList
    context_object_name = 'playlist'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        try:
            self.obj = model.PlayList.objects.prefetch_related(Prefetch('music'), Prefetch('music__album')).get(
                pk=self.kwargs.get('pk', None))
        except model.PlayList.DoesNotExist:
            raise Http404
        return self.obj

    def get(self, request, *args, **kwargs):
        self.object = self.obj
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def test_func(self):
        if self.get_object() not in self.request.user.playlists.all():
            return False
        return True


class DeletePlayListView(LoginRequiredMixin, UserPassesTestMixin, drf_generic.GenericAPIView):
    """
    The view is deleting playlist from user playlists.
    """

    def get_playlist(self):
        return get_object_or_404(model.PlayList, pk=self.kwargs.get('pk'))

    def delete(self, request, *args, **kwargs):
        playlist = self.get_playlist()
        playlist.delete()
        return Response({'status': 'ok'})

    def test_func(self):
        return self.get_playlist().user == self.request.user


class UpdatePlatListView(LoginRequiredMixin, UserPassesTestMixin, drf_generic.GenericAPIView):
    """
    The view is updating playlist data.
    """

    def get_playlist(self):
        return get_object_or_404(model.PlayList, pk=self.kwargs.get('playlist_pk'))

    def update(self):
        data = {
            'name': self.request.POST.get('name', None),
            'cover': self.request.FILES.get('cover', self.playlist.cover)  # if cover not given, use the current one.
        }
        playlist_serializer = PlayListSerializer(instance=self.playlist, data=data)
        playlist_serializer.is_valid(raise_exception=True)
        playlist_serializer.save()
        return playlist_serializer.data

    def put(self, request, *args, **kwargs):
        playlist = self.update()
        return Response({'playlist': playlist})

    def test_func(self):
        self.playlist = self.get_playlist()
        return self.playlist.user == self.request.user


class AlbumMusicListView(generic.DetailView):
    """
    The view to render album page.
    """
    model = model.Album
    template_name = 'player/album.html'
    context_object_name = 'album'
    slug_url_kwarg = 'slug'


class AlbumMetaDataAudioAPIView(MetaDataAudioMixin, drf_generic.GenericAPIView):
    """
    The view returns next or prev audio from mixin.
    """
    by_field = '-id'

    def get_query(self):
        return get_object_or_404(model.Album, slug=self.kwargs.get('slug')).musics.all()

    def post(self, request, *args, **kwargs):
        return Response({'data': TrackMetaDataSerializer(self.get_audio()).data})


class GetAudioSuggestionAPIView(drf_generic.GenericAPIView):
    """
    The view is return suggestion for search audio.
    """

    def get_audio(self):
        query = self.request.GET.get('q')
        tracks = model.Music.objects.filter(
            Q(name__icontains=query) | Q(name__in=query.split()) | Q(genre__name__icontains=query) | Q(
                genre__name__in=query.split()) | Q(album__name__icontains=query) | Q(album__name__in=query.split()))[:5]
        return tracks

    def get(self, request, *args, **kwargs):
        return Response({'data': TrackSuggestionSerializer(self.get_audio(), many=True).data})


class FilteredListAudioView(generic.ListView):
    """
    The view is rendering page for filtered data.
    """
    model = model.Music
    template_name = 'home.html'
    context_object_name = 'musics'
    paginate_by = 5

    def get_queryset(self):
        query = self.request.GET.get('q')
        tracks = model.Music.objects.filter(
            Q(name__in=query.split()) | Q(name__icontains=query) | Q(genre__name__icontains=query) | Q(
                genre__name__in=query.split()) | Q(album__name__icontains=query) | Q(
                album__name__in=query.split())).prefetch_related(
            Prefetch('author', queryset=model.Author.objects.all(), to_attr='author_names')
        ).all()
        return tracks

    def get_context_data(self, *args, **kwargs):
        context = super(FilteredListAudioView, self).get_context_data(*args, **kwargs)
        if self.request.user.is_authenticated:
            context['user_playlists'] = self.request.user.playlists.all()
            context['user_favorites'] = self.request.user.favorites.all()
        return context

    def get(self, request, *args, **kwargs):
        """
        To use filtered and pagination, we retrieve the query from the old query if it exists, and the current page,
        and then redirect the user to the correct url.
        """
        if (self.request.GET.get('q', None)) is None:
            meta = self.request.META
            page = self.request.GET.get('page')
            http_referer = meta.get('HTTP_REFERER', None)
            if http_referer is not None and 'q=' in http_referer:
                start = http_referer.find('q=')
                end = http_referer.find('&')
                if end == -1:
                    end = len(http_referer)
                return redirect(
                    str(reverse('search_track')) + '?' + http_referer[start:end] + '&page=' + str(page))
        return super(FilteredListAudioView, self).get(request=request, *args, **kwargs)
