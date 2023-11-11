from django.contrib import admin
from django.contrib.auth import get_user_model

from account.models import Role, EmailInvitation

User = get_user_model()

admin.site.register(User)
admin.site.register(Role)
admin.site.register(EmailInvitation)
