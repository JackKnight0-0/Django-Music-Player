from django.urls import path

from .views import CreateReviewReplyAPIView, DeleteReviewAPIView, DeleteReplyAPIView, \
    AddRemoveLikeReplyReviewAPIView, NextReviewsAPIView, NextReplyAPIView

urlpatterns = [
    path('delete/<int:review_id>/', DeleteReviewAPIView.as_view()),
    path('delete/reply/<int:reply_id>/', DeleteReplyAPIView.as_view()),
    path('create/<slug:track_slug>/', CreateReviewReplyAPIView.as_view()),
    path('like/', AddRemoveLikeReplyReviewAPIView.as_view()),
    path('next/<slug:track_slug>/<int:review_id>/', NextReviewsAPIView.as_view()),
    path('next/replies/<int:review_id>/<int:reply_id>/', NextReplyAPIView.as_view())
]
