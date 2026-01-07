from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from user.views import UserViewSet, CreateUserView, ManageUserView

app_name = "user"

router = DefaultRouter()
router.register("", UserViewSet, basename="user")

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path(
        "create/",
        CreateUserView.as_view(),
        name="user-create",
    ),
    path("me/", ManageUserView.as_view(), name="me"),
    path("", include(router.urls)),
]
