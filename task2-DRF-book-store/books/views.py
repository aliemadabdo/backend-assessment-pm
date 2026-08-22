from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from django.core.exceptions import ObjectDoesNotExist

from .models import Book, Review
from .serializers import BookDetailSerializer, BookListSerializer, ReviewSerializer


class BookListView(ListAPIView):
    """Return a paginated list of books with review metadata."""

    serializer_class = BookListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["title", "author"]
    ordering_fields = ["title", "published_date"]
    filterset_fields = {
        'author': ['icontains'],
        'published_date': ['gte', 'lte'],
    }

    def get_queryset(self):
        # If this is the DRF documentation view, return no results
        if getattr(self, "swagger_fake_view", False):
            return Book.objects.none()

        # we only fetch minimal fields for listing performance;
        return Book.objects.only("id", "title", "author", "published_date")

    @extend_schema(
        tags=["Books"],
        parameters=[
            # Search
            OpenApiParameter(
                name="search",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search by book title or author. Example: ?search=Hemingway",
            ),
            # Ordering
            OpenApiParameter(
                name="ordering",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list for ordering. Options: 'title', 'published_date', prefix with '-' for descending order. Example: ?ordering=-published_date,title",
            ),
            # Filter: author
            OpenApiParameter(
                name="author__icontains",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter books by case-insensitive fragment of the author's name. Example: ?author__icontains=doe",
            ),
            # Filter: published_date_gte
            OpenApiParameter(
                name="published_date__gte",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter books published on or after a specific date (YYYY-MM-DD). Example: ?published_date__gte=2022-01-01",
            ),
            # Filter: published_date_lte
            OpenApiParameter(
                name="published_date__lte",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter books published on or before a specific date (YYYY-MM-DD). Example: ?published_date__lte=2023-01-01",
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            return Response({"detail": "An error occurred while fetching books."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BookDetailView(RetrieveAPIView):
    """Return the details for a single book including average rating and review count."""

    serializer_class = BookDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Book.objects.none()
        return Book.objects.annotate(average_rating=Avg("reviews__rating"), review_count=Count("reviews"))

    @extend_schema(tags=["Books"])
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return Response({"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": "An error occurred while fetching the book details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookReviewListCreateView(ListCreateAPIView):
    """List and create reviews for a specific book."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        return (
            Review.objects
            .filter(book_id=self.kwargs["pk"])
            .select_related("book", "user")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["book_id"] = self.kwargs["pk"]  # for Clarity and testability in serializer
        return context

    @extend_schema(
        tags=["Reviews"],
        examples=[
            OpenApiExample(
                "Review creation example",
                value={"rating": 5, "comment": "Excellent read!"},
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            return Response({"detail": "An error occurred while creating the review."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(tags=["Reviews"])
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": "An error occurred while fetching the reviews."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)