from django.contrib.auth import get_user_model


class ReplyReviewSerializerMixin(object):
    """
    Mixin for change representation of user and add more information about like, dislike in the object.
    """

    def get_user_to_representation(self, user_pk, user_serializer):
        user = get_user_model().objects.get(pk=user_pk)
        user_serializer = user_serializer(user).data
        user_serializer['owner'] = False
        if user_pk == self.context.get('user').pk:
            user_serializer['owner'] = True
        return user_serializer

    def like_dislike_user_to_representation(self, representation):
        user_pk = self.context.get('user').pk
        representation['metadata'] = {
            'like_count': len(representation['user_liked']),
            'dislike_count': len(representation['user_disliked']),
            'liked': user_pk in representation['user_liked'],
            'disliked': user_pk in representation['user_disliked']
        }
        del representation['user_disliked']
        del representation['user_liked']
        return representation
