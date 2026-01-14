from typing import Type

from rest_framework.viewsets import ModelViewSet

from books.models import Book
from books.permissions import IsAdminAllOrAuthenticatedReadOnly
from books.serializers import BookSerializer, BookListSerializer


# Create your views here.
class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = (IsAdminAllOrAuthenticatedReadOnly,)

    def get_serializer_class(self) -> Type[BookListSerializer | BookSerializer]:
        if self.action == "list":
            return BookListSerializer
        return BookSerializer
