from django.contrib.auth.decorators import login_required
from django.urls import path
from users.views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    SaveYouTubeChannelView,
    UpdateProfileView,
    delete_youtube_channel,
    upload_image
)

app_name = 'users'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('registration/', UserRegistrationView.as_view(), name='registration'),
    path('profile/<int:pk>/', login_required(UserProfileView.as_view()), name='profile'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('delete_youtube/<int:pk>/', delete_youtube_channel, name='delete_youtube'),
    path('save_youtube_channel/<int:pk>/', SaveYouTubeChannelView.as_view(), name='save_youtube_channel'),
    path('update_profile/<int:pk>/', UpdateProfileView.as_view(), name='update_profile'),
    path('upload_image/', upload_image, name='upload_image'),
]