from django.db.models import Prefetch
from rest_framework import generics
from rest_framework.viewsets import ModelViewSet

from borrowings.models import Borrowing
from user.models import User
from user.serializers import (
    UserSerializer,
    UserListSerializer,
    UserRetrieveSerializer,
)


# Create your views here.
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        elif self.action == "retrieve":
            return UserRetrieveSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "retrieve":
            active_borrowings = Borrowing.objects.filter(
                actual_return_date__isnull=True
            ).select_related("book")

            queryset = queryset.prefetch_related(
                Prefetch("borrowings", queryset=active_borrowings),
            )
        if not self.request.user.is_staff:
            return queryset.filter(id=self.request.user.id).distinct()
        return queryset


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
