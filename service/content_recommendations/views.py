import requests
import datetime
from django.shortcuts import render
from django.core.paginator import Paginator
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from common.views import TitleMixin

class IndexView(TitleMixin, TemplateView):
    template_name = 'content_recommendations/index.html'
    title = 'Welcome'

class RatesView(TitleMixin, TemplateView):
    template_name = 'content_recommendations/rates.html'
    title = 'Rates'

def trending_videos(request):
    youtube_videos = get_youtube_videos()

    # Создание пагинатора для списка видео с YouTube
    youtube_paginator = Paginator(youtube_videos, 6)
    youtube_page_number = request.GET.get('youtube_page')
    youtube_page_obj = youtube_paginator.get_page(youtube_page_number)

    # Получение списка видео с VK
    vk_videos = get_vk_videos()

    # Создание пагинатора для списка видео с VK
    vk_paginator = Paginator(vk_videos, 6)
    vk_page_number = request.GET.get('vk_page')  # Исправлено на 'vk_page'
    vk_page_obj = vk_paginator.get_page(vk_page_number)

    return render(request, 'content_recommendations/trending_videos.html', {
        'youtube_page_obj': youtube_page_obj,
        'vk_page_obj': vk_page_obj  # Исправлено на 'vk_page_obj'
    })

def get_vk_videos():
    access_token = 'vk1.a.4iIUJE46eZAdXxlY-5yS-drisFqUWkhwauTgiNgAXU0iMSoABdFeQW4MPHvdVrAbb4QkkqIrltXCjZHLvX0oLPJPTI8ug3ctRJdOy4FPEb1muMGHKW_EVxdI38nE3GJZyv-KYij19kOkaOlmF2mlx1D4HwpoGouIJPohQaTgW-ziOrW_gV2SRNhDkG4N3KLau-s_VGBT7_HQ0y_EmewWdg'
    api_version = '5.131'
    count = 50  # количество видео

    response = requests.get(
        'https://api.vk.com/method/video.getPopular',
        params={
            'access_token': access_token,
            'v': api_version,
            'count': count,
            'adult': 0,  # исключаем видео с возрастными ограничениями
            'extended': 1  # получаем расширенную информацию о видео
        }
    )

    vk_videos = []
    items = response.json().get('response', {}).get('items', [])
    for item in items:
        vk_video = {
            'title': item.get('title', 'Без названия'),
            'thumbnail': item.get('photo_320', ''),  # использование меньшего изображения для миниатюры
            'link': f"https://vk.com/video{item.get('owner_id', '')}_{item.get('id', '')}",
            'views': item.get('views', 0),
            'published_at': datetime.datetime.fromtimestamp(item.get('date', 0)) if item.get('date') else None,
            'description': item.get('description', '')
        }
        vk_videos.append(vk_video)
    return vk_videos

def get_youtube_videos():
    api_key = 'AIzaSyBG-ts9VMkNhKuznu5ZQQ4HQ76DX_2ZWOk'
    url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&maxResults=50&key={api_key}'

    response = requests.get(url)
    data = response.json()

    videos = []

    for item in data.get('items', []):
        video = {
            'title': item['snippet'].get('title', 'Без названия'),
            'thumbnail': item['snippet']['thumbnails']['high'].get('url', '') if 'thumbnails' in item['snippet'] else '',
            'link': f"https://www.youtube.com/watch?v={item.get('id', '')}",
            'views': item['statistics'].get('viewCount', '0') if 'statistics' in item else '0',
            'published_at': None
        }
        if 'snippet' in item and 'publishedAt' in item['snippet']:
            try:
                video['published_at'] = datetime.datetime.strptime(item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
            except (ValueError, TypeError):
                video['published_at'] = None
        videos.append(video)
    return videos