from django.urls import path

import player.views as views

urlpatterns = [
    path('favorites/', views.UserFavoritesMusicView.as_view(), name='favorite_musics'),
    path('playlist/', views.PlaylistView.as_view(), name='my_playlist'),
    path('playlist/<int:pk>/', views.PlayListDetail.as_view(), name='playlist_detail'),
    path('track/<slug:track_slug>/', views.TrackPreviewView.as_view(), name='track-detail'),
    path('album/<slug:slug>/', views.AlbumMusicListView.as_view(), name='album'),
    path('search/track/', views.FilteredListAudioView.as_view(), name='search_track'),
    # api
    path('api/v1/playlist/add/<slug:track_slug>/<int:playlist_pk>/', views.AddToPlayListAPIView.as_view()),
    path('api/v1/playlist/remove/<slug:track_slug>/<int:playlist_pk>/', views.RemoveMusicFromPlayListAPIView.as_view()),
    path('api/v1/playlist/create/<slug:track_slug>/', views.CreatePlayListAPIView.as_view()),
    path('api/v1/playlist/update/<int:playlist_pk>/', views.UpdatePlatListView.as_view()),
    path('api/v1/playlist/delete/<int:pk>/', views.DeletePlayListView.as_view()),
    path('api/v1/track/favorite/', views.AddRemoveFavorite.as_view()),
    path('api/v1/track/<slug:track_slug>/', views.SteamAudioAPI.as_view()),
    path('api/v1/track/metadata/<slug:track_slug>/', views.MetaDataAudioAPIView.as_view()),
    path('api/v1/playlist/track/<int:playlist>/', views.MetaDataAudioFromPlaylistAPIView.as_view()),
    path('api/v1/metadata/next/<slug:track_slug>/', views.MetaDataGlobalAudio.as_view()),
    path('api/v1/metadata/album/<slug:slug>/', views.AlbumMetaDataAudioAPIView.as_view()),
    path('api/v1/search/track/', views.GetAudioSuggestionAPIView.as_view())
]
