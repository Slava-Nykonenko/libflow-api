from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer, BookListSerializer

BOOKS_URL = reverse("books:books-list")


def sample_book(**params) -> Book:
    defaults = {
        "title": "1984",
        "author": "George Orwell",
        "cover": "HARD",
        "inventory": 1,
        "daily_fee": 0.25,
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class UnauthenticatedBookTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BOOKS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


def detail_url(book_id):
    return reverse("books:books-detail", args=(book_id,))


class AuthenticatedBookTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="usertest@example.com",
            password="test@password",
        )
        self.client.force_authenticate(user=self.user)

    def test_books_list(self):
        sample_book()
        res = self.client.get(BOOKS_URL)
        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_book(self):
        book = sample_book()
        url = detail_url(book.id)

        res = self.client.get(url)

        serializer = BookSerializer(book)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_user_create_book_forbidden(self):
        payload = {
            "title": "1984",
            "author": "George Orwell",
            "cover": "HARD",
            "inventory": 1,
            "daily_fee": 0.25,
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admintest@example.com",
            password="admin#test@password",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_admin_create_book_success(self):
        payload = {
            "title": "1984",
            "author": "George Orwell",
            "cover": "HARD",
            "inventory": 1,
            "daily_fee": 0.25,
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_admin_put_patch_delete_book(self):
        book = sample_book()
        payload = {
            "title": "Harry Potter and The Phoenix Order",
            "author": "J.K. Rowling",
            "cover": "SOFT",
            "inventory": 2,
            "daily_fee": 0.20,
        }
        res = self.client.put(detail_url(book.pk), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.patch(
            detail_url(book.pk),
            {"id": book.pk, "title": "Harry Potter and The Philosopher's Stone"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.delete(detail_url(book.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
