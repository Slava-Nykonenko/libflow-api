from django.db import models
from django.db.models import CheckConstraint, F, Q

from books.models import Book
from user.models import User


# Create your models here.
class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowings")

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(expected_return_date__gte=F("borrow_date")),
                name="expected_return_after_borrow",
            ),
            CheckConstraint(
                check=Q(actual_return_date__gte=F("borrow_date")),
                name="actual_return_after_borrow",
            ),
        ]
        ordering = ["-id"]

    def __str__(self):
        return (
            f"{self.book.title} borrowed by {self.user.first_name} "
            f"{self.user.last_name}"
        )
