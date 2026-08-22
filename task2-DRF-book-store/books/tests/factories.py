import factory
from django.contrib.auth import get_user_model

from books.models import Book, Review
from users.tests.factories import UserFactory

User = get_user_model()


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda n: f"Book {n}")
    author = factory.Sequence(lambda n: f"Author {n}")
    description = "A compelling story."
    published_date = "2024-01-01"


class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    book = factory.SubFactory(BookFactory)
    user = factory.SubFactory(UserFactory)
    rating = 5
    comment = "Excellent read."
