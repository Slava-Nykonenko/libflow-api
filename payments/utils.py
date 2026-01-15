import stripe
from django.http import HttpRequest
from django.utils import timezone
from rest_framework.reverse import reverse
from stripe.checkout import Session

from borrowings.models import Borrowing
from payments.models import Payment


def create_stripe_session(request: HttpRequest, borrowing: Borrowing) -> Session:
    actual_return = borrowing.actual_return_date or timezone.now().date()
    total_days = max(1, (actual_return - borrowing.borrow_date).days)

    extra_days = 0
    if actual_return > borrowing.expected_return_date:
        extra_days = (actual_return - borrowing.expected_return_date).days
    amount_in_cents = int(borrowing.book.daily_fee * (total_days + extra_days) * 100)
    if amount_in_cents < 50:
        amount_in_cents = 50

    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "unit_amount": amount_in_cents,
                    "product_data": {"name": borrowing.book.title},
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=request.build_absolute_uri(reverse("payments:success"))
        + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri(reverse("payments:cancel"))
        + f"?borrowing_id={borrowing.id}",
        metadata={"borrowing_id": borrowing.id},
    )

    Payment.objects.create(
        borrowing=borrowing,
        session_id=checkout_session.id,
        session_url=checkout_session.url,
        amount=amount_in_cents / 100,
        type=Payment.Type.FINE if extra_days > 0 else Payment.Type.PAYMENT,
    )
    return checkout_session
