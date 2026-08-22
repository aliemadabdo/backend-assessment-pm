# books/management/commands/seed_books.py
from datetime import date

from django.core.management.base import BaseCommand

from books.models import Book


BOOKS = [
    {
        "title": "The Silent Algorithm",
        "author": "Mona Farid",
        "description": "A software engineer uncovers a hidden pattern in her company's codebase that predicts market crashes before they happen.",
        "published_date": date(2018, 3, 12),
    },
    {
        "title": "Sands of Alexandria",
        "author": "Karim El-Sayed",
        "description": "A historical novel following a young librarian protecting ancient manuscripts during the fall of the great library.",
        "published_date": date(2015, 7, 4),
    },
    {
        "title": "The Last Compiler",
        "author": "Jonas Berg",
        "description": "In a future where AI writes all software, one programmer discovers a bug that could end civilization.",
        "published_date": date(2021, 11, 20),
    },
    {
        "title": "Threads of the Nile",
        "author": "Layla Hassan",
        "description": "A multi-generational family saga set along the banks of the Nile, spanning three wars and one unbreakable promise.",
        "published_date": date(2012, 5, 30),
    },
    {
        "title": "Concurrent Minds",
        "author": "David Okonkwo",
        "description": "A philosophical thriller exploring consciousness through the lens of distributed systems and race conditions.",
        "published_date": date(2019, 9, 15),
    },
    {
        "title": "The Cairo Cipher",
        "author": "Youssef Adel",
        "description": "A cryptographer races against time to decode a centuries-old cipher hidden beneath the streets of old Cairo.",
        "published_date": date(2017, 1, 22),
    },
    {
        "title": "Migrations",
        "author": "Sara Ibrahim",
        "description": "A quiet, character-driven story about a database engineer rebuilding her life after a career-ending mistake.",
        "published_date": date(2020, 6, 8),
    },
    {
        "title": "The Reader's Ledger",
        "author": "Omar Nabil",
        "description": "A mystery set inside a small-town bookstore, where the marginalia in old books starts predicting real events.",
        "published_date": date(2014, 10, 3),
    },
    {
        "title": "Echoes in the Stack",
        "author": "Nadia Fahmy",
        "description": "A young hacker infiltrates a corrupt corporation only to find the real conspiracy runs deeper than the code.",
        "published_date": date(2022, 2, 14),
    },
    {
        "title": "Desert Protocol",
        "author": "Ahmed Zaki",
        "description": "An embedded systems engineer stranded in the desert must repair a failing satellite uplink before rescue arrives.",
        "published_date": date(2016, 8, 27),
    },
]


class Command(BaseCommand):
    help = "Seeds the database with 10 sample books. Safe to run multiple times (skips duplicates by title)."

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        print("Seeding Books...")
        for book_data in BOOKS:
            _, created = Book.objects.get_or_create(
                title=book_data["title"],
                defaults=book_data,
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1
   
        print(f"Seeding complete: {created_count} created, {skipped_count} already existed.")
   