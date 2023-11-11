from django.contrib.auth import get_user_model
from django.db import models

from tracking.models.base_tracking_model import TrackingBaseModel

User = get_user_model()


class PasswordResetTrackingManager(models.Manager):
    def create_password_reset_tracking(self, **kwargs):
        return self.create(**kwargs)


class PasswordResetTracking(TrackingBaseModel):

    is_password_changed: bool = models.BooleanField(default=False)

    objects = PasswordResetTrackingManager()
