from django.urls import path
from .views import BookDetailView, BookListView, BookReviewListCreateView

urlpatterns = [
    path("books/", BookListView.as_view(), name="book-list"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book-detail"),
    path("books/<int:pk>/reviews/", BookReviewListCreateView.as_view(), name="book-review-list-create"),
]
