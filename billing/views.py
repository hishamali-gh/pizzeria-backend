import razorpay

import time

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings

from .models import CurrentSubscription, SubscriptionAuditLog
from .serializers import RazorpayOrderSerializer, RazorpayPaymentSerializer


class SubscriptionUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):
        serializer = RazorpayPaymentSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        sub = CurrentSubscription.objects.get(tenant=request.tenant)
        sub.plan = serializer.validated_data.get('plan')
        sub.status = 'ACTIVE'
        sub.save()

        SubscriptionAuditLog.objects.create(
            tenant=request.tenant,
            plan=sub.plan,
            status=sub.status
        )

        return Response({"message": f"Subscription updated to {sub.plan}"})


client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class CreateRazorpayOrderAPIView(APIView):
    def post(self, request):
        serializer = RazorpayOrderSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        plan_amount_map = {
            'BASE': 299,
            'PLUS': 799,
            'PRO': 1499
        }

        plan = serializer.validated_data.get('plan')
        amount = plan_amount_map.get(plan)

        amount_in_cents = int(round(amount * 100))

        order_data = {
            'amount': amount_in_cents,
            'currency': 'INR', # INR for now. Toggle the "International Payments" option on in the Razorpay dashboard to avail USD.
            'payment_capture': 1,  # 1 means automatic capture
            'receipt': f"rcpt_{plan.lower()}_{int(time.time())}" # Industrial tracking
        }

        try:
            razorpay_order = client.order.create(data=order_data)

            return Response({
                'order': razorpay_order,
                'key_id': settings.RAZORPAY_KEY_ID
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
