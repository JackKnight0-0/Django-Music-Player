import allauth.account.views as account_generic
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import reverse, redirect
from django.views import generic

import accounts.forms as account_forms


class CustomLoginView(account_generic.LoginView):
    template_name = 'account/login.html'
    form_class = account_forms.CustomLoginForm

    def get_success_url(self):
        return reverse('home')


class CustomSignUpView(account_generic.SignupView):
    template_name = 'account/signup.html'
    form_class = account_forms.CustomSignUpForm

    def get_success_url(self):
        return reverse('home')


class CustomChangePasswordView(PasswordChangeView):
    form_class = account_forms.CustomChangePasswordForm
    template_name = 'account/password_change.html'

    def get_success_url(self):
        return reverse('home')

    def get(self, request, *args, **kwargs):
        if self.request.user.has_usable_password():
            return super(CustomChangePasswordView, self).get(request=request, *args, **kwargs)
        else:
            return redirect(reverse('account_set_password'))


class SetPasswordView(generic.FormView):
    form_class = account_forms.SetPasswordForm
    template_name = 'account/set_password.html'

    def get_success_url(self):
        return redirect(reverse('home'))

    def post(self, request, *args, **kwargs):
        form = account_forms.SetPasswordForm(self.request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = get_user_model().objects.get(pk=self.request.user.pk)
            user.set_password(cd.get('password2'))
            user.save()
            update_session_auth_hash(self.request, user)
            return self.get_success_url()
        return self.render_to_response(context={'form': form})


class UpdateUserProfile(generic.FormView):
    template_name = 'account/update_profile.html'

    def get_context_data(self, **kwargs):
        context = dict()
        context['form'] = account_forms.UpdateUserProfileForm(instance=self.request.user)
        return context

    def get_success_url(self):
        return redirect(reverse('account_profile_update'))

    def post(self, request, *args, **kwargs):
        form = account_forms.UpdateUserProfileForm(self.request.POST, self.request.FILES, instance=self.request.user)
        if form.is_valid():
            form.save()
            return self.get_success_url()
        return self.render_to_response(context={'form': form})


class CustomResetPasswordView(account_generic.PasswordResetView):
    template_name = 'account/password_reset.html'
    form_class = account_forms.CustomResetPasswordForm


class CustomResetPasswordFromKeyView(account_generic.PasswordResetFromKeyView):
    template_name = 'account/password_reset_from_key.html'
    form_class = account_forms.CustomResetPasswordFromKeyForm


class CustomResetPasswordDoneView(account_generic.PasswordResetDoneView):
    template_name = 'account/password_reset_done.html'

    def check_referer_page(self):
        return str(self.request.META.get('HTTP_REFERER')).endswith(str(reverse('account_reset_password')))

    def get(self, request, *args, **kwargs):
        if self.check_referer_page():
            return super(CustomResetPasswordDoneView, self).get(request, *args, **kwargs)
        else:
            return redirect(reverse('home'))


class CustomResetPasswordFromKeyDoneView(account_generic.PasswordResetDoneView):
    template_name = 'account/password_reset_complete.html'

    def check_referer_page(self):
        return str(self.request.META.get('HTTP_REFERER')).endswith(
            str(reverse('account_reset_password_from_key', kwargs={'uidb36': '1', 'key': 'set-password'})))

    def get(self, request, *args, **kwargs):
        if self.check_referer_page():
            return super(CustomResetPasswordFromKeyDoneView, self).get(request, *args, **kwargs)
        else:
            return redirect(reverse('home'))
