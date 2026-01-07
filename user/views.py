from rest_framework import generics
from rest_framework.viewsets import ModelViewSet

from user.models import User
from user.serializers import (
    UserSerializer,
    UserListSerializer,
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
        return UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
