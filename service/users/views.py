import re
import requests
import json
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate
import django.db.models as models
from users.forms import UserLoginForm, UserRegistrationForm
from users.models import CustomUser,UserActivity, YouTubeChannelStats
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
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        # YouTube данные
        if user.youtube_channel:
            youtube_info = get_user_info(user, self.request)
            context['youtube_info'] = json.dumps(youtube_info, ensure_ascii=False)
        else:
            context['youtube_info'] = json.dumps({
                'labels': [],
                'subscribers': [],
                'views': [],
                'likes': [],
                'comments': [],
                'title': '',
                'description': '',
                'thumbnail': '',
                'videos': 0
            })

        # Данные активности
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        activities = user.activities.filter(created_at__range=(start_date, end_date)) \
            .annotate(date=TruncDate('created_at')) \
            .values('date') \
            .annotate(count=Count('id')) \
            .order_by('date')

        activity_labels = [activity['date'].strftime('%d.%m.%Y') for activity in activities]
        activity_data = [activity['count'] for activity in activities]

        print("Activity labels:", activity_labels)
        print("Activity data:", activity_data)

        context['activity_info'] = json.dumps({
            'labels': activity_labels,
            'data': activity_data
        })

        return context


class SaveYouTubeChannelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        youtube_channel = request.POST.get('youtube_channel')
        if not re.match(r'^https:\/\/www\.youtube\.com\/(@|channel\/|user\/|c\/)[\w-]+$', youtube_channel):
            messages.error(request, 'Некорректная ссылка на YouTube')
            return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))
        user.youtube_channel = youtube_channel
        user.save()
        messages.success(request, 'YouTube-канал успешно сохранён')
        return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))


class UpdateProfileView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        if request.user.pk != pk:
            messages.error(request, 'Вы не можете редактировать чужой профиль')
            return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()
        messages.success(request, 'Профиль успешно обновлён')
        return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))


def delete_youtube_channel(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST' and request.user.pk == pk:
        user.youtube_channel = None
        user.save()
        # Очистка кэша YouTubeChannelStats для пользователя
        YouTubeChannelStats.objects.filter(user=user).delete()
        messages.success(request, 'YouTube-канал успешно удалён')
    else:
        messages.error(request, 'Вы не можете удалять YouTube-канал другого пользователя')
    return HttpResponseRedirect(reverse_lazy('users:profile', kwargs={'pk': pk}))


def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        if not image.content_type.startswith('image/'):
            messages.error(request, 'Недопустимый тип файла')
            return HttpResponse('Недопустимый тип файла', status=400)
        if image.size > 5 * 1024 * 1024:
            messages.error(request, 'Файл слишком большой (максимум 5MB)')
            return HttpResponse('Файл слишком большой', status=400)
        request.user.image = image
        request.user.save()
        messages.success(request, 'Изображение успешно загружено')
        return HttpResponse('Изображение загружено', status=200)
    messages.error(request, 'Ошибка загрузки изображения')
    return HttpResponse('Ошибка загрузки', status=400)


def extract_username(channel_url):
    patterns = [
        r'(?:youtube\.com\/@|youtube\.com\/user\/|youtube\.com\/c\/)([^\/&?]+)',  # @имя, user/имя, c/имя
        r'(?:youtube\.com\/channel\/)([a-zA-Z0-9_-]{24,})',  # channel/ID
    ]
    for pattern in patterns:
        match = re.search(pattern, channel_url)
        if match:
            return match.group(1)
    return None

def get_user_info(user, request=None):
    """Получает данные о YouTube-канале пользователя через YouTube Data API."""
    channel_url = user.youtube_channel
    if not channel_url:
        print("Ошибка: YouTube-канал не указан")
        if request:
            messages.error(request, 'YouTube-канал не указан')
        return empty_youtube_data()

    username = extract_username(channel_url)
    if not username:
        print(f"Ошибка: Некорректный URL канала: {channel_url}")
        if request:
            messages.error(request, 'Некорректный URL YouTube-канала')
        return empty_youtube_data()

    print(f"Извлечённое имя канала: {username}")

    # Проверка кэша (обновляется раз в 24 часа)
    cache = YouTubeChannelStats.objects.filter(user=user).first()
    if cache and cache.updated_at > timezone.now() - timedelta(hours=24):
        print(f"Используется кэш для {username}: {cache.data}")
        return cache.data

    api_key = 'AIzaSyBG-ts9VMkNhKuznu5ZQQ4HQ76DX_2ZWOk'  # Лучше брать из .env
    result = empty_youtube_data()

    try:
        # Сначала пробуем найти через forUsername
        channels_url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet ,statistics&forUsername={username}&key={api_key}'
        response = requests.get(channels_url)

        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                print("Канал найден через forUsername")
                return process_and_save_channel_data(data['items'][0], user, api_key, result)

        # Если не найдено — пробуем как channel_id
        channels_url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet ,statistics&id={username}&key={api_key}'
        response = requests.get(channels_url)

        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                print("Канал найден через ID")
                return process_and_save_channel_data(data['items'][0], user, api_key, result)

        print(f"Канал не найден: {username}")
        if request:
            messages.warning(request, 'Канал не найден на YouTube')
        return result

    except requests.RequestException as e:
        error_message = f"Ошибка при запросе к YouTube API: {str(e)}"
        print(error_message)
        print(f"Ответ сервера: {e.response.text if e.response else 'Нет ответа'}")
        if request:
            messages.error(request, error_message)
        return result


def empty_youtube_data():
    return {
        'labels': [], 'subscribers': [], 'views': [], 'likes': [], 'comments': [],
        'title': '', 'description': '', 'thumbnail': '', 'videos': 0
    }


def get_user_info(user, request=None):
    """Получает данные о YouTube-канале через YouTube Data API."""
    channel_url = user.youtube_channel
    if not channel_url:
        print("Ошибка: YouTube-канал не указан")
        if request:
            messages.error(request, 'YouTube-канал не указан')
        return empty_youtube_data()

    username = extract_username(channel_url)
    if not username:
        print(f"Ошибка: Некорректный URL канала: {channel_url}")
        if request:
            messages.error(request, 'Некорректный URL YouTube-канала')
        return empty_youtube_data()

    print(f"Извлечённое имя канала: {username}")

    # Проверка кэша
    cache = YouTubeChannelStats.objects.filter(user=user).first()
    if cache and cache.updated_at > timezone.now() - timedelta(hours=24):
        print(f"Используется кэш для {username}: {cache.data}")
        return cache.data

    api_key = 'AIzaSyBG-ts9VMkNhKuznu5ZQQ4HQ76DX_2ZWOk'
    result = empty_youtube_data()

    try:
        # Сначала пытаемся найти через forHandle (новый способ вместо устаревшего forUsername)
        channels_url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&forHandle={username}&maxResults=1&key={api_key}'
        response = requests.get(channels_url)

        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                print("Канал найден через forHandle")
                return process_and_save_channel_data(data['items'][0], user, api_key, result)

        # Если не найдено — попробуем как channel_id
        channels_url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={username}&maxResults=1&key={api_key}'
        response = requests.get(channels_url)

        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                print("Канал найден через ID")
                return process_and_save_channel_data(data['items'][0], user, api_key, result)

        print(f"Канал не найден: {username}")
        if request:
            messages.warning(request, 'Канал не найден на YouTube')
        return result

    except requests.RequestException as e:
        error_message = f"Ошибка при запросе к YouTube API: {str(e)}"
        print(error_message)
        print(f"Ответ сервера: {e.response.text if e.response else 'Нет ответа'}")
        if request:
            messages.error(request, error_message)
        return result
    
def empty_youtube_data():
    """Возвращает шаблон пустых данных YouTube-канала."""
    return {
        'labels': [], 'subscribers': [], 'views': [], 'likes': [], 'comments': [],
        'title': '', 'description': '', 'thumbnail': '', 'videos': 0
    }


def process_and_save_channel_data(channel_data, user, api_key, result):
    """Обрабатывает данные канала и собирает статистику по последним видео."""
    snippet = channel_data['snippet']
    stats = channel_data['statistics']
    channel_id = channel_data['id']

    result.update({
        'title': snippet.get('title', ''),
        'description': snippet.get('description', ''),
        'thumbnail': snippet['thumbnails']['high'].get('url', ''),
        'subscribers': [int(stats.get('subscriberCount', 0))],
        'views': [int(stats.get('viewCount', 0))],
        'videos': int(stats.get('videoCount', 0))
    })

    # Получаем последние видео
    videos_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=12&order=date&key={api_key}'
    videos_response = requests.get(videos_url)
    videos_response.raise_for_status()
    videos_data = videos_response.json()

    video_ids = [item['id']['videoId'] for item in videos_data.get('items', []) if item.get('id', {}).get('videoId')]
    print(f"Найденные video_ids: {video_ids}")

    if video_ids:
        videos_stats_url = f'https://www.googleapis.com/youtube/v3/videos?part=statistics&id={",".join(video_ids)}&key={api_key}'
        videos_stats_response = requests.get(videos_stats_url)
        videos_stats_response.raise_for_status()
        videos_stats_data = videos_stats_response.json()

        labels = [item['snippet']['publishedAt'][:10] for item in videos_data['items'] if 'videoId' in item['id']]
        likes = [int(video['statistics'].get('likeCount', 0)) for video in videos_stats_data.get('items', [])]
        comments = [int(video['statistics'].get('commentCount', 0)) for video in videos_stats_data.get('items', [])]
        views = [int(video['statistics'].get('viewCount', 0)) for video in videos_stats_data.get('items', [])]

        result.update({
            'labels': labels[::-1],     # самые свежие слева
            'likes': likes[::-1],
            'comments': comments[::-1],
            'views': views[::-1],
        })

    # Сохраняем в кэш
    YouTubeChannelStats.objects.update_or_create(
        user=user,
        channel_id=channel_id,
        defaults={'data': result}
    )

    print(f"Сохранено в кэш: {result}")
    return result

def get_youtube_stats_for_ai(user):
    if not user.youtube_channel:
        return {}
    stats = YouTubeChannelStats.objects.filter(user=user).first()
    if stats and stats.updated_at > timezone.now() - timedelta(hours=24):
        return stats.data
    else:
        return {}