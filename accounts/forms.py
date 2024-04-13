from allauth.account.forms import SignupForm, LoginForm, ChangePasswordForm, ResetPasswordForm, ResetPasswordKeyForm
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSignUpForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(CustomSignUpForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Password ( again )'})
        self.fields['email'].widget = forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
        self.fields['username'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
        self.fields['login'].widget = forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Email Or Username'})


class CustomChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super(CustomChangePasswordForm, self).__init__(*args, **kwargs)
        self.fields['oldpassword'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Old Password'})
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'New Password'})
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'New Password ( again )'})


class SetPasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
                                label='Password')
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password ( again )'}),
        label='Password ( again )')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password1') != cd.get('password2'):
            self.add_error('password2', "The passwords don't match!")
        return cd.get('password2')


class UpdateUserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'username',
            'avatar'
        )

    def __init__(self, *args, **kwargs):
        super(UpdateUserProfileForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(
            attrs={'class': 'username-input', 'placeholder': 'New username'})
        self.fields['avatar'].widget = forms.FileInput(attrs={'id': 'avatar'})


class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(CustomResetPasswordForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget = forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})


class CustomResetPasswordFromKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super(CustomResetPasswordFromKeyForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'New Password'})
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'New Password ( again )'})
