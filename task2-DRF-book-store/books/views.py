import logging
from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated

from .models import Book, Review
from .serializers import BookDetailSerializer, BookListSerializer, ReviewSerializer

logger = logging.getLogger(__name__)

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
        # For schema generation - out of test coverage
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
        logger.info("BookListView GET requested by user %s", request.user)
        return super().get(request, *args, **kwargs)

class BookDetailView(RetrieveAPIView):
    """Return the details for a single book including average rating and review count."""

    serializer_class = BookDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # for schema generation - out of test coverage
        if getattr(self, "swagger_fake_view", False):
            return Book.objects.none()
        return Book.objects.annotate(average_rating=Avg("reviews__rating"), review_count=Count("reviews"))

    @extend_schema(tags=["Books"])
    def get(self, request, *args, **kwargs):
        logger.info("BookDetailView GET requested for book id %s by user %s", kwargs.get("pk"), request.user)
        return super().get(request, *args, **kwargs)


class BookReviewListCreateView(ListCreateAPIView):
    """List and create reviews for a specific book."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # for schema generation - out of test coverage
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()

        book = get_object_or_404(Book, pk=self.kwargs["pk"])

        return (
            Review.objects
            .filter(book=book)
            .select_related("book", "user")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["book"] = get_object_or_404(Book, pk=self.kwargs["pk"])  # for Clarity and testability in serializer
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
        logger.info(
            "BookReviewListCreateView POST: Creating review for book id %s by user %s",
            kwargs.get("pk"), request.user
        )
        return super().post(request, *args, **kwargs)

    @extend_schema(tags=["Reviews"])
    def get(self, request, *args, **kwargs):
        logger.info(
            "BookReviewListCreateView GET: Listing reviews for book id %s by user %s",
            kwargs.get("pk"), request.user
        )
        return super().get(request, *args, **kwargs)