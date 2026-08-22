import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates a default superuser if one doesn't already exist. Safe to run multiple times."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.environ.get("DEFAULT_ADMIN_USERNAME", "admin"))
        parser.add_argument("--email", default=os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@example.com"))
        parser.add_argument("--password", default=os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123"))

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        email = options["email"]
        password = options["password"]

        if User.objects.filter(username=username).exists():
            print(f"Superuser '{username}' already exists, skipping.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser created: {username} / {password}")
   