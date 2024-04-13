import allauth.account.views as account_views
from django.urls import path, re_path

from accounts import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='account_login'),
    path('signup/', views.CustomSignUpView.as_view(), name='account_signup'),
    path('logout/', account_views.LogoutView.as_view(), name='account_logout'),
    path('change/password/', views.CustomChangePasswordView.as_view(), name='account_change_password'),
    path('set/password/', views.SetPasswordView.as_view(), name='account_set_password'),
    path('reset/password/', views.CustomResetPasswordView.as_view(), name='account_reset_password'),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$", views.CustomResetPasswordFromKeyView.as_view(),
        name='account_reset_password_from_key'),
    path('reset/password/done/', views.CustomResetPasswordDoneView.as_view(), name='account_reset_password_done'),
    path('reset/password/complete/', views.CustomResetPasswordFromKeyDoneView.as_view(),
         name='account_reset_password_from_key_done'),
    path('profile/update/', views.UpdateUserProfile.as_view(), name='account_profile_update')
]
