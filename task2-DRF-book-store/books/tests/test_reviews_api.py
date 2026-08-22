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

        # Should reject unauthenticated access to review list
        response = client.get(f"/api/books/{book.id}/reviews/")

        assert response.status_code == 401

    def test_review_list_returns_expected_values_in_order(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()
        # Review by older user (should be second after ordering)
        older_review = ReviewFactory(book=book, user=UserFactory(username="older"), rating=3, comment="Older")
        # Most recent review by newer user (should appear first, assuming reverse chronological order)
        recent_review = ReviewFactory(book=book, user=UserFactory(username="newer"), rating=5, comment="Newer")

        # Should return list of reviews ordered so newest review is first
        response = client.get(f"/api/books/{book.id}/reviews/")

        assert response.status_code == 200
        # Verify fields of the most recent review
        assert response.data["results"][0]["book_title"] == book.title
        assert response.data["results"][0]["user_name"] == recent_review.user.username
        assert response.data["results"][0]["rating"] == recent_review.rating
        assert response.data["results"][0]["comment"] == recent_review.comment
        # Check older review comes after in the list
        assert response.data["results"][1]["comment"] == older_review.comment

    def test_authenticated_user_can_create_review(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()

        # Should allow authenticated user to create a valid review
        response = client.post(
            f"/api/books/{book.id}/reviews/",
            {"rating": 5, "comment": "Fantastic"},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["rating"] == 5
        assert response.data["comment"] == "Fantastic"
        assert response.data["user_name"] == user.username
        # Review must actually exist in database
        assert Review.objects.filter(book=book, user=user).count() == 1

    def test_review_creation_validates_comment_and_rating(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()

        invalid_payloads = [
            # Comment is empty
            {"rating": 5, "comment": ""},
            # Comment exceeds 1000 character limit
            {"rating": 5, "comment": "x" * 1001},
            # Rating is below minimum allowed (1)
            {"rating": 0, "comment": "Nope"},
            # Rating is above maximum allowed (5)
            {"rating": 6, "comment": "Nope"},
            # Rating is empty
            {"rating": None, "comment": "Missing rating"},
        ]

        # All invalid inputs should be rejected with 400 error
        for payload in invalid_payloads:
            response = client.post(f"/api/books/{book.id}/reviews/", payload, format="json")
            assert response.status_code == 400

    def test_duplicate_review_is_rejected(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()
        # User already has a review for this book
        ReviewFactory(book=book, user=user, rating=4)

        # Submitting a second review for same book should fail
        response = client.post(
            f"/api/books/{book.id}/reviews/",
            {"rating": 5, "comment": "Duplicate"},
            format="json",
        )

        assert response.status_code == 400
        # Error message should indicate a duplicate/unique constraint issue
        assert "already reviewed" in str(response.data).lower()

    def test_review_belongs_to_authenticated_user(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        book = BookFactory()

        # User tries to submit a review; review should be credited to them
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
        # Unauthenticated GET to reviews endpoint
        response = client.get(f"/api/books/{book.id}/reviews/")
        assert response.status_code == 401

    def test_invalid_book_id_returns_404(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)

        # Use an ID that does not exist for GET
        invalid_book_id = 99999
        response = client.get(f"/api/books/{invalid_book_id}/reviews/")
        assert response.status_code == 404

        # Use an ID that does not exist for POST
        response_post = client.post(
            f"/api/books/{invalid_book_id}/reviews/",
            {"rating": 5, "comment": "Nonexistent"},
            format="json",
        )
        assert response_post.status_code == 404

#