from django.core.management.base import BaseCommand
from django.utils import timezone
from siriusyogaclass.core.models import Booking
from siriusyogaclass.core.utils import send_class_reminder
import datetime


class Command(BaseCommand):
    help = 'Send class reminders — 24h and 1h before sessions'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        sent = 0

        # 24-hour reminders
        tomorrow = (now + datetime.timedelta(hours=24)).date()
        tomorrow_hour = (now + datetime.timedelta(hours=24)).hour
        bookings_24h = Booking.objects.filter(
            session__date=tomorrow,
            session__start_time__hour=tomorrow_hour,
            status='accepted',
            payment_status__in=['paid', 'free'],
        ).select_related('user', 'yoga_class', 'session', 'yoga_class__instructor')
        for b in bookings_24h:
            send_class_reminder(b, 24)
            sent += 1

        # 1-hour reminders
        in_one_hour = now + datetime.timedelta(hours=1)
        bookings_1h = Booking.objects.filter(
            session__date=in_one_hour.date(),
            session__start_time__hour=in_one_hour.hour,
            status='accepted',
            payment_status__in=['paid', 'free'],
        ).select_related('user', 'yoga_class', 'session', 'yoga_class__instructor')
        for b in bookings_1h:
            send_class_reminder(b, 1)
            sent += 1

        self.stdout.write(self.style.SUCCESS(f'Sent {sent} reminder emails.'))
