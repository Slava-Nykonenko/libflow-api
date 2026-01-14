from django.urls import path, include
from rest_framework.routers import DefaultRouter

from payments.views import (
    CancelView,
    SuccessView,
    PaymentViewSet,
    checkout_view,
    stripe_webhook,
)

router = DefaultRouter()
router.register("", PaymentViewSet, basename="payment")

app_name = "payments"

urlpatterns = [
    path("checkout/?<int:borrowing_id>/", checkout_view, name="checkout"),
    path("cancel/", CancelView.as_view(), name="cancel"),
    path(
        "success/",
        SuccessView.as_view(template_name="payments/success.html"),
        name="success",
    ),
    path("webhook/", stripe_webhook, name="webhook"),
    path("", include(router.urls)),
]
