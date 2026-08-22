import pytest
from rest_framework.test import APIClient

from books.models import Review
from books.tests.factories import BookFactory, ReviewFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestReviewsAPI:
    def test_review_list_requires_authentication(self):
        client = APIClient()
        book = BookFactory()

        response = client.get(f"/api/books/{book.id}/reviews/")

        assert response.status_code == 401

    def test_review_list_returns_expected_values_in_order(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()
        older_review = ReviewFactory(book=book, user=UserFactory(username="older"), rating=3, comment="Older")
        recent_review = ReviewFactory(book=book, user=UserFactory(username="newer"), rating=5, comment="Newer")

        response = client.get(f"/api/books/{book.id}/reviews/")

        assert response.status_code == 200
        assert response.data["results"][0]["book_title"] == book.title
        assert response.data["results"][0]["user_name"] == recent_review.user.username
        assert response.data["results"][0]["rating"] == 5
        assert response.data["results"][0]["comment"] == "Newer"
        assert response.data["results"][1]["comment"] == older_review.comment

    def test_authenticated_user_can_create_review(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()

        response = client.post(
            f"/api/books/{book.id}/reviews/",
            {"rating": 5, "comment": "Fantastic"},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["rating"] == 5
        assert response.data["comment"] == "Fantastic"
        assert response.data["user_name"] == user.username
        assert Review.objects.filter(book=book, user=user).count() == 1

    def test_review_creation_validates_comment_and_rating(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()

        invalid_payloads = [
            {"rating": 5, "comment": ""},
            {"rating": 5, "comment": "x" * 1001},
            {"rating": 0, "comment": "Nope"},
            {"rating": 6, "comment": "Nope"},
        ]

        for payload in invalid_payloads:
            response = client.post(f"/api/books/{book.id}/reviews/", payload, format="json")
            assert response.status_code == 400

    def test_duplicate_review_is_rejected(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()
        ReviewFactory(book=book, user=user, rating=4)

        response = client.post(
            f"/api/books/{book.id}/reviews/",
            {"rating": 5, "comment": "Duplicate"},
            format="json",
        )

        assert response.status_code == 400
        assert "already reviewed" in str(response.data).lower()

    def test_review_belongs_to_authenticated_user(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()

        response = client.post(
            f"/api/books/{book.id}/reviews/",
            {"rating": 4, "comment": "OK"},
            format="json",
        )

        review = Review.objects.get(book=book, user=user)
        assert response.data["user_name"] == user.username
        assert review.user == user

    def test_unauthenticated_requests_return_401(self):
        client = APIClient()
        book = BookFactory()
        response = client.get(f"/api/books/{book.id}/reviews/")
        assert response.status_code == 401

    def test_invalid_book_id_returns_404(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)

        # Use an ID that does not exist
        invalid_book_id = 66666
        response = client.get(f"/api/books/{invalid_book_id}/reviews/")
        assert response.status_code == 404

        # Also test POST to invalid book id
        response_post = client.post(
            f"/api/books/{invalid_book_id}/reviews/",
            {"rating": 5, "comment": "Nonexistent"},
            format="json",
        )
        assert response_post.status_code == 404

# 