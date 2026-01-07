from django.urls import include, path
from rest_framework.routers import DefaultRouter

from user.views import UserViewSet, CreateUserView, ManageUserView

app_name = "user"

router = DefaultRouter()
router.register("", UserViewSet, basename="user")

urlpatterns = [
    path(
        "create/",
        CreateUserView.as_view(),
        name="user-create",
    ),
    path("me/", ManageUserView.as_view(), name="me"),
    path("", include(router.urls)),
]
