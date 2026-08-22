from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Book, Review

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
        book_id = self.context.get("book_id")
        user = getattr(request, "user", None)
   
        if book_id is not None and user is not None:
            if Review.objects.filter(book_id=book_id, user=user).exists():
                raise serializers.ValidationError("You have already reviewed this book.")

        return attrs

    def create(self, validated_data):
        book_id = validated_data.pop("book_id", self.context["book_id"])
        user = validated_data.pop("user", self.context["request"].user)
        return Review.objects.create(book_id=book_id, user=user, **validated_data)
