from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse
from django.utils.timezone import now


class CustomUser(AbstractUser):
    image = models.ImageField(upload_to='users_images', null=True, blank=True)
    is_verified_email = models.BooleanField(default=False)
    youtube_channel = models.URLField(max_length=200, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('users:profile', kwargs={'pk': self.pk})

class UserActivity(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=100)  # Например, "upload_video", "update_profile"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        
class YouTubeChannelStats(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    channel_id = models.CharField(max_length=100)
    data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'channel_id']
# class EmailVerification(models.Model):
#     code = models.UUIDField(unique=True)
#     user = models.ForeignKey(to=User, on_delete=models.CASCADE)
#     created = models.DateTimeField(auto_now_add=True)
#     expiration = models.DateTimeField()


#     def __str__(self) -> str:
#         return f'EmailVerification object for {self.user}'
    
#     def send_verification_email(self):
#         link = reverse('users:email_verification',kwargs={'email' : self.user.email, 'code' : self.code})
#         verification_link = f'{settings.DOMAIN_NAME}{link}'
#         subject = f'Подтверждение учетной записи для {self.user.username}'
#         message = 'Для подтверждения учетной записи для {} перейдите по ссылке {}'.format(
#             self.user.email,
#             verification_link
#         )
#         send_mail(
#                 subject=subject,
#                 message=message,
#                 from_email=settings.EMAIL_HOST_USER,
#                 recipient_list=[self.user.email],
#                 fail_silently=False,
#                 )
#     def is_expired(self):
#         return True if now() <= self.expiration else False