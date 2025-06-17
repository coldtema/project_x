from celery import shared_task
from apps.core.utils import NotificationsClearer


@shared_task
def clear_notifications():
    NotificationsClearer(True).run()
    NotificationsClearer(False).run()
    return True

