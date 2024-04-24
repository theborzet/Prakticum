# from celery import shared_task
# from django.utils.timezone import now
# from datetime import timedelta
# import uuid
# from users.models import CustomUser


# @shared_task
# def send_email_verification(user_id):
#     user = CustomUser.objects.get(id=user_id)
#     expitarion = now() + timedelta(hours=48)
#     # record = EmailVerification.objects.create(code=uuid.uuid4(), user=user, expiration=expitarion)
#     # record.send_verification_email()