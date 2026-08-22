import logging
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Book, Review

logger = logging.getLogger(__name__)

User = get_user_model()


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "published_date"]


class BookDetailSerializer(serializers.ModelSerializer):
    average_rating = serializers.DecimalField(read_only=True, max_digits=4, decimal_places=2)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "description",
            "published_date",
            "created_at",
            "average_rating",
            "review_count",
        ]


class ReviewSerializer(serializers.ModelSerializer):

    book_title = serializers.CharField(source="book.title", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "book_title",
            "user_name",
            "rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "book_title", "user_name", "created_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        book = self.context.get("book")
        user = getattr(request, "user", None)

        if book is not None and user is not None:
            if Review.objects.filter(book=book, user=user).exists():
                logger.info(
                    f"User '{user}' attempted to review book {book} which was already reviewed by them."
                )
                raise serializers.ValidationError("You have already reviewed this book.")
        return attrs

    def create(self, validated_data):
        try:
            book = validated_data.pop("book", self.context["book"])
            user = validated_data.pop("user", self.context["request"].user)
            review = Review.objects.create(book=book, user=user, **validated_data)
            logger.info(
                f"Review created by user '{user}' for book {book}: Review ID {review.id}"
            )
            return review
        except Exception as e:
            logger.error(f"An error occurred while creating the review: {str(e)}")
            raise serializers.ValidationError(f"An error occurred while creating the review: {str(e)}")
