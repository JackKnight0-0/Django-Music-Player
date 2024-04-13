from django.contrib import admin

from player.models import Music, Album, Author, Genre, PlayList


@admin.register(Music)
class MusicAdmin(admin.ModelAdmin):
    readonly_fields = ['slug', 'play_time']

    def delete_queryset(self, request, queryset):
        for query in queryset:
            query.music.delete()
            query.cover.delete()
        queryset.delete()


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    readonly_fields = ['slug', ]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    pass


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass

@admin.register(PlayList)
class PlayListAdmin(admin.ModelAdmin):
    pass