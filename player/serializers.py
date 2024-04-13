from rest_framework import serializers

from player.models import PlayList, Music, Author


class PlayListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayList
        fields = (
            'name',
            'cover'
        )


class TrackMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Music
        fields = (
            'name',
            'slug',
            'cover',
            'author'
        )

    def get_author(self, authors):
        return [name[0] for name in Author.objects.filter(pk__in=authors).values_list('name')]

    def to_representation(self, instance):
        r = super().to_representation(instance=instance)
        r['author'] = self.get_author(r['author'])
        return r


class TrackSuggestionSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Music
        fields = (
            'name',
            'url'
        )
