from django.contrib import admin
from users.models import CustomUser

# Register your models here.

@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username',)
    

# @admin.register(EmailVerification)
# class EmailVerificationAdmin(admin.ModelAdmin):
#     list_display = ('code', 'user', 'expiration')
#     fields = ('code', 'user', 'expiration', 'created')
#     readonly_fields = ('created', )