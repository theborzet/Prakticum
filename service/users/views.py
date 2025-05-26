import re
import requests
import json
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from common.views import TitleMixin
from users.forms import UserLoginForm, UserRegistrationForm
from users.models import CustomUser

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
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        if user.youtube_channel:
            youtube_info = get_user_info(user.youtube_channel)
            context['youtube_info'] = json.dumps(youtube_info, ensure_ascii=False)
        else:
            context['youtube_info'] = json.dumps({})
        return context

class SaveYouTubeChannelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        youtube_channel = request.POST.get('youtube_channel')
        if not re.match(r'^https:\/\/www\.youtube\.com\/@[\w-]+$', youtube_channel):
            messages.error(request, 'Некорректная ссылка на YouTube')
            return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))
        user.youtube_channel = youtube_channel
        user.save()
        messages.success(request, 'YouTube-канал успешно сохранен')
        return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))

class UpdateProfileView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        if request.user.pk != pk:
            messages.error(request, 'Вы не можете редактировать чужой профиль')
            return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()
        messages.success(request, 'Профиль успешно обновлен')
        return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))

def delete_youtube_channel(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        if request.user.pk != pk:
            messages.error(request, 'Вы не можете удалять YouTube-канал другого пользователя')
            return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))
        user.youtube_channel = None
        user.save()
        messages.success(request, 'YouTube-канал успешно удален')
        return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))
    return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))

def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        if not image.content_type.startswith('image/'):
            messages.error(request, 'Недопустимый тип файла')
            return HttpResponse('Недопустимый тип файла', status=400)
        if image.size > 5 * 1024 * 1024:  # 5MB
            messages.error(request, 'Файл слишком большой (максимум 5MB)')
            return HttpResponse('Файл слишком большой', status=400)
        user = request.user
        user.image = image
        user.save()
        messages.success(request, 'Изображение успешно загружено')
        return HttpResponse('Изображение загружено', status=200)
    messages.error(request, 'Ошибка загрузки изображения')
    return HttpResponse('Ошибка загрузки', status=400)

def extract_username(channel_url):
    pattern = r'https://www\.youtube\.com/@(\w+)'
    match = re.match(pattern, channel_url)
    if match:
        return match.group(1)
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
    if not username:
        return {}
    api_key = 'YOUR_YOUTUBE_API_KEY'  # Замените на ваш ключ
    search_url = f'https://www.googleapis.com/youtube/v3/search?channelType=any&q=%40{username}&key={api_key}'
    
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()
        channel_id = extract_channel_id(data)
        
        if channel_id:
            stats_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={channel_id}&key={api_key}'
            stats_response = requests.get(stats_url)
            stats_response.raise_for_status()
            channel_data = stats_response.json()
            
            channel_info = {}
            if 'items' in channel_data and channel_data['items']:
                snippet = channel_data['items'][0]['snippet']
                stats = channel_data['items'][0]['statistics']
                channel_info = {
                    'title': snippet['title'],
                    'description': snippet['description'],
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'subscribers': int(stats.get('subscriberCount', 0)),
                    'views': int(stats.get('viewCount', 0)),
                    'videos': int(stats.get('videoCount', 0))
                }
                
                videos_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=12&order=date&key={api_key}'
                videos_response = requests.get(videos_url)
                videos_response.raise_for_status()
                videos_data = videos_response.json()
                
                likes = []
                comments = []
                views = []
                labels = []
                for item in videos_data.get('items', [])[:12]:
                    video_id = item['id'].get('videoId')
                    if video_id:
                        video_stats_url = f'https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={api_key}'
                        video_stats_response = requests.get(video_stats_url)
                        video_stats_response.raise_for_status()
                        video_stats = video_stats_response.json()
                        if 'items' in video_stats and video_stats['items']:
                            stats = video_stats['items'][0]['statistics']
                            likes.append(int(stats.get('likeCount', 0)))
                            comments.append(int(stats.get('commentCount', 0)))
                            views.append(int(stats.get('viewCount', 0)))
                            labels.append(item['snippet']['publishedAt'][:10])
                
                channel_info['likes'] = likes[::-1]
                channel_info['comments'] = comments[::-1]
                channel_info['views'] = views[::-1]
                channel_info['labels'] = labels[::-1]
            return channel_info
    except requests.RequestException as e:
        print(f"Ошибка YouTube API: {e}")
        return {}
    return {}