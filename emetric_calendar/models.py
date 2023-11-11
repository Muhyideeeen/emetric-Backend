from django.contrib.auth import get_user_model
from django.db import models

from tasks.models.detail import Task

User = get_user_model()


class UserScheduledEventCalendar(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(
        User, to_field="user_id", on_delete=models.CASCADE
    )
    task = models.ForeignKey(
        Task, to_field="task_id", on_delete=models.CASCADE
    )
    is_free = models.BooleanField(default=False)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    objects = models.Manager()

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name


class Holiday(models.Model):
    """Keeps track of holidays in the system"""

    name = models.CharField(max_length=255)
    date = models.DateField(db_index=True, unique=True)

    objects = models.Manager()

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return self.date.strftime("%Y-%m-%d")

    def delete_related_tasks(self):
        """Delete all related tasks"""
        Task.objects.filter(start_date=self.date).delete()
