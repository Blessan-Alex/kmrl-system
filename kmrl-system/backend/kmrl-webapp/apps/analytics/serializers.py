"""
Serializers for analytics app
"""

from rest_framework import serializers
from .models import Analytics

class AnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for Analytics model"""
    
    class Meta:
        model = Analytics
        fields = ['id', 'metric_name', 'metric_value', 'metric_type', 'department', 'created_at']
        read_only_fields = ['id', 'created_at']
