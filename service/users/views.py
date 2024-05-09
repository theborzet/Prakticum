import re
import requests

from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import DetailView



from common.views import TitleMixin
from users.forms import UserLoginForm, UserRegistrationForm
from users.models import CustomUser

from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.views.generic import View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from users.models import CustomUser
from users.forms import UserLoginForm, UserRegistrationForm
from common.views import TitleMixin

class UserRegistrationView(TitleMixin, SuccessMessageMixin, CreateView):
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

class UserProfileView(DetailView):
    model = CustomUser
    template_name = 'users/profile.html'
    context_object_name = 'user_profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        if user.youtube_channel:
            # print("Channel URL:", user.youtube_channel)  # Выводим URL канала для проверки
            youtube_info = get_user_info(user.youtube_channel)
            # print("YouTube Info:", youtube_info)
            context['youtube_info'] = youtube_info
        return context
    
class SaveYouTubeChannelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        youtube_channel = request.POST.get('youtube_channel')
        user.youtube_channel = youtube_channel
        user.save()

        return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))


def extract_username(channel_url):
    pattern = r'https://www\.youtube\.com/@(\w+)'
    match = re.match(pattern, channel_url)
    if match:
        return match.group(1)
    else:
        return None

def extract_channel_id(search_data):
    for item in search_data.get('items', []):
        if item.get('id', {}).get('kind') == 'youtube#channel':
            return item['id'].get('channelId')
        elif item.get('id', {}).get('kind') == 'youtube#user':
            return item['id'].get('channelId')
    return None

def get_user_info(channel_url):
    username = extract_username(channel_url)
    api_key = 'AIzaSyBG-ts9VMkNhKuznu5ZQQ4HQ76DX_2ZWOk'
    search_url = f'https://www.googleapis.com/youtube/v3/search?channelType=any&q=%40{username}&key={api_key}'
    
    # Выполняем поиск канала по имени пользователя
    response = requests.get(search_url)
    data = response.json()
    
    # Извлекаем ID канала
    channel_id = extract_channel_id(data)
    
    # Если канал найден, получаем информацию о нем
    if channel_id:
        channel_info_url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet&id={channel_id}&key={api_key}'
        channel_response = requests.get(channel_info_url)
        channel_data = channel_response.json()
        
        # Обработка ответа и извлечение информации о канале
        channel_info = {}
        if 'items' in channel_data and channel_data['items']:
            channel_info['title'] = channel_data['items'][0]['snippet']['title']
            channel_info['description'] = channel_data['items'][0]['snippet']['description']
            channel_info['thumbnail'] = channel_data['items'][0]['snippet']['thumbnails']['high']['url']
        
        return channel_info
    
    return {}