from django.db import transaction
from rest_framework.viewsets import ModelViewSet

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingRetrieveSerializer,
)


# Create your views here.
class BorrowingViewSet(ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        elif self.action == "retrieve":
            return BorrowingRetrieveSerializer
        return BorrowingSerializer

    def get_queryset(self):
        queryset = self.queryset.select_related("user", "book")
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        if self.action in ("list", "retrieve"):
            user_id = self.request.query_params.get("user_id")
            is_active = self.request.query_params.get("is_active")
            if user_id:
                queryset = queryset.filter(user=user_id)
            if is_active:
                queryset = queryset.filter(
                    actual_return_date__isnull=is_active.lower() == "true"
                )
        return queryset

    def perform_create(self, serializer):
        with transaction.atomic():
            borrowing = serializer.save(user=self.request.user)
            book = borrowing.book
            book.inventory -= 1
            book.save()
