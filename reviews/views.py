from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from player.models import Music
from .models import Review, Reply
from .serializer import ReviewSerializer, ReplySerializer, ReviewDetailSerializer, ReplyDetailSerializer


class CreateReviewReplyAPIView(LoginRequiredMixin, generics.GenericAPIView):
    """
    CreateReviewReplyAPIView creates a review or reply object,
    specifying the review id for the reply and track_slug for the review.
    """

    def get_review(self):
        review_id = self.request.data.get('review_id')
        return get_object_or_404(Review, id=review_id)

    def get_track(self):
        slug = self.kwargs.get('track_slug')
        return get_object_or_404(Music, slug=slug)

    def create_reply(self):
        """
        To create reply, we need review pk, a user and, text.
        """
        data = dict()
        data['review'] = self.get_review().pk
        data['text'] = self.request.data.get('text')
        data['user'] = self.request.user.pk
        serializer_reply = ReplySerializer(data=data)
        serializer_reply.is_valid(raise_exception=True)
        serializer_reply.save()
        return serializer_reply.data

    def create_review(self):
        """
        To create review, we need track slug, a user and, text.
        """
        data = dict()
        track = self.get_track()
        data['user'] = self.request.user.pk
        data['music'] = track.pk
        data['text'] = self.request.data.get('text', None)
        serializer_review = ReviewSerializer(data=data)
        serializer_review.is_valid(raise_exception=True)
        serializer_review.save()
        return serializer_review.data

    def create(self):
        """
        Checking if request contains reply, return data serializer.
        """
        is_reply = self.request.data.get('reply', False)
        response = None
        if is_reply:
            response = self.create_reply()
        else:
            response = self.create_review()
        return response

    def post(self, request, *args, **kwargs):
        return Response({'data': self.create()})


class DeleteReviewAPIView(LoginRequiredMixin, UserPassesTestMixin, generics.GenericAPIView):
    """
    Delete a review if it belongs to a user.
    """

    def get_object(self):
        return get_object_or_404(Review, pk=self.kwargs.get('review_id'))

    def delete(self, request, *args, **kwargs):
        review = self.get_object()
        review.delete()
        response = Response()
        response.status_code = 204
        return response

    def test_func(self):
        review = self.get_object()
        if review.user == self.request.user:
            return True
        return False


class DeleteReplyAPIView(LoginRequiredMixin, UserPassesTestMixin, generics.GenericAPIView):
    """
    Delete a reply if it belongs to a user.
    """

    def get_object(self):
        return get_object_or_404(Reply, pk=self.kwargs.get('reply_id'))

    def delete(self, request, *args, **kwargs):
        reply = self.get_object()
        reply.delete()
        response = Response()
        response.status_code = 204
        return response

    def test_func(self):
        reply = self.get_object()
        if reply.user == self.request.user:
            return True
        return False


class AddRemoveLikeReplyReviewAPIView(LoginRequiredMixin, generics.GenericAPIView):
    """
    This view will remove or add a liked/dislike review or reply,
    depending on the type of id and whether a like from that user already exists in the object.
    """

    def get_review(self):
        return get_object_or_404(Review, pk=self.request.data.get('review_id'))

    def get_reply(self):
        return get_object_or_404(Reply, pk=self.request.data.get('reply_id'))

    def put_like(self, like_query, dislike_query):
        """
        Add or remove the like from a given query, remove dislike if exists
        """
        if self.user in like_query.all():
            like_query.remove(self.user)
            return 'like_removed'
        else:
            self.check_like_dislike(dislike_query)
            like_query.add(self.user)
            return 'liked'

    def check_like_dislike(self, query):
        """
        Check if user in dislike/like query, if so, remove user and add to response extra data
        """
        if self.user in query.all():
            query.remove(self.user)
            if self.action == 'like':
                self.removed_extra = 'dislike'
            else:
                self.removed_extra = 'like'

    def put_dislike(self, dislike_query, like_query):
        """
        Add or remove the like from a given query, remove like if exists
        """
        if self.user in dislike_query.all():
            dislike_query.remove(self.user)
            return 'dislike_removed'
        else:
            self.check_like_dislike(like_query)
            dislike_query.add(self.user)
            return 'disliked'

    def put_like_dislike_for_reply(self):
        """
        Checking which action is given, then delegating another function
        """
        reply = self.get_reply()
        reply_liked_users = reply.user_liked
        reply_disliked_users = reply.user_disliked
        if self.action == 'like':
            return self.put_like(reply_liked_users, reply_disliked_users)
        else:
            return self.put_dislike(reply_disliked_users, reply_liked_users)

    def put_like_dislike_for_review(self):
        review = self.get_review()
        review_liked_users = review.user_liked
        review_disliked_users = review.user_disliked
        if self.action == 'like':
            return self.put_like(review_liked_users, review_disliked_users)
        else:
            return self.put_dislike(review_disliked_users, review_liked_users)

    def put_like_dislike(self):
        if 'reply_id' in self.request.data:
            return self.put_like_dislike_for_reply()
        else:
            return self.put_like_dislike_for_review()

    def put(self, request, *args, **kwargs):
        self.user = self.request.user
        self.action = self.request.data.get('action')
        self.removed_extra = None
        return Response({'action': self.put_like_dislike(), 'extra': self.removed_extra})


class NextReviewsAPIView(generics.GenericAPIView):
    """
    View used to optimize a page with a large number of reviews by giving 10 records.
    """
    def get_track(self):
        return get_object_or_404(Music, slug=self.kwargs.get('track_slug'))

    def get_current_review(self):
        self.track = self.get_track()
        return get_object_or_404(Review, pk=self.kwargs.get('review_id'), music=self.track)

    def get_next_query(self):
        current_review = self.get_current_review()
        next_reviews = Review.objects.filter(id__lt=current_review.pk, music_id=self.track.pk)[:11]
        response = {
            'next_reviews': ReviewDetailSerializer(next_reviews[:10], many=True,
                                                   context={'user': self.request.user}).data,
            'last': False
        }
        if len(next_reviews) < 11:
            response['last'] = True

        return response

    def get(self, request, *args, **kwargs):
        return Response(self.get_next_query())


class NextReplyAPIView(generics.GenericAPIView):
    def get_review(self):
        return get_object_or_404(Review, pk=self.kwargs.get('review_id'))

    def get_reply(self):
        reply_id = self.kwargs.get('reply_id', None)
        if reply_id == 0:
            return 'first'
        return get_object_or_404(Reply, pk=self.kwargs.get('reply_id'))

    def get_next_replies(self):
        self.review = self.get_review()
        reply = self.get_reply()
        if reply == 'first': # check if it's first call from review replies
            replies = Reply.objects.filter(review_id=self.review.pk)[:11]
        else:
            replies = Reply.objects.filter(review_id=self.review.pk, id__lt=reply.id)[:11]
        data = {
            'next_replies': ReplyDetailSerializer(replies[:10], many=True, context={'user': self.request.user}).data,
            'last': False
        }
        if len(replies) < 11:
            data['last'] = True
        return data

    def get(self, request, *args, **kwargs):
        replies = self.get_next_replies()
        return Response(replies)
