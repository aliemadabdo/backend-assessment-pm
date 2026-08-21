from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Book, Review


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "published_date", "created_at")
    search_fields = ("title", "author")
    list_filter = ("published_date",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("book__title", "user__username", "comment")
