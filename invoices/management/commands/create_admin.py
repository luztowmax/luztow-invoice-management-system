
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create an initial production superuser"

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_ADMIN_USERNAME")
        email = os.getenv("DJANGO_ADMIN_EMAIL")
        password = os.getenv("DJANGO_ADMIN_PASSWORD")

        if not all([username, email, password]):
            raise CommandError(
                "DJANGO_ADMIN_USERNAME, "
                "DJANGO_ADMIN_EMAIL and "
                "DJANGO_ADMIN_PASSWORD must be configured."
            )

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                "Administrator already exists. No changes made."
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS("Production administrator created.")
        )
