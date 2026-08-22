from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models


class Book(models.Model):
    """A practical book entry for the online bookstore."""

    title = models.CharField(max_length=255, db_index=True)
    author = models.CharField(max_length=255, db_index=True)
    description = models.TextField(max_length=1000, validators=[MaxLengthValidator(1000)])
    published_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def clean(self):
        super().clean()
        published_date = self.published_date
        if isinstance(published_date, date) and published_date > date.today():
            raise ValidationError({"published_date": "Published date cannot be in the future."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Review(models.Model):
    """Each user may have only one review per book; duplicate review creation should be rejected."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=1000, validators=[MaxLengthValidator(1000)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["book", "user"], name="unique_review_per_user_book")
        ]
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.rating is not None and not 1 <= self.rating <= 5:
            raise ValidationError({"rating": "Rating must be between 1 and 5."})
        if self.comment is not None and not self.comment.strip():
            raise ValidationError({"comment": "This field cannot be blank."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} reviewed {self.book}"
