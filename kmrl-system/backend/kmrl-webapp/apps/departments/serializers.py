"""
Serializers for departments app
"""

from rest_framework import serializers
from .models import Department

class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description', 'head', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
