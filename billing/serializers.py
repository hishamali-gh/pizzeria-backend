from rest_framework import serializers

from .models import CurrentSubscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentSubscription
        fields = ['plan']
