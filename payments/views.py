from decimal import Decimal

import stripe
from django.conf import settings
from django.http import HttpResponse, HttpRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import GenericViewSet

from borrowings.models import Borrowing
from libflow_api.tasks import send_telegram_notification
from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.utils import create_stripe_session

stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(["POST", "GET"])
def checkout_view(request, borrowing_id):
    borrowing = get_object_or_404(Borrowing, id=borrowing_id, user=request.user)
    session = create_stripe_session(request, borrowing)
    return Response({"session_url": session.url}, status=status.HTTP_201_CREATED)


class SuccessView(TemplateView):
    template_name = "payments/success.html"


class CancelView(TemplateView):
    template_name = "payments/cancel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["borrowing_id"] = self.request.GET.get("borrowing_id")
        return context


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        try:
            payment = Payment.objects.get(session_id=session.id)
            payment.status = Payment.Status.PAID
            payment.save()

            message = (
                f"<b>Borrowing has been paid!</b>\n"
                f"Borrowing ID: {payment.borrowing.id}\n"
                f"User ID: {payment.borrowing.user.id}\n"
                f"Amount: {payment.amount} euro.\n"
            )
            send_telegram_notification.apply_async(args=[message])
            print(f"Payment {payment.id} marked as PAID")
        except Payment.DoesNotExist:
            print("Payment record not found for session")

    return HttpResponse(status=200)


class PaymentViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.all()
        if not self.request.user.is_staff:
            return queryset.filter(borrowing__user=self.request.user)
        return queryset
