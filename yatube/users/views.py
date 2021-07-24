from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, \
    PasswordResetView, PasswordChangeView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('login')
    template_name = 'users/signup.html'


class Login(LoginView):
    template_name = 'users/login.html'


class Logout(LogoutView):
    template_name = 'users/logged_out.html'


class PasswordChange(PasswordChangeView):
    template_name = 'users/password_change_form.html'


class PasswordReset(PasswordResetView):
    template_name = 'users/password_reset_form.html'
