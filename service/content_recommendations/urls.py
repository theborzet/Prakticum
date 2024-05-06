from django.contrib.auth.decorators import login_required
from django.urls import path

from content_recommendations.views import trending_videos, RatesView

app_name = 'content_recommendations'

urlpatterns = [
    path('', trending_videos, name='trend'),
    path('rates/', RatesView.as_view(), name='rates'),
    # path('registration/', UserRegistrationView.as_view(), name='registration'),
    # # path('profile/<int:pk>/', login_required(UserProfileView.as_view()), name='profile'), #в pk передаётся id пользователя
    # path('logout/', UserLogoutView.as_view(), name='logout'),
    # # path('verify/<str:email>/<uuid:code>', EmailVerificationView.as_view(), name='email_verification'),

]

