from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from borrowings.models import Borrowing
import requests
from django.conf import settings


@shared_task
def send_telegram_notification(message: str) -> None:
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Telegram error: {e}")


@shared_task
def borrowing_overdue() -> None:
    borrowings = Borrowing.objects.filter(
        Q(actual_return_date__isnull=True)
        & Q(expected_return_date__lt=timezone.now().date())
    )
    if borrowings:
        message = f"<b>Expired borrowings:</b>\n"
        for i, borrowing in enumerate(borrowings, start=1):
            message += (
                f"\n{i}. Borrowing ID: {borrowing.id}\n"
                f"User: {borrowing.user.first_name} {borrowing.user.last_name}\n"
                f"User's e-mail: {borrowing.user.email}\n"
                f"Book: {borrowing.book.title}\n"
            )
        send_telegram_notification.apply_async(args=[message])
    else:
        send_telegram_notification.apply_async(args=["<b>No expired borrowings!</b>"])
