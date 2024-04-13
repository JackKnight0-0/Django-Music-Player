import os
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import StreamingHttpResponse
from django.shortcuts import reverse
from django.template.defaultfilters import slugify
from rest_framework.test import APIClient

import player.models as player_models
from player.serializers import TrackMetaDataSerializer, PlayListSerializer
from reviews.test_mixin import TestMixin

User = get_user_model()


class TestDate(TestMixin):
    @classmethod
    def setUp(cls):
        cls.user = User.objects.create(username='TestUser', password='testpass123', email='testemail@gmail.com')
        cls.user1 = User.objects.create(username='TestUser1', password='testpass123', email='testemail1@gmail.com')
        cls.author = player_models.Author.objects.create(name='SomeAuthor')
        cls.genre = player_models.Genre.objects.create(name='SomeGenre')
        cls.music = player_models.Music.objects.create(
            name='some music',
            music='music/test_music.mp3',
            cover='cover/test_cover.png',
            play_time='00:03:00'
        )
        cls.music.author.add(cls.author)
        cls.music.genre.add(cls.genre)
        cls.playlist = player_models.PlayList.objects.create(
            user=cls.user,
            name=cls.music.name,
            cover=cls.music.cover
        )
        cls.extra_track = player_models.Music.objects.create(
            name='some music 1',
            music='music/test_music.mp3',
            cover='cover/test_cover.png',
            play_time='00:03:00'
        )
        cls.extra_track.author.add(cls.author)
        cls.extra_track.genre.add(cls.genre)
        cls.playlist.music.add(cls.music)
        cls.album = cls.music.album
        cls.client_factory = APIClient()

    def base_model_test(self, model, created_obj, obj, count=1):
        self.assertEqual(model.objects.count(), count)
        self.assertEqual(created_obj, obj)
        self.assertEqual(created_obj.name, obj.name)
        if hasattr(created_obj, 'slug'):
            self.assertEqual(created_obj.slug, slugify(obj.name))
        self.assertEqual(created_obj.__str__(), obj.name[:50])


class ModelPlayerTest(TestDate):
    def test_music_model(self):

        new_obj = player_models.Music.objects.first()
        self.base_model_test(player_models.Music, new_obj, self.extra_track, count=2)

        self.assertEqual(new_obj.get_absolute_url(),
                         reverse('track-detail', kwargs={'track_slug': self.extra_track.slug}))

        image_800_x_800 = SimpleUploadedFile(name='png800x800.png',
                                             content=open('media/cover/png800x800.png', 'rb').read(),
                                             content_type='image/png')
        test_music = SimpleUploadedFile(name='test_music.mp3', content=open('media/music/test_music.mp3', 'rb').read(),
                                        content_type='audio/mpeg')
        music_800_x_800 = player_models.Music.objects.create(
            name='some music800x8000',
            cover=image_800_x_800,
            music=test_music,
        )

        music_800_x_800.author.add(self.author)
        music_800_x_800.genre.add(self.genre)

        image_path = music_800_x_800.cover.path
        music_path = music_800_x_800.music.path

        self.assertEqual(music_800_x_800.cover.height, 300)
        self.assertEqual(music_800_x_800.cover.width, 300)

        music_800_x_800.delete()
        self.assertEqual(os.path.exists(image_path), False)
        self.assertEqual(os.path.exists(music_path), False)

    def test_author_model(self):
        self.base_model_test(player_models.Author, player_models.Author.objects.first(), self.author)

    def test_genre_model(self):
        self.base_model_test(player_models.Genre, player_models.Genre.objects.first(), self.genre)

    def test_album_model(self):
        created_album = player_models.Album.objects.first()

        self.base_model_test(player_models.Album, created_album, self.album, count=2)

        self.assertEqual(created_album.get_absolute_url(), reverse('album', kwargs={'slug': created_album.slug}))
        self.assertEqual(created_album.type, player_models.Album.ChooseType.single)
        music = []
        for i in range(7):
            copy_music = player_models.Music.objects.first()
            copy_music.pk = None
            copy_music.name = 'music' + str(i)
            copy_music.save()
            music_count = copy_music.album.musics.count()
            if 2 <= music_count < 7:
                self.assertEqual(copy_music.album.type, player_models.Album.ChooseType.mini_album)
            elif i >= 6:
                self.assertEqual(copy_music.album.type, player_models.Album.ChooseType.album)
            music.append(copy_music.pk)
        new_musics = player_models.Music.objects.filter(pk__in=music)
        new_musics.delete()

    def test_playlist_model(self):
        extra_music = player_models.Music.objects.create(
            name='extra music',
            cover='cover/test_cover.png',
            music='music/test_music.mp3',
            play_time='00:03:00'
        )
        self.base_model_test(player_models.PlayList, player_models.PlayList.objects.first(), self.playlist)
        self.assertEqual(self.playlist.get_absolute_url(), reverse('playlist_detail', kwargs={'pk': self.playlist.pk}))
        self.assertEqual(self.playlist.get_tracks_count(), 1)
        self.assertEqual(self.playlist.get_total_playtime(), self.music.play_time)
        self.assertEqual(self.playlist.cover, self.playlist.music.first().cover)
        self.assertEqual(self.playlist.name, self.playlist.music.first().name)
        self.playlist.cover = None
        self.playlist.name = None
        self.playlist.save()
        self.assertEqual(self.playlist.cover, self.playlist.music.first().cover)
        self.assertEqual(self.playlist.name, self.playlist.music.first().name)
        self.playlist.music.add(extra_music)
        count = time.strftime('%H:%M:%S',
                              time.gmtime(time.mktime(time.strptime(extra_music.play_time, '%H:%M:%S')) + time.mktime(
                                  time.strptime(self.music.play_time, '%H:%M:%S'))))
        self.assertEqual(self.playlist.get_total_playtime(), count)


class PlayerTestView(TestDate):

    def test_home_page_view_logout(self):
        self.client_factory.logout()
        response = self.request_base_test('/', request_model=self.client_factory)

        self.assertEqual(response.context.get('user_playlists', None), None)
        self.assertEqual(response.context.get('user_playlists', None), None)

    def test_home_page_view_login(self):
        self.client_factory.force_login(user=self.user)
        response = self.request_base_test('/', request_model=self.client_factory)

        self.assertQuerysetEqual(response.context.get('user_playlists', None), self.user.playlists.all())
        self.assertQuerysetEqual(response.context.get('user_favorites', None), self.user.favorites.all())

    def test_music_detail_view_logout(self):
        response = self.request_base_test(reverse('track-detail', kwargs={'track_slug': self.music.slug}),
                                          template_used='player/track_preview.html')
        self.assertEqual(response.context['track'], self.music)
        self.assertEqual(response.context.get('user_playlists', None), None)
        self.assertEqual(response.context.get('user_playlists', None), None)

    def test_music_detail_view_logged(self):
        self.client_factory.force_login(user=self.user)
        response = self.request_base_test('/player/track/', slug=self.music.slug,
                                          request_model=self.client_factory)
        self.assertQuerysetEqual(response.context.get('user_playlists', None), self.user.playlists.all())
        self.assertQuerysetEqual(response.context.get('user_reviews', None), self.user.reviews.filter(music=self.music))

    def test_music_favorite_view_logged(self):
        self.client_factory.force_login(user=self.user)
        response = self.request_base_test('/player/favorites/', request_model=self.client_factory,
                                          template_used='player/favorites_list.html')
        self.assertQuerysetEqual(response.context.get('favorites', None), self.user.favorites.all())
        self.user.favorites.add(self.music)
        response = self.request_base_test(reverse('favorite_musics'), request_model=self.client_factory)
        self.assertQuerysetEqual(response.context.get('favorites', None), self.user.favorites.all())

    def test_music_favorite_view_logout(self):
        self.obj_logout_user_test('/player/favorites/', method='get', request_model=self.client_factory)

    def test_playlist_view_logged(self):
        self.client_factory.force_login(self.user)
        response = self.request_base_test('/player/playlist/', request_model=self.client_factory,
                                          template_used='player/playlist.html')
        self.assertContains(response, self.playlist)
        user_playlists = self.user.playlists.all()
        self.assertQuerysetEqual(response.context.get('playlists'), user_playlists)
        self.assertQuerysetEqual(response.context.get('playlists'), user_playlists)
        self.assertEqual(response.request.get('PATH_INFO'), reverse('my_playlist'))

    def test_playlists_view_logout(self):
        self.obj_logout_user_test('/player/playlist/', request_model=self.client_factory, method='get')

    def test_playlist_detail_logged_owner(self):
        self.client_factory.force_login(self.user)
        response = self.request_base_test('/player/playlist/', pk=self.playlist.pk, request_model=self.client_factory,
                                          template_used='player/playlist_detail.html')
        self.assertEqual(response.context.get('playlist', None), self.playlist)
        self.assertEqual(response.request.get('PATH_INFO'), reverse('playlist_detail', kwargs={'pk': self.playlist.pk}))

    def test_playlist_detail_logged_not_owner(self):
        self.client_factory.force_login(self.user1)
        self.request_base_test('/player/playlist/', pk=self.playlist.pk, status_code=403,
                               request_model=self.client_factory)

    def test_playlist_detail_logout_user(self):
        self.obj_logout_user_test('/player/playlist/', method='get', path_pk=self.playlist.pk,
                                  request_model=self.client_factory)

    def test_album_view(self):
        response = self.request_base_test('/player/album/', template_used='player/album.html', slug=self.album.slug,
                                          request_model=self.client_factory)
        self.assertEqual(response.context.get('album'), self.album)
        self.assertEqual(response.request.get('PATH_INFO', None), reverse('album', kwargs={'slug': self.album.slug}))

    def test_search_track_view(self):
        self.client_factory.force_login(self.user)
        response = self.request_base_test('/player/search/track/', request_model=self.client_factory,
                                          template_used='home.html', query_param='some')
        self.assertQuerysetEqual(response.context.get('musics', None),
                                 player_models.Music.objects.filter(name__icontains='some'))
        self.assertEqual(response.request.get('PATH_INFO'), reverse('search_track'))
        self.assertIsNotNone(response.context.get('user_playlists'))
        self.assertIsNotNone(response.context.get('user_favorites'))

        client_ref = APIClient(HTTP_REFERER='/player/search/track/?q=some')
        response = self.request_base_test('/player/search/track/?page=1', error_test=False, request_model=client_ref,
                                          status_code=302)
        self.assertEqual(response.url, '/player/search/track/?q=some&page=1')

    def test_audio_metadata_api_view(self):
        response = self.request_base_test('/player/api/v1/track/metadata/', slug=self.music.slug)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.data.get('data'), TrackMetaDataSerializer(self.music).data)

    def test_stream_audio_api_view(self):
        slug = self.music.slug
        response = self.request_base_test('/player/api/v1/track/', slug=slug)
        self.assertEqual(response['content-type'], 'audio/mpeg')
        self.assertIsInstance(response, StreamingHttpResponse)

        with open(self.music.music.path, 'rb') as file_music:
            for b in response:
                self.assertEqual(file_music.read(settings.AUDIO_CHUNK_SIZE), b)
        self.assertEqual(player_models.Music.objects.get(slug=slug).watched, 1)

    def test_metadata_global_audio_api_view(self):
        response = self.request_base_test('/player/api/v1/metadata/next/', slug=self.music.slug, method='post',
                                          not_allowed_method='get', request_model=self.client_factory)

        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.data.get('redirect'), self.extra_track.get_absolute_url())

        response = self.request_base_test('/player/api/v1/metadata/next/', slug=self.music.slug, data={
            'next': True,
            'last_track': self.music.slug,
        }, method='post', not_allowed_method='get', request_model=self.client_factory)

        self.assertEqual(response.data.get('redirect'), self.extra_track.get_absolute_url())

        response = self.request_base_test('/player/api/v1/metadata/next/', slug=self.music.slug, data={
            'previous': True,
            'last_track': self.music.slug,
        }, method='post', not_allowed_method='get', request_model=self.client_factory)

        self.assertEqual(response.data.get('redirect'), self.extra_track.get_absolute_url())

        response = self.request_base_test('/player/api/v1/metadata/next/', slug=self.music.slug, data={
            'random': True,
            'last_track': self.extra_track.slug
        }, method='post', not_allowed_method='get', request_model=self.client_factory)

        self.assertEqual(response.data.get('redirect'), self.music.get_absolute_url())

    def test_metadata_audio_from_playlist_api_view(self):
        response = self.request_base_test('/player/api/v1/playlist/track/', pk=self.playlist.pk, method='post',
                                          not_allowed_method='get', request_model=self.client_factory)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.data.get('data'), TrackMetaDataSerializer(self.playlist.music.first()).data)

    def test_metadata_audio_from_album_api_view(self):
        response = self.request_base_test('/player/api/v1/metadata/album/', slug=self.album.slug, method='post',
                                          not_allowed_method='get', request_model=self.client_factory)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.data.get('data'), TrackMetaDataSerializer(self.album.musics.first()).data)

    def test_add_remove_favorite_api_view_logged(self):
        self.client_factory.force_login(self.user)
        response = self.request_base_test('/player/api/v1/track/favorite/', data={
            'track-slug': self.music.slug
        }, method='put', not_allowed_method='delete', request_model=self.client_factory)
        self.assertEqual(response.data.get('action'), 1)

        response = self.request_base_test('/player/api/v1/track/favorite/', data={
            'track-slug': self.music.slug
        }, method='put', not_allowed_method='delete', request_model=self.client_factory)
        self.assertEqual(response.data.get('action'), 0)

    def test_add_remove_favorite_api_view_logout(self):
        self.obj_logout_user_test('/player/api/v1/track/favorite/', method='put', request_model=self.client_factory)

    def test_create_playlist_api_view_logged(self):
        self.client_factory.force_login(self.user)
        response = self.request_base_test('/player/api/v1/playlist/create/', slug=self.music.slug,
                                          request_model=self.client_factory, method='post', not_allowed_method='get')
        new_playlist = player_models.PlayList.objects.create(
            name=self.music.name,
            cover=self.music.cover,
            user=self.user,
        )
        new_playlist.music.add(self.music)
        self.assertEqual(response.data.get('playlist'), PlayListSerializer(new_playlist).data)

        new_playlist.delete()

    def test_create_playlist_api_view_logout(self):
        self.obj_logout_user_test(request_model=self.client_factory, path='/player/api/v1/playlist/create/',
                                  path_slug=self.music.slug, method='post')

    def test_add_to_playlist_api_view_logged(self):
        self.client_factory.force_login(self.user)

        response = self.request_base_test(f'/player/api/v1/playlist/add/{self.extra_track.slug}/', pk=self.playlist.pk,
                                          request_model=self.client_factory, method='post')

        self.assertEqual(response.data.get('answer'), 'ok')

    def test_add_to_playlist_api_view_logout(self):
        self.obj_logout_user_test(f'/player/api/v1/playlist/add/{self.extra_track.slug}/', method='post',
                                  request_model=self.client_factory, path_pk=self.playlist.pk)

    def test_remove_music_playlist_api_view_logged_owner(self):
        self.client_factory.force_login(self.user)

        self.playlist.music.add(self.extra_track)

        response = self.request_base_test(f'/player/api/v1/playlist/remove/{self.extra_track.slug}/',
                                          pk=self.playlist.pk,
                                          request_model=self.client_factory, method='delete')

        self.assertEqual(response.data.get('status'), 'ok')

        self.request_base_test(f'/player/api/v1/playlist/remove/{self.extra_track.slug}/',
                               pk=self.playlist.pk, status_code=404,
                               request_model=self.client_factory, method='delete')

    def test_remove_music_playlist_api_view_logged_not_owner(self):
        self.client_factory.force_login(self.user1)

        self.request_base_test(f'/player/api/v1/playlist/remove/{self.music.slug}/',
                               pk=self.playlist.pk,
                               request_model=self.client_factory, error_test=False, status_code=404, method='delete')

    def test_remove_music_playlist_api_view_logout(self):
        self.obj_logout_user_test(f'/player/api/v1/playlist/remove/{self.extra_track.slug}/', method='delete',
                                  request_model=self.client_factory, path_pk=self.playlist.pk)

    def test_delete_playlist_api_view_logged_not_owner(self):
        self.client_factory.force_login(self.user1)
        self.request_base_test('/player/api/v1/playlist/delete/', pk=self.playlist.pk,
                               request_model=self.client_factory, status_code=403, method='delete')

    def test_delete_playlist_api_view_logged_owner(self):
        self.client_factory.force_login(self.user)
        response = self.request_base_test('/player/api/v1/playlist/delete/', pk=self.playlist.pk,
                                          request_model=self.client_factory, method='delete')

        self.assertEqual(response.data.get('status'), 'ok')

    def test_delete_playlist_api_view_logout(self):
        self.obj_logout_user_test('/player/api/v1/playlist/delete/', path_pk=self.playlist.pk, method='delete',
                                  request_model=self.client_factory)

    def test_update_playlist_api_view_owner(self):
        self.client_factory.force_login(self.user)

        test_cover = SimpleUploadedFile(name='png800x800.png', content=open('media/cover/png800x800.png', 'rb').read(),
                                        content_type='image/png')
        response = self.request_base_test('/player/api/v1/playlist/update/', not_allowed_method='get',
                                          pk=self.playlist.pk, method='put', data={'name': 'New Name',
                                                                                   'cover': test_cover},
                                          request_model=self.client_factory)
        playlist_updated = player_models.PlayList.objects.get(pk=self.playlist.pk)

        self.assertEqual(response.data.get('playlist'), PlayListSerializer(playlist_updated).data)

    def test_update_playlist_api_view_not_owner(self):
        self.client_factory.force_login(self.user1)
        self.request_base_test('/player/api/v1/playlist/update/', error_test=False,
                               pk=self.playlist.pk, method='put',
                               data={'name': 'New Name',
                                     'cover': 'cover'}, status_code=403,
                               request_model=self.client_factory)

    def test_update_playlist_api_view_logout(self):
        self.obj_logout_user_test('/player/api/v1/playlist/update/', path_pk=self.playlist.pk,
                                  request_model=self.client_factory, method='put')

    def test_get_audio_suggestion_api_view(self):
        response = self.request_base_test('/player/api/v1/search/track/',  query_param=self.music.name)

        self.assertEqual(len(response.data.get('data')), 2)

