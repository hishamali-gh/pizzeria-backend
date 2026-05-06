from rest_framework import serializers

from .models import CurrentSubscription
from .utils import verify_razorpay_signature


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentSubscription
        fields = ['plan']


class RazorpayOrderSerializer(serializers.Serializer):
    PLAN_CHOICES = ['BASE', 'PLUS', 'PRO']

    plan = serializers.ChoiceField(choices=PLAN_CHOICES)

    def validate_plan(self, value):
        return value.upper()


class RazorpayPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()

    plan = serializers.ChoiceField(choices=['BASE', 'PLUS', 'PRO'])

    def validate(self, data):
        if not verify_razorpay_signature(
            data['razorpay_order_id'],
            data['razorpay_payment_id'],
            data['razorpay_signature']
        ):
            raise serializers.ValidationError({"payment": "Cryptographic signature mismatch. Forgery detected."})
        
        return data
