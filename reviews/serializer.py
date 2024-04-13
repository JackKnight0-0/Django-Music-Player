from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Review, Reply
from .utils import ReplyReviewSerializerMixin

User = get_user_model()


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = (
            'id',
            'user',
            'music',
            'text',
        )

    def get_user_to_representation(self, user_pk):
        user_serializer = get_user_model().objects.get(pk=user_pk)
        return UserSerializer(user_serializer).data

    def to_representation(self, instance):
        """
        Changing representation of user to more detail one.
        """
        representation = super(ReviewSerializer, self).to_representation(instance=instance)
        representation['user'] = self.get_user_to_representation(representation['user'])
        return representation


class ReviewDetailSerializer(ReplyReviewSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = (
            'id',
            'user',
            'text',
            'user_liked',
            'user_disliked',
        )

    def to_representation(self, instance):
        representation = super(ReviewDetailSerializer, self).to_representation(instance=instance)
        representation['user'] = self.get_user_to_representation(representation['user'], UserSerializer)
        representation['auth'] = self.context.get('user').is_authenticated
        representation['replies'] = False
        if instance.replies.first() is not None:
            representation['replies'] = True
        self.like_dislike_user_to_representation(representation)
        return representation


class ReplyDetailSerializer(ReplyReviewSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Reply
        fields = (
            'id',
            'user',
            'text',
            'user_liked',
            'user_disliked'
        )

    def to_representation(self, instance):
        representation = super(ReplyDetailSerializer, self).to_representation(instance=instance)
        representation['user'] = self.get_user_to_representation(representation['user'], UserSerializer)
        representation['auth'] = self.context.get('user').is_authenticated
        self.like_dislike_user_to_representation(representation)
        return representation


class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply
        fields = (
            'id',
            'user',
            'text',
            'review'
        )

    def get_user_to_representation(self, user_pk):
        user_serializer = get_user_model().objects.get(pk=user_pk)
        return UserSerializer(user_serializer).data

    def to_representation(self, instance):
        representation = super(ReplySerializer, self).to_representation(instance=instance)
        representation['user'] = self.get_user_to_representation(representation['user'])
        return representation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'avatar'
        )
