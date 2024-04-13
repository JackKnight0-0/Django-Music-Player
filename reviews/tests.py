import json

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, APIClient

from player.models import Music, Author, Genre
from reviews.models import Review, Reply
from reviews.serializer import ReviewSerializer, ReplySerializer, ReviewDetailSerializer, ReplyDetailSerializer
from reviews.test_mixin import TestMixin

User = get_user_model()


class TestData(TestMixin):
    @classmethod
    def setUp(cls):
        cls.user = User.objects.create(username='TestUser', password='testpass123', email='testemail@gmail.com')
        cls.user1 = User.objects.create(username='TestUser1', password='testpass123', email='testemail1@gmail.com')
        author = Author.objects.create(name='SomeAuthor')
        genre = Genre.objects.create(name='SomeGenre')
        cls.music = Music.objects.create(
            name='some music',
            music='music/test_music.mp3',
            cover='cover/test_cover.png',
        )
        cls.music.author.add(author)
        cls.music.genre.add(genre)
        cls.review = Review.objects.create(
            user=cls.user,
            music=cls.music,
            text='SomeText',
        )
        cls.reply = Reply.objects.create(
            user=cls.user,
            review=cls.review,
            text='SomeReplyText'
        )
        cls.factory = APIRequestFactory()
        cls.client_factory = APIClient()


class TestReviewReplyModelSerializer(TestData):

    def object_reply_review_test(self, obj_model, obj, text='SomeText'):
        self.assertEqual(obj_model.objects.count(), 1)
        self.assertEqual(text, obj.text)
        self.assertEqual(self.user, obj.user)
        self.assertEqual(obj.__str__(), str(obj.pk) + ' ' + obj.text[:50])

        self.assertEqual(obj.liked_count(), 0)
        self.assertEqual(obj.disliked_count(), 0)

    def test_review(self):
        self.object_reply_review_test(Review, self.review)
        self.assertEqual(self.music, self.review.music)

    def test_reply(self):
        self.object_reply_review_test(Reply, self.reply, 'SomeReplyText')
        self.assertEqual(self.reply.review, self.review)

    def test_review_serializer(self):
        review_serializer = ReviewSerializer(self.review)
        self.assertJSONEqual(json.dumps(review_serializer.data), json.dumps({
            'id': self.review.id,
            'user': {
                'username': self.user.username,
                'avatar': self.user.avatar.url
            },
            'music': self.music.id,
            'text': self.review.text
        }))

    def test_reply_serializer(self):
        reply_serializer = ReplySerializer(self.reply)
        self.assertJSONEqual(json.dumps(reply_serializer.data), json.dumps({
            'id': self.reply.id,
            'user': {
                'username': self.user.username,
                'avatar': self.user.avatar.url
            },
            'text': self.reply.text,
            'review': self.review.pk
        }))


class TestReviewReplyView(TestData):

    def delete_obj_owner(self, obj, model, owner, path):
        self.client_factory.logout()
        self.client_factory.force_login(user=owner)
        self.request_base_test(path=path, pk=obj.pk, method='delete',
                               request_model=self.client_factory, status_code=204)
        self.assertEqual(model.objects.count(), 0)

    def delete_obj_not_owner(self, obj, model, user, path):
        self.client_factory.logout()
        self.client_factory.force_login(user=user)
        self.request_base_test(path=path, pk=obj.pk, method='delete',
                               request_model=self.client_factory, status_code=403)
        self.assertEqual(model.objects.count(), 1)

    def create_obj_logged_user(self, obj, data, user, path, serializer, response_kwargs=None, path_slug=None,
                               path_pk=None, not_valid_data=None):
        self.client_factory.force_login(user)
        request_data = {
            'path': path,
            'method': 'post',
            'request_model': self.client_factory,
            'not_allowed_method': 'get',
            'data': data,
        }
        if path_pk is not None:
            request_data['pk'] = path_pk
        elif path_slug is not None:
            request_data['slug'] = path_slug
        response = self.request_base_test(**request_data)
        self.assertEqual(response['content-type'], 'application/json')
        response_data = None
        if response_kwargs is not None:
            for kwarg in response_kwargs:
                if response_data is None:
                    response_data = response.data.get(kwarg)
                else:
                    response_data = response_data.get(kwarg)
        else:
            response_data = response.data
        self.assertEqual(response_data, serializer(obj.objects.first()).data)

        request_data['data'] = not_valid_data
        request_data['status_code'] = 400
        self.request_base_test(**request_data)

    def test_delete_review_view_not_owner(self):
        self.delete_obj_not_owner(obj=self.review, model=Review, user=self.user1, path='/reviews/api/v1/delete/')

    def test_delete_review_view_owner(self):
        self.delete_obj_owner(owner=self.user, path='/reviews/api/v1/delete/', obj=self.review, model=Review)

    def test_delete_reply_view_owner(self):
        self.delete_obj_owner(obj=self.reply, model=Reply, owner=self.user, path='/reviews/api/v1/delete/reply/')

    def test_delete_reply_view_not_owner(self):
        self.delete_obj_not_owner(obj=self.reply, model=Reply, user=self.user1, path='/reviews/api/v1/delete/reply/')

    def test_create_review_logged_user(self):
        text = 'NewReview'
        self.create_obj_logged_user(obj=Review, data={'text': text}, user=self.user, path='/reviews/api/v1/create/',
                                    serializer=ReviewSerializer, response_kwargs=['data', ], path_slug=self.music.slug,
                                    not_valid_data={'text': text * 200})

    def test_create_review_reply_logout_user(self):
        self.obj_logout_user_test(path='/reviews/api/v1/create/', request_model=self.client_factory,
                                  path_slug=self.music.slug, method='post')

    def test_create_reply_logged_user(self):
        text = 'NewReply'
        self.create_obj_logged_user(obj=Reply, data={'text': text, 'reply': True, 'review_id': self.review.pk},
                                    user=self.user,
                                    path='/reviews/api/v1/create/',
                                    serializer=ReplySerializer, response_kwargs=['data', ], path_slug=self.music.slug,
                                    not_valid_data={'text': text * 200})

    def like_dislike_logged_user_test(self, user, path, data, status_code, response_expected_data, count_keys,
                                      obj,
                                      field_test,
                                      path_slug=None,
                                      path_pk=None):
        self.client_factory.force_login(user)
        request_data = {
            'path': path,
            'method': 'put',
            'status_code': status_code,
            'request_model': self.client_factory,
            'data': data
        }

        if path_slug is not None:
            request_data['slug'] = path_slug
        elif path_pk is not None:
            request_data['pk'] = path_pk

        response = self.request_base_test(**request_data)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(len(response.data.keys()), count_keys)
        for value, key in field_test.items():
            self.assertEqual(getattr(getattr(obj, value), key[0])(), key[1])
        for value, key in response_expected_data.items():
            self.assertEqual(response.data[value], key)

    def test_like_dislike_review_logged_user(self):
        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'like', 'review_id': self.review.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'liked',
                                               'extra': None
                                           }, obj=self.review, field_test={'user_liked': ('count', 1)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'like', 'review_id': self.review.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'like_removed',
                                               'extra': None
                                           }, obj=self.review, field_test={'user_liked': ('count', 0)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'dislike', 'review_id': self.review.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'disliked',
                                               'extra': None
                                           }, obj=self.review, field_test={'user_disliked': ('count', 1)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'dislike', 'review_id': self.review.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'dislike_removed',
                                               'extra': None
                                           }, obj=self.review, field_test={'user_disliked': ('count', 0)})

    def test_like_dislike_review_mixed(self):
        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'like', 'review_id': self.review.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'liked',
                                               'extra': None
                                           }, obj=self.review, field_test={'user_liked': ('count', 1)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'dislike', 'review_id': self.review.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'disliked',
                                               'extra': 'like'
                                           }, obj=self.review,
                                           field_test={'user_disliked': ('count', 1), 'user_liked': ('count', 0)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'like', 'review_id': self.review.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'liked',
                                               'extra': 'dislike'
                                           }, obj=self.review,
                                           field_test={'user_disliked': ('count', 0), 'user_liked': ('count', 1)})

    def test_like_dislike_reply_logged_user(self):
        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'like', 'reply_id': self.reply.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'liked',
                                               'extra': None
                                           }, obj=self.reply, field_test={'user_liked': ('count', 1)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'like', 'reply_id': self.reply.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'like_removed',
                                               'extra': None
                                           }, obj=self.reply, field_test={'user_liked': ('count', 0)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'dislike', 'reply_id': self.reply.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'disliked',
                                               'extra': None
                                           }, obj=self.reply, field_test={'user_disliked': ('count', 1)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'dislike', 'reply_id': self.reply.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'dislike_removed',
                                               'extra': None
                                           }, obj=self.reply, field_test={'user_disliked': ('count', 0)})

    def test_like_dislike_reply_mixed(self):
        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'like', 'reply_id': self.reply.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'liked',
                                               'extra': None
                                           }, obj=self.reply, field_test={'user_liked': ('count', 1)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'dislike', 'reply_id': self.reply.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'disliked',
                                               'extra': 'like'
                                           }, obj=self.reply,
                                           field_test={'user_disliked': ('count', 1), 'user_liked': ('count', 0)})

        self.like_dislike_logged_user_test(user=self.user, path='/reviews/api/v1/like/', count_keys=2,
                                           data={'action': 'like', 'reply_id': self.reply.pk}, status_code=200,
                                           response_expected_data={
                                               'action': 'liked',
                                               'extra': 'dislike'
                                           }, obj=self.reply,
                                           field_test={'user_disliked': ('count', 0), 'user_liked': ('count', 1)})

    def test_like_logout_user(self):
        self.obj_logout_user_test(path='/reviews/api/v1/like/', request_model=self.client_factory, method='put')

    def test_next_review_api_view(self):
        self.client_factory.force_login(self.user)
        for _ in range(10):
            Review.objects.create(
                user=self.user,
                music=self.music,
                text='some_text',
            )
        response = self.request_base_test(request_model=self.client_factory,
                                          path=f'/reviews/api/v1/next/{self.music.slug}/',
                                          pk=Review.objects.first().pk)
        data = response.data

        self.assertEqual(len(data.get('next_reviews')), 10)
        self.assertEqual(data.get('next_reviews'), ReviewDetailSerializer(
            Review.objects.filter(id__lt=Review.objects.first().pk, music_id=self.music.pk), many=True,
            context={'user': self.user}).data)
        self.assertEqual(data.get('last'), True)

    def test_next_reply_api_view(self):
        self.client_factory.force_login(self.user)
        for _ in range(10):
            Reply.objects.create(
                user=self.user,
                text='Some text',
                review=self.review
            )

        response = self.request_base_test(request_model=self.client_factory,
                                          path=f'/reviews/api/v1/next/replies/{self.review.pk}/',
                                          pk=Reply.objects.first().pk)

        data = response.data

        self.assertEqual(len(data.get('next_replies')), 10)
        self.assertEqual(data.get('next_replies'),
                         ReplyDetailSerializer(
                             Reply.objects.filter(id__lt=Reply.objects.first().id, review_id=self.review.id),
                             many=True, context={'user': self.user}).data)
        self.assertEqual(data.get('last'), True)
