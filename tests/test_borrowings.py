from datetime import timedelta
from django.test import TestCase
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer, BorrowingRetrieveSerializer
from tests.test_books import sample_book
from user.models import User

BORROWINGS_URL = reverse("borrowings_app:borrowing-list")


class AnonymousBorrowingTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BORROWINGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


def borrowing_create(**params) -> Borrowing:
    defaults = {
        "expected_return_date": timezone.now().date() + timedelta(days=1),
        "book": sample_book(),
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


def sample_user_create() -> User:
    return get_user_model().objects.create_user(
        email=f"{uuid4()}@example.com",
        password=f"{uuid4()}@password",
    )


class AuthenticatedUserBorrowingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="usertest@example.com",
            password="test@password",
        )
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.user.delete()

    def test_create_borrowing(self):
        book_1 = sample_book()
        payload_1 = {
            "expected_return_date": timezone.now().date() + timedelta(days=1),
            "book": book_1.id,
        }
        book_2 = sample_book(title=f"{uuid4()}")
        user_2 = sample_user_create()
        borrowing_2 = borrowing_create(
            book=book_2,
            user=user_2,
        )
        res = self.client.post(BORROWINGS_URL, payload_1)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        book_1.refresh_from_db()
        self.assertEqual(book_1.inventory, 0)

        borrowing = Borrowing.objects.get(id=res.data["id"])
        res = self.client.get(BORROWINGS_URL)
        self.assertTrue(any(borrow["id"] == borrowing.id for borrow in res.data))
        self.assertFalse(any(borrow["id"] == borrowing_2.id for borrow in res.data))

    def test_create_invalid_borrowings(self):
        book = sample_book()
        payload = {
            "expected_return_date": timezone.now().date() - timedelta(days=1),
            "book": book.id,
        }
        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        book = sample_book()
        payload = {
            "expected_return_date": timezone.now().date(),
            "book": book.id,
        }
        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_borrowing(self):
        borrowing = BorrowingRetrieveSerializer(borrowing_create(user=self.user)).data
        url = reverse("borrowings_app:borrowing-detail", args=(borrowing["id"],))
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(borrowing, res.data)

    def test_borrowing_return(self):
        book = sample_book(inventory=0)  # Start with 0
        borrowing = borrowing_create(user=self.user, book=book)

        url = BORROWINGS_URL + f"{borrowing.id}/return/"
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        borrowing.refresh_from_db()
        self.assertEqual(borrowing.actual_return_date, timezone.now().date())

        book.refresh_from_db()
        self.assertEqual(book.inventory, 1)


class AdminBorrowingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admintest@example.com",
            password="admin#test@password",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_borrowing_filtering(self):
        user_1 = sample_user_create()
        user_2 = sample_user_create()
        borrowing_1 = BorrowingListSerializer(
            borrowing_create(user=user_1, book=sample_book())
        ).data
        borrowing_2 = BorrowingListSerializer(
            borrowing_create(user=user_2, book=sample_book())
        ).data
        res = self.client.get(BORROWINGS_URL)
        self.assertIn(borrowing_1, res.data)

        res = self.client.get(BORROWINGS_URL + f"?user_id={user_1.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(borrowing_1, res.data)
        self.assertNotIn(borrowing_2, res.data)

        self.client.get(BORROWINGS_URL + f"{borrowing_1['id']}/return/")
        res = self.client.get(BORROWINGS_URL + "?is_active=true")
        self.assertIn(borrowing_2, res.data)
        self.assertNotIn(borrowing_1, res.data)
