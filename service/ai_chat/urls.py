from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    path('chat/', login_required(views.chat_view), name='chat'),
    path('api/chat/', login_required(views.chat_api), name='chat_api'),
]