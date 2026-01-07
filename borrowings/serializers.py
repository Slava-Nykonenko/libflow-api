from datetime import date

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from borrowings.models import Borrowing
from user.serializers import UserListSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "expected_return_date",
            "actual_return_date",
            "book",
        )
        read_only_fields = ("id", "actual_return_date")

    def validate(self, data):
        book = data.get("book")
        if book.inventory <= 0:
            raise ValidationError({"book": "This book is currently out of stock."})

        expected_return = data.get("expected_return_date")
        if expected_return and expected_return <= date.today():
            raise ValidationError(
                {"expected_return_date": "Expected return date cannot be in the past."}
            )

        return data


class BorrowingListSerializer(BorrowingSerializer):
    book_title = serializers.CharField(read_only=True, source="book.title")

    class Meta(BorrowingSerializer.Meta):
        fields = ("id", "borrow_date", "expected_return_date", "book_title")


class BorrowingRetrieveSerializer(BorrowingListSerializer):
    user = UserListSerializer(read_only=True)

    class Meta(BorrowingListSerializer.Meta):
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book_title",
            "user",
        )
