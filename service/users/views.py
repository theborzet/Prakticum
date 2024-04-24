from django.contrib.messages.views import SuccessMessageMixin

from django.urls import reverse, reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView

from common.views import TitleMixin
from users.forms import UserLoginForm, UserRegistrationForm
from users.models import CustomUser

# Create your views here.
class UserRegistrationView(TitleMixin, SuccessMessageMixin,CreateView):
    model = CustomUser
    template_name = 'users/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('users:login')
    success_message = 'Вы успешно зарегистрировались!'
    title = 'Analisis - Регистрация'

class UserLoginView(TitleMixin, LoginView):
    title = 'Analisis - Авторизация'
    template_name = 'users/login.html'
    form_class = UserLoginForm

class UserLogoutView(LogoutView):
    pass