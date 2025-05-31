from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from users.models import CustomUser
from users.views import get_youtube_stats_for_ai

# G4F
from g4f.client import Client
from g4f.Provider import You
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

def chat_view(request):
    return render(request, 'ai_chat/chat.html')


@csrf_exempt
@require_GET
def chat_api(request):
    user_message = request.GET.get('message', '').strip()
    user_id = request.GET.get('user_id')

    if not user_message:
        return JsonResponse({'reply': 'Пожалуйста, введите сообщение.'}, status=400)

    youtube_data = {}
    if user_id:
        try:
            user = CustomUser.objects.get(id=user_id)
            youtube_data = get_youtube_stats_for_ai(user)
        except CustomUser.DoesNotExist:
            return JsonResponse({'reply': 'Пользователь не найден.'}, status=404)
        except Exception as e:
            logger.error(f"Ошибка получения данных пользователя: {str(e)}")
            youtube_data = {}

    system_prompt = (
        "Вы — эксперт по YouTube-аналитике.\n"
        f"Данные канала: {youtube_data}\n\n"
        "На основе этих данных отвечайте на вопросы по улучшению контента.\n"
        "Отвечайте на русском языке."
    )

    full_prompt = f"{system_prompt}\n\nПользователь спрашивает: {user_message}"

    try:
        client = Client()
        response = client.chat.completions.create(
            model="claude-3-haiku",  # или claude-3-haiku, llama3
            messages=[{"role": "user", "content": full_prompt}],
        )
        bot_reply = response.choices[0].message.content.strip()
    except IndexError:
        logger.error("Нет ответа от ИИ")
        return JsonResponse({'reply': 'Нет ответа от модели.'}, status=500)
    except Exception as e:
        logger.error(f"Ошибка G4F: {str(e)}")
        return JsonResponse({'reply': 'Ошибка сервера. Попробуйте позже.'}, status=500)

    return JsonResponse({'reply': bot_reply})