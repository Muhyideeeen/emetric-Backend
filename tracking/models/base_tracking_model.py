from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class TrackingBaseModel(models.Model):

    user: User = models.ForeignKey(User, to_field='user_id', on_delete=models.CASCADE)
    email: str = models.EmailField(max_length=255, blank=True, null=True)
    device: str = models.CharField(max_length=255, blank=True, null=True)
    os: str = models.CharField(max_length=255, blank=True, null=True)
    os_version: str = models.CharField(max_length=255, blank=True, null=True)
    browser: str = models.CharField(max_length=255, blank=True, null=True)
    browser_version: str = models.CharField(max_length=255, blank=True, null=True)
    ip_address: str = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['-id']

    def __str__(self):
        return self.email
