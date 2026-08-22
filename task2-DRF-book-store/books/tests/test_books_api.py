import pytest
from rest_framework.test import APIClient

from books.tests.factories import BookFactory, ReviewFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestBooksAPI:
    def test_book_list_requires_authentication(self):
        client = APIClient()

        response = client.get("/api/books/")

        assert response.status_code == 401

    def test_book_list_supports_search_ordering_filtering_and_pagination(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)

        BookFactory(title="Zeta Blue", author="Mira", published_date="2023-01-01")
        BookFactory(title="Alpha Red", author="Avery", published_date="2022-02-02")
        BookFactory(title="Alpha Green", author="Mara", published_date="2024-03-03")
        for i in range(12):
            BookFactory(title=f"Book {i}", author="Archive", published_date="2021-01-01")

        response = client.get("/api/books/?search=Alpha&ordering=title&author__icontains=a&published_date__gte=2022-01-01&published_date__lte=2025-12-31")

        assert response.status_code == 200
        assert response.data["count"] == 2
        assert [book["title"] for book in response.data["results"]] == ["Alpha Green", "Alpha Red"]

        paginated_response = client.get("/api/books/")

        assert paginated_response.status_code == 200
        assert "results" in paginated_response.data
        assert paginated_response.data["count"] >= 15
        assert len(paginated_response.data["results"]) == 10

    def test_book_detail_requires_authentication(self):
        client = APIClient()
        book = BookFactory()

        response = client.get(f"/api/books/{book.id}/")

        assert response.status_code == 401

    def test_book_detail_returns_expected_values(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)

        book = BookFactory(title="Django Deep Dive", author="Jane Jones")
        ReviewFactory(book=book, rating=5)
        ReviewFactory(book=book, rating=3)

        response = client.get(f"/api/books/{book.id}/")

        assert response.status_code == 200
        assert response.data["id"] == book.id
        assert response.data["title"] == "Django Deep Dive"
        assert response.data["author"] == "Jane Jones"
        assert response.data["description"] == book.description
        assert float(response.data["average_rating"]) == 4.0
        assert response.data["review_count"] == 2
