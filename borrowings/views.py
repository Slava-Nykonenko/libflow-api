from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from borrowings.models import Borrowing
from borrowings.notifications import send_telegram_notification
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

            message = (
                f"<b>A new borrowing!</b>\n"
                f"User: {borrowing.user.email}\n"
                f"Book: {book.title}\n"
                f"Expected return date: {borrowing.expected_return_date}"
            )
            send_telegram_notification(message)

    @action(detail=True, methods=["post"], url_path="return")
    def book_return(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date:
            return Response(
                {"detail": "This book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            borrowing.actual_return_date = timezone.now().date()
            borrowing.save()

            book = borrowing.book
            book.inventory += 1
            book.save()

            message = (
                f"<b>A book returned!</b>\n"
                f"User: {borrowing.user.email}\n"
                f"Book: {book.title}"
            )
            send_telegram_notification(message)

        return Response(
            {"detail": "The book returned successfully."}, status=status.HTTP_200_OK
        )
