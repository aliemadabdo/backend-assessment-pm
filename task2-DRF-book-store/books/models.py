from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Book(models.Model):
    """A practical book entry for the online bookstore."""

    title = models.CharField(max_length=255, db_index=True)
    author = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    published_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Review(models.Model):
    """Each user may have only one review per book; duplicate review creation should be rejected."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["book", "user"], name="unique_review_per_user_book")
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} reviewed {self.book}"
