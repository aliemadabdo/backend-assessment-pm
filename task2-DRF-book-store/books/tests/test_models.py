from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from books.models import Book, Review
from books.tests.factories import BookFactory, ReviewFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestModels:
    def test_book_fields_are_validated(self):
        invalid_cases = [
            # Title is empty
            {"title": "", "author": "Jane Doe", "description": "A good read.", "published_date": date.today()},

            # Title exceeds 255 characters
            {"title": "x" * 256, "author": "Jane Doe", "description": "A good read.", "published_date": date.today()},

            # Author is empty
            {"title": "Clean Code", "author": "", "description": "A good read.", "published_date": date.today()},

            # Author exceeds 255 characters
            {"title": "Clean Code", "author": "x" * 256, "description": "A good read.", "published_date": date.today()},

            # Description is empty
            {"title": "Clean Code", "author": "Jane Doe", "description": "", "published_date": date.today()},

            # Description exceeds 1000 characters
            {"title": "Clean Code", "author": "Jane Doe", "description": "x" * 1001, "published_date": date.today()},

            # Published date is None
            {"title": "Clean Code", "author": "Jane Doe", "description": "A good read.", "published_date": None},

            # Published date is in the future
            {"title": "Clean Code", "author": "Jane Doe", "description": "A good read.", "published_date": date.today() + timedelta(days=1)},
        ]

        for payload in invalid_cases:
            book = Book(**payload)
            with pytest.raises(ValidationError):
                book.full_clean()

    def test_book_created_at_is_auto_generated(self):
        book = BookFactory()

        assert book.created_at is not None
        assert book.created_at <= timezone.now()

    def test_review_fields_are_validated(self):
        book = BookFactory()
        user = UserFactory()

        invalid_cases = [
            # Book is None
            {"book": None, "user": user, "rating": 4, "comment": "Good"},

            # User is None
            {"book": book, "user": None, "rating": 4, "comment": "Good"},

            # Rating is None
            {"book": book, "user": user, "rating": None, "comment": "Good"},

            # Rating is less than minimum allowed (1)
            {"book": book, "user": user, "rating": -1, "comment": "Good"},

            # Rating exceeds maximum allowed (5)
            {"book": book, "user": user, "rating": 6, "comment": "Good"},

            # Comment is empty
            {"book": book, "user": user, "rating": 3, "comment": ""},

            # Comment exceeds 1000 characters
            {"book": book, "user": user, "rating": 3, "comment": "x" * 1001},
        ]

        for payload in invalid_cases:
            review = Review(**payload)
            with pytest.raises(ValidationError):
                review.full_clean()

    def test_review_created_at_is_auto_generated(self):
        review = ReviewFactory()

        assert review.created_at is not None
        assert review.created_at <= timezone.now()

    def test_review_uniqueness(self):
        user = UserFactory()
        book = BookFactory()
        # Create the initial review for uniqueness constraint
        ReviewFactory(user=user, book=book)

        # Attempt to create another review with the same user and book (should fail)
        review = Review(user=user, book=book, rating=4, comment="Another review")

        with pytest.raises(ValidationError):
            review.full_clean()

    def test_book_str(self):
        book = BookFactory(title="Django for Everyone")
        # __str__ should return the book's title
        assert str(book) == "Django for Everyone"

    def test_review_str(self):
        review = ReviewFactory(comment="Lovely book")
        # __str__ should return "{user} reviewed {book}"
        assert str(review) == f"{review.user} reviewed {review.book}"
